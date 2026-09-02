"""Contract tests for development-only K-Means archetype profiles."""

from __future__ import annotations

from ml.clustering.archetype_profiles import (
    PROFILE_SEMANTICS,
    build_development_archetype_profile_report,
)
from ml.clustering.preprocessing import (
    MODEL_FEATURE_COLUMNS,
    NUMERIC_FEATURE_COLUMNS,
    ROLE_CATEGORIES,
)


EXPECTED_ARCHETYPE_NAMES = {
    "0": "Elevated Behavioral Activity",
    "1": "Routine Behavioral Activity",
}

EXPECTED_CLUSTER_SIZES = {
    "0": 76,
    "1": 616,
}


def test_profile_report_uses_development_partition_only() -> None:
    report = build_development_archetype_profile_report()

    assert report["profile_partition"] == "fit_plus_validation"
    assert report["development_rows"] == 692
    assert report["development_users"] == 40
    assert report["test_rows_evaluated"] == 0

    assert report["partition_rows"] == {
        "fit": 554,
        "validation": 138,
    }


def test_profile_report_preserves_frozen_cluster_semantics() -> None:
    report = build_development_archetype_profile_report()

    assert report["selected_k"] == 2

    assert report["canonical_archetype_names"] == (
        EXPECTED_ARCHETYPE_NAMES
    )

    assert report["development_cluster_sizes"] == (
        EXPECTED_CLUSTER_SIZES
    )

    assert sum(
        report["development_cluster_sizes"].values()
    ) == 692

    assert report["semantics"] == PROFILE_SEMANTICS

    assert PROFILE_SEMANTICS == (
        "behavioral context only; cluster IDs are not risk "
        "classes or access-control decisions"
    )


def test_profile_report_is_unsupervised_and_policy_free() -> None:
    report = build_development_archetype_profile_report()

    assert report["task"] == (
        "development_behavioral_archetype_profiling"
    )

    assert report["risk_label_used_for_profile"] is False
    assert report["scenario_type_used_for_profile"] is False
    assert report["test_partition_used_for_profile"] is False
    assert report["policy_decision_produced"] is False


def test_profile_report_uses_exact_operational_feature_contract() -> None:
    report = build_development_archetype_profile_report()

    assert report["source_features"] == list(
        MODEL_FEATURE_COLUMNS
    )

    assert len(
        report["source_features"]
    ) == 14

    assert "user_id" not in report["source_features"]
    assert "risk_label" not in report["source_features"]
    assert "scenario_type" not in report["source_features"]


def test_profile_contains_exact_two_canonical_profiles() -> None:
    report = build_development_archetype_profile_report()

    profiles = report["profiles"]

    assert set(profiles) == {
        "0",
        "1",
    }

    for cluster_id, expected_name in (
        EXPECTED_ARCHETYPE_NAMES.items()
    ):
        profile = profiles[cluster_id]

        assert profile["cluster_id"] == int(
            cluster_id
        )

        assert profile["archetype_name"] == expected_name

        assert profile["row_count"] == (
            EXPECTED_CLUSTER_SIZES[
                cluster_id
            ]
        )

        assert 0.0 < profile["row_fraction"] < 1.0


def test_each_profile_contains_role_distribution() -> None:
    report = build_development_archetype_profile_report()

    expected_roles = set(
        ROLE_CATEGORIES
    )

    for profile in report["profiles"].values():
        role_distribution = profile[
            "role_distribution"
        ]

        assert set(
            role_distribution
        ) == expected_roles

        assert abs(
            sum(
                role_distribution.values()
            )
            - 1.0
        ) < 1e-12

        assert all(
            0.0 <= proportion <= 1.0
            for proportion in (
                role_distribution.values()
            )
        )


def test_each_profile_contains_numeric_source_feature_means() -> None:
    report = build_development_archetype_profile_report()

    expected_features = set(
        NUMERIC_FEATURE_COLUMNS
    )

    assert len(
        expected_features
    ) == 13

    for profile in report["profiles"].values():
        means = profile[
            "numeric_feature_means"
        ]

        assert set(
            means
        ) == expected_features

        assert all(
            isinstance(
                value,
                float,
            )
            for value in means.values()
        )


def test_cluster_fractions_match_development_counts() -> None:
    report = build_development_archetype_profile_report()

    for cluster_id, count in (
        EXPECTED_CLUSTER_SIZES.items()
    ):
        expected_fraction = (
            count / 692
        )

        actual_fraction = report[
            "profiles"
        ][cluster_id][
            "row_fraction"
        ]

        assert abs(
            actual_fraction
            - expected_fraction
        ) < 1e-12


def test_elevated_profile_has_higher_activity_score() -> None:
    report = build_development_archetype_profile_report()

    elevated = report[
        "profiles"
    ]["0"][
        "standardized_activity_score"
    ]

    routine = report[
        "profiles"
    ]["1"][
        "standardized_activity_score"
    ]

    assert elevated > routine


def test_profile_report_is_deterministic() -> None:
    first = build_development_archetype_profile_report()
    second = build_development_archetype_profile_report()

    assert first == second
