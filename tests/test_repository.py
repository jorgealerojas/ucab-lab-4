from __future__ import annotations

import os
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepositoryContractTests(unittest.TestCase):
    def test_required_material_exists(self) -> None:
        required = [
            "README.md",
            "LAB_GUIDE.md",
            "TROUBLESHOOTING.md",
            "evidence/evidence-template.md",
            "infra/lab-stack.yaml",
            "pyproject.toml",
            "scripts/deploy-lab.sh",
            "scripts/cleanup-lab.sh",
        ]
        missing = [path for path in required if not (ROOT / path).is_file()]
        self.assertEqual(missing, [])

    def test_scripts_are_executable(self) -> None:
        for path in (ROOT / "scripts").iterdir():
            if path.suffix in {".sh", ".py"}:
                with self.subTest(path=path.name):
                    self.assertTrue(os.access(path, os.X_OK), f"{path} is not executable")

    def test_documented_script_paths_exist(self) -> None:
        documents = [ROOT / "README.md", ROOT / "LAB_GUIDE.md", ROOT / "TROUBLESHOOTING.md"]
        referenced: set[str] = set()
        for document in documents:
            text = document.read_text(encoding="utf-8")
            referenced.update(re.findall(r"(?:\./)?(scripts/[a-z0-9_.-]+(?:\.sh|\.py))", text))
        missing = sorted(path for path in referenced if not (ROOT / path).is_file())
        self.assertEqual(missing, [])

    def test_template_contains_safety_and_learning_controls(self) -> None:
        template = (ROOT / "infra/lab-stack.yaml").read_text(encoding="utf-8")
        required_fragments = [
            "HttpTokens: required",
            "AuthorizationType: AWS_IAM",
            "FunctionResponseTypes:",
            "ReportBatchItemFailures",
            "BillingMode: PAY_PER_REQUEST",
            "AmazonSSMManagedInstanceCore",
            "RetentionInDays: 1",
            "SqsManagedSseEnabled: true",
            "python3.12 -m venv",
        ]
        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, template)
        self.assertNotIn("SecurityGroupIngress:", template)
        self.assertNotRegex(template, r"(?m)^\s*Action:\s*[\"']?\*[\"']?\s*$")

    def test_duration_is_exactly_105_minutes(self) -> None:
        guide = (ROOT / "LAB_GUIDE.md").read_text(encoding="utf-8")
        ranges = re.findall(r"^## (\d+)–(\d+) min", guide, flags=re.MULTILINE)
        self.assertEqual(
            [(int(start), int(end)) for start, end in ranges],
            [(0, 8), (8, 20), (20, 32), (32, 47), (47, 62), (62, 75), (75, 90), (90, 98), (98, 105)],
        )

    def test_lab_scope_is_explicit(self) -> None:
        guide = (ROOT / "LAB_GUIDE.md").read_text(encoding="utf-8").lower()
        for model in [
            "iaas",
            "paas",
            "data as a service",
            "faas",
        ]:
            with self.subTest(model=model):
                self.assertIn(model, guide)

if __name__ == "__main__":
    unittest.main()
