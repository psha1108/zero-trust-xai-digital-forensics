"""Frozen candidate protocol for operational Random Forest selection."""

from __future__ import annotations

from typing import Final


PRIMARY_SELECTION_METRIC: Final[str] = "macro_f1"

SECONDARY_SELECTION_METRIC: Final[str] = (
    "balanced_accuracy"
)

TERTIARY_SELECTION_METRIC: Final[str] = "log_loss"

RANDOM_STATE: Final[int] = 42
N_ESTIMATORS: Final[int] = 300
N_JOBS: Final[int] = 1


CANDIDATE_CONFIGURATIONS: Final[list[dict]] = [
    {
        "candidate_id": "rf_baseline",
        "criterion": "gini",
        "max_depth": None,
        "min_samples_split": 2,
        "min_samples_leaf": 1,
        "max_features": "sqrt",
        "class_weight": None,
        "bootstrap": True,
    },
    {
        "candidate_id": "rf_balanced",
        "criterion": "gini",
        "max_depth": None,
        "min_samples_split": 2,
        "min_samples_leaf": 1,
        "max_features": "sqrt",
        "class_weight": "balanced",
        "bootstrap": True,
    },
    {
        "candidate_id": "rf_leaf2",
        "criterion": "gini",
        "max_depth": None,
        "min_samples_split": 2,
        "min_samples_leaf": 2,
        "max_features": "sqrt",
        "class_weight": None,
        "bootstrap": True,
    },
    {
        "candidate_id": "rf_balanced_leaf2",
        "criterion": "gini",
        "max_depth": None,
        "min_samples_split": 2,
        "min_samples_leaf": 2,
        "max_features": "sqrt",
        "class_weight": "balanced",
        "bootstrap": True,
    },
    {
        "candidate_id": "rf_depth12",
        "criterion": "gini",
        "max_depth": 12,
        "min_samples_split": 2,
        "min_samples_leaf": 1,
        "max_features": "sqrt",
        "class_weight": None,
        "bootstrap": True,
    },
    {
        "candidate_id": "rf_balanced_depth12",
        "criterion": "gini",
        "max_depth": 12,
        "min_samples_split": 2,
        "min_samples_leaf": 1,
        "max_features": "sqrt",
        "class_weight": "balanced",
        "bootstrap": True,
    },
    {
        "candidate_id": "rf_entropy",
        "criterion": "entropy",
        "max_depth": None,
        "min_samples_split": 2,
        "min_samples_leaf": 1,
        "max_features": "sqrt",
        "class_weight": None,
        "bootstrap": True,
    },
    {
        "candidate_id": "rf_balanced_entropy",
        "criterion": "entropy",
        "max_depth": None,
        "min_samples_split": 2,
        "min_samples_leaf": 1,
        "max_features": "sqrt",
        "class_weight": "balanced",
        "bootstrap": True,
    },
]


def get_candidate_parameters(
    candidate: dict,
) -> dict:
    """Return explicit sklearn RandomForestClassifier parameters."""

    return {
        "n_estimators": N_ESTIMATORS,
        "criterion": candidate["criterion"],
        "max_depth": candidate["max_depth"],
        "min_samples_split": candidate[
            "min_samples_split"
        ],
        "min_samples_leaf": candidate[
            "min_samples_leaf"
        ],
        "max_features": candidate[
            "max_features"
        ],
        "bootstrap": candidate["bootstrap"],
        "class_weight": candidate[
            "class_weight"
        ],
        "random_state": RANDOM_STATE,
        "n_jobs": N_JOBS,
    }
