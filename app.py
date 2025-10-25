import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="Retail Dashboard (Demo)", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("Sales Data.csv", parse_dates=["OrderDate"])
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
fdf = df[mask] # fdf = filtered dataframe

# ---- Main Page Layout ----

# 1) KPIs
total_sales = fdf["Sales"].sum()
total_profit = fdf["Profit"].sum()
total_orders = fdf["OrderID"].nunique()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Sales", f"${total_sales:,.0f}")
with col2:
    st.metric("Total Profit", f"${total_profit:,.0f}")
with col3:
    st.metric("Total Orders", f"{total_orders:,}")

st.markdown("---")

# 2) Sales over Time (line chart)
st.subheader("Sales over Time")
line_chart = alt.Chart(fdf).mark_line().encode(
    x=alt.X("OrderDate", title="Order Date"),
    y=alt.Y("Sales", title="Sales"),
    tooltip=["OrderDate", "Sales"]
).interactive()
st.altair_chart(line_chart, use_container_width=True)

# 3) Sales by Category (bar chart)
cat = fdf.groupby("Category", as_index=False)["Sales"].sum().sort_values("Sales", ascending=False)
bar_chart = alt.Chart(cat).mark_bar().encode(
    x=alt.X("Sales:Q", title="Sales"),
    y=alt.Y("Category:N", sort="-x"),
    tooltip=[alt.Tooltip("Sales:Q", format=",.0f")]
).properties(height=300)
st.subheader("Sales by Category")
st.altair_chart(bar_chart, use_container_width=True)

# 4) Region vs Profit (scatter)
reg = fdf.groupby("Region", as_index=False).agg({"Sales":"sum", "Profit":"sum"})
scatter = alt.Chart(reg).mark_circle(size=120).encode(
    x=alt.X("Sales:Q", title="Sales"),
    y=alt.Y("Profit:Q", title="Profit"),
    tooltip=[alt.Tooltip("Sales:Q", format=",.0f"), alt.Tooltip("Profit:Q", format=",.0f"), "Region"]
).properties(height=300)
st.subheader("Region: Sales vs Profit")
st.altair_chart(scatter, use_container_width=True)

# 5) Top 10 Products by Sales
top_products = fdf.groupby("Product", as_index=False)["Sales"].sum().sort_values("Sales", ascending=False).head(10)
st.subheader("Top 10 Products by Sales")
st.dataframe(top_products, use_container_width=True, hide_index=True)