"""
Configuration module for Component 1: Adaptive Web Attack Detection & Correlation Model
Final Year Research - Group J26-CS-303
"""

from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "Dataset"
RAW_DATA_FILE = DATA_DIR / "data_capec_multilabel.csv"
RESULTS_DIR = BASE_DIR / "results"
MODELS_DIR = BASE_DIR / "models"
DOCS_DIR = BASE_DIR / "docs"
NOTEBOOKS_DIR = BASE_DIR / "notebooks"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Processed split paths
X_TRAIN_PATH = PROCESSED_DATA_DIR / "X_train.joblib"
X_TEST_PATH = PROCESSED_DATA_DIR / "X_test.joblib"
Y_TRAIN_PATH = PROCESSED_DATA_DIR / "y_train.joblib"
Y_TEST_PATH = PROCESSED_DATA_DIR / "y_test.joblib"
CONTEXT_TEST_PATH = PROCESSED_DATA_DIR / "context_test.joblib"
CONTEXT_TEST_CSV = PROCESSED_DATA_DIR / "context_test.csv"
CLEAN_DATASET_CSV = PROCESSED_DATA_DIR / "clean_dataset_summary.csv"

# Core columns required for valid HTTP records
CORE_COLUMNS = [
    "timestamp",
    "src_ip",
    "src_port",
    "dst_ip",
    "dst_port",
    "request_http_method",
    "request_http_request",
    "request_http_protocol",
]

# 5 Contextual attributes preserved strictly for Stage 2 (Event Correlation in PP2)
CONTEXT_COLUMNS = [
    "timestamp",
    "src_ip",
    "src_port",
    "dst_ip",
    "dst_port",
]

# 14 Request-side detection features (Inputs for Stage 1 Detection Model in PP1)
TEXT_FEATURES = [
    "request_http_request",
    "request_body",
]

CATEGORICAL_FEATURES = [
    "request_http_method",
    "request_http_protocol",
    "request_host",
    "request_user_agent",
    "request_referer",
    "request_origin",
    "request_cookie",
    "request_content_type",
    "request_accept",
    "request_accept_language",
    "request_accept_encoding",
    "request_connection",
]

DETECTION_FEATURES = TEXT_FEATURES + CATEGORICAL_FEATURES

# Excluded from detection model to prevent data leakage and distortion
RESPONSE_FEATURES = [
    "response_http_protocol",
    "response_http_status_code",
    "response_http_status_message",
    "response_content_length",
]

SPARSE_EXCLUDED_FEATURES = [
    "request_do_not_track",
]

# All 14 multi-label CAPEC attack targets in the original dataset
ALL_LABEL_COLUMNS = [
    "000 - Normal",
    "272 - Protocol Manipulation",
    "242 - Code Injection",
    "88 - OS Command Injection",
    "126 - Path Traversal",
    "66 - SQL Injection",
    "16 - Dictionary-based Password Attack",
    "310 - Scanning for Vulnerable Software",
    "153 - Input Data Manipulation",
    "248 - Command Injection",
    "274 - HTTP Verb Tampering",
    "194 - Fake the Source of Data",
    "34 - HTTP Response Splitting",
    "33 - HTTP Request Smuggling",
]

# Excluded from supervised training due to having only 1 positive sample
RARE_LABEL = "248 - Command Injection"

# 13 Attack labels used for supervised model training and evaluation
MODEL_LABEL_COLUMNS = [col for col in ALL_LABEL_COLUMNS if col != RARE_LABEL]

# Experimental parameters
RANDOM_STATE = 42
TEST_SIZE = 0.20

# Model and Preprocessor artifact paths
MODEL_PATH = MODELS_DIR / "detection_model.joblib"
PREPROCESSOR_PATH = MODELS_DIR / "detection_preprocessor.joblib"

# Output artifacts
DETECTION_OUTPUT_CSV = RESULTS_DIR / "detection_output.csv"
CORRELATION_INPUT_CSV = RESULTS_DIR / "correlation_input.csv"

