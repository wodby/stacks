import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import update_repository_readmes as readme_generator  # noqa: E402
from update_repository_readmes import (  # noqa: E402
    GENERATED_END,
    GENERATED_START,
    build_boilerplates,
    public_stack_guide_url,
    public_stack_url,
    render_stack_readme,
)


class ReadmeGeneratorTest(unittest.TestCase):
    def render_demo(
        self,
        readme: str,
        *,
        migrate: bool = False,
        guide: bool = True,
        infrastructure: bool = False,
    ) -> tuple[str, Path]:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        workspace = Path(directory.name)
        catalog_dir = workspace / "docs/2.0/docs/stacks/catalog"
        catalog_dir.mkdir(parents=True)
        if guide:
            guide_path = catalog_dir / "demo/index.md"
            guide_path.parent.mkdir(parents=True)
            guide_path.write_text("# Demo\n", encoding="utf-8")
        repo_dir = workspace / "stack-demo"
        repo_dir.mkdir()
        (repo_dir / "stack.yml").write_text(
            """\
name: demo
title: Demo
services:
- name: php
  title: PHP
  service: php
  required: true
""",
            encoding="utf-8",
        )
        (repo_dir / "README.md").write_text(readme, encoding="utf-8")
        catalog = {
            "php": {
                "repo": "service-php",
                "title": "PHP",
                "type": "infrastructure" if infrastructure else "service",
                "labels": [],
                "infrastructure": infrastructure,
                "boilerplates": [],
            }
        }
        with mock.patch.object(readme_generator, "WORKSPACE", workspace):
            rendered, _, _ = render_stack_readme(
                "stack-demo",
                catalog,
                migrate=migrate,
            )
        return rendered, repo_dir

    def test_public_stack_url_uses_repository_slug(self) -> None:
        self.assertEqual(
            public_stack_url("stack-drupal"),
            "https://wodby.com/stacks/drupal",
        )

    def test_reads_canonical_boilerplates(self) -> None:
        boilerplates = [{"name": "demo"}]

        self.assertEqual(
            build_boilerplates({"build": {"boilerplates": boilerplates}}),
            boilerplates,
        )

    def test_reads_legacy_templates_during_rollout(self) -> None:
        templates = [{"name": "demo"}]

        self.assertEqual(
            build_boilerplates({"build": {"templates": templates}}),
            templates,
        )

    def test_rejects_canonical_and_legacy_fields_together(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "cannot define both"):
            build_boilerplates({"build": {"boilerplates": [], "templates": []}})

    def test_discovers_public_stack_guide(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            guide = workspace / "docs/2.0/docs/stacks/catalog/demo/index.md"
            guide.parent.mkdir(parents=True)
            guide.write_text("# Demo\n", encoding="utf-8")

            with mock.patch.object(readme_generator, "WORKSPACE", workspace):
                self.assertEqual(
                    public_stack_guide_url("stack-demo"),
                    "https://wodby.com/docs/2.0/stacks/catalog/demo/",
                )

    def test_marked_update_preserves_manual_bytes_and_replaces_stale_contract(
        self,
    ) -> None:
        prefix = "# Demo stack\n\nManual introduction.\n\n> Keep this warning.\n\n"
        suffix = "\n\n## Operations\n\nKeep this repository-specific guidance.\n"
        readme = (
            prefix
            + GENERATED_START
            + "\n\nStale Tailscale component.\n\n"
            + GENERATED_END
            + suffix
        )

        rendered, _ = self.render_demo(readme)

        self.assertTrue(rendered.startswith(prefix + GENERATED_START))
        self.assertTrue(rendered.endswith(GENERATED_END + suffix))
        self.assertNotIn("Tailscale", rendered)
        self.assertIn("| PHP<br>`php` | required; enabled by default |", rendered)
        self.assertIn("## Operations", rendered)

    def test_migration_preserves_warning_and_custom_sections(self) -> None:
        readme = """\
# Demo stack

Manual introduction.

> Keep this warning.

This repository defines the stack.

- [Browse Wodby application stacks](https://wodby.com/stacks)
- [Wodby stack documentation](https://wodby.com/docs/2.0/stacks/)

## Service definitions

- [Stale service](https://github.com/wodby/service-stale)

## What's included

Stale component table.

## Deploy this stack

Keep this deployment guidance.

## Connect Drupal to Solr

Keep this repository-specific guidance.

Validate the manifests with:

```bash
wodby stack validate-manifest old.yml --org <org-id>
```

See the [stack manifest reference](https://wodby.com/docs/2.0/stacks/template/).
"""

        rendered, repo_dir = self.render_demo(readme, migrate=True)

        self.assertIn("> Keep this warning.", rendered)
        self.assertIn("## Connect Drupal to Solr", rendered)
        self.assertIn("Keep this repository-specific guidance.", rendered)
        self.assertNotIn("Stale service", rendered)
        self.assertNotIn("Stale component table", rendered)
        self.assertNotIn("old.yml", rendered)
        self.assertEqual(rendered.count(GENERATED_START), 1)
        self.assertEqual(rendered.count(GENERATED_END), 1)
        self.assertIn(
            "- [Demo stack guide](https://wodby.com/docs/2.0/stacks/catalog/demo/)",
            rendered,
        )

        (repo_dir / "README.md").write_text(rendered, encoding="utf-8")
        with mock.patch.object(readme_generator, "WORKSPACE", repo_dir.parent):
            rerendered, _, _ = render_stack_readme(
                "stack-demo",
                {
                    "php": {
                        "repo": "service-php",
                        "title": "PHP",
                        "type": "service",
                        "labels": [],
                        "infrastructure": False,
                        "boilerplates": [],
                    }
                },
            )
        self.assertEqual(rerendered, rendered)

    def test_migration_preserves_fully_manual_introduction(self) -> None:
        readme = """\
# Distribution Registry stack

Deploy a private registry with tailored storage and authentication guidance.

Validate the manifest with:

```bash
wodby stack validate-manifest stack.yml --org <org-id>
```
"""

        rendered, _ = self.render_demo(readme, migrate=True)

        self.assertIn(
            "Deploy a private registry with tailored storage and authentication guidance.",
            rendered,
        )
        self.assertEqual(rendered.count("wodby stack validate-manifest"), 1)
        self.assertIn(GENERATED_START, rendered)

    def test_migration_drops_known_generic_infrastructure_tail(self) -> None:
        readme = """\
# Demo Kubernetes system stack for Wodby

Manual infrastructure introduction.

- [Wodby Kubernetes platform](https://wodby.com)

## System service definitions

- [PHP system service](https://github.com/wodby/service-php)

## What's included

Old table.

## Role in Wodby infrastructure

Old generic role text.

## Platform maintenance

Old generic maintenance text.
"""

        rendered, _ = self.render_demo(
            readme,
            migrate=True,
            infrastructure=True,
        )

        self.assertIn("Manual infrastructure introduction.", rendered)
        self.assertNotIn("## Role in Wodby infrastructure", rendered)
        self.assertNotIn("## Platform maintenance", rendered)
        self.assertIn("## System service definitions", rendered)

    def test_normal_update_requires_markers(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "run with --migrate"):
            self.render_demo("# Demo\n")

    def test_rejects_duplicate_or_unbalanced_markers(self) -> None:
        for readme in (
            f"# Demo\n\n{GENERATED_START}\n\n{GENERATED_START}\n\n{GENERATED_END}\n",
            f"# Demo\n\n{GENERATED_END}\n",
            f"# Demo\n\n{GENERATED_END}\n\n{GENERATED_START}\n",
        ):
            with self.subTest(readme=readme):
                with self.assertRaisesRegex(RuntimeError, "marker"):
                    self.render_demo(readme)

    def test_migration_rejects_incomplete_legacy_generated_region(self) -> None:
        readme = """\
# Demo

- [Browse Wodby application stacks](https://wodby.com/stacks)
"""

        with self.assertRaisesRegex(RuntimeError, "incomplete"):
            self.render_demo(readme, migrate=True)

    def test_render_without_stack_specific_guide(self) -> None:
        readme = f"# Demo\n\n{GENERATED_START}\n\nOld.\n\n{GENERATED_END}\n"

        rendered, _ = self.render_demo(readme, guide=False)

        self.assertNotIn("stack guide](", rendered)


if __name__ == "__main__":
    unittest.main()
