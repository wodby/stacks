import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from update_repository_readmes import build_boilerplates  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
