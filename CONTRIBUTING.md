# Contributing to the MLOps Platforms Directory

Thank you for helping keep this directory accurate and unbiased!

## Adding or Updating a Platform

1. Edit `tools.json` at the repository root.
2. Sync the static web dataset:
   ```bash
   cp tools.json docs/tools.json
   ```
3. Validate the schema and run the test suite:
   ```bash
   python3 mlops_advisor.py --validate
   python3 -m unittest discover -s tests -v
   ```
4. Open a Pull Request describing the change (and linking to official docs or release notes for verification).

## `tools.json` Schema Reference

Each entry in `tools` must include:
- `id` (string, kebab-case, unique)
- `name` (string)
- `tagline` (string, concise one-line summary)
- `category` (string)
- `jobs` (non-empty array from: `end-to-end-oss`, `experiment-tracking`, `kubernetes-mlops`, `managed-cloud`, `model-serving`, `llmops`, `regulated-enterprise`)
- `license_type` (`"open-source"` or `"commercial"`)
- `license_name` (string, e.g., `"Apache-2.0"`, `"Commercial"`)
- `deployment` (non-empty array from: `local-cli`, `self-hosted`, `kubernetes`, `cloud-saas`, `vpc-onprem`)
- `pricing` (string)
- `website` (URL string)
- `github` (URL string or `null`)
- `github_stars_approx` (string or `null`)
- `capabilities` (object with booleans: `experiment_tracking`, `pipeline_orchestration`, `model_registry`, `model_serving`, `feature_store`, `data_versioning`, `kubernetes_native`, `llmops_support`)
- `compliance` (array of strings, e.g. `["SOC 2", "HIPAA"]`)
- `best_for` (string)
