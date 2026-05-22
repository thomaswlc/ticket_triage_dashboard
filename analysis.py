# analysis.py
# This module contains the data loading, triage application, and KPI computation logic for the IT support ticket triage dashboard.
import pandas as pd
from datetime import datetime
from triage import triage_ticket

DATE_COL = "Date logged"

def load_tickets(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    # Normalize key fields
    if DATE_COL in df.columns:
        df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")
    # Ensure consistent columns
    for c in ["Issue description", "Severity", "Department", "Number of users affected",
              "Escalated or not", "Resolution time", "Status", "Assigned team", "Location"]:
        if c not in df.columns:
            df[c] = None
    return df

def apply_triage(df: pd.DataFrame) -> pd.DataFrame:
    triaged = df.apply(lambda row: triage_ticket(row.to_dict()), axis=1, result_type="expand")
    return pd.DataFrame(triaged)

def compute_kpis(df: pd.DataFrame) -> dict:
    kpis = {}
    kpis["total_tickets"] = len(df)
    kpis["open_tickets"] = int((df["Status"].astype(str).str.lower().isin(["open", "in progress", "new"])).sum())
    kpis["urgent_now"] = int((df["Suggested priority"] == "Urgent").sum())
    # Average resolution time if numeric hours or parseable
    if "Resolution time" in df.columns:
        rt = pd.to_numeric(df["Resolution time"], errors="coerce")
        if rt.notna().any():
            kpis["avg_resolution_time_h"] = float(rt.mean())
    return kpis

def frequency_by(df: pd.DataFrame, col: str) -> pd.Series:
    return df[col].value_counts().sort_values(ascending=False)

def busiest_periods(df: pd.DataFrame, freq: str = "W") -> pd.Series:
    if DATE_COL not in df or not pd.api.types.is_datetime64_any_dtype(df[DATE_COL]):
        return pd.Series(dtype=int)
    s = df.set_index(DATE_COL).sort_index()
    return s.resample(freq).size()

def repeated_incidents(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    # Simple heuristic: same Department + Issue type + Location recurring
    grp = df.groupby(["Department", "Issue type", "Location"]).size().reset_index(name="Count")
    return grp.sort_values("Count", ascending=False).head(top_n)
