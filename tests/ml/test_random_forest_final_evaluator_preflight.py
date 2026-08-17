"""Preflight tests for the frozen Random Forest final evaluator."""

from __future__ import annotations

from pathlib import Path

import pytest

import ml.classification.evaluate_operational_test as evaluator
from ml.classification.inference import (
    load_random_forest_bundle,
)


def test_final_evaluator_output_paths_are_frozen() -> None:
    """Final RF reporting artifacts must use the approved locations."""

    assert evaluator.METRICS_PATH == (
        evaluator.PROJECT_ROOT
        / "results"
        / "metrics"
        / "operational_random_forest_test_metrics.json"
    )

    assert evaluator.SCENARIO_RESULTS_PATH == (
        evaluator.PROJECT_ROOT
        / "results"
        / "metrics"
        / "operational_random_forest_test_scenarios.csv"
    )

    assert evaluator.PREDICTIONS_PATH == (
        evaluator.PROJECT_ROOT
        / "results"
        / "predictions"
        / "operational_random_forest_test_predictions.csv"
    )


def test_final_evaluator_frozen_identity_matches_artifact() -> None:
    """Evaluator must reference the already-frozen RF artifact."""

    bundle = load_random_forest_bundle()

    assert (
        evaluator.EXPECTED_MODEL_SEMANTIC_FINGERPRINT
        ==
        bundle["semantic_fingerprint"]
    )

    assert (
        evaluator.EXPECTED_CLASS_ORDER
        ==
        bundle["class_order"]
    )

    assert evaluator.REPORT_LABEL_ORDER == [
        "low",
        "medium",
        "high",
    ]


def test_final_evaluator_metadata_preflight_passes() -> None:
    """Training metadata must pass evaluator provenance validation."""

    metadata = (
        evaluator._load_and_validate_model_metadata()
    )

    assert metadata[
        "metadata_semantic_fingerprint"
    ] == (
        evaluator.EXPECTED_METADATA_SEMANTIC_FINGERPRINT
    )

    assert metadata[
        "semantic_fingerprint"
    ] == (
        evaluator.EXPECTED_MODEL_SEMANTIC_FINGERPRINT
    )

    assert metadata[
        "final_test_accessed"
    ] is False


def test_one_time_guard_accepts_clean_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Evaluator must allow reporting when no result artifacts exist."""

    metrics_path = (
        tmp_path
        / "operational_random_forest_test_metrics.json"
    )

    scenarios_path = (
        tmp_path
        / "operational_random_forest_test_scenarios.csv"
    )

    predictions_path = (
        tmp_path
        / "operational_random_forest_test_predictions.csv"
    )

    monkeypatch.setattr(
        evaluator,
        "PROJECT_ROOT",
        tmp_path,
    )

    monkeypatch.setattr(
        evaluator,
        "METRICS_PATH",
        metrics_path,
    )

    monkeypatch.setattr(
        evaluator,
        "SCENARIO_RESULTS_PATH",
        scenarios_path,
    )

    monkeypatch.setattr(
        evaluator,
        "PREDICTIONS_PATH",
        predictions_path,
    )

    evaluator._refuse_existing_results()


def test_one_time_guard_rejects_existing_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Evaluator must refuse to overwrite an existing outer-test result."""

    metrics_path = (
        tmp_path
        / "operational_random_forest_test_metrics.json"
    )

    scenarios_path = (
        tmp_path
        / "operational_random_forest_test_scenarios.csv"
    )

    predictions_path = (
        tmp_path
        / "operational_random_forest_test_predictions.csv"
    )

    metrics_path.write_text(
        "{}\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        evaluator,
        "PROJECT_ROOT",
        tmp_path,
    )

    monkeypatch.setattr(
        evaluator,
        "METRICS_PATH",
        metrics_path,
    )

    monkeypatch.setattr(
        evaluator,
        "SCENARIO_RESULTS_PATH",
        scenarios_path,
    )

    monkeypatch.setattr(
        evaluator,
        "PREDICTIONS_PATH",
        predictions_path,
    )

    with pytest.raises(
        FileExistsError,
        match="refusing to overwrite or rerun",
    ):
        evaluator._refuse_existing_results()
