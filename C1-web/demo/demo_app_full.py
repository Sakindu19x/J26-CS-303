"""
PP1 Visual Demonstration - Multi-Label Web Attack Detection
Component 1: Adaptive Web Attack Detection & Correlation Model
Final Year Research - Group J26-CS-303

Run from the RA 1 folder:
    python -m streamlit run demo/demo_app_full.py
"""

from pathlib import Path
from urllib.parse import quote, quote_plus

import altair as alt
import joblib
import numpy as np
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent   # the RA 1 folder (this file lives in RA 1/demo)
MODEL_DIR = PROJECT_ROOT / "models"
DATA_DIR = PROJECT_ROOT / "Dataset" / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"

THRESHOLD = 0.5

st.set_page_config(
    page_title="Web Attack Detection Demo",
    page_icon="🛡️",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Loading (cached so the model is only loaded once)
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner="Loading trained model...")
def load_model():
    model = joblib.load(MODEL_DIR / "detection_model.joblib")
    preprocessor = joblib.load(MODEL_DIR / "detection_preprocessor.joblib")
    return model, preprocessor


@st.cache_data(show_spinner="Loading held-out test set...")
def load_test_data():
    X_test = joblib.load(DATA_DIR / "X_test.joblib")
    y_test = joblib.load(DATA_DIR / "y_test.joblib")
    return X_test, y_test


@st.cache_data(show_spinner="Running the model on all 181,014 test requests...")
def predict_all_test():
    model, preprocessor = load_model()
    X_test, _ = load_test_data()
    return model.predict(preprocessor.transform(X_test))


model, preprocessor = load_model()
X_test, y_test = load_test_data()
LABELS = list(y_test.columns)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def encode_uri(uri):
    """Percent-encode a typed URI the way a browser / web server log stores it."""
    path, has_query, query = uri.partition("?")
    path = quote(path, safe="/")
    if not has_query:
        return path
    encoded_pairs = []
    for pair in query.split("&"):
        key, has_equals, value = pair.partition("=")
        encoded_pairs.append(quote_plus(key) + has_equals + quote_plus(value))
    return path + "?" + "&".join(encoded_pairs)


def build_request(uri, method, body):
    request = {column: "" for column in X_test.columns}
    request["request_http_method"] = method
    request["request_http_protocol"] = "HTTP/1.1"
    request["request_host"] = "test-site.com"
    request["request_http_request"] = encode_uri(uri)
    request["request_body"] = body
    return pd.DataFrame([request])[X_test.columns]


def predict(request_df):
    return model.predict_proba(preprocessor.transform(request_df))[0]


def show_verdict(probabilities):
    detected = [
        (label, p) for label, p in zip(LABELS, probabilities) if p >= THRESHOLD
    ]
    attacks = [(label, p) for label, p in detected if label != "000 - Normal"]

    if attacks:
        names = ", ".join(f"**{label}** ({p * 100:.1f}%)" for label, p in attacks)
        st.error(f"🚨 Attack detected: {names}")
    elif detected:
        st.success(f"✅ Normal request ({detected[0][1] * 100:.1f}% confidence)")
    else:
        top_label, top_p = max(zip(LABELS, probabilities), key=lambda x: x[1])
        st.warning(
            f"⚠️ No label reached {THRESHOLD:.0%}. "
            f"Highest: {top_label} ({top_p * 100:.1f}%)"
        )


def probability_chart(probabilities, actual=None):
    chart_df = pd.DataFrame({
        "Attack Label": LABELS,
        "Probability (%)": (np.asarray(probabilities) * 100).round(2),
    })
    detected = chart_df["Probability (%)"] >= THRESHOLD * 100
    chart_df["Decision"] = np.select(
        [detected & (chart_df["Attack Label"] == "000 - Normal"), detected],
        ["Normal", "Attack detected"],
        default="Not detected",
    )
    if actual is not None:
        chart_df["Actual"] = np.where(np.asarray(actual) == 1, "Yes", "No")

    bars = alt.Chart(chart_df).mark_bar(cornerRadiusEnd=3).encode(
        x=alt.X("Probability (%):Q", scale=alt.Scale(domain=[0, 100]), title="Probability (%)"),
        y=alt.Y(
            "Attack Label:N", sort=None, title=None,
            axis=alt.Axis(labelLimit=320, labelOverlap=False),
        ),
        color=alt.Color(
            "Decision:N",
            scale=alt.Scale(
                domain=["Attack detected", "Normal", "Not detected"],
                range=["#d64545", "#2e9e5b", "#9aa5b1"],
            ),
            legend=alt.Legend(orient="bottom", title=None),
        ),
        tooltip=list(chart_df.columns),
    )
    rule = alt.Chart(pd.DataFrame({"x": [THRESHOLD * 100]})).mark_rule(
        strokeDash=[4, 4], color="#555"
    ).encode(x=alt.X("x:Q", title="Probability (%)"))
    st.altair_chart((bars + rule).properties(height=450), use_container_width=True)


