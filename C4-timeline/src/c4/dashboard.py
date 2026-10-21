"""Streamlit dashboard. Run: streamlit run src/c4/dashboard.py"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.express as px
import streamlit as st

from c4.data_loading import REPORTS_DIR

st.set_page_config(page_title="C4 Dataset Inventory", layout="wide")
st.title("C4 - CAM-LDS dataset inventory")

path = REPORTS_DIR / "dataset_inventory.json"
if not path.exists():
    st.warning("reports/dataset_inventory.json not found. Run: python scripts/run_inventory.py")
    st.stop()

inv = json.loads(path.read_text(encoding="utf-8"))
rows = [{"archive": a["archive"], "present": a["present"], "readable": a["readable"], "files": a.get("n_files", 0)}
        for a in inv["archives"]]
df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True)
st.plotly_chart(px.bar(df, x="archive", y="files", title="Files per archive"), use_container_width=True)
st.subheader("Issues")
st.json(inv["issues"])
