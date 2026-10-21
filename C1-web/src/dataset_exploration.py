"""
Dataset Exploration Script for SR-BH 2020 Multi-Label Web Attack Dataset.
Final Year Research - Group J26-CS-303
Component 1: Adaptive Web Attack Detection & Correlation Model
"""

import time
import pandas as pd
import numpy as np
from pathlib import Path
from src.config import (
    RAW_DATA_FILE,
    RESULTS_DIR,
    DOCS_DIR,
    CORE_COLUMNS,
    CONTEXT_COLUMNS,
    DETECTION_FEATURES,
    RESPONSE_FEATURES,
    ALL_LABEL_COLUMNS,
    RARE_LABEL,
    MODEL_LABEL_COLUMNS,
)


def run_exploration():
    print("=" * 70)
    print("STEP 1: SR-BH 2020 DATASET EXPLORATION & SCHEMA VERIFICATION")
    print("=" * 70)

    # Ensure output directories exist
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Loading raw dataset from:\n  {RAW_DATA_FILE}")
    start_time = time.time()
    
    # Load dataset with low_memory=False to handle mixed types cleanly
    df = pd.read_csv(RAW_DATA_FILE, low_memory=False)
    load_time = time.time() - start_time
    print(f"Dataset loaded in {load_time:.2f} seconds.")

    # 1. Dimensions
    total_rows, total_cols = df.shape
    print(f"\n1. DATASET DIMENSIONS:")
    print(f"   - Total records (rows): {total_rows:,}")
    print(f"   - Total attributes (columns): {total_cols}")

    # 2. Schema Breakdown
    print(f"\n2. SCHEMA BREAKDOWN:")
    print(f"   - Request/Context attributes: {len(df.columns[:24])}")
    print(f"   - CAPEC Target Multi-Labels : {len(df.columns[24:])}")
    print(f"   - Contextual fields preserved for PP2 correlation: {len(CONTEXT_COLUMNS)}")
    print(f"   - Request-side detection features for PP1 ML: {len(DETECTION_FEATURES)}")
    print(f"   - Response-side attributes (excluded from detection): {len(RESPONSE_FEATURES)}")

    # 3. Duplicate Detection
    print(f"\n3. DUPLICATE CHECK:")
    duplicate_count = df.duplicated().sum()
    duplicate_pct = (duplicate_count / total_rows) * 100
    print(f"   - Exact duplicate rows: {duplicate_count:,} ({duplicate_pct:.2f}%)")

    # 4. Incomplete Core HTTP Records
    print(f"\n4. INCOMPLETE CORE RECORDS CHECK:")
    core_missing_mask = df[CORE_COLUMNS].isnull().any(axis=1)
    core_missing_count = core_missing_mask.sum()
    print(f"   - Records missing essential core HTTP request info: {core_missing_count}")
    if core_missing_count > 0:
        bad_indices = df[core_missing_mask].index.tolist()
        print(f"   - Indices of incomplete records: {bad_indices}")

    # 5. Missing Values Summary
    print(f"\n5. MISSING VALUES ANALYSIS:")
    missing_counts = df.isnull().sum()
    missing_pct = (missing_counts / total_rows) * 100
    missing_df = pd.DataFrame({
        "Attribute": df.columns,
        "Missing_Count": missing_counts.values,
        "Missing_Percentage": missing_pct.values,
        "Data_Type": df.dtypes.astype(str).values
    }).sort_values("Missing_Count", ascending=False)

    missing_csv_path = RESULTS_DIR / "missing_values_summary.csv"
    missing_df.to_csv(missing_csv_path, index=False)
    print(f"   - Saved full missing value breakdown to: {missing_csv_path.name}")
    print("\n   Top columns with missing values:")
    for _, row in missing_df[missing_df["Missing_Count"] > 0].head(10).iterrows():
        print(f"     * {row['Attribute']:<28}: {row['Missing_Count']:>8,} ({row['Missing_Percentage']:.2f}%)")

    # 6. CAPEC Target Multi-Label Distribution
    print(f"\n6. CAPEC ATTACK LABEL DISTRIBUTION:")
    label_counts = df[ALL_LABEL_COLUMNS].sum().sort_values(ascending=False)
    label_pct = (label_counts / total_rows) * 100
    label_df = pd.DataFrame({
        "CAPEC_Label": label_counts.index,
        "Positive_Samples": label_counts.values,
        "Percentage_of_Total": label_pct.values
    })
    label_csv_path = RESULTS_DIR / "label_distribution_raw.csv"
    label_df.to_csv(label_csv_path, index=False)
    print(f"   - Saved label distribution to: {label_csv_path.name}")

    print("\n   Positive instances per attack category:")
    for _, row in label_df.iterrows():
        note = " <-- EXCLUDED FROM SUPERVISED TRAINING (N=1)" if row["CAPEC_Label"] == RARE_LABEL else ""
        print(f"     * {row['CAPEC_Label']:<40}: {int(row['Positive_Samples']):>8,} ({row['Percentage_of_Total']:.4f}%){note}")

    # 7. Multi-Label Complexity
    print(f"\n7. MULTI-LABEL CHARACTERISTICS:")
    labels_per_row = df[ALL_LABEL_COLUMNS].sum(axis=1)
    label_counts_summary = labels_per_row.value_counts().sort_index()
    print("   Distribution of active labels per HTTP request:")
    for num_labels, count in label_counts_summary.items():
        pct = (count / total_rows) * 100
        print(f"     * Requests with {num_labels} active labels: {count:>8,} ({pct:.2f}%)")

    # 8. Markdown Summary Document
    summary_md_path = DOCS_DIR / "01_dataset_exploration_summary.md"
    with open(summary_md_path, "w", encoding="utf-8") as f:
        f.write("# Dataset Exploration and Schema Verification Summary\n\n")
        f.write(f"- **Dataset File:** `{RAW_DATA_FILE.name}`\n")
        f.write(f"- **Total Records:** {total_rows:,}\n")
        f.write(f"- **Total Attributes:** {total_cols}\n")
        f.write(f"- **Exact Duplicates:** {duplicate_count:,}\n")
        f.write(f"- **Incomplete Core Records:** {core_missing_count}\n")
        f.write(f"- **Clean Record Count (after cleaning):** {total_rows - duplicate_count - core_missing_count:,}\n\n")
        f.write("## Label Distribution (14 CAPEC Classes)\n\n")
        f.write("| CAPEC Label | Positive Samples | Percentage (%) |\n")
        f.write("| :--- | :--- | :--- |\n")
        for _, row in label_df.iterrows():
            f.write(f"| {row['CAPEC_Label']} | {int(row['Positive_Samples']):,} | {row['Percentage_of_Total']:.4f}% |\n")
        f.write("\n\n## Missing Values in Top Attributes\n\n")
        f.write("| Attribute | Missing Count | Missing (%) | Data Type |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        for _, row in missing_df[missing_df["Missing_Count"] > 0].iterrows():
            f.write(f"| {row['Attribute']} | {int(row['Missing_Count']):,} | {row['Missing_Percentage']:.2f}% | {row['Data_Type']} |\n")
        f.write("\n")

    print(f"\n   - Full human-readable documentation saved to: {summary_md_path.name}")
    print("\n" + "=" * 70)
    print("EXPLORATION COMPLETE - DATASET IS READY FOR PHASE 2 (DATA PREPARATION)")
    print("=" * 70)

    return {
        "total_rows": total_rows,
        "total_cols": total_cols,
        "duplicate_count": duplicate_count,
        "core_missing_count": core_missing_count,
        "label_counts": label_counts.to_dict(),
    }


if __name__ == "__main__":
    run_exploration()
