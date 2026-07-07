
# ============================================================
# KPMD ME&L STREAMLIT DASHBOARD
# Run with: streamlit run kpmd_dashboard_app.py
# ============================================================
import io
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="KPMD ME&L Dashboard", layout="wide")

MONTH_ORDER = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05"]
COUNTY_ORDER = ["Overall", "Samburu", "Kajiado", "Narok"]
GROUP_ORDER = ["KPMD", "Non-KPMD", "All"]

@st.cache_data
def load_data():
    monthly = pd.read_csv("kpmd_outputs/monthly_summary.csv")
    comparison = pd.read_csv("kpmd_outputs/kpmd_vs_non_kpmd_comparison.csv")
    baseline = pd.read_csv("kpmd_outputs/baseline_midline_comparison.csv")
    cleaned = pd.read_csv("kpmd_outputs/03_outlier_cleaned_dataset.csv")
    outliers = pd.read_csv("kpmd_outputs/04_outlier_log.csv")
    zeros = pd.read_csv("kpmd_outputs/05_zero_flag_log.csv")
    return monthly, comparison, baseline, cleaned, outliers, zeros

monthly, comparison, baseline, cleaned, outliers, zeros = load_data()

st.title("KPMD Household Monitoring ME&L Dashboard")
st.caption("Monthly analysis for Jan-May comparing KPMD and Non-KPMD households")

# Sidebar filters
st.sidebar.header("Filters")
county = st.sidebar.selectbox("Dashboard / County", COUNTY_ORDER, index=0)
months = st.sidebar.multiselect("Month", MONTH_ORDER, default=MONTH_ORDER)
groups = st.sidebar.multiselect("Group", GROUP_ORDER, default=["KPMD", "Non-KPMD"] if "KPMD" in GROUP_ORDER else GROUP_ORDER)
themes = sorted(monthly["theme"].dropna().unique().tolist())
theme = st.sidebar.selectbox("Indicator theme", ["All"] + themes)

filtered = monthly.copy()
filtered = filtered[filtered["county"].eq(county)]
filtered = filtered[filtered["month_cat"].isin(months)]
filtered = filtered[filtered["group"].isin(groups)]
if theme != "All":
    filtered = filtered[filtered["theme"].eq(theme)]

indicator_options = sorted(filtered["indicator"].dropna().unique().tolist())
if len(indicator_options) == 0:
    st.warning("No data available for the selected filters.")
    st.stop()

indicator = st.sidebar.selectbox("Indicator", indicator_options)
plot_df = filtered[filtered["indicator"].eq(indicator)].copy()

# KPI cards
st.subheader(f"{county} Dashboard: {indicator}")
col1, col2, col3, col4 = st.columns(4)
mean_latest = plot_df.sort_values("month_cat").groupby("group")["mean"].last()
log_latest = plot_df.sort_values("month_cat").groupby("group")["log_mean"].last()
n_obs = plot_df["n_obs"].sum()

with col1:
    st.metric("Total observations", f"{n_obs:,.0f}")
with col2:
    st.metric("Latest KPMD mean", f"{mean_latest.get('KPMD', np.nan):,.2f}")
with col3:
    st.metric("Latest Non-KPMD mean", f"{mean_latest.get('Non-KPMD', np.nan):,.2f}")
with col4:
    diff = mean_latest.get("KPMD", np.nan) - mean_latest.get("Non-KPMD", np.nan)
    st.metric("Latest KPMD - Non-KPMD", f"{diff:,.2f}" if pd.notna(diff) else "NA")

# Charts
st.markdown("### Monthly trend")
fig = px.line(
    plot_df,
    x="month_cat",
    y="mean",
    color="group",
    markers=True,
    category_orders={"month_cat": MONTH_ORDER},
    title=f"Mean trend: {indicator}"
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("### KPMD vs Non-KPMD comparison")
fig2 = px.bar(
    plot_df,
    x="month_cat",
    y="mean",
    color="group",
    barmode="group",
    category_orders={"month_cat": MONTH_ORDER},
    title=f"KPMD vs Non-KPMD: {indicator}"
)
st.plotly_chart(fig2, use_container_width=True)

# Tabs
mean_tab, log_tab, baseline_tab, downloads_tab = st.tabs([
    "Mean results", "Log-mean results", "Baseline vs Midline", "Downloads"
])

with mean_tab:
    st.dataframe(plot_df[["county", "month_cat", "group", "theme", "indicator", "unit", "n_obs", "mean", "median", "std", "min", "max"]], use_container_width=True)

with log_tab:
    st.dataframe(plot_df[["county", "month_cat", "group", "theme", "indicator", "unit", "n_obs", "log_mean"]], use_container_width=True)
    fig3 = px.line(
        plot_df,
        x="month_cat",
        y="log_mean",
        color="group",
        markers=True,
        category_orders={"month_cat": MONTH_ORDER},
        title=f"Log mean trend: {indicator}"
    )
    st.plotly_chart(fig3, use_container_width=True)

with baseline_tab:
    st.dataframe(baseline, use_container_width=True)
    fig4 = px.bar(
        baseline,
        x="indicator",
        y=["baseline_kpmd", "baseline_non_kpmd", "midline_kpmd", "midline_non_kpmd"],
        barmode="group",
        title="Baseline and Midline Comparison"
    )
    st.plotly_chart(fig4, use_container_width=True)

with downloads_tab:
    st.markdown("Download key datasets")
    def csv_download_button(df, label, filename):
        st.download_button(
            label=label,
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=filename,
            mime="text/csv"
        )

    csv_download_button(cleaned, "Download outlier-cleaned data", "outlier_cleaned_dataset.csv")
    csv_download_button(monthly, "Download monthly summary", "monthly_summary.csv")
    csv_download_button(comparison, "Download KPMD comparison", "kpmd_vs_non_kpmd_comparison.csv")
    csv_download_button(outliers, "Download outlier log", "outlier_log.csv")
    csv_download_button(zeros, "Download zero flag log", "zero_flag_log.csv")
