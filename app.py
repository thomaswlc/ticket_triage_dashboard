# app.py
from pathlib import Path
import streamlit as st
import pandas as pd
from analysis import load_tickets, apply_triage, compute_kpis, frequency_by, busiest_periods, repeated_incidents

st.set_page_config(page_title="IT Support Triage Dashboard", layout="wide")

st.title("IT Support Ticket Triage Dashboard")

# Data source
st.sidebar.header("Data")
use_sample = st.sidebar.checkbox("Use included sample_tickets.csv", value=True)
uploaded = None
if not use_sample:
    uploaded = st.sidebar.file_uploader("Upload CSV", type=["csv"])

# Load
if use_sample:
    DATA_PATH = Path("data/test_data.csv")
    df_raw = load_tickets(DATA_PATH)
else:
    if uploaded is None:
        st.info("Upload a CSV or select the sample to continue.")
        st.stop()
    df_raw = load_tickets(uploaded)

# Apply triage
df = apply_triage(df_raw.copy())

# Sidebar filters
st.sidebar.header("Filters")
dept_filter = st.sidebar.multiselect("Department", sorted(df["Department"].dropna().unique().tolist()))
type_filter = st.sidebar.multiselect("Issue type", sorted(df["Issue type"].dropna().unique().tolist()))
priority_filter = st.sidebar.multiselect("Suggested priority", sorted(df["Suggested priority"].dropna().unique().tolist()))
status_filter = st.sidebar.multiselect("Status", sorted(df["Status"].dropna().unique().tolist()))

mask = pd.Series([True] * len(df))
if dept_filter:
    mask &= df["Department"].isin(dept_filter)
if type_filter:
    mask &= df["Issue type"].isin(type_filter)
if priority_filter:
    mask &= df["Suggested priority"].isin(priority_filter)
if status_filter:
    mask &= df["Status"].isin(status_filter)

df_f = df[mask]

# KPIs
kpis = compute_kpis(df_f)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total tickets", kpis.get("total_tickets", 0))
col2.metric("Open tickets", kpis.get("open_tickets", 0))
col3.metric("Urgent suggested", kpis.get("urgent_now", 0))
if "avg_resolution_time_h" in kpis:
    col4.metric("Avg resolution (h)", f"{kpis['avg_resolution_time_h']:.1f}")

st.markdown("---")

# Urgent shortlist
st.subheader("Most urgent tickets")
urgent_df = df_f[df_f["Suggested priority"].isin(["Urgent", "High"])].copy()
# Simple recency sort if date present, else by users affected desc
if "Date logged" in urgent_df.columns and pd.api.types.is_datetime64_any_dtype(urgent_df["Date logged"]):
    urgent_df = urgent_df.sort_values(["Suggested priority", "Date logged"], ascending=[False, False])
else:
    if "Number of users affected" in urgent_df.columns:
        urgent_df["Number of users affected"] = pd.to_numeric(urgent_df["Number of users affected"], errors="coerce")
        urgent_df = urgent_df.sort_values(["Suggested priority", "Number of users affected"], ascending=[False, False])

cols_show = ["Ticket ID", "Date logged", "Department", "Issue description", "Issue type",
             "Suggested priority", "Suggested team", "Status", "Number of users affected"]
cols_show = [c for c in cols_show if c in urgent_df.columns]
st.dataframe(urgent_df[cols_show], use_container_width=True, height=300)

# Trends and summaries
left, right = st.columns(2)
with left:
    st.subheader("Top issue types")
    st.bar_chart(frequency_by(df_f, "Issue type"))

    st.subheader("Tickets by priority")
    st.bar_chart(frequency_by(df_f, "Suggested priority"))

with right:
    st.subheader("Busiest periods (weekly)")
    bc = busiest_periods(df_f, "W")
    if not bc.empty:
        st.line_chart(bc)
    else:
        st.info("No valid dates to plot periods.")

    st.subheader("Repeated incidents (top 10)")
    rep = repeated_incidents(df_f, 10)
    st.dataframe(rep, use_container_width=True)

# Full table
st.markdown("---")
st.subheader("All tickets (with triage)")
st.dataframe(df_f, use_container_width=True)

# Download triaged CSV
csv_bytes = df_f.to_csv(index=False).encode("utf-8")
st.download_button("Download triaged CSV", data=csv_bytes, file_name="triaged_tickets.csv", mime="text/csv")
