import os
import re

import google.generativeai as genai
import pandas as pd
import streamlit as st
from google.cloud import bigquery
from google.api_core.exceptions import NotFound

PROJECT_ID = os.environ["GCP_PROJECT_ID"]

st.set_page_config(page_title="Israel Alarms Intelligence", layout="wide")
st.title("Israel Alarms Dashboard")

client = bigquery.Client(project=PROJECT_ID)


@st.cache_data(ttl=300)
def query(sql: str):
    return client.query(sql).to_dataframe()


tab_data, tab_map, tab_chat = st.tabs(["Data", "Map", "Ask Me About the Data"])

with tab_data:
    st.subheader("Tzeva Adom Alerts")

    col_search, col_cat, col_date = st.columns([3, 2, 2])
    with col_search:
        search = st.text_input("Search city", placeholder="e.g. Tel Aviv")
    with col_cat:
        cat_filter = st.text_input("Category description", placeholder="e.g. Missile")
    with col_date:
        date_range = st.date_input("Date range", value=[], key="date_range")

    try:
        df = query(f"SELECT * FROM `{PROJECT_ID}.analysis_dataset.fct_alerts` ORDER BY alerted_at DESC")

        if search:
            df = df[df["city"].str.contains(search, case=False, na=False)]
        if cat_filter:
            df = df[df["category_desc"].str.contains(cat_filter, case=False, na=False)]
        if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
            start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
            df = df[(df["alert_date"] >= start.date()) & (df["alert_date"] <= end.date())]

        # Metrics row
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Alerts", f"{len(df):,}")
        m2.metric("Cities Affected", df["city"].nunique() if "city" in df.columns else "-")
        m3.metric("Categories", df["category_desc"].nunique() if "category_desc" in df.columns else "-")
        if "alerted_at" in df.columns and not df.empty:
            earliest = df["alerted_at"].min()
            latest = df["alerted_at"].max()
            m4.metric("Tracking Since", str(earliest)[:10])
            m5.metric("Latest Alert", str(latest)[:16])
        else:
            m4.metric("Tracking Since", "-")
            m5.metric("Latest Alert", "-")

        st.divider()

        if not df.empty:
            ch1, ch2 = st.columns(2)
            with ch1:
                st.markdown("**Alerts by Category**")
                st.bar_chart(df["category_desc"].value_counts().head(10))
            with ch2:
                st.markdown("**Alerts by Hour of Day**")
                if "alert_hour" in df.columns:
                    st.bar_chart(df["alert_hour"].value_counts().sort_index())

            st.markdown("**Alerts Over Time**")
            if "alert_date" in df.columns:
                st.line_chart(df.groupby("alert_date").size().rename("alerts"))

        st.divider()
        st.markdown(f"**{len(df):,} rows** — scroll to explore")
        st.dataframe(df, use_container_width=True, height=400)

    except NotFound:
        st.warning("Alerts table not found yet. Run the pipeline to populate data.")

with tab_map:
    st.subheader("Alert Heatmap")
    try:
        df_map = query(f"""
            SELECT
                latitude,
                longitude,
                city,
                COUNT(*) as alert_count
            FROM `{PROJECT_ID}.analysis_dataset.fct_alerts`
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            GROUP BY latitude, longitude, city
            ORDER BY alert_count DESC
        """)

        if df_map.empty:
            st.warning("No location data available yet.")
        else:
            top_city = df_map.iloc[0]

            c1, c2, c3 = st.columns(3)
            c1.metric("Cities on Map", f"{len(df_map):,}")
            c2.metric("Most Targeted", top_city["city"])
            c3.metric("Alerts There", f"{int(top_city['alert_count']):,}")

            st.divider()

            # Scale dot size by alert count
            df_map["size"] = (
                (df_map["alert_count"] - df_map["alert_count"].min())
                / (df_map["alert_count"].max() - df_map["alert_count"].min() + 1)
                * 40000
                + 3000
            )

            st.map(
                df_map.rename(columns={"latitude": "lat", "longitude": "lon"}),
                latitude="lat",
                longitude="lon",
                size="size",
                color="#ff4b4b",
            )

            st.divider()
            st.markdown("**Top 10 Most Targeted Cities**")
            st.dataframe(
                df_map[["city", "alert_count"]].head(10).reset_index(drop=True),
                use_container_width=True,
                column_config={"alert_count": st.column_config.ProgressColumn(
                    "Alert Count",
                    min_value=0,
                    max_value=int(df_map["alert_count"].max()),
                )},
            )

    except NotFound:
        st.warning("Alerts table not found yet. Run the pipeline to populate data.")

with tab_chat:
    st.subheader("Ask Me About the Data")
    st.caption("Powered by Gemini 2.5 Pro — ask anything about the alerts dataset.")

    SCHEMA = """
    Table: `{project}.analysis_dataset.fct_alerts`
    Columns:
      - alarm_id        INTEGER   primary key
      - city            STRING    city or area name (may include district, e.g. "Haifa - North")
      - category        INTEGER   numeric category code
      - category_desc   STRING    human-readable category (e.g. "Missile", "Hostile aircraft intrusion")
      - matrix_id       INTEGER   alert matrix zone id
      - alerted_at      TIMESTAMP when the alarm fired (UTC)
      - ingested_at     TIMESTAMP when the record was ingested
      - alert_date      DATE      date of alert in Asia/Jerusalem timezone
      - alert_time      TIME      time of alert in Asia/Jerusalem timezone
      - alert_hour      INTEGER   hour (0-23) in Asia/Jerusalem timezone
      - alert_day_of_week INTEGER day of week (1=Sunday … 7=Saturday) in Asia/Jerusalem timezone
      - city_id         INTEGER   city lookup id
      - population      INTEGER   city population
      - latitude        FLOAT     city latitude
      - longitude       FLOAT     city longitude
    """.format(project=PROJECT_ID)

    SQL_PROMPT = """You are a BigQuery SQL expert. Given the schema below and a user question,
write a single valid BigQuery SQL query that answers it. Return ONLY the SQL, no explanation, no markdown.

{schema}

Question: {question}
"""

    ANSWER_PROMPT = """You are an analyst for an Israel rocket alert monitoring system.
The user asked: "{question}"
The SQL query returned these results:
{results}
Answer in 1-3 clear sentences. Be direct and specific with numbers. If results are empty, say so."""

    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if not gemini_key:
        st.error("GEMINI_API_KEY environment variable is not set.")
    else:
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel("gemini-2.5-pro")

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Ask a question about the alerts data..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        # Step 1: generate SQL
                        sql_response = model.generate_content(
                            SQL_PROMPT.format(schema=SCHEMA, question=prompt)
                        )
                        sql = sql_response.text.strip()
                        sql = re.sub(r"^```sql\s*|^```\s*|```$", "", sql, flags=re.MULTILINE).strip()

                        # Step 2: run SQL on BigQuery
                        result_df = client.query(sql).to_dataframe()
                        results_str = result_df.to_string(index=False) if not result_df.empty else "No results."

                        # Step 3: answer in natural language
                        answer_response = model.generate_content(
                            ANSWER_PROMPT.format(question=prompt, results=results_str)
                        )
                        answer = answer_response.text.strip()

                        st.markdown(answer)

                        with st.expander("SQL used"):
                            st.code(sql, language="sql")

                        if not result_df.empty:
                            with st.expander("Raw results"):
                                st.dataframe(result_df, use_container_width=True)

                        st.session_state.chat_history.append({"role": "assistant", "content": answer})

                    except Exception as e:
                        err = f"Error: {e}"
                        st.error(err)
                        st.session_state.chat_history.append({"role": "assistant", "content": err})
