import streamlit as st
import pandas as pd
import altair as alt
import re

# Page setup
st.set_page_config(page_title="Combined Dashboard", layout="wide")
st.title("Sales & US Population Dashboard")

# --- 1. Sales Data Section ---
st.header("Retail Sales Dashboard")

@st.cache_data
def load_sales_data():
    # [cite_start]Load sales data [cite: 2]
    df = pd.read_csv("Sales Data.csv", parse_dates=["OrderDate"])
    return df

df_sales = load_sales_data()

# --- Sidebar Filters for Sales ---
st.sidebar.header("Sales Filters")
min_date = df_sales["OrderDate"].min().date()
max_date = df_sales["OrderDate"].max().date()

date_range = st.sidebar.date_input(
    "Order Date Range", 
    (min_date, max_date), 
    min_value=min_date, 
    max_value=max_date
)

regions = st.sidebar.multiselect(
    "Region", 
    sorted(df_sales["Region"].unique()), 
    default=list(sorted(df_sales["Region"].unique()))
)

categories = st.sidebar.multiselect(
    "Category", 
    sorted(df_sales["Category"].unique()), 
    default=list(sorted(df_sales["Category"].unique()))
)

# --- Apply Sales Filters ---
fdf = df_sales[
    (df_sales["OrderDate"].dt.date >= date_range[0]) &
    (df_sales["OrderDate"].dt.date <= date_range[1]) &
    (df_sales["Region"].isin(regions)) &
    (df_sales["Category"].isin(categories))
]

# --- Sales KPIs ---
total_sales = fdf["Sales"].sum()
total_profit = fdf["Profit"].sum()

col1, col2 = st.columns(2)
with col1:
    st.metric("Total Sales", f"${total_sales:,.0f}")
with col2:
    st.metric("Total Profit", f"${total_profit:,.0f}")

# --- Sales Charts ---
# 1) Sales by Category
cat_sales = fdf.groupby("Category", as_index=False)["Sales"].sum().sort_values("Sales", ascending=False)
bar_chart = alt.Chart(cat_sales).mark_bar().encode(
    x=alt.X("Sales:Q", title="Sales"),
    y=alt.Y("Category:N", sort="-x"),
    tooltip=[alt.Tooltip("Sales:Q", format="$,.0f")]
).properties(
    title="Sales by Category"
)
st.altair_chart(bar_chart, use_container_width=True)

# 2) Sales over time
line_chart = alt.Chart(fdf).mark_line().encode(
    x=alt.X("OrderDate", title="Order Date"),
    y=alt.Y("Sales", title="Sales"),
    tooltip=["OrderDate", alt.Tooltip("Sales", format="$,.0f")]
).properties(
    title="Sales Over Time"
).interactive()
st.altair_chart(line_chart, use_container_width=True)


# --- 2. US Population Data Section ---
st.header("US Population Dashboard (2010-2019)")

@st.cache_data
def load_population_data():
    # [cite_start]Load population data [cite: 3]
    df = pd.read_csv("us-population-2010-2019 (1).csv")
    
    # Clean data:
    # Get list of year columns
    year_cols = [col for col in df.columns if re.match(r"^\d{4}$", col)]
    
    # Remove commas and convert to numeric
    for col in year_cols:
        df[col] = df[col].replace({',': ''}, regex=True).astype(int)
        
    # Melt dataframe from wide to long format for charting
    df_long = df.melt(
        id_vars=["states", "id"], 
        value_vars=year_cols, 
        var_name="Year", 
        value_name="Population"
    )
    # Convert Year to datetime object for proper time-axis scaling
    df_long['Year'] = pd.to_datetime(df_long['Year'], format='%Y')
    return df_long, df

df_pop_long, df_pop_wide = load_population_data()

# --- Population Controls ---
st.sidebar.header("Population Filters")
all_states = sorted(df_pop_long["states"].unique())
selected_state = st.sidebar.selectbox("Select State", all_states, index=all_states.index("California"))

# --- Filter Population Data ---
state_data = df_pop_long[df_pop_long["states"] == selected_state]

# --- Population Chart ---
st.subheader(f"Population Trend for {selected_state}")
pop_line_chart = alt.Chart(state_data).mark_line(point=True).encode(
    x=alt.X("Year:T", title="Year"),
    y=alt.Y("Population:Q", title="Population"),
    tooltip=[
        "Year:T", 
        alt.Tooltip("Population:Q", format=",")
    ]
).properties(
    title=f"Population (2010-2019)"
).interactive()
st.altair_chart(pop_line_chart, use_container_width=True)

# --- Raw Population Data ---
st.subheader("Raw Population Data (2010-2019)")
st.dataframe(df_pop_wide)