def results_table(probabilities, actual):
    table = pd.DataFrame({
        "Attack Label": LABELS,
        "Probability (%)": (np.asarray(probabilities) * 100).round(4),
        "Predicted": (np.asarray(probabilities) >= THRESHOLD).astype(int),
        "Actual": np.asarray(actual).astype(int),
    })
    table["Correct"] = np.where(table["Predicted"] == table["Actual"], "✅", "❌")
    return table


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("🛡️ Multi-Label Web Attack Detection")
st.caption(
    "Component 1 — Adaptive Web Attack Detection & Correlation Model · "
    "One-vs-Rest Logistic Regression · SR-BH 2020 dataset · 13 CAPEC labels"
)

tab_test, tab_batch, tab_live, tab_perf = st.tabs([
    "🗂️ Test set: one request",
    "📋 Test set: batch run",
    "🔍 Type a request",
    "📊 Model performance",
])


# ---------------------------------------------------------------------------
# Tab 1: Live request
# ---------------------------------------------------------------------------

EXAMPLES = {
    "Normal - blog post": ("GET", "/blog/index.php/2020/03/22/hello-world/", ""),
    "Normal - page query": ("GET", "/blog/index.php?p=1", ""),
    "SQL Injection - UNION": (
        "GET", "/blog/index.php?id=1' UNION ALL SELECT username,password FROM users-- -", ""
    ),
    "SQL Injection - time based": ("GET", "/blog/index.php?id=1) AND SLEEP(5)#", ""),
    "Path Traversal": ("GET", "/blog/index.php?page=../../../../etc/passwd", ""),
    "Code Injection": ("GET", "/blog/index.php?q=${@print(chr(122).chr(97))}", ""),
    "HTTP Response Splitting": (
        "GET", "/blog/index.php?url=any\r\nSet-cookie: Tamper=1", ""
    ),
    "OS Command Injection (known miss)": (
        "GET", "/blog/index.php?ver=1';cat /etc/passwd", ""
    ),
}

with tab_live:
    st.markdown(
        "Type an HTTP request, or pick an example. The URL is percent-encoded "
        "exactly as a web server log stores it, then passed through the saved "
        "TF-IDF + One-Hot preprocessor and the trained model."
    )

    example = st.selectbox("Load an example", ["(type my own)"] + list(EXAMPLES))
    default_method, default_uri, default_body = EXAMPLES.get(
        example, ("GET", "/blog/index.php?id=5 OR 1=1", "")
    )

    col_method, col_uri = st.columns([1, 6])
    methods = ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"]
    method = col_method.selectbox(
        "Method", methods, index=methods.index(default_method), key=f"m_{example}"
    )
    uri = col_uri.text_input("Request URI", value=default_uri, key=f"u_{example}")
    body = st.text_area(
        "Request body (optional)", value=default_body, height=70, key=f"b_{example}"
    )

    if uri.strip():
        request_df = build_request(uri, method, body)
        probabilities = predict(request_df)

        st.markdown("**Encoded request sent to the model:**")
        st.code(f"{method} {request_df['request_http_request'].iloc[0]}", language=None)

        show_verdict(probabilities)
        probability_chart(probabilities)

        with st.expander("All 13 label probabilities"):
            st.dataframe(
                pd.DataFrame({
                    "Attack Label": LABELS,
                    "Probability (%)": (probabilities * 100).round(4),
                    "Detected": np.where(probabilities >= THRESHOLD, "Yes", ""),
                }),
                hide_index=True,
                use_container_width=True,
            )


# ---------------------------------------------------------------------------
# Tab 2: Held-out test set
# ---------------------------------------------------------------------------

