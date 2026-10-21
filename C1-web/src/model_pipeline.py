"""
Multi-Label Web Attack Detection Model Pipeline
Component 1: Adaptive Web Attack Detection & Correlation Model
Final Year Research - Group J26-CS-303
"""

import time
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    hamming_loss,
    classification_report,
)

from src.config import (
    X_TRAIN_PATH,
    X_TEST_PATH,
    Y_TRAIN_PATH,
    Y_TEST_PATH,
    CONTEXT_TEST_PATH,
    CATEGORICAL_FEATURES,
    TEXT_FEATURES,
    MODEL_LABEL_COLUMNS,
    RANDOM_STATE,
    MODELS_DIR,
    RESULTS_DIR,
    DOCS_DIR,
    MODEL_PATH,
    PREPROCESSOR_PATH,
    DETECTION_OUTPUT_CSV,
    CORRELATION_INPUT_CSV,
)


def run_detection_pipeline():
    print("=" * 70)
    print("STEP 3: FEATURE PREPROCESSING, MODEL TRAINING & DETECTION EVALUATION")
    print("=" * 70)

    # Ensure output directories exist
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load Clean Partitions
    print("\n1. LOADING PREPARED SPLITS:")
    load_start = time.time()
    X_train = joblib.load(X_TRAIN_PATH)
    X_test = joblib.load(X_TEST_PATH)
    y_train = joblib.load(Y_TRAIN_PATH)
    y_test = joblib.load(Y_TEST_PATH)
    context_test = joblib.load(CONTEXT_TEST_PATH)
    print(f"   Loaded partitions in {time.time() - load_start:.2f}s:")
    print(f"   - X_train: {X_train.shape}")
    print(f"   - X_test : {X_test.shape}")
    print(f"   - y_train: {y_train.shape}")
    print(f"   - y_test : {y_test.shape}")
    print(f"   - context_test: {context_test.shape}")

    # 2. Configure ColumnTransformer Preprocessor
    print("\n2. CONFIGURING PREPROCESSING PIPELINE:")
    print(f"   - Text Vectorizers (TF-IDF, max_features=10,000):")
    print(f"     * request_http_request (URI path & query)")
    print(f"     * request_body (POST/PUT payload)")
    print(f"   - Categorical Encoder (One-Hot Encoding, handle_unknown='ignore'):")
    print(f"     * {len(CATEGORICAL_FEATURES)} HTTP request headers and method")

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "request_tfidf",
                TfidfVectorizer(max_features=10000),
                "request_http_request",
            ),
            (
                "body_tfidf",
                TfidfVectorizer(max_features=10000),
                "request_body",
            ),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                CATEGORICAL_FEATURES,
            ),
        ]
    )

    # 3. Fit Preprocessor Strictly on Training Data (Avoiding Data Leakage)
    print("\n3. FITTING PREPROCESSOR & TRANSFORMING DATA:")
    prep_start = time.time()
    print("   - Fitting preprocessor on X_train only...")
    X_train_transformed = preprocessor.fit_transform(X_train)
    X_train_transformed.sort_indices()
    print("   - Transforming X_test using fitted preprocessor...")
    X_test_transformed = preprocessor.transform(X_test)
    X_test_transformed.sort_indices()
    prep_time = time.time() - prep_start
    print(f"   Preprocessing completed in {prep_time:.2f}s:")
    print(f"   - Transformed X_train shape: {X_train_transformed.shape}")
    print(f"   - Transformed X_test shape : {X_test_transformed.shape}")
    print(f"   - Total sparse features: {X_train_transformed.shape[1]:,}")

    # Save fitted preprocessor
    print(f"   - Saving preprocessor to: {PREPROCESSOR_PATH.name}")
    joblib.dump(preprocessor, PREPROCESSOR_PATH, compress=3)

    # 4. Configure One-vs-Rest Logistic Regression Classifier
    print("\n4. CONFIGURING MULTI-LABEL CLASSIFIER:")
    print(f"   - Algorithm: One-vs-Rest (OvR) Logistic Regression")
    print(f"   - Solver: liblinear (ideal for high-dimensional sparse text data)")
    print(f"   - Max iterations: 1,000")
    print(f"   - Target labels: {len(MODEL_LABEL_COLUMNS)}")

    base_classifier = LogisticRegression(
        solver="liblinear",
        max_iter=1000,
        random_state=RANDOM_STATE,
    )
    model = OneVsRestClassifier(base_classifier, n_jobs=1)

    # 5. Train the Model
    print("\n5. TRAINING THE MODEL (One-vs-Rest sequential binary classifiers):")
    train_start = time.time()
    model.fit(X_train_transformed, y_train)
    train_time = time.time() - train_start
    print(f"   Model training completed in {train_time:.2f}s ({train_time/60:.2f} minutes).")
    print(f"   - Fitted binary estimators: {len(model.estimators_)}")

    # Save trained model
    print(f"   - Saving trained model to: {MODEL_PATH.name}")
    joblib.dump(model, MODEL_PATH, compress=3)

    # 6. Generate Predictions & Probabilities on Test Data
    print("\n6. GENERATING TEST PREDICTIONS & CONFIDENCE PROBABILITIES:")
    pred_start = time.time()
    y_pred = model.predict(X_test_transformed)
    y_prob = model.predict_proba(X_test_transformed)
    pred_time = time.time() - pred_start
    print(f"   Predictions generated for {len(y_pred):,} test samples in {pred_time:.2f}s.")
    print(f"   - Binary predictions shape: {y_pred.shape}")
    print(f"   - Probability scores shape: {y_prob.shape}")

    # 7. Overall Evaluation Metrics
    print("\n7. OVERALL MULTI-LABEL PERFORMANCE METRICS:")
    micro_p = precision_score(y_test, y_pred, average="micro", zero_division=0)
    micro_r = recall_score(y_test, y_pred, average="micro", zero_division=0)
    micro_f1 = f1_score(y_test, y_pred, average="micro", zero_division=0)

    macro_p = precision_score(y_test, y_pred, average="macro", zero_division=0)
    macro_r = recall_score(y_test, y_pred, average="macro", zero_division=0)
    macro_f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)

    h_loss = hamming_loss(y_test, y_pred)

    print("   " + "-" * 50)
    print(f"   Micro Precision : {micro_p:.4f}")
    print(f"   Micro Recall    : {micro_r:.4f}")
    print(f"   Micro F1-Score  : {micro_f1:.4f}")
    print("   " + "-" * 50)
    print(f"   Macro Precision : {macro_p:.4f}")
    print(f"   Macro Recall    : {macro_r:.4f}")
    print(f"   Macro F1-Score  : {macro_f1:.4f}")
    print("   " + "-" * 50)
    print(f"   Hamming Loss    : {h_loss:.4f} (Incorrect label fraction)")
    print("   " + "-" * 50)

    overall_metrics_df = pd.DataFrame([
        {"Metric": "Micro Precision", "Value": round(micro_p, 4)},
        {"Metric": "Micro Recall", "Value": round(micro_r, 4)},
        {"Metric": "Micro F1-Score", "Value": round(micro_f1, 4)},
        {"Metric": "Macro Precision", "Value": round(macro_p, 4)},
        {"Metric": "Macro Recall", "Value": round(macro_r, 4)},
        {"Metric": "Macro F1-Score", "Value": round(macro_f1, 4)},
        {"Metric": "Hamming Loss", "Value": round(h_loss, 4)},
    ])
    overall_csv_path = RESULTS_DIR / "detection_overall_metrics.csv"
    overall_metrics_df.to_csv(overall_csv_path, index=False)

    # 8. Per-Label Detailed Performance
    print("\n8. PER-LABEL PERFORMANCE BREAKDOWN:")
    report_dict = classification_report(
        y_test,
        y_pred,
        target_names=MODEL_LABEL_COLUMNS,
        output_dict=True,
        zero_division=0,
    )
    per_label_df = (
        pd.DataFrame(report_dict)
        .transpose()
        .loc[MODEL_LABEL_COLUMNS, ["precision", "recall", "f1-score", "support"]]
    )
    per_label_df["support"] = per_label_df["support"].astype(int)
    per_label_csv_path = RESULTS_DIR / "detection_per_label_metrics.csv"
    per_label_df.to_csv(per_label_csv_path, index=True)

    for label, row in per_label_df.iterrows():
        print(f"   * {label:<38}: P={row['precision']:.4f} | R={row['recall']:.4f} | F1={row['f1-score']:.4f} | Support={row['support']:>6,}")

    # 9. Prediction Error Analysis
    print("\n9. PREDICTION ERROR & UNDER-DETECTION ANALYSIS:")
    actual_positives = y_test.sum(axis=0)
    predicted_positives = y_pred.sum(axis=0)
    error_analysis_df = pd.DataFrame({
        "Attack Category": MODEL_LABEL_COLUMNS,
        "Actual Positives (Ground Truth)": actual_positives.values,
        "Predicted Positives": predicted_positives,
        "Difference (Pred - Actual)": predicted_positives - actual_positives.values,
    }).sort_values("Actual Positives (Ground Truth)", ascending=False)

    error_csv_path = RESULTS_DIR / "detection_error_analysis.csv"
    error_analysis_df.to_csv(error_csv_path, index=False)
    for _, row in error_analysis_df.iterrows():
        diff_str = f"+{row['Difference (Pred - Actual)']}" if row['Difference (Pred - Actual)'] > 0 else f"{row['Difference (Pred - Actual)']}"
        print(f"   * {row['Attack Category']:<38}: Actual={int(row['Actual Positives (Ground Truth)']):>6,} | Pred={int(row['Predicted Positives']):>6,} | Diff={diff_str:>5}")

    # 10. PP1-to-PP2 Handover Artifact: Correlation Input Generation
    print("\n10. PREPARING PP1-TO-PP2 HANDOVER ARTIFACT (correlation_input.csv):")
    # Convert predictions and probabilities into DataFrames with matching test index
    y_pred_df = pd.DataFrame(
        y_pred,
        index=X_test.index,
        columns=MODEL_LABEL_COLUMNS,
    )
    prob_columns = [f"{col} - Probability" for col in MODEL_LABEL_COLUMNS]
    y_prob_df = pd.DataFrame(
        y_prob,
        index=X_test.index,
        columns=prob_columns,
    )

    # Detection output: predictions + probabilities
    detection_output = pd.concat([y_pred_df, y_prob_df], axis=1)
    detection_output.to_csv(DETECTION_OUTPUT_CSV, index=True)
    print(f"   - Saved detection output (predictions + probabilities) to: {DETECTION_OUTPUT_CSV.name}")

    # Correlation input: preserved context (5 cols) + predictions (13 cols) + probabilities (13 cols) = 31 cols
    correlation_input = pd.concat([context_test, detection_output], axis=1)
    correlation_input.to_csv(CORRELATION_INPUT_CSV, index=True)
    print(f"   - Saved correlation input ({correlation_input.shape[0]:,} rows x {correlation_input.shape[1]} cols) to: {CORRELATION_INPUT_CSV.name}")

    # 11. Comprehensive Documentation
    doc_path = DOCS_DIR / "03_detection_model_summary.md"
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write("# Phase 3: Web Attack Detection Model & Evaluation Summary\n\n")
        f.write(f"- **Algorithm:** One-vs-Rest Logistic Regression (`solver='liblinear'`, `max_iter=1000`)\n")
        f.write(f"- **Preprocessing:** TF-IDF (10,000 max features for URI and Body) + One-Hot Encoding for 12 categorical headers\n")
        f.write(f"- **Total Sparse Input Features:** {X_train_transformed.shape[1]:,}\n")
        f.write(f"- **Training Samples:** {len(X_train):,}\n")
        f.write(f"- **Testing Samples:** {len(X_test):,}\n")
        f.write(f"- **Training Time:** {train_time:.2f} seconds\n\n")
        f.write("## 1. Overall Performance Metrics\n\n")
        f.write("| Metric | Value |\n| :--- | :--- |\n")
        for _, row in overall_metrics_df.iterrows():
            f.write(f"| {row['Metric']} | {row['Value']} |\n")
        f.write("\n## 2. Per-Label Performance\n\n")
        f.write("| Attack Category | Precision | Recall | F1-Score | Support |\n| :--- | :--- | :--- | :--- | :--- |\n")
        for label, row in per_label_df.iterrows():
            f.write(f"| {label} | {row['precision']:.4f} | {row['recall']:.4f} | {row['f1-score']:.4f} | {int(row['support']):,} |\n")
        f.write("\n## 3. Minority Class Under-Detection Analysis\n\n")
        f.write("| Attack Category | Actual Positives | Predicted Positives | Difference |\n| :--- | :--- | :--- | :--- |\n")
        for _, row in error_analysis_df.iterrows():
            f.write(f"| {row['Attack Category']} | {int(row['Actual Positives (Ground Truth)']):,} | {int(row['Predicted Positives']):,} | {int(row['Difference (Pred - Actual)']):,} |\n")
        f.write("\n")

    print(f"   - Detailed documentation saved to: {doc_path.name}")
    print("\n" + "=" * 70)
    print("STEP 3 COMPLETED SUCCESSFULLY - PP1 DETECTION STAGE IS FULLY IMPLEMENTED")
    print("=" * 70)

    return {
        "train_time": train_time,
        "micro_f1": micro_f1,
        "macro_f1": macro_f1,
        "hamming_loss": h_loss,
        "correlation_input_shape": correlation_input.shape,
    }


if __name__ == "__main__":
    run_detection_pipeline()
