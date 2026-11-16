#!/usr/bin/env python3
"""MLOps Platforms Advisor — zero-dependency CLI to filter, compare, and validate tools.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT_DIR = Path(__file__).resolve().parent
TOOLS_PATH = ROOT_DIR / "tools.json"
DOCS_TOOLS_PATH = ROOT_DIR / "docs" / "tools.json"

REQUIRED_CAPABILITIES = (
    "experiment_tracking",
    "pipeline_orchestration",
    "model_registry",
    "model_serving",
    "feature_store",
    "data_versioning",
    "kubernetes_native",
    "llmops_support",
)

VALID_LICENSE_TYPES = {"open-source", "commercial"}

VALID_JOBS = {
    "end-to-end-oss",
    "experiment-tracking",
    "kubernetes-mlops",
    "managed-cloud",
    "model-serving",
    "llmops",
    "regulated-enterprise",
}

VALID_DEPLOYMENTS = {
    "local-cli",
    "self-hosted",
    "kubernetes",
    "cloud-saas",
    "vpc-onprem",
}


def load_dataset(path: Path = TOOLS_PATH) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def validate_dataset(path: Path = TOOLS_PATH) -> List[str]:
    errors: List[str] = []
    if not path.exists():
        return [f"Dataset not found: {path}"]

    try:
        data = load_dataset(path)
    except json.JSONDecodeError as exc:
        return [f"Invalid JSON in {path}: {exc}"]

    if not isinstance(data, dict):
        return ["Top-level JSON value must be an object."]

    for key in ("schema_version", "last_verified", "tools"):
        if key not in data:
            errors.append(f"Missing top-level key: {key}")

    tools = data.get("tools")
    if not isinstance(tools, list) or not tools:
        errors.append("'tools' must be a non-empty list.")
        return errors

    seen_ids = set()
    for idx, tool in enumerate(tools):
        prefix = f"tools[{idx}]"
        if not isinstance(tool, dict):
            errors.append(f"{prefix} must be an object.")
            continue

        tid = tool.get("id")
        if not tid or not isinstance(tid, str):
            errors.append(f"{prefix}.id must be a non-empty string.")
        elif tid in seen_ids:
            errors.append(f"Duplicate tool id: {tid}")
        else:
            seen_ids.add(tid)

        for req_str in ("name", "tagline", "category", "license_name", "pricing", "website", "best_for"):
            val = tool.get(req_str)
            if not val or not isinstance(val, str):
                errors.append(f"{prefix}.{req_str} ({tid}) must be a non-empty string.")

        lic_type = tool.get("license_type")
        if lic_type not in VALID_LICENSE_TYPES:
            errors.append(f"{prefix}.license_type ({tid}) invalid: {lic_type}")

        jobs = tool.get("jobs")
        if not isinstance(jobs, list) or not jobs or not all(j in VALID_JOBS for j in jobs):
            errors.append(f"{prefix}.jobs ({tid}) must be a non-empty list of valid jobs.")

        deployment = tool.get("deployment")
        if not isinstance(deployment, list) or not deployment or not all(d in VALID_DEPLOYMENTS for d in deployment):
            errors.append(f"{prefix}.deployment ({tid}) must be a non-empty list of valid deployments.")

        caps = tool.get("capabilities")
        if not isinstance(caps, dict):
            errors.append(f"{prefix}.capabilities ({tid}) must be an object.")
        else:
            for cap in REQUIRED_CAPABILITIES:
                if cap not in caps or not isinstance(caps[cap], bool):
                    errors.append(f"{prefix}.capabilities.{cap} ({tid}) must be a boolean.")

        compliance = tool.get("compliance")
        if not isinstance(compliance, list) or not all(isinstance(c, str) for c in compliance):
            errors.append(f"{prefix}.compliance ({tid}) must be a list of strings.")

    if DOCS_TOOLS_PATH.exists():
        try:
            docs_data = load_dataset(DOCS_TOOLS_PATH)
            if docs_data != data:
                errors.append("docs/tools.json is out of sync with tools.json (copy tools.json to docs/tools.json).")
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid JSON in docs/tools.json: {exc}")

    return errors


def filter_tools(
    tools: List[Dict[str, Any]],
    license_type: Optional[str] = None,
    job: Optional[str] = None,
    compliance: Optional[str] = None,
    capabilities: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    result = tools
    if license_type:
        result = [t for t in result if t["license_type"] == license_type]
    if job:
        result = [t for t in result if job in t["jobs"]]
    if compliance:
        needle = compliance.lower()
        result = [t for t in result if any(needle in c.lower() for c in t["compliance"])]
    if capabilities:
        for cap in capabilities:
            result = [t for t in result if t["capabilities"].get(cap) is True]
    return result


def recommend_tools(
    tools: List[Dict[str, Any]],
    workflow: Optional[str] = None,
    budget: Optional[str] = None,
    k8s: bool = False,
    llmops: bool = False,
    regulated: bool = False,
    top_n: int = 5,
) -> List[Dict[str, Any]]:
    scored: List[tuple[int, Dict[str, Any]]] = []
    for tool in tools:
        score = 0
        if workflow and workflow in tool["jobs"]:
            score += 4
        if workflow and tool["category"] == workflow:
            score += 2
        if budget == "free":
            if tool["license_type"] == "open-source":
                score += 3
            elif "free" in tool["pricing"].lower():
                score += 1
        elif budget == "paid" and tool["license_type"] == "commercial":
            score += 2
        if k8s:
            if tool["capabilities"]["kubernetes_native"]:
                score += 2
            else:
                score -= 1
        if llmops and tool["capabilities"]["llmops_support"]:
            score += 2
        if regulated:
            if tool["compliance"]:
                score += 2
            if "regulated-enterprise" in tool["jobs"]:
                score += 2
        # Slight tie-breaker for breadth of capabilities
        score += sum(1 for v in tool["capabilities"].values() if v) // 4
        scored.append((score, tool))

    scored.sort(key=lambda item: (-item[0], item[1]["name"]))
    return [item[1] for item in scored[:top_n]]


def format_table(tools: List[Dict[str, Any]]) -> str:
    if not tools:
        return "No matching MLOps platforms found."
    lines = [
        f"{'ID':<22} {'Name':<25} {'License':<12} {'K8s':<5} {'LLMOps':<7} {'Pricing'}",
        "-" * 96,
    ]
    for t in tools:
        caps = t["capabilities"]
        k8s = "Yes" if caps["kubernetes_native"] else "No"
        llm = "Yes" if caps["llmops_support"] else "No"
        lines.append(
            f"{t['id']:<22} {t['name']:<25} {t['license_type']:<12} {k8s:<5} {llm:<7} {t['pricing']}"
        )
    return "\n".join(lines)


def format_comparison(tools: List[Dict[str, Any]]) -> str:
    if not tools:
        return "No tools found for comparison."
    col_w = 26
    header = f"{'Attribute':<24} | " + " | ".join(f"{t['name']:<{col_w}}" for t in tools)
    sep = "-" * len(header)
    rows = [header, sep]

    def add_row(label: str, values: List[str]) -> None:
        rows.append(f"{label:<24} | " + " | ".join(f"{v[:col_w]:<{col_w}}" for v in values))

    add_row("License Type", [t["license_type"] for t in tools])
    add_row("License Name", [t["license_name"] for t in tools])
    add_row("Pricing", [t["pricing"] for t in tools])
    add_row("Deployment", [", ".join(t["deployment"]) for t in tools])
    add_row("Compliance", [", ".join(t["compliance"]) or "None listed" for t in tools])

    for cap in REQUIRED_CAPABILITIES:
        label = cap.replace("_", " ").title()
        add_row(label, ["Yes" if t["capabilities"][cap] else "No" for t in tools])

    add_row("Website", [t["website"] for t in tools])
    return "\n".join(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="MLOps Platforms Advisor — filter, compare, and recommend MLOps platforms."
    )
    parser.add_argument("--validate", action="store_true", help="Validate tools.json schema and sync.")
    parser.add_argument("--list", action="store_true", help="List all platforms.")
    parser.add_argument("--license", choices=sorted(VALID_LICENSE_TYPES), help="Filter by license type.")
    parser.add_argument("--job", choices=sorted(VALID_JOBS), help="Filter by engineering job.")
    parser.add_argument("--compliance", help="Filter by compliance standard (e.g. 'SOC 2', 'HIPAA').")
    parser.add_argument("--k8s", action="store_true", help="Require Kubernetes-native support.")
    parser.add_argument("--llmops", action="store_true", help="Require LLMOps / GenAI support.")
    parser.add_argument("--serving", action="store_true", help="Require model serving capability.")
    parser.add_argument("--tracking", action="store_true", help="Require experiment tracking capability.")
    parser.add_argument("--pipelines", action="store_true", help="Require pipeline orchestration capability.")
    parser.add_argument("--feature-store", action="store_true", help="Require feature store capability.")
    parser.add_argument("--compare", nargs="+", metavar="ID", help="Compare 2-3 platform IDs side-by-side.")
    parser.add_argument("--recommend", action="store_true", help="Recommend top platforms for a workflow.")
    parser.add_argument("--workflow", choices=sorted(VALID_JOBS), help="Target workflow for --recommend.")
    parser.add_argument("--budget", choices=["free", "paid"], help="Budget preference for --recommend.")
    parser.add_argument("--regulated", action="store_true", help="Prioritize compliance/governance for --recommend.")
    parser.add_argument("--json", action="store_true", help="Output results as JSON.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.validate:
        errors = validate_dataset(TOOLS_PATH)
        if errors:
            for err in errors:
                print(f"ERROR: {err}", file=sys.stderr)
            return 1
        data = load_dataset(TOOLS_PATH)
        print(f"OK: {len(data['tools'])} platforms validated in {TOOLS_PATH.name} (last_verified: {data['last_verified']}).")
        return 0

    data = load_dataset(TOOLS_PATH)
    tools = data["tools"]

    if args.compare:
        if len(args.compare) > 3:
            print("ERROR: Please provide at most 3 platform IDs for --compare.", file=sys.stderr)
            return 2
        lookup = {t["id"]: t for t in tools}
        missing = [tid for tid in args.compare if tid not in lookup]
        if missing:
            print(f"ERROR: Unknown platform ID(s): {', '.join(missing)}", file=sys.stderr)
            return 2
        selected = [lookup[tid] for tid in args.compare]
        print(json.dumps(selected, indent=2) if args.json else format_comparison(selected))
        return 0

    if args.recommend:
        recs = recommend_tools(
            tools,
            workflow=args.workflow,
            budget=args.budget,
            k8s=args.k8s,
            llmops=args.llmops,
            regulated=args.regulated,
        )
        print(json.dumps(recs, indent=2) if args.json else format_table(recs))
        return 0

    caps: List[str] = []
    if args.k8s:
        caps.append("kubernetes_native")
    if args.llmops:
        caps.append("llmops_support")
    if args.serving:
        caps.append("model_serving")
    if args.tracking:
        caps.append("experiment_tracking")
    if args.pipelines:
        caps.append("pipeline_orchestration")
    if args.feature_store:
        caps.append("feature_store")

    filtered = filter_tools(
        tools,
        license_type=args.license,
        job=args.job,
        compliance=args.compliance,
        capabilities=caps or None,
    )
    print(json.dumps(filtered, indent=2) if args.json else format_table(filtered))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
