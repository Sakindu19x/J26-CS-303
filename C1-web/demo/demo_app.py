"""
PP1 Demo - Multi-Label Web Attack Detection (simple version)
Component 1: Adaptive Web Attack Detection & Correlation Model
Final Year Research - Group J26-CS-303

A thin page over the saved model files: it loads them and adds no logic.
The previous, larger version is kept in demo_app_full.py.

Run from the RA 1 folder:
    python -m streamlit run demo/demo_app.py
"""

from pathlib import Path
from urllib.parse import quote, quote_plus

import joblib
import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent   # the RA 1 folder (this file lives in RA 1/demo)
THRESHOLD = 0.5

st.set_page_config(page_title="Web Attack Detection", page_icon="🛡️", layout="centered")


# ---------------------------------------------------------------- load once
@st.cache_resource(show_spinner="Loading the trained model...")
def load_model():
    return (
        joblib.load(ROOT / "models" / "detection_model.joblib"),
        joblib.load(ROOT / "models" / "detection_preprocessor.joblib"),
    )


@st.cache_data(show_spinner="Loading the test set...")
def load_test_set():
    return (
        joblib.load(ROOT / "Dataset" / "processed" / "X_test.joblib"),
        joblib.load(ROOT / "Dataset" / "processed" / "y_test.joblib"),
    )


model, preprocessor = load_model()
X_test, y_test = load_test_set()
LABELS = list(y_test.columns)


@st.cache_data(show_spinner="Preparing example row numbers...")
def example_rows(per_type=5, candidates=60):
    """
    Example test row numbers per attack type (ones the model gets fully right), plus
    multi-label examples and known misses, so they can be typed into the row box.
    """
    def correct_ids(ids):
        ids = list(ids[:candidates])
        if not ids:
            return [], []
        predicted = model.predict(preprocessor.transform(X_test.loc[ids]))
        right = (predicted == y_test.loc[ids].values).all(axis=1)
        return [i for i, ok in zip(ids, right) if ok], [i for i, ok in zip(ids, right) if not ok]

    rows = []
    for label in LABELS:
        right, _ = correct_ids(y_test.index[y_test[label] == 1])
        rows.append({"Attack type": label, "Row numbers": ", ".join(map(str, right[:per_type]))})
    right, _ = correct_ids(y_test.index[y_test.values.sum(axis=1) >= 2])
    rows.append({"Attack type": "Several attacks at once (multi-label)", "Row numbers": ", ".join(map(str, right[:per_type]))})
    _, missed = correct_ids(y_test.index[y_test["33 - HTTP Request Smuggling"] == 1])
    rows.append({"Attack type": "Known misses (model gets it wrong)", "Row numbers": ", ".join(map(str, missed[:per_type]))})
    return pd.DataFrame(rows)


def predict(request_df):
    return model.predict_proba(preprocessor.transform(request_df))[0]


def detected(probabilities):
    return [label for label, p in zip(LABELS, probabilities) if p >= THRESHOLD]


def show_output(probabilities):
    """The model's answer: detected labels first, then all 13 probabilities."""
    found = detected(probabilities)
    attacks = [label for label in found if label != "000 - Normal"]
    if attacks:
        st.error("**Attack detected:** " + ", ".join(attacks))
    elif found:
        st.success("**Normal request**")
    else:
        st.warning("**No label reached 50%**")

    table = pd.DataFrame({"Label": LABELS, "Probability": np.asarray(probabilities) * 100})
    table = table.sort_values("Probability", ascending=False)
    with st.expander("See all 13 probabilities"):
        st.dataframe(
            table,
            hide_index=True,
            column_config={
                "Probability": st.column_config.ProgressColumn(
                    "Probability (%)", min_value=0, max_value=100, format="%.1f%%"
                )
            },
        )


# ---------------------------------------------------------------- header
st.title("🛡️ Web Attack Detection")
st.caption(
    "Detects 13 CAPEC attack types in HTTP requests · One-vs-Rest Logistic Regression · "
    "trained on SR-BH 2020 · this page only loads the saved model"
)

tab_results, tab_test, tab_type = st.tabs(["1 · Results", "2 · Test a request", "3 · Type a request"])


