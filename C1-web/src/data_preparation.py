"""
Data Preparation & Split Creation Script
Component 1: Adaptive Web Attack Detection & Correlation Model
Final Year Research - Group J26-CS-303
"""

import time
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split

from src.config import (
    RAW_DATA_FILE,
    PROCESSED_DATA_DIR,
    RESULTS_DIR,
    DOCS_DIR,
    CORE_COLUMNS,
    CONTEXT_COLUMNS,
    DETECTION_FEATURES,
    TEXT_FEATURES,
    CATEGORICAL_FEATURES,
    RESPONSE_FEATURES,
    SPARSE_EXCLUDED_FEATURES,
    ALL_LABEL_COLUMNS,
    RARE_LABEL,
    MODEL_LABEL_COLUMNS,
    RANDOM_STATE,
    TEST_SIZE,
    X_TRAIN_PATH,
    X_TEST_PATH,
    Y_TRAIN_PATH,
    Y_TEST_PATH,
    CONTEXT_TEST_PATH,
    CONTEXT_TEST_CSV,
)


def run_data_preparation():
    print("=" * 70)
    print("STEP 2: DATA CLEANING, FEATURE ISOLATION & TRAIN/TEST SPLIT")
    print("=" * 70)

    # Ensure output directories exist
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load Raw Dataset
    print(f"\n1. LOADING RAW DATASET:")
    print(f"   Source: {RAW_DATA_FILE}")
    start_time = time.time()
    df = pd.read_csv(RAW_DATA_FILE, low_memory=False)
    initial_rows, initial_cols = df.shape
    print(f"   Loaded {initial_rows:,} records and {initial_cols} columns in {time.time() - start_time:.2f}s.")

    # 2. Duplicate Removal
    print(f"\n2. REMOVING EXACT DUPLICATES:")
    duplicate_count = df.duplicated().sum()
    df = df.drop_duplicates().copy()
    rows_after_dedup = len(df)
    print(f"   - Removed duplicate records: {duplicate_count:,}")
    print(f"   - Records remaining: {rows_after_dedup:,}")

    # 3. Incomplete Core Record Removal
    print(f"\n3. REMOVING INCOMPLETE CORE RECORDS:")
    core_missing_mask = df[CORE_COLUMNS].isnull().any(axis=1)
    incomplete_count = core_missing_mask.sum()
    df = df.dropna(subset=CORE_COLUMNS).copy()
    clean_total_rows = len(df)
    print(f"   - Core columns inspected: {CORE_COLUMNS}")
    print(f"   - Incomplete records removed: {incomplete_count:,}")
    print(f"   - Final verified clean dataset size: {clean_total_rows:,} records")

    # 4. Handle Missing Values in Optional HTTP Headers
    print(f"\n4. HANDLING OPTIONAL HTTP ATTRIBUTES:")
    # In HTTP protocols, absent headers (cookie, referer, body, etc.) are normal.
    # Missing text attributes are represented as empty strings ("")
    optional_columns = [
        "request_user_agent",
        "request_referer",
        "request_origin",
        "request_cookie",
        "request_content_type",
        "request_accept",
        "request_accept_language",
        "request_accept_encoding",
        "request_connection",
        "request_body",
        "request_host",
    ]
    df[optional_columns] = df[optional_columns].fillna("")
    remaining_nans = df[DETECTION_FEATURES].isnull().sum().sum()
    print(f"   - Replaced NaNs with empty strings ('') for {len(optional_columns)} optional fields.")
    print(f"   - Remaining NaNs in detection features: {remaining_nans}")

    # 5. Isolate Features, Targets, and Context
    print(f"\n5. FEATURE & CONTEXT ISOLATION:")
    print(f"   - Detection Features (X): {len(DETECTION_FEATURES)} request-side attributes")
    print(f"   - Model Target Labels (y): {len(MODEL_LABEL_COLUMNS)} attack categories (excluded {RARE_LABEL})")
    print(f"   - Preserved Context (context): {len(CONTEXT_COLUMNS)} network/temporal attributes for PP2")

    X = df[DETECTION_FEATURES].copy()
    y = df[MODEL_LABEL_COLUMNS].copy()
    context_df = df[CONTEXT_COLUMNS].copy()

    # 6. Reproducible Train / Test Split (80:20)
    print(f"\n6. PARTITIONING DATASET (80% Train, 20% Test, random_state={RANDOM_STATE}):")
    start_split = time.time()
    (
        X_train,
        X_test,
        y_train,
        y_test,
        context_train,
        context_test,
    ) = train_test_split(
        X,
        y,
        context_df,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )
    print(f"   Split completed in {time.time() - start_split:.2f}s:")
    print(f"   - X_train shape: {X_train.shape}")
    print(f"   - X_test  shape: {X_test.shape}")
    print(f"   - y_train shape: {y_train.shape}")
    print(f"   - y_test  shape: {y_test.shape}")
    print(f"   - context_test shape: {context_test.shape}")

    # 7. Verify Label Distribution Across Splits
    print(f"\n7. VERIFYING LABEL REPRESENTATION ACROSS SPLITS:")
    train_counts = y_train.sum(axis=0)
    test_counts = y_test.sum(axis=0)
    split_summary = pd.DataFrame({
        "Attack_Label": MODEL_LABEL_COLUMNS,
        "Total_Clean_Positives": y.sum(axis=0).values,
        "Train_Positives": train_counts.values,
        "Test_Positives": test_counts.values,
        "Test_Ratio_%": ((test_counts.values / y.sum(axis=0).values) * 100).round(2),
    }).sort_values("Total_Clean_Positives", ascending=False)

    split_csv_path = RESULTS_DIR / "split_distribution_summary.csv"
    split_summary.to_csv(split_csv_path, index=False)
    print(f"   Saved split distribution summary to: {split_csv_path.name}")
    print("\n   Sample representation in Test Partition:")
    for _, row in split_summary.iterrows():
        print(f"     * {row['Attack_Label']:<38}: Train={int(row['Train_Positives']):>7,} | Test={int(row['Test_Positives']):>6,} ({row['Test_Ratio_%']}%)")

    # 8. Save Processed Artifacts
    print(f"\n8. SAVING SERIALIZED SPLIT ARTIFACTS:")
    save_start = time.time()
    
    print(f"   - Saving X_train to: {X_TRAIN_PATH.name}")
    joblib.dump(X_train, X_TRAIN_PATH, compress=3)
    
    print(f"   - Saving X_test  to: {X_TEST_PATH.name}")
    joblib.dump(X_test, X_TEST_PATH, compress=3)
    
    print(f"   - Saving y_train to: {Y_TRAIN_PATH.name}")
    joblib.dump(y_train, Y_TRAIN_PATH, compress=3)
    
    print(f"   - Saving y_test  to: {Y_TEST_PATH.name}")
    joblib.dump(y_test, Y_TEST_PATH, compress=3)
    
    print(f"   - Saving context_test to: {CONTEXT_TEST_PATH.name} and {CONTEXT_TEST_CSV.name}")
    joblib.dump(context_test, CONTEXT_TEST_PATH, compress=3)
    context_test.to_csv(CONTEXT_TEST_CSV, index=True)

    print(f"   All artifacts serialized in {time.time() - save_start:.2f}s.")

    # 9. Generate Human-Readable Markdown Documentation
    doc_path = DOCS_DIR / "02_data_preparation_summary.md"
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write("# Phase 2: Data Cleaning and Dataset Split Summary\n\n")
        f.write("## 1. Cleaning Results\n\n")
        f.write(f"- **Initial Records:** {initial_rows:,}\n")
        f.write(f"- **Exact Duplicates Removed:** {duplicate_count:,}\n")
        f.write(f"- **Incomplete Core Records Removed:** {incomplete_count:,}\n")
        f.write(f"- **Clean Record Count:** {clean_total_rows:,}\n\n")
        f.write("## 2. Partition Dimensions\n\n")
        f.write(f"- **Training Set (80%):** {len(X_train):,} requests (`X_train`: {X_train.shape}, `y_train`: {y_train.shape})\n")
        f.write(f"- **Testing Set (20%):** {len(X_test):,} requests (`X_test`: {X_test.shape}, `y_test`: {y_test.shape})\n")
        f.write(f"- **Preserved Test Context:** {len(context_test):,} records with attributes: `{', '.join(CONTEXT_COLUMNS)}`\n\n")
        f.write("## 3. Label Distribution in Splits\n\n")
        f.write("| Attack Label | Clean Total | Train Positives | Test Positives | Test Ratio (%) |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        for _, row in split_summary.iterrows():
            f.write(f"| {row['Attack_Label']} | {int(row['Total_Clean_Positives']):,} | {int(row['Train_Positives']):,} | {int(row['Test_Positives']):,} | {row['Test_Ratio_%']}% |\n")
        f.write("\n")

    print(f"   - Detailed documentation saved to: {doc_path.name}")
    print("\n" + "=" * 70)
    print("STEP 2 COMPLETED SUCCESSFULLY - READY FOR PHASE 3 (PREPROCESSING & MODEL TRAINING)")
    print("=" * 70)

    return {
        "clean_rows": clean_total_rows,
        "X_train_shape": X_train.shape,
        "X_test_shape": X_test.shape,
        "y_train_shape": y_train.shape,
        "y_test_shape": y_test.shape,
        "context_test_shape": context_test.shape,
    }


if __name__ == "__main__":
    run_data_preparation()