with tab_test:
    st.markdown(
        "These requests come from the **20% held-out test set (181,014 requests)** "
        "that the model never saw during training, so the true labels are known."
    )

    y_values = y_test.values
    label_counts = y_values.sum(axis=1)
    normal_col = LABELS.index("000 - Normal")

    choice = st.radio(
        "Show me",
        [
            "A random normal request",
            "A random attack request",
            "A specific attack type",
            "A multi-label attack (2+ labels)",
            "A request the model gets wrong",
        ],
        horizontal=True,
    )

    if choice == "A random normal request":
        pool = np.where(y_values[:, normal_col] == 1)[0]
    elif choice == "A random attack request":
        pool = np.where(y_values[:, normal_col] == 0)[0]
    elif choice == "A specific attack type":
        attack_type = st.selectbox(
            "Attack type", [label for label in LABELS if label != "000 - Normal"]
        )
        pool = np.where(y_values[:, LABELS.index(attack_type)] == 1)[0]
    elif choice == "A multi-label attack (2+ labels)":
        all_predictions = predict_all_test()
        pool = np.where(
            (label_counts >= 2) & (all_predictions == y_values).all(axis=1)
        )[0]
        st.caption(
            f"{len(pool):,} of {int((label_counts >= 2).sum()):,} multi-label requests "
            "have all 13 labels predicted correctly (69.65%)."
        )
    else:
        all_predictions = predict_all_test()
        pool = np.where((all_predictions != y_values).any(axis=1))[0]

    if "pick_seed" not in st.session_state:
        st.session_state.pick_seed = 0
    if st.button("🎲 Pick another"):
        st.session_state.pick_seed += 1

    rng = np.random.default_rng(st.session_state.pick_seed)
    position = int(rng.choice(pool))
    sample = X_test.iloc[[position]]
    actual = y_values[position]
    probabilities = predict(sample)

    st.caption(f"Pool size: {len(pool):,} requests · showing test row {sample.index[0]}")

    st.markdown("**HTTP request:**")
    st.code(
        f"{sample['request_http_method'].iloc[0]} {sample['request_http_request'].iloc[0]}",
        language=None,
    )
    if str(sample["request_body"].iloc[0]).strip():
        st.markdown("**Body:**")
        st.code(str(sample["request_body"].iloc[0])[:500], language=None)

    show_verdict(probabilities)

    left, right = st.columns([1, 1])
    with left:
        probability_chart(probabilities, actual)
    with right:
        table = results_table(probabilities, actual)
        predicted_names = table.loc[table["Predicted"] == 1, "Attack Label"].tolist()
        actual_names = table.loc[table["Actual"] == 1, "Attack Label"].tolist()
        st.markdown(f"**Predicted:** {', '.join(predicted_names) or 'none'}")
        st.markdown(f"**Actual:** {', '.join(actual_names)}")
        if (table["Predicted"] == table["Actual"]).all():
            st.success("All 13 labels matched")
        else:
            st.error("Mismatch on at least one label")
        st.dataframe(
            table[["Attack Label", "Probability (%)", "Predicted", "Actual", "Correct"]],
            hide_index=True,
            use_container_width=True,
            height=490,
        )


# ---------------------------------------------------------------------------
# Tab: Batch run on the test set
# ---------------------------------------------------------------------------

def label_names(row):
    return ", ".join(np.array(LABELS)[np.asarray(row) == 1]) or "(none)"