# ---------------------------------------------------------------- 1. results
with tab_results:
    st.markdown("Tested on **181,014 requests** the model never saw during training.")

    overall = pd.read_csv(ROOT / "results" / "detection_overall_metrics.csv").set_index("Metric")["Value"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Micro F1", f"{overall['Micro F1-Score']:.3f}", help="Overall score across all label decisions")
    c2.metric("Macro F1", f"{overall['Macro F1-Score']:.3f}", help="Average where every attack type counts equally")
    c3.metric("Wrong decisions", f"{overall['Hamming Loss'] * 100:.2f}%", help="Hamming loss: share of the 13 yes/no decisions that were wrong")

    per_label = pd.read_csv(ROOT / "results" / "detection_per_label_metrics.csv", index_col=0)
    recall = pd.DataFrame({
        "Attack type": per_label.index,
        "Caught (recall)": per_label["recall"].values * 100,
        "Test requests": per_label["support"].astype(int).values,
    }).sort_values("Caught (recall)", ascending=False)

    st.markdown("**How many of each type the model catches**")
    st.dataframe(
        recall,
        hide_index=True,
        column_config={
            "Caught (recall)": st.column_config.ProgressColumn(
                "Caught (recall)", min_value=0, max_value=100, format="%.1f%%"
            )
        },
    )
    st.info(
        "**Weakness:** the three rarest types (Smuggling, Protocol Manipulation, OS Command "
        "Injection) are caught only 48-64% of the time. Next step: a separate threshold per label."
    )


# ---------------------------------------------------------------- 2. test a request
def show_test_row(row_id):
    """Input -> model output -> proof that the output tallies with the dataset label."""
    sample = X_test.loc[[row_id]]
    actual = [label for label, v in zip(LABELS, y_test.loc[row_id].values) if v == 1]
    probabilities = predict(sample)
    found = detected(probabilities)

    # ------------------------------------------------ input
    st.markdown(f"**Input** · test row `{row_id}`")
    st.code(f"{sample['request_http_method'].iloc[0]} {sample['request_http_request'].iloc[0]}", language=None, wrap_lines=True)
    if str(sample["request_body"].iloc[0]).strip():
        st.code(str(sample["request_body"].iloc[0])[:400], language=None, wrap_lines=True)
    with st.expander("All input fields the model used"):
        fields = sample.iloc[0]
        st.dataframe(
            pd.DataFrame({"Field": fields.index, "Value": [str(v)[:150] or "(empty)" for v in fields.values]}),
            hide_index=True,
        )

    # ------------------------------------------------ output
    st.markdown("**Model output**")
    show_output(probabilities)

    # ------------------------------------------------ proof
    st.markdown("---")
    st.subheader("Proof: model output vs the dataset's label")
    p1, p2 = st.columns(2)
    p1.markdown(f"**Test row:** `{row_id}`  \n**Source:** `X_test.joblib` (input) and `y_test.joblib` (true label)")
    p2.markdown("**Model:** `detection_model.joblib`  \n**Rule:** a label is detected if its probability ≥ 50%")

    proof = pd.DataFrame({
        "Label": LABELS,
        "Dataset": ["✔" if label in actual else "" for label in LABELS],
        "Model": ["✔" if label in found else "" for label in LABELS],
        "Prob. %": (np.asarray(probabilities) * 100).round(2),
    })
    proof["Tallies"] = np.where(proof["Dataset"] == proof["Model"], "✅", "❌")
    relevant = proof[(proof["Dataset"] != "") | (proof["Model"] != "")]
    st.dataframe(
        relevant,
        hide_index=True,
        width="stretch",
        column_config={
            "Label": st.column_config.TextColumn("Label", width="medium"),
            "Dataset": st.column_config.TextColumn("Dataset", width="small"),
            "Model": st.column_config.TextColumn("Model", width="small"),
            "Prob. %": st.column_config.NumberColumn("Prob. %", width="small"),
            "Tallies": st.column_config.TextColumn("Tallies", width="small"),
        },
    )
    st.caption(f"The other {len(proof) - len(relevant)} labels are absent in both the dataset and the prediction.")

    if set(found) == set(actual):
        st.success(f"✅ Tallied: for row {row_id}, the model's output matches the dataset label on all 13 labels.")
    else:
        st.error(f"❌ Not tallied: for row {row_id}, the model's output differs from the dataset label.")


with tab_test:
    st.markdown(
        "Type a **test row number**. The request comes from the held-out test set "
        "(`Dataset/processed/X_test.joblib`, never used in training), so its true label is known."
    )

    row_text = st.text_input("Test row number", value="443732")

    with st.expander("📋 Example row numbers (copy any into the box above)"):
        examples = example_rows()
        st.dataframe(examples, hide_index=True, height=(len(examples) + 1) * 35 + 3)
        st.caption(
            "Any row number from `Dataset/processed/readable/test_sample.csv` also works. "
            "The row number is the request's row in the original `data_capec_multilabel.csv`."
        )

    row_id = int(row_text.strip()) if row_text.strip().isdigit() else None
    if row_id is None:
        st.warning("Please type a whole number, e.g. 443732.")
    elif row_id not in X_test.index:
        st.warning(f"Row {row_id} is not in the test set (it may be a training row). Pick one from the examples.")
    else:
        show_test_row(row_id)


# ---------------------------------------------------------------- 3. type a request
EXAMPLES = {
    "Normal page": "/blog/index.php/2020/03/22/hello-world/",
    "SQL Injection": "/blog/index.php?id=1' UNION ALL SELECT username,password FROM users-- -",
    "Path Traversal": "/blog/index.php?page=../../../../etc/passwd",
    "Code Injection": "/blog/index.php?q=${@print(chr(122).chr(97))}",
    "Response Splitting": "/blog/index.php?url=any\r\nSet-cookie: Tamper=1",
    "OS Command Injection (known miss)": "/blog/index.php?ver=1';cat /etc/passwd",
}


def encode_uri(uri):
    """Percent-encode a typed URL the way a web server log stores it."""
    path, has_query, query = uri.partition("?")
    path = quote(path, safe="/")
    if not has_query:
        return path
    pairs = []
    for pair in query.split("&"):
        key, eq, value = pair.partition("=")
        pairs.append(quote_plus(key) + eq + quote_plus(value))
    return path + "?" + "&".join(pairs)


with tab_type:
    st.markdown("Type a request URL, or load an example.")
    example = st.selectbox("Example", ["(type my own)"] + list(EXAMPLES))
    method = st.radio("Method", ["GET", "POST"], horizontal=True)
    uri = st.text_input("Request URL", value=EXAMPLES.get(example, "/blog/index.php?id=5 OR 1=1"), key=f"uri_{example}")

    if uri.strip():
        request = {column: "" for column in X_test.columns}
        request.update({
            "request_http_method": method,
            "request_http_protocol": "HTTP/1.1",
            "request_host": "test-site.com",
            "request_http_request": encode_uri(uri),
        })
        request_df = pd.DataFrame([request])[X_test.columns]

        st.markdown("**Input** · encoded the way a server log stores it")
        st.code(f"{method} {request['request_http_request']}", language=None, wrap_lines=True)

        st.markdown("**Model output**")
        show_output(predict(request_df))
