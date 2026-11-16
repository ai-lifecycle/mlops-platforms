import json
import unittest
from pathlib import Path

import mlops_advisor


class TestMlopsAdvisor(unittest.TestCase):
    def setUp(self) -> None:
        self.dataset = mlops_advisor.load_dataset()
        self.tools = self.dataset["tools"]

    def test_validate_dataset(self) -> None:
        errors = mlops_advisor.validate_dataset()
        self.assertEqual(errors, [], f"Validation errors: {errors}")

    def test_filter_open_source_k8s(self) -> None:
        results = mlops_advisor.filter_tools(
            self.tools,
            license_type="open-source",
            capabilities=["kubernetes_native"],
        )
        ids = {t["id"] for t in results}
        self.assertIn("kubeflow", ids)
        self.assertIn("kserve", ids)
        self.assertNotIn("aws-sagemaker", ids)

    def test_filter_compliance_hipaa(self) -> None:
        results = mlops_advisor.filter_tools(self.tools, compliance="HIPAA")
        ids = {t["id"] for t in results}
        self.assertIn("aws-sagemaker", ids)
        self.assertIn("weights-and-biases", ids)
        self.assertNotIn("mlflow", ids)

    def test_recommend_free_llmops(self) -> None:
        recs = mlops_advisor.recommend_tools(
            self.tools,
            workflow="llmops",
            budget="free",
            llmops=True,
            top_n=5,
        )
        self.assertEqual(len(recs), 5)
        self.assertTrue(all(r["capabilities"]["llmops_support"] for r in recs[:3]))

    def test_cli_compare_json(self) -> None:
        from io import StringIO
        from contextlib import redirect_stdout

        buf = StringIO()
        with redirect_stdout(buf):
            rc = mlops_advisor.main(["--compare", "mlflow", "kubeflow", "--json"])
        self.assertEqual(rc, 0)
        parsed = json.loads(buf.getvalue())
        self.assertEqual([p["id"] for p in parsed], ["mlflow", "kubeflow"])


if __name__ == "__main__":
    unittest.main()
