"""
Benchmark runner for DocForge prompt tuning and pipeline evaluation across 20 real-world API endpoints.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List

from app.core.pipeline import run_pipeline, PROMPT_REGISTRY
from benchmark.benchmark_fixtures import BENCHMARK_ENDPOINTS


def run_benchmark() -> Dict[str, Any]:
    """Execute AI pipeline against all 20 benchmark fixtures and calculate key metrics."""
    print("🚀 Starting DocForge 20-Endpoint Pipeline Benchmark...")
    results: List[Dict[str, Any]] = []
    
    first_attempt_approves = 0
    total_quality_scores = 0.0
    valid_scores_count = 0
    total_latency_ms = 0.0

    for fixture in BENCHMARK_ENDPOINTS:
        fixture_id = fixture["id"]
        route = fixture["route"]
        source_code = fixture["source_code"]

        start_time = time.time()
        result = run_pipeline(route, source_code)
        latency_ms = round((time.time() - start_time) * 1000, 2)
        total_latency_ms += latency_ms

        score = result.quality_score if result.quality_score is not None else 0.0
        if result.quality_score is not None:
            total_quality_scores += score
            valid_scores_count += 1

        is_first_attempt_approve = (result.final_verdict == "approved" and result.attempts == 1)
        if is_first_attempt_approve:
            first_attempt_approves += 1

        print(
            f"  [{fixture_id}] {route.method} {route.path} -> verdict: {result.final_verdict} | "
            f"attempts: {result.attempts} | score: {score:.2f} | latency: {latency_ms}ms"
        )

        results.append({
            "fixture_id": fixture_id,
            "method": route.method,
            "path": route.path,
            "verdict": result.final_verdict,
            "attempts": result.attempts,
            "quality_score": score,
            "needs_human_review": result.needs_human_review,
            "latency_ms": latency_ms,
        })

    total_fixtures = len(BENCHMARK_ENDPOINTS)
    first_attempt_pass_rate = round((first_attempt_approves / total_fixtures) * 100, 2)
    mean_quality_score = round(total_quality_scores / max(1, valid_scores_count), 2)
    avg_latency_ms = round(total_latency_ms / total_fixtures, 2)

    summary = {
        "total_endpoints": total_fixtures,
        "first_attempt_approves": first_attempt_approves,
        "first_attempt_pass_rate_pct": first_attempt_pass_rate,
        "mean_quality_score": mean_quality_score,
        "avg_latency_ms": avg_latency_ms,
        "prompt_versions": dict(PROMPT_REGISTRY),
        "target_pass_rate_met": first_attempt_pass_rate >= 80.0,
        "target_quality_met": mean_quality_score >= 7.0,
    }

    print("\n📊 BENCHMARK SUMMARY REPORT")
    print(f"  • Total Endpoints Tested:      {total_fixtures}")
    print(f"  • First-Attempt Approve Rate: {first_attempt_pass_rate}% (Target: ≥ 80%)")
    print(f"  • Mean Quality Score:         {mean_quality_score} / 10.0 (Target: ≥ 7.0)")
    print(f"  • Avg Pipeline Latency:       {avg_latency_ms}ms")
    print(f"  • Target Criteria Passed:     {'✅ PASS' if summary['target_pass_rate_met'] and summary['target_quality_met'] else '❌ FAIL'}")

    # Output JSON artifact
    os.makedirs("benchmark/results", exist_ok=True)
    with open("benchmark/results/benchmark_report.json", "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2)

    return summary


if __name__ == "__main__":
    run_benchmark()