with tab_batch:
    st.markdown(
        "Run the trained model on a random batch of **held-out test requests** "
        "and compare every prediction with the true labels."
    )

    col_size, col_seed = st.columns([3, 1])
    batch_size = col_size.select_slider(
        "Number of test requests", options=[50, 100, 500, 1000, 5000, 10000], value=100
    )
    batch_seed = col_seed.number_input("Random seed", min_value=0, value=42, step=1)

    if st.button("▶️ Run detection on batch", type="primary"):
        rng = np.random.default_rng(int(batch_seed))
        positions = np.sort(rng.choice(len(X_test), size=batch_size, replace=False))
        batch_X = X_test.iloc[positions]
        batch_actual = y_test.values[positions]

        batch_probabilities = model.predict_proba(preprocessor.transform(batch_X))
        batch_predicted = (batch_probabilities >= THRESHOLD).astype(int)
        exact = (batch_predicted == batch_actual).all(axis=1)

        st.session_state.batch = {
            "X": batch_X,
            "actual": batch_actual,
            "predicted": batch_predicted,
            "probabilities": batch_probabilities,
            "exact": exact,
        }

    if "batch" in st.session_state:
        batch = st.session_state.batch
        batch_actual, batch_predicted = batch["actual"], batch["predicted"]
        exact = batch["exact"]
        attack_rows = batch_actual[:, LABELS.index("000 - Normal")] == 0

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Requests analysed", f"{len(exact):,}")
        k2.metric("Attacks in batch", f"{int(attack_rows.sum()):,}")
        k3.metric("All 13 labels correct", f"{exact.mean() * 100:.2f}%")
        k4.metric(
            "Wrong label decisions",
            f"{(batch_predicted != batch_actual).mean() * 100:.3f}%",
            help="Hamming loss on this batch: share of the 13 yes/no decisions that were wrong.",
        )

        batch_table = pd.DataFrame({
            "Match": np.where(exact, "✅", "❌"),
            "Predicted": [label_names(row) for row in batch_predicted],
            "Actual": [label_names(row) for row in batch_actual],
            "Method": batch["X"]["request_http_method"].values,
            "Request URI": batch["X"]["request_http_request"].str.slice(0, 120).values,
            "Test Row": batch["X"].index,
        })

        show = st.radio(
            "Show", ["All requests", "Attacks only", "Mismatches only"], horizontal=True
        )
        if show == "Attacks only":
            batch_table = batch_table[attack_rows]
        elif show == "Mismatches only":
            batch_table = batch_table[~exact]

        st.dataframe(batch_table, hide_index=True, use_container_width=True, height=420)

        st.markdown("**Detected attack types in this batch**")
        counts = pd.DataFrame({
            "Attack Label": LABELS,
            "Actual": batch_actual.sum(axis=0),
            "Predicted": batch_predicted.sum(axis=0),
        })
        counts = counts[(counts["Actual"] > 0) | (counts["Predicted"] > 0)]
        st.dataframe(counts, hide_index=True, use_container_width=True)


# ---------------------------------------------------------------------------
# Tab 3: Model performance
# ---------------------------------------------------------------------------

with tab_perf:
    overall = pd.read_csv(RESULTS_DIR / "detection_overall_metrics.csv").set_index("Metric")["Value"]
    per_label = pd.read_csv(RESULTS_DIR / "detection_per_label_metrics.csv", index_col=0)

    st.markdown("**Evaluated on 181,014 held-out test requests**")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Micro F1", f"{overall['Micro F1-Score']:.4f}")
    m2.metric("Macro F1", f"{overall['Macro F1-Score']:.4f}")
    m3.metric("Hamming Loss", f"{overall['Hamming Loss']:.4f}")
    m4.metric("Micro Precision / Recall", f"{overall['Micro Precision']:.3f} / {overall['Micro Recall']:.3f}")

    st.markdown("**Per-label recall** — rare classes are the main weakness")
    recall_df = per_label.reset_index().rename(columns={"index": "Attack Label"})
    recall_df["Recall (%)"] = (recall_df["recall"] * 100).round(2)
    recall_df["Group"] = np.where(recall_df["recall"] < 0.8, "Below 80%", "80% or higher")
    recall_chart = alt.Chart(recall_df).mark_bar(cornerRadiusEnd=3).encode(
        x=alt.X("Recall (%):Q", scale=alt.Scale(domain=[0, 100])),
        y=alt.Y(
            "Attack Label:N", sort="-x", title=None,
            axis=alt.Axis(labelLimit=320, labelOverlap=False),
        ),
        color=alt.Color(
            "Group:N",
            scale=alt.Scale(domain=["80% or higher", "Below 80%"], range=["#3b7dd8", "#d64545"]),
            legend=alt.Legend(orient="bottom", title=None),
        ),
        tooltip=["Attack Label", "Recall (%)", "support"],
    ).properties(height=450)
    st.altair_chart(recall_chart, use_container_width=True)

    st.dataframe(
        per_label.rename(columns=str.title).round(4),
        use_container_width=True,
    )

    st.markdown("**Pipeline**")
    st.markdown(
        "- 907,815 raw requests → 905,068 after removing 2,746 duplicates + 1 malformed row\n"
        "- 80/20 split → 724,054 train / 181,014 test (`random_state=42`)\n"
        "- TF-IDF (10,000 features each) on URI and body + One-Hot on 12 headers → 34,822 features, fitted on train only\n"
        "- One-vs-Rest Logistic Regression: 13 independent binary classifiers, threshold 0.5\n"
        "- IPs, ports and timestamps kept out of the detector and saved for the correlation stage"
    )
