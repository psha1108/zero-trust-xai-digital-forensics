"""Train and evaluate the baseline operational Isolation Forest."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
)

from ml.anomaly_detection.preprocessing import (
    build_operational_preprocessor,
    get_transformed_feature_names,
    select_operational_features,
    transform_operational_features,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "synthetic"
    / "ml_training_dataset.csv"
)

ASSIGNMENT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "operational"
    / "isolation_forest_split_assignments.csv"
)

RISK_LABEL_ORDER = [
    "low",
    "medium",
    "high",
]

RANDOM_STATE = 42
N_ESTIMATORS = 300
MAX_SAMPLES = 128


def load_training_data() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
]:
    """Load and validate source data and split assignments."""

    dataframe = pd.read_csv(DATASET_PATH)
    assignments = pd.read_csv(ASSIGNMENT_PATH)

    if dataframe.shape != (845, 17):
        raise ValueError(
            f"Unexpected source dataset shape: {dataframe.shape}"
        )

    if assignments.shape != (845, 7):
        raise ValueError(
            "Unexpected assignment artifact shape: "
            f"{assignments.shape}"
        )

    expected_indices = list(range(len(dataframe)))

    if (
        assignments["source_row_index"].tolist()
        != expected_indices
    ):
        raise ValueError(
            "Split assignments are not aligned with source rows."
        )

    for column in [
        "user_id",
        "role",
        "risk_label",
        "scenario_type",
    ]:
        pd.testing.assert_series_equal(
            dataframe[column].reset_index(drop=True),
            assignments[column].reset_index(drop=True),
            check_names=False,
            check_dtype=False,
        )

    working_df = dataframe.copy()

    working_df["source_row_index"] = (
        assignments["source_row_index"].to_numpy()
    )

    working_df["partition"] = (
        assignments["partition"].to_numpy()
    )

    working_df["used_for_model_fit"] = (
        assignments[
            "used_for_model_fit"
        ].to_numpy()
    )

    fit_low_df = working_df.loc[
        working_df[
            "used_for_model_fit"
        ].eq(1)
    ].copy()

    validation_df = working_df.loc[
        working_df["partition"]
        .eq("validation")
    ].copy()

    if len(fit_low_df) != 362:
        raise ValueError(
            "Expected 362 low-risk fitting rows, "
            f"received {len(fit_low_df)}."
        )

    if len(validation_df) != 138:
        raise ValueError(
            "Expected 138 validation rows, "
            f"received {len(validation_df)}."
        )

    if not fit_low_df["risk_label"].eq("low").all():
        raise ValueError(
            "Model-fitting data contains non-low-risk records."
        )

    if set(
        validation_df["risk_label"]
    ) != set(RISK_LABEL_ORDER):
        raise ValueError(
            "Validation partition does not contain "
            "all expected risk labels."
        )

    return fit_low_df, validation_df


def main() -> None:
    """Fit the baseline model and report validation metrics."""

    fit_low_df, validation_df = (
        load_training_data()
    )

    fit_features = select_operational_features(
        fit_low_df
    )

    preprocessor = (
        build_operational_preprocessor()
    )

    fit_matrix = np.asarray(
        preprocessor.fit_transform(
            fit_features
        ),
        dtype=np.float64,
    )

    validation_matrix = (
        transform_operational_features(
            preprocessor,
            validation_df,
        )
    )

    transformed_feature_names = (
        get_transformed_feature_names(
            preprocessor
        )
    )

    if fit_matrix.shape != (362, 18):
        raise ValueError(
            "Unexpected fitting matrix shape: "
            f"{fit_matrix.shape}"
        )

    if validation_matrix.shape != (138, 18):
        raise ValueError(
            "Unexpected validation matrix shape: "
            f"{validation_matrix.shape}"
        )

    model = IsolationForest(
        n_estimators=N_ESTIMATORS,
        max_samples=MAX_SAMPLES,
        contamination="auto",
        max_features=1.0,
        bootstrap=False,
        random_state=RANDOM_STATE,
        n_jobs=1,
    )

    training_start = perf_counter()

    model.fit(fit_matrix)

    training_seconds = (
        perf_counter()
        -
        training_start
    )

    # sklearn score_samples returns lower values for
    # more abnormal observations. Negating it produces
    # an intuitive score where higher means more anomalous.
    fit_anomaly_scores = -model.score_samples(
        fit_matrix
    )

    validation_anomaly_scores = (
        -model.score_samples(
            validation_matrix
        )
    )

    validation_binary_labels = (
        validation_df["risk_label"]
        .ne("low")
        .astype("uint8")
        .to_numpy()
    )

    roc_auc = roc_auc_score(
        validation_binary_labels,
        validation_anomaly_scores,
    )

    average_precision = (
        average_precision_score(
            validation_binary_labels,
            validation_anomaly_scores,
        )
    )

    validation_prevalence = float(
        validation_binary_labels.mean()
    )

    scored_validation_df = validation_df[
        [
            "source_row_index",
            "user_id",
            "role",
            "scenario_type",
            "risk_label",
        ]
    ].copy()

    scored_validation_df[
        "anomaly_score"
    ] = validation_anomaly_scores

    risk_score_summary = (
        scored_validation_df
        .groupby(
            "risk_label",
            observed=True,
        )["anomaly_score"]
        .agg(
            [
                "count",
                "mean",
                "median",
                "min",
                "max",
            ]
        )
        .reindex(RISK_LABEL_ORDER)
        .round(6)
    )

    top_anomalies_df = (
        scored_validation_df
        .sort_values(
            "anomaly_score",
            ascending=False,
        )
        .head(15)
        .reset_index(drop=True)
    )

    fit_score_quantiles = (
        pd.Series(
            fit_anomaly_scores
        )
        .quantile(
            [
                0.00,
                0.05,
                0.25,
                0.50,
                0.75,
                0.95,
                1.00,
            ]
        )
        .round(6)
    )

    print("Baseline operational Isolation Forest")
    print("=" * 100)

    print("scikit-learn version:", sklearn.__version__)
    print("Random state:", RANDOM_STATE)
    print("Number of estimators:", N_ESTIMATORS)
    print("Maximum samples per tree:", MAX_SAMPLES)
    print("Contamination setting: auto")
    print("Parallel jobs: 1")

    print("\nTraining data")
    print("-" * 100)

    print("Low-risk fitting rows:", len(fit_low_df))
    print("Validation rows:", len(validation_df))
    print("Source feature count:", fit_features.shape[1])
    print(
        "Transformed feature count:",
        len(transformed_feature_names),
    )
    print("Fitting matrix shape:", fit_matrix.shape)
    print(
        "Validation matrix shape:",
        validation_matrix.shape,
    )
    print(
        "Training time in seconds:",
        round(training_seconds, 6),
    )

    print("\nValidation labels")
    print("-" * 100)

    print(
        validation_df["risk_label"]
        .value_counts()
        .reindex(
            RISK_LABEL_ORDER,
            fill_value=0,
        )
        .to_string()
    )

    print(
        "\nBinary anomaly prevalence:",
        round(validation_prevalence, 6),
    )

    print("\nThreshold-independent validation metrics")
    print("-" * 100)

    print(
        "ROC-AUC:",
        round(float(roc_auc), 6),
    )

    print(
        "Average precision:",
        round(
            float(average_precision),
            6,
        ),
    )

    print(
        "Random-ranking AP baseline:",
        round(validation_prevalence, 6),
    )

    print("\nValidation anomaly scores by risk label")
    print("-" * 100)

    print(risk_score_summary.to_string())

    print("\nLow-risk fitting-score quantiles")
    print("-" * 100)

    print(fit_score_quantiles.to_string())

    print("\nTop 15 validation anomaly scores")
    print("-" * 140)

    print(
        top_anomalies_df.to_string(
            index=False
        )
    )

    print(
        "\nBaseline Isolation Forest training "
        "completed successfully."
    )


if __name__ == "__main__":
    main()
