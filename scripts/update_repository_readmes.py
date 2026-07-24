#!/usr/bin/env python3
"""Render README files for the public Wodby stack repositories.

The aggregate README is the stack inventory. A stack is classified as a
Kubernetes system stack when any referenced service manifest has
``type: infrastructure``.
"""

from __future__ import annotations

import argparse
import re
import sys
import textwrap
from pathlib import Path
from typing import Any

import yaml


STACKS_REPOSITORY = Path(__file__).resolve().parents[1]
WORKSPACE = STACKS_REPOSITORY.parent
SERVICES_REPOSITORY = WORKSPACE / "services"

INFRASTRUCTURE_SUMMARIES = {
    "stack-aws-lb-controller": (
        "AWS Load Balancer Controller supplies AWS load-balancer integration "
        "for Wodby Kubernetes clusters that require the AWS controller."
    ),
    "stack-envoy-gateway": (
        "Envoy Gateway supplies the Kubernetes Gateway API and ingress control "
        "plane for Wodby clusters configured to use Envoy Gateway."
    ),
    "stack-frpc": (
        "FRPC supplies tunneling infrastructure for Wodby cluster networking "
        "configurations that require an FRP client."
    ),
    "stack-metrics": (
        "Metrics supplies Kubernetes resource and object-state metrics for "
        "Wodby cluster operations."
    ),
    "stack-monitoring": (
        "Monitoring supplies node, workload, and Kubernetes object telemetry "
        "for Wodby cluster observability."
    ),
}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        value = yaml.safe_load(source)
    return value if isinstance(value, dict) else {}


def repository_names(index_path: Path, prefix: str) -> list[str]:
    pattern = re.compile(rf"https://github\.com/wodby/({re.escape(prefix)}[a-z0-9-]+)")
    return sorted(set(pattern.findall(index_path.read_text(encoding="utf-8"))))


def indexed_manifest_paths(repo_dir: Path, entity: str) -> list[Path]:
    root_manifest = repo_dir / f"{entity}.yml"
    if root_manifest.exists():
        return [root_manifest]
    index_path = repo_dir / "index.yml"
    if not index_path.exists():
        return []

    result: list[Path] = []
    for entry in load_yaml(index_path).get(f"{entity}s", []):
        name = entry if isinstance(entry, (str, int)) else entry.get("name", "")
        path = repo_dir / str(name) / f"{entity}.yml"
        if path.exists():
            result.append(path)
    return result


