import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import update_repository_readmes as readme_generator  # noqa: E402
from update_repository_readmes import (  # noqa: E402
    build_boilerplates,
    public_stack_guide_url,
    render_stack_readme,
)


class BuildBoilerplatesTest(unittest.TestCase):
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
            build_boilerplates(
                {"build": {"boilerplates": [], "templates": []}}
            )

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

    def test_render_links_public_guide_and_drops_embedded_article(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            guide = workspace / "docs/2.0/docs/stacks/catalog/demo/index.md"
            guide.parent.mkdir(parents=True)
            guide.write_text("# Demo\n", encoding="utf-8")
            repo_dir = workspace / "stack-demo"
            repo_dir.mkdir()
            (repo_dir / "stack.yml").write_text(
                """\
name: demo
title: Demo
services:
- name: php
  service: php
""",
                encoding="utf-8",
            )
            (repo_dir / "README.md").write_text(
                """\
# Demo application stack for Kubernetes on Wodby

## What's included

Existing overview.

## Deploy this stack

Generated deployment guidance.

## Connect Drupal to Solr

Keep this repository-specific guidance.

## Maintain a custom version
""",
                encoding="utf-8",
            )
            catalog = {
                "php": {
                    "repo": "service-php",
                    "title": "PHP",
                    "type": "service",
                    "labels": [],
                    "infrastructure": False,
                    "boilerplates": [],
                }
            }

            with mock.patch.object(readme_generator, "WORKSPACE", workspace):
                rendered, _, _ = render_stack_readme("stack-demo", catalog)

        self.assertIn(
            "- [Demo stack guide](https://wodby.com/docs/2.0/stacks/catalog/demo/)",
            rendered,
        )
        self.assertNotIn("## Connect Drupal to Solr", rendered)

    def test_render_without_stack_specific_guide(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            (workspace / "docs/2.0/docs/stacks/catalog").mkdir(parents=True)
            repo_dir = workspace / "stack-demo"
            repo_dir.mkdir()
            (repo_dir / "stack.yml").write_text(
                """\
name: demo
title: Demo
services:
- name: php
  service: php
""",
                encoding="utf-8",
            )
            catalog = {
                "php": {
                    "repo": "service-php",
                    "title": "PHP",
                    "type": "service",
                    "labels": [],
                    "infrastructure": False,
                    "boilerplates": [],
                }
            }

            with mock.patch.object(readme_generator, "WORKSPACE", workspace):
                rendered, _, _ = render_stack_readme("stack-demo", catalog)

        self.assertNotIn("stack guide](", rendered)


if __name__ == "__main__":
    unittest.main()
