import os

import streamlit as st
from google.cloud import bigquery

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
DATASET = "alarms"

st.set_page_config(page_title="Israel Alarms Intelligence", layout="wide")
st.title("Israel Alarms Intelligence Dashboard")

client = bigquery.Client(project=PROJECT_ID)


@st.cache_data(ttl=300)
def query(sql: str):
    return client.query(sql).to_dataframe()


tab_alerts, tab_weather, tab_sitrep = st.tabs(["Alerts", "Weather", "Daily Sitrep"])

with tab_alerts:
    st.subheader("Tzeva Adom Alerts")
    df = query(f"SELECT * FROM `{PROJECT_ID}.{DATASET}.alerts` ORDER BY alert_time DESC LIMIT 500")
    st.dataframe(df, use_container_width=True)

with tab_weather:
    st.subheader("Weather Context")
    df = query(f"SELECT * FROM `{PROJECT_ID}.{DATASET}.weather` ORDER BY recorded_at DESC LIMIT 500")
    st.dataframe(df, use_container_width=True)

with tab_sitrep:
    st.subheader("Daily Sitrep")
    df = query(f"SELECT * FROM `{PROJECT_ID}.{DATASET}.sitrep` ORDER BY report_date DESC LIMIT 30")
    for _, row in df.iterrows():
        with st.expander(str(row.get("report_date", ""))):
            st.markdown(row.get("content", ""))
