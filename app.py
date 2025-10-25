import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(page_title="Retail Dashboard (Demo)", layout="wide")

st.title("Retail Sales Dashboard — Streamlit Demo")
st.caption("Follow the 4 pillars: Connect → Clean → Design → Develop")

# -----------------------------
# File Upload Section
# -----------------------------
st.sidebar.header("📂 Upload Two Excel/CSV Files")

uploaded_files = st.sidebar.file_uploader(
    "Upload exactly two Excel or CSV files",
    type=["csv", "xlsx"],
    accept_multiple_files=True
)

if len(uploaded_files) != 2:
    st.warning("Please upload exactly two files to proceed.")
    st.stop()

# -----------------------------
# Load and Combine Data
# -----------------------------
@st.cache_data
def load_data(files):
    dataframes = []
    for file in files:
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        dataframes.append(df)
    
    # Combine both files
    combined_df = pd.concat(dataframes, ignore_index=True)
    
    # Try to parse date columns automatically
    for col in combined_df.columns:
        if "date" in col.lower():
            combined_df[col] = pd.to_datetime(combined_df[col], errors="ignore")
    
    return combined_df

df = load_data(uploaded_files)

# Check data structure
st.sidebar.success("✅ Files combined successfully!")

# -----------------------------
# Basic column validation
# -----------------------------
required_columns = ["OrderDate", "Region", "CustomerSegment", "Category", "Sales", "Profit", "OrderID"]
missing_cols = [c for c in required_columns if c not in df.columns]

if missing_cols:
    st.error(f"Missing required columns: {', '.join(missing_cols)}")
    st.stop()

# -----------------------------
# Sidebar Filters
# -----------------------------
st.sidebar.header("Filters")

min_date = pd.to_datetime(df["OrderDate"]).min().date()
max_date = pd.to_datetime(df["OrderDate"]).max().date()
date_range = st.sidebar.date_input("Order Date Range", (min_date, max_date), min_value=min_date, max_value=max_date)

regions = st.sidebar.multiselect("Region", sorted(df["Region"].dropna().unique()), default=list(sorted(df["Region"].dropna().unique())))
segments = st.sidebar.multiselect("Customer Segment", sorted(df["CustomerSegment"].dropna().unique()), default=list(sorted(df["CustomerSegment"].dropna().unique())))
categories = st.sidebar.multiselect("Category", sorted(df["Category"].dropna().unique()), default=list(sorted(df["Category"].dropna().unique())))

# -----------------------------
# Apply Filters
# -----------------------------
mask = (
    (pd.to_datetime(df["OrderDate"]).dt.date >= date_range[0]) &
    (pd.to_datetime(df["OrderDate"]).dt.date <= date_range[1]) &
    (df["Region"].isin(regions)) &
    (df["CustomerSegment"].isin(segments)) &
    (df["Category"].isin(categories))
)

fdf = df.loc[mask].copy()
fdf["Month"] = pd.to_datetime(fdf["OrderDate"]).dt.to_period("M").dt.to_timestamp()

# -----------------------------
# KPI Cards
# -----------------------------
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

# -----------------------------
# Charts
# -----------------------------

# 1️⃣ Sales over time
sales_over_time = fdf.groupby("Month", as_index=False)["Sales"].sum()
line_chart = alt.Chart(sales_over_time).mark_line(point=True).encode(
    x=alt.X("Month:T", title="Month"),
    y=alt.Y("Sales:Q", title="Sales"),
    tooltip=["Month:T", alt.Tooltip("Sales:Q", format=",.0f")]
).properties(height=300)
st.subheader("Sales Over Time")
st.altair_chart(line_chart, use_container_width=True)

# 2️⃣ Sales by Category
cat = fdf.groupby("Category", as_index=False)["Sales"].sum().sort_values("Sales", ascending=False)
bar_chart = alt.Chart(cat).mark_bar().encode(
    x=alt.X("Sales:Q", title="Sales"),
    y=alt.Y("Category:N", sort="-x"),
    tooltip=[alt.Tooltip("Sales:Q", format=",.0f")]
).properties(height=300)
st.subheader("Sales by Category")
st.altair_chart(bar_chart, use_container_width=True)

# 3️⃣ Region vs Profit (scatter)
reg = fdf.groupby("Region", as_index=False).agg({"Sales": "sum", "Profit": "sum"})
scatter = alt.Chart(reg).mark_circle(size=120).encode(
    x=alt.X("Sales:Q", title="Sales"),
    y=alt.Y("Profit:Q", title="Profit"),
    tooltip=[alt.Tooltip("Sales:Q", format=",.0f"), alt.Tooltip("Profit:Q", format=",.0f"), "Region"]
).properties(height=300)
st.subheader("Region: Sales vs Profit")
st.altair_chart(scatter, use_container_width=True)

# 4️⃣ Top 10 Products by Sales
if "Product" in fdf.columns:
    top_products = fdf.groupby("Product", as_index=False)["Sales"].sum().sort_values("Sales", ascending=False).head(10)
    st.subheader("Top 10 Products by Sales")
    st.dataframe(top_products, use_container_width=True, hide_index=True)

# -----------------------------
# Download Filtered Data
# -----------------------------
with st.expander("Show Filtered Data"):
    st.dataframe(fdf.sort_values("OrderDate"), use_container_width=True)
    st.download_button("Download filtered data as CSV", data=fdf.to_csv(index=False), file_name="filtered_data.csv")

st.caption("Tip: Add more visuals (e.g., Profit by SubCategory, Discount impact, etc.) to deepen the analysis.")