def build_boilerplates(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    build = manifest.get("build") or {}
    boilerplates = build.get("boilerplates")
    templates = build.get("templates")
    if boilerplates is not None and templates is not None:
        raise RuntimeError('service build cannot define both "boilerplates" and legacy "templates"')
    value = boilerplates if boilerplates is not None else templates
    return value if isinstance(value, list) else []


def wrapped(value: str) -> str:
    links: list[str] = []

    def preserve_link(match: re.Match[str]) -> str:
        links.append(match.group(0))
        return f"WODBYMARKDOWNLINK{len(links) - 1}"

    protected = re.sub(r"\[[^\]]+\]\([^)]+\)", preserve_link, value)
    result = textwrap.fill(
        protected,
        width=79,
        break_long_words=False,
        break_on_hyphens=False,
    )
    for index in range(len(links) - 1, -1, -1):
        link = links[index]
        result = result.replace(f"WODBYMARKDOWNLINK{index}", link)
    return result


def service_catalog() -> dict[str, dict[str, Any]]:
    catalog: dict[str, dict[str, Any]] = {}
    service_repositories = repository_names(SERVICES_REPOSITORY / "README.md", "service-")
    for repo_name in service_repositories:
        repo_dir = WORKSPACE / repo_name
        for manifest_path in indexed_manifest_paths(repo_dir, "service"):
            manifest = load_yaml(manifest_path)
            name = str(manifest.get("name", "")).strip()
            if not name:
                continue
            boilerplates = []
            for boilerplate in build_boilerplates(manifest):
                repo = str(boilerplate.get("repo", "")).strip()
                if not repo:
                    continue
                boilerplates.append(
                    {
                        "title": str(
                            boilerplate.get("title")
                            or boilerplate.get("name")
                            or "Starter boilerplate"
                        ),
                        "repo": repo,
                    }
                )
            catalog[name] = {
                "repo": repo_name,
                "title": str(manifest.get("title") or name),
                "type": str(manifest.get("type") or "service"),
                "labels": [
                    str(label) for label in manifest.get("labels") or []
                ],
                "infrastructure": manifest.get("type") == "infrastructure",
                "boilerplates": boilerplates,
            }
    return catalog


def stack_references(manifests: list[dict[str, Any]]) -> list[str]:
    return [
        str(service.get("service", "")).split("@", 1)[0]
        for manifest in manifests
        for service in manifest.get("services") or []
        if service.get("service")
    ]


def repository_display_name(repo_name: str, manifests: list[dict[str, Any]], readme: str) -> str:
    heading = readme.splitlines()[0].removeprefix("# ").strip() if readme else ""
    for suffix in (
        " Kubernetes system stack for Wodby",
        " application stack for Kubernetes on Wodby",
        " stacks for Wodby",
        " stack for Wodby",
        " stack",
    ):
        if heading.lower().endswith(suffix.lower()):
            heading = heading[: -len(suffix)].strip()
            break
    if len(manifests) == 1:
        manifest_title = str(manifests[0].get("title", "")).strip()
        if manifest_title:
            return manifest_title
    if heading and not heading.startswith("stack-"):
        return heading
    return repo_name.removeprefix("stack-").replace("-", " ").title()


def application_summary(display_name: str, references: list[str], catalog: dict[str, dict[str, Any]]) -> str:
    del references, catalog
    return f"Deploy {display_name} applications on Kubernetes with Wodby."


def starter_boilerplates(
    references: list[str],
    catalog: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    boilerplates: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for reference in references:
        for boilerplate in catalog.get(reference, {}).get("boilerplates", []):
            key = (boilerplate["title"], boilerplate["repo"])
            if key in seen:
                continue
            seen.add(key)
            boilerplates.append(boilerplate)
    return boilerplates


def service_sources(
    references: list[str],
    catalog: dict[str, dict[str, Any]],
) -> list[tuple[str, str]]:
    sources: list[tuple[str, str]] = []
    seen: set[str] = set()
    for reference in references:
        service = catalog.get(reference)
        if not service or service["repo"] in seen:
            continue
        seen.add(service["repo"])
        sources.append((service["title"], service["repo"]))
    return sources


def format_versions(service: dict[str, Any]) -> str:
    versions = service.get("versions") or []
    if not versions:
        return ""
    values = []
    for version in versions:
        name = str(version.get("name") or version.get("version") or "").strip()
        if not name:
            continue
        values.append(f"`{name}`" + (" by default" if version.get("default") else ""))
    return ", ".join(values)


def format_volumes(service: dict[str, Any]) -> str:
    values = []
    for volume in service.get("volumes") or []:
        value = f"`{volume.get('name', 'volume')}`"
        if volume.get("size") is not None:
            value += f" {volume['size']} GB"
        values.append(value)
    return ", ".join(values)


def format_links(service: dict[str, Any]) -> str:
    return ", ".join(
        f"`{link.get('name', 'link')}` → `{link.get('service', '')}`"
        for link in service.get("links") or []
    )


def generated_overview(
    repo_dir: Path,
    manifests: list[dict[str, Any]],
    manifest_paths: list[Path],
) -> str:
    plural = len(manifests) > 1
    lines = ["## Stack entries" if plural else "## What's included", ""]
    for manifest, path in zip(manifests, manifest_paths):
        if plural:
            lines.extend([f"### {manifest.get('title', manifest.get('name', 'Stack'))}", ""])
        lines.extend(
            [
                "| Component / service | Default configuration |",
                "| --- | --- |",
            ]
        )
        for service in manifest.get("services") or []:
            title = str(service.get("title") or service.get("name") or "Service")
            reference = str(service.get("service", ""))
            local_name = str(service.get("name", reference))
            state = "required" if service.get("required") else "optional"
            state += "; disabled by default" if service.get("disabled") else "; enabled by default"
            details = [state]
            versions = format_versions(service)
            volumes = format_volumes(service)
            links = format_links(service)
            if versions:
                details.append(f"versions: {versions}")
            if volumes:
                details.append(f"volumes: {volumes}")
            if links:
                details.append(f"links: {links}")
            lines.append(
                f"| {title}<br>`{local_name}` | {'; '.join(details)} |"
            )
        relative = path.relative_to(repo_dir).as_posix()
        if relative != "stack.yml":
            lines.extend(["", f"Manifest: [`{relative}`]({relative})"])
        lines.append("")
    return "\n".join(lines).rstrip()


def preserved_overview(readme: str, infrastructure: bool) -> str | None:
    start = re.search(r"^## (?:What's included|Stack entries)\s*$", readme, re.MULTILINE)
    if not start:
        return None
    end = re.search(
        r"^## (?:Use this stack|Deploy this stack|Role in Wodby infrastructure)\s*$",
        readme[start.end() :],
        re.MULTILINE,
    )
    if not end:
        overview = readme[start.start() :].strip()
    else:
        overview = readme[start.start() : start.end() + end.start()].strip()
    if infrastructure:
        overview = re.sub(
            r"\nEnabled optional services are selected by default.*?"
            r"Required services cannot be excluded\.\n?",
            "\n"
            + wrapped(
                "System services are enabled or disabled according to the cluster "
                "provider and infrastructure configuration."
            )
            + "\n",
            overview,
            flags=re.DOTALL,
        )
        overview = re.sub(
            r"System services are enabled or disabled according to the cluster "
            r"provider and infrastructure configuration\.",
            wrapped(
                "System services are enabled or disabled according to the cluster "
                "provider and infrastructure configuration."
            ),
            overview,
        )
    return overview


def validation_commands(repo_dir: Path, manifest_paths: list[Path]) -> str:
    return "\n".join(
        f"wodby stack validate-manifest {path.relative_to(repo_dir).as_posix()} --org <org-id>"
        for path in manifest_paths
    )


def render_stack_readme(
    repo_name: str,
    catalog: dict[str, dict[str, Any]],
) -> tuple[str, bool, str]:
    repo_dir = WORKSPACE / repo_name
    readme_path = repo_dir / "README.md"
    old_readme = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
    manifest_paths = indexed_manifest_paths(repo_dir, "stack")
    if not manifest_paths:
        raise RuntimeError(f"{repo_name}: no stack manifests found")
    manifests = [load_yaml(path) for path in manifest_paths]
    references = stack_references(manifests)
    unresolved = sorted({reference for reference in references if reference not in catalog})
    if unresolved:
        raise RuntimeError(
            f"{repo_name}: unresolved service references: {', '.join(unresolved)}"
        )
    infrastructure = any(catalog[reference]["infrastructure"] for reference in references)
    display_name = repository_display_name(repo_name, manifests, old_readme)
    summary = (
        INFRASTRUCTURE_SUMMARIES.get(
            repo_name,
            f"{display_name} supplies Kubernetes system infrastructure for Wodby clusters.",
        )
        if infrastructure
        else application_summary(display_name, references, catalog)
    )
    boilerplates = starter_boilerplates(references, catalog)
    sources = service_sources(references, catalog)
    overview = preserved_overview(old_readme, infrastructure) or generated_overview(
        repo_dir, manifests, manifest_paths
    )

    title = (
        f"# {display_name} Kubernetes system stack for Wodby"
        if infrastructure
        else f"# {display_name} application stack for Kubernetes on Wodby"
    )
    lines = [
        title,
        "",
        wrapped(summary),
        "",
        wrapped(
            f"This repository defines the Wodby stack manifests and default "
            f"service composition for {display_name}."
        ),
        "",
        (
            "- [Wodby Kubernetes platform](https://wodby.com)"
            if infrastructure
            else "- [Browse Wodby application stacks](https://wodby.com/stacks)"
        ),
        "- [Wodby stack documentation](https://wodby.com/docs/2.0/stacks/)",
        "- [Stack manifest reference](https://wodby.com/docs/2.0/stacks/template/)",
    ]

    if boilerplates and not infrastructure:
        lines.extend(["", "## Start from a boilerplate", ""])
        lines.append(
            wrapped(
                "Use one of the compatible boilerplates exposed by this stack's "
                "services to start with Wodby CI build configuration:"
            )
        )
        lines.append("")
        for boilerplate in boilerplates:
            lines.append(
                f"- [{boilerplate['title']}]({boilerplate['repo']})"
            )

    if sources:
        heading = (
            "## System service definitions"
            if infrastructure
            else "## Service definitions"
        )
        lines.extend(["", heading, ""])
        for service_title, service_repo in sources:
            role = "system service" if infrastructure else "service"
            lines.append(
                f"- [{service_title} {role}](https://github.com/wodby/{service_repo})"
            )

    lines.extend(["", overview, ""])
    commands = validation_commands(repo_dir, manifest_paths)

    if infrastructure:
        lines.extend(
            [
                "## Role in Wodby infrastructure",
                "",
                wrapped(
                    "Wodby installs this stack as a cluster-owned system app when it "
                    "is required by the Kubernetes provider or selected infrastructure "
                    "configuration. It is not a template for user-deployed applications."
                ),
                "",
                wrapped(
                    "Installation order, enabled services, and settings can vary by "
                    "cluster type. Wodby coordinates its lifecycle with cluster "
                    "provisioning and infrastructure upgrades."
                ),
                "",
                "## Platform maintenance",
                "",
                wrapped(
                    "Changes can affect existing clusters. Preserve stack service names "
                    "and service references unless the backend provisioning and upgrade "
                    "paths are updated at the same time."
                ),
                "",
                "Wodby platform maintainers can validate the manifests with:",
            ]
        )
    else:
        starter_links = ", ".join(
            f"[{boilerplate['title']}]({boilerplate['repo']})"
            for boilerplate in boilerplates
        )
        start_sentence = (
            f"Start from {starter_links}, or connect your own compatible source repository."
            if starter_links
            else "Add this stack from the Wodby catalog, then configure its enabled services and integrations."
        )
        lines.extend(
            [
                "## Deploy this stack",
                "",
                wrapped(start_sentence),
                "",
                wrapped(
                    "Review service versions, storage, links, and optional components "
                    "when creating the application. The same stack can be reused across "
                    "development, staging, and production environments."
                ),
                "",
                "## Maintain a custom version",
                "",
                "1. Fork this repository.",
                "2. Edit the stack manifest.",
                "3. Import the repository as a "
                "[Git-backed stack](https://wodby.com/docs/2.0/stacks/create/#create-a-git-backed-stack).",
                "",
                wrapped(
                    "When replacing or renaming a stack service, update every related "
                    "link target and derivative reference. Stack-local names and "
                    "referenced service names are distinct identifiers."
                ),
                "",
                "Validate the manifests with:",
            ]
        )

    lines.extend(
        [
            "",
            "```bash",
            commands,
            "```",
            "",
            (
                "See the [stack manifest "
                "reference](https://wodby.com/docs/2.0/stacks/template/) and the "
                "[managed services index](https://github.com/wodby/services)."
            ),
            "",
        ]
    )
    return "\n".join(lines), infrastructure, display_name


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Fail if a README is out of date")
    mode.add_argument("--write", action="store_true", help="Write rendered README files")
    parser.add_argument("repositories", nargs="*", help="Optional stack repository names")
    args = parser.parse_args()

    available = repository_names(STACKS_REPOSITORY / "README.md", "stack-")
    repositories = args.repositories or available
    unknown = sorted(set(repositories) - set(available))
    if unknown:
        parser.error(f"repositories are not in the managed index: {', '.join(unknown)}")

    catalog = service_catalog()
    changed: list[str] = []
    infrastructure_count = 0
    for repo_name in repositories:
        readme, infrastructure, _ = render_stack_readme(repo_name, catalog)
        infrastructure_count += int(infrastructure)
        readme_path = WORKSPACE / repo_name / "README.md"
        current = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
        if current == readme:
            continue
        changed.append(repo_name)
        if args.write:
            readme_path.write_text(readme, encoding="utf-8")

    action = "updated" if args.write else "out of date"
    for repo_name in changed:
        print(f"{repo_name}: README {action}")
    print(
        f"checked {len(repositories)} stack repositories; "
        f"{infrastructure_count} infrastructure; {len(changed)} {action}"
    )
    return 1 if args.check and changed else 0


if __name__ == "__main__":
    sys.exit(main())
