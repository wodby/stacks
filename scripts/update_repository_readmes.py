#!/usr/bin/env python3
"""Update generated sections in public Wodby stack repository READMEs.

The aggregate README is the stack inventory. A stack is classified as a
Kubernetes system stack when any referenced service manifest has
``type: infrastructure``. Stack-specific public documentation is discovered
from the sibling ``docs`` repository.

Only content between ``GENERATED_START`` and ``GENERATED_END`` is replaced
during normal updates. Everything outside those markers is maintained by
humans and must remain byte-for-byte unchanged. Legacy READMEs require an
explicit one-time ``--migrate`` operation before normal synchronization.
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
PUBLIC_DOCS_URL = "https://wodby.com/docs/2.0/stacks/catalog"
PUBLIC_STACKS_URL = "https://wodby.com/stacks"
GENERATED_START = "<!-- wodby:generated:start -->"
GENERATED_END = "<!-- wodby:generated:end -->"

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
        raise RuntimeError(
            'service build cannot define both "boilerplates" and legacy "templates"'
        )
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
    service_repositories = repository_names(
        SERVICES_REPOSITORY / "README.md", "service-"
    )
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
                "labels": [str(label) for label in manifest.get("labels") or []],
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


def repository_display_name(
    repo_name: str, manifests: list[dict[str, Any]], readme: str
) -> str:
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


def application_summary(
    display_name: str, references: list[str], catalog: dict[str, dict[str, Any]]
) -> str:
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


def public_stack_guide_url(repo_name: str) -> str | None:
    catalog_dir = WORKSPACE / "docs" / "2.0" / "docs" / "stacks" / "catalog"
    if not catalog_dir.is_dir():
        raise RuntimeError(
            "public docs catalog not found; clone wodby/docs as the sibling docs repository"
        )
    slug = repo_name.removeprefix("stack-")
    return (
        f"{PUBLIC_DOCS_URL}/{slug}/"
        if (catalog_dir / slug / "index.md").is_file()
        else None
    )


def public_stack_url(repo_name: str) -> str:
    """Return the stable public catalog URL for a managed stack repository."""
    slug = repo_name.removeprefix("stack-")
    return f"{PUBLIC_STACKS_URL}/{slug}"


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
    for manifest, path in zip(manifests, manifest_paths, strict=True):
        if plural:
            lines.extend(
                [f"### {manifest.get('title', manifest.get('name', 'Stack'))}", ""]
            )
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
            state += (
                "; disabled by default"
                if service.get("disabled")
                else "; enabled by default"
            )
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
            lines.append(f"| {title}<br>`{local_name}` | {'; '.join(details)} |")
        relative = path.relative_to(repo_dir).as_posix()
        if relative != "stack.yml":
            lines.extend(["", f"Manifest: [`{relative}`]({relative})"])
        lines.append("")
    return "\n".join(lines).rstrip()


def marked_generated_content(content: str) -> str:
    """Wrap generated content in the stable README ownership markers."""
    return f"{GENERATED_START}\n\n{content.strip()}\n\n{GENERATED_END}"


def generated_marker_span(readme: str) -> tuple[int, int] | None:
    """Return the generated marker span and reject ambiguous marker layouts."""
    start_matches = list(
        re.finditer(rf"^{re.escape(GENERATED_START)}[ \t]*$", readme, re.MULTILINE)
    )
    end_matches = list(
        re.finditer(rf"^{re.escape(GENERATED_END)}[ \t]*$", readme, re.MULTILINE)
    )
    if not start_matches and not end_matches:
        return None
    if len(start_matches) != 1 or len(end_matches) != 1:
        raise RuntimeError("README must contain exactly one generated marker pair")
    start = start_matches[0]
    end = end_matches[0]
    if start.end() >= end.start():
        raise RuntimeError("README generated markers are out of order")
    return start.start(), end.end()


def replace_generated_content(readme: str, content: str) -> str:
    """Replace only the marked block while preserving all manual bytes."""
    span = generated_marker_span(readme)
    if span is None:
        raise RuntimeError("README has no generated markers; run with --migrate first")
    start, end = span
    return readme[:start] + marked_generated_content(content) + readme[end:]


def remove_legacy_validation_footer(readme: str) -> str:
    """Remove the old generated validation footer during one-time migration."""
    footer = re.compile(
        r"\n(?:Wodby platform maintainers can validate the manifests with:|"
        r"Validate the manifests? with:)\n\n"
        r"```bash\n.*?\n```"
        r"(?:\n\nSee the \[stack manifest reference\].*?)?\n?$",
        re.DOTALL,
    )
    return footer.sub("", readme).rstrip()


def migrate_legacy_readme(
    readme: str,
    content: str,
    *,
    infrastructure: bool,
) -> str:
    """Insert markers once while preserving legacy manual documentation.

    The old renderer owned the link, boilerplate, service-definition, and
    component-table region. Known generic validation and infrastructure tails
    are removed because their dynamic content now lives inside the marked
    contract. Other leading and trailing prose is retained.
    """
    if generated_marker_span(readme) is not None:
        return replace_generated_content(readme, content)

    link_start = re.search(
        r"^- \[(?:[^\]]+ stack on Wodby|Browse Wodby application stacks|"
        r"Wodby Kubernetes platform)\]\(",
        readme,
        re.MULTILINE,
    )
    overview = re.search(
        r"^## (?:What's included|Stack entries)\s*$",
        readme,
        re.MULTILINE,
    )
    if bool(link_start) != bool(overview):
        raise RuntimeError(
            "legacy README generated region is incomplete; migrate it manually"
        )

    if link_start and overview:
        if link_start.start() >= overview.start():
            raise RuntimeError("legacy README generated sections are out of order")
        next_heading = re.search(r"^## ", readme[overview.end() :], re.MULTILINE)
        generated_end = (
            overview.end() + next_heading.start() if next_heading else len(readme)
        )
        prefix = readme[: link_start.start()].rstrip()
        suffix = readme[generated_end:].lstrip()
        if infrastructure and suffix.startswith("## Role in Wodby infrastructure"):
            suffix = ""
        suffix = remove_legacy_validation_footer(suffix)
    else:
        prefix = remove_legacy_validation_footer(readme)
        suffix = ""

    parts = [
        part for part in (prefix, marked_generated_content(content), suffix) if part
    ]
    return "\n\n".join(parts).rstrip() + "\n"


def validation_commands(repo_dir: Path, manifest_paths: list[Path]) -> str:
    return "\n".join(
        f"wodby stack validate-manifest {path.relative_to(repo_dir).as_posix()} --org <org-id>"
        for path in manifest_paths
    )


def generated_contract(
    *,
    repo_name: str,
    display_name: str,
    infrastructure: bool,
    repo_dir: Path,
    manifests: list[dict[str, Any]],
    manifest_paths: list[Path],
    boilerplates: list[dict[str, str]],
    sources: list[tuple[str, str]],
    guide_url: str | None,
) -> str:
    """Render the manifest-derived README content owned by automation."""
    lines = [
        "## Stack contract",
        "",
        f"- [{display_name} stack on Wodby]({public_stack_url(repo_name)})",
        (
            "- [Wodby Kubernetes platform](https://wodby.com)"
            if infrastructure
            else "- [Browse Wodby application stacks](https://wodby.com/stacks)"
        ),
    ]
    if guide_url:
        lines.append(f"- [{display_name} stack guide]({guide_url})")
    lines.extend(
        [
            "- [Wodby stack documentation](https://wodby.com/docs/2.0/stacks/)",
            "- [Stack manifest reference](https://wodby.com/docs/2.0/stacks/template/)",
        ]
    )

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
            lines.append(f"- [{boilerplate['title']}]({boilerplate['repo']})")

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

    lines.extend(
        [
            "",
            generated_overview(repo_dir, manifests, manifest_paths),
            "",
            wrapped(
                "System services are enabled or disabled according to the cluster "
                "provider and infrastructure configuration."
                if infrastructure
                else "Enabled optional services are selected by default but can be "
                "excluded when an app is created. Disabled optional services are "
                "available but not selected by default. Required services cannot be "
                "excluded."
            ),
            "",
            (
                "## Validate the stack manifests"
                if len(manifest_paths) > 1
                else "## Validate the stack manifest"
            ),
            "",
            "```bash",
            validation_commands(repo_dir, manifest_paths),
            "```",
        ]
    )
    return "\n".join(lines)


def render_stack_readme(
    repo_name: str,
    catalog: dict[str, dict[str, Any]],
    *,
    migrate: bool = False,
) -> tuple[str, bool, str]:
    repo_dir = WORKSPACE / repo_name
    readme_path = repo_dir / "README.md"
    old_readme = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
    manifest_paths = indexed_manifest_paths(repo_dir, "stack")
    if not manifest_paths:
        raise RuntimeError(f"{repo_name}: no stack manifests found")
    manifests = [load_yaml(path) for path in manifest_paths]
    references = stack_references(manifests)
    unresolved = sorted(
        {reference for reference in references if reference not in catalog}
    )
    if unresolved:
        raise RuntimeError(
            f"{repo_name}: unresolved service references: {', '.join(unresolved)}"
        )
    infrastructure = any(
        catalog[reference]["infrastructure"] for reference in references
    )
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
    guide_url = public_stack_guide_url(repo_name)
    content = generated_contract(
        repo_name=repo_name,
        display_name=display_name,
        infrastructure=infrastructure,
        repo_dir=repo_dir,
        manifests=manifests,
        manifest_paths=manifest_paths,
        boilerplates=boilerplates,
        sources=sources,
        guide_url=guide_url,
    )

    if old_readme:
        readme = (
            migrate_legacy_readme(
                old_readme,
                content,
                infrastructure=infrastructure,
            )
            if migrate
            else replace_generated_content(old_readme, content)
        )
    else:
        if not migrate:
            raise RuntimeError(
                f"{repo_name}: README has no generated markers; run with --migrate first"
            )
        title = (
            f"# {display_name} Kubernetes system stack for Wodby"
            if infrastructure
            else f"# {display_name} application stack for Kubernetes on Wodby"
        )
        introduction = "\n\n".join(
            [
                title,
                wrapped(summary),
                wrapped(
                    f"This repository defines the Wodby stack manifests and default "
                    f"service composition for {display_name}."
                ),
            ]
        )
        readme = f"{introduction}\n\n{marked_generated_content(content)}\n"
    return readme, infrastructure, display_name


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--check", action="store_true", help="Fail if a README is out of date"
    )
    mode.add_argument(
        "--write", action="store_true", help="Write rendered README files"
    )
    mode.add_argument(
        "--migrate",
        action="store_true",
        help="Insert ownership markers into legacy READMEs once",
    )
    parser.add_argument(
        "repositories", nargs="*", help="Optional stack repository names"
    )
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
        readme, infrastructure, _ = render_stack_readme(
            repo_name,
            catalog,
            migrate=args.migrate,
        )
        infrastructure_count += int(infrastructure)
        readme_path = WORKSPACE / repo_name / "README.md"
        current = (
            readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
        )
        if current == readme:
            continue
        changed.append(repo_name)
        if args.write or args.migrate:
            readme_path.write_text(readme, encoding="utf-8")

    action = "migrated" if args.migrate else "updated" if args.write else "out of date"
    for repo_name in changed:
        print(f"{repo_name}: README {action}")
    print(
        f"checked {len(repositories)} stack repositories; "
        f"{infrastructure_count} infrastructure; {len(changed)} {action}"
    )
    return 1 if args.check and changed else 0


if __name__ == "__main__":
    sys.exit(main())
