
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="Retail Dashboard (Demo)", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("Sales Data.csv","us-population-2010-2019 (1)" parse_dates=["OrderDate"])
    return df

df = load_data()


st.title("Retail Sales Dashboard — Streamlit Demo")
st.caption("Follow the 4 pillars: Connect → Clean → Design → Develop")

# ---- Sidebar Filters ----
st.sidebar.header("Filters")

min_date = df["OrderDate"].min().date()
max_date = df["OrderDate"].max().date()
date_range = st.sidebar.date_input("Order Date Range", (min_date, max_date), min_value=min_date, max_value=max_date)

regions = st.sidebar.multiselect("Region", sorted(df["Region"].unique()), default=list(sorted(df["Region"].unique())))
segments = st.sidebar.multiselect("Customer Segment", sorted(df["CustomerSegment"].unique()), default=list(sorted(df["CustomerSegment"].unique())))
categories = st.sidebar.multiselect("Category", sorted(df["Category"].unique()), default=list(sorted(df["Category"].unique())))

# ---- Apply filters ----
mask = (
    (df["OrderDate"].dt.date >= date_range[0]) &
    (df["OrderDate"].dt.date <= date_range[1]) &
    (df["Region"].isin(regions)) &
    (df["CustomerSegment"].isin(segments)) &
    (df["Category"].isin(categories))
)

fdf = df.loc[mask].copy()
fdf["Month"] = fdf["OrderDate"].dt.to_period("M").dt.to_timestamp()

# ---- KPI Cards ----
total_sales = float(fdf["Sales"].sum())
total_profit = float(fdf["Profit"].sum())
orders = int(fdf["OrderID"].nunique())
profit_margin = (total_profit / total_sales) if total_sales else 0.0
avg_order_value = (total_sales / orders) if orders else 0.0

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Sales", f"${total_sales:,.0f}")
kpi2.metric("Total Profit", f"${total_profit:,.0f}")
kpi3.metric("Profit Margin", f"{profit_margin:.1%}")
kpi4.metric("Avg Order Value", f"${avg_order_value:,.0f}")

st.divider()

# ---- Charts ----
# 1) Sales over time
sales_over_time = fdf.groupby("Month", as_index=False)["Sales"].sum()
line_chart = alt.Chart(sales_over_time).mark_line(point=True).encode(
    x=alt.X("Month:T", title="Month"),
    y=alt.Y("Sales:Q", title="Sales"),
    tooltip=["Month:T", alt.Tooltip("Sales:Q", format=",.0f")]
).properties(height=300)
st.subheader("Sales Over Time")
st.altair_chart(line_chart, use_container_width=True)

# 2) Sales by Category
cat = fdf.groupby("Category", as_index=False)["Sales"].sum().sort_values("Sales", ascending=False)
bar_chart = alt.Chart(cat).mark_bar().encode(
    x=alt.X("Sales:Q", title="Sales"),
    y=alt.Y("Category:N", sort="-x"),
    tooltip=[alt.Tooltip("Sales:Q", format=",.0f")]
).properties(height=300)
st.subheader("Sales by Category")
st.altair_chart(bar_chart, use_container_width=True)

# 3) Region vs Profit (scatter)
reg = fdf.groupby("Region", as_index=False).agg({"Sales":"sum", "Profit":"sum"})
scatter = alt.Chart(reg).mark_circle(size=120).encode(
    x=alt.X("Sales:Q", title="Sales"),
    y=alt.Y("Profit:Q", title="Profit"),
    tooltip=[alt.Tooltip("Sales:Q", format=",.0f"), alt.Tooltip("Profit:Q", format=",.0f"), "Region"]
).properties(height=300)
st.subheader("Region: Sales vs Profit")
st.altair_chart(scatter, use_container_width=True)

# 4) Top 10 Products by Sales
top_products = fdf.groupby("Product", as_index=False)["Sales"].sum().sort_values("Sales", ascending=False).head(10)
st.subheader("Top 10 Products by Sales")
st.dataframe(top_products, use_container_width=True, hide_index=True)

# ---- Raw data (filtered) + download ----
with st.expander("Show Filtered Data"):
    st.dataframe(fdf.sort_values("OrderDate"), use_container_width=True)
    st.download_button("Download filtered data as CSV", data=fdf.to_csv(index=False), file_name="filtered_data.csv")

st.caption("Tip: Add more visuals (e.g., Profit by SubCategory, Discount impact, etc.) to deepen the analysis.")
