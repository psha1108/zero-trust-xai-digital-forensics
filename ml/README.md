# Machine Learning Pipeline

This directory contains the machine learning components for:

**Securing Systems with Explainable AI Enabled Zero Trust Security and Post Incident Digital Forensics Investigation**

The ML package is modular and independent of Flask, SQLAlchemy, authentication, and database logic.

## ML Component Status

| Component | Purpose | Status |
|---|---|---|
| Synthetic data generation | Generate behavioral login, session, and access logs | Complete |
| Public dataset preparation | Prepare UNSW-NB15 and CIC-IDS2017 datasets | Complete |
| Isolation Forest | Detect anomalous user and session behavior | Complete |
| Random Forest | Classify Low, Medium, and High risk | Pending |
| K-Means | Group similar behavioral patterns | Pending |
| Composite risk engine | Combine model outputs and security indicators | Pending |
| SHAP | Explain model decisions | Pending |
| Backend integration | Provide ML results to the Zero Trust policy engine | Pending |

## Operational Dataset and Feature Contract

The operational machine learning dataset is stored at:

- data/synthetic/ml_training_dataset.csv

Current dataset details:

| Property | Value |
|---|---:|
| Records | 845 |
| Users | 50 |
| Low-risk records | 550 |
| Medium-risk records | 197 |
| High-risk records | 98 |
| Model input features | 14 |

The Isolation Forest uses these behavioral features:

- role
- login_hour
- is_working_hour
- failed_attempt_count
- is_new_ip
- is_new_device
- is_unusual_time
- session_duration_minutes
- resource_sensitivity_score
- access_count_5min
- unauthorized_access_attempt
- ip_changed_during_session
- device_changed_during_session
- sensitive_resource_access_count

The following columns are excluded from model inputs:

- user_id
- scenario_type
- risk_label

These columns are retained for grouped splitting, evaluation, and reporting.

After preprocessing, the model receives 18 numeric features: five one-hot role columns and thirteen numeric behavioral features.

## Leakage-Aware Data Splitting

The operational dataset is split by user_id so that the same user cannot appear in more than one partition.

The deterministic split is created with:

- py -3.11 -m ml.anomaly_detection.create_operational_split

Saved split artifacts:

- data/processed/operational/isolation_forest_split_assignments.csv
- data/processed/operational/isolation_forest_split_metadata.json

| Partition | Records | Users | Purpose |
|---|---:|---:|---|
| Fit | 554 | 32 | Model fitting and development |
| Validation | 138 | 8 | Configuration and threshold selection |
| Outer test | 153 | 10 | Final reporting only |

Only 362 low-risk records from the fit partition were used during Isolation Forest configuration selection.

After configuration and threshold selection were frozen, the final model was trained on 452 low-risk records from the fit and validation partitions.

The outer test partition was evaluated only after the model and threshold were committed to Git.

## Operational Isolation Forest

Selected model configuration:

| Parameter | Value |
|---|---:|
| n_estimators | 300 |
| max_samples | 128 |
| max_features | 1.0 |
| contamination | auto |
| bootstrap | False |
| random_state | 42 |
| n_jobs | 1 |

The final anomaly threshold is:

- 0.5532259181941123

A record is classified as anomalous when its anomaly score is greater than or equal to this threshold.

The frozen model was evaluated once on 153 records belonging to 10 unseen users.

## Final Outer-Test Results

| Metric | Result |
|---|---:|
| ROC-AUC | 0.943414 |
| Average precision | 0.926041 |
| True negatives | 85 |
| False positives | 13 |
| False negatives | 4 |
| True positives | 51 |
| Precision | 0.796875 |
| Recall | 0.927273 |
| F1 score | 0.857143 |
| Balanced accuracy | 0.897310 |
| False-positive rate | 0.132653 |

Detection by risk level:

- Medium risk: 31 of 35 records detected, or 88.57 percent.
- High risk: 20 of 20 records detected, or 100 percent.

All four false negatives were medium-risk records: three unusual_time_login records and one slightly_high_failed_attempts record.

The outer-test results are for final reporting only and must not be used to change the feature schema, model configuration, or threshold.

## Model Artifacts and Inference

The final trained model and metadata are stored at:

- model_artifacts/operational/isolation_forest_bundle.joblib
- model_artifacts/operational/isolation_forest_metadata.json

The model bundle contains the fitted preprocessor, fitted Isolation Forest, feature schema, model parameters, calibrated threshold, and semantic fingerprint.

Current semantic fingerprint:

- 77b1dc298717107f1b1bd353d6da4a01c6fd2f00bf348a3cb4026cde0897d44e

Reusable production inference is provided by:

- ml/anomaly_detection/inference.py

The inference module supports both single-record and batch scoring without depending on Flask or the database.

Each inference result contains:

- anomaly_score
- anomaly_threshold
- threshold_margin
- is_anomaly

## Main Commands

Create the deterministic grouped split:

- py -3.11 -m ml.anomaly_detection.create_operational_split

Run the development baseline:

- py -3.11 -m ml.anomaly_detection.train_operational_baseline

Train and save the final operational model:

- py -3.11 -m ml.anomaly_detection.train_operational_model

Regenerate the frozen final evaluation artifacts:

- py -3.11 -m ml.anomaly_detection.evaluate_operational_test

Run the complete ML test suite:

- py -3.11 -m pytest tests/ml -q -W error::FutureWarning

Current expected test result:

- 54 passed
