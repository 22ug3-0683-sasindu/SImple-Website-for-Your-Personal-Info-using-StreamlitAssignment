import streamlit as st
import pandas as pd
import plotly.express as px
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Set page configuration for a wide layout
st.set_page_config(layout="wide", page_title="Multi-Dataset Dashboard")

# --- Data Loading Functions with Caching ---

@st.cache_data
def load_sales_data():
    """
    Loads the Sales Data.csv file, converts OrderDate to datetime,
    and handles potential FileNotFoundError.
    """
    try:
        df = pd.read_csv("Sales Data.csv")
        df['OrderDate'] = pd.to_datetime(df['OrderDate'])
        return df
    except FileNotFoundError:
        st.error("Error: 'Sales Data.csv' not found. Please place it in the same directory as this script.")
        return None
    except Exception as e:
        st.error(f"An error occurred loading sales data: {e}")
        return None

@st.cache_data
def load_population_data():
    """
    Loads the US Population csv, cleans numeric columns (removes commas),
    and 'melts' the data from wide to long format for easier plotting.
    """
    try:
        df = pd.read_csv("us-population-2010-2019 (1).csv")
        
        # Get year columns (from '2010' to '2019')
        year_cols = [str(y) for y in range(2010, 2020)]
        
        # Clean data: remove commas and convert to integer
        for col in year_cols:
            if col in df.columns:
                df[col] = df[col].replace(',', '', regex=True).astype(int)
            
        # Melt dataframe from wide to long format
        df_long = df.melt(
            id_vars=['states', 'id'], 
            value_vars=year_cols, 
            var_name='Year', 
            value_name='Population'
        )
        
        # Convert Year to integer
        df_long['Year'] = df_long['Year'].astype(int)
        return df_long
        
    except FileNotFoundError:
        st.error("Error: 'us-population-2010-2019 (1).csv' not found. Please place it in the same directory as this script.")
        return None
    except Exception as e:
        st.error(f"An error occurred loading population data: {e}")
        return None

# --- Dashboard Page Functions ---

def show_home_page():
    """Displays the Home page."""
    st.header("Welcome to the Multi-Dataset Dashboard")
    st.write("Use the navigation in the sidebar to explore either the **Sales Data** or the **US Population** datasets.")
    st.image("https://streamlit.io/images/brand/streamlit-logo-primary-col.svg", width=400)


def show_sales_dashboard(df):
    """Displays the Sales Data dashboard."""
    st.title("📈 Sales Data Dashboard")

    # --- Sidebar Filters for Sales ---
    st.sidebar.header("Sales Filters")
    
    # Region Filter
    regions = st.sidebar.multiselect(
        "Select Region(s)",
        options=df['Region'].unique(),
        default=df['Region'].unique()
    )
    
    # Category Filter
    categories = st.sidebar.multiselect(
        "Select Category(ies)",
        options=df['Category'].unique(),
        default=df['Category'].unique()
    )

    # Filter dataframe based on selection
    filtered_df = df.query("Region in @regions and Category in @categories")

    if filtered_df.empty:
        st.warning("No data matches the selected filters.")
        return

    # --- KPIs ---
    st.header("Key Performance Indicators (KPIs)")
    total_sales = filtered_df['Sales'].sum()
    total_profit = filtered_df['Profit'].sum()
    avg_discount = filtered_df['Discount'].mean()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Sales", f"${total_sales:,.2f}")
    col2.metric("Total Profit", f"${total_profit:,.2f}")
    col3.metric("Avg. Discount", f"{avg_discount:.1%}")

    st.markdown("---")

    # --- Charts ---
    st.header("Visualizations")
    col1, col2 = st.columns(2)

    with col1:
        # Sales over Time (Line Chart)
        st.subheader("Monthly Sales Trend")
        sales_over_time = filtered_df.set_index('OrderDate').resample('M')['Sales'].sum().reset_index()
        fig_time = px.line(sales_over_time, x='OrderDate', y='Sales', title="Sales Over Time")
        st.plotly_chart(fig_time, use_container_width=True)

        # Sales vs. Profit (Scatter Plot)
        st.subheader("Sales vs. Profit")
        fig_scatter = px.scatter(
            filtered_df, 
            x='Sales', 
            y='Profit', 
            color='Category', 
            hover_name='Product',
            title="Sales vs. Profit by Category"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    with col2:
        # Sales by Category (Bar Chart)
        st.subheader("Sales by Category")
        sales_by_cat = filtered_df.groupby('Category')['Sales'].sum().reset_index()
        fig_cat = px.bar(
            sales_by_cat.sort_values('Sales', ascending=False), 
            x='Category', 
            y='Sales', 
            title="Total Sales by Category",
            color='Category'
        )
        st.plotly_chart(fig_cat, use_container_width=True)

        # Sales by Region (Bar Chart)
        st.subheader("Sales by Region")
        sales_by_region = filtered_df.groupby('Region')['Sales'].sum().reset_index()
        fig_region = px.bar(
            sales_by_region.sort_values('Sales', ascending=False), 
            x='Region', 
            y='Sales', 
            title="Total Sales by Region",
            color='Region'
        )
        st.plotly_chart(fig_region, use_container_width=True)

    # --- Raw Data ---
    if st.checkbox("Show Raw Sales Data"):
        st.subheader("Raw Sales Data")
        st.dataframe(filtered_df)


def show_population_dashboard(df):
    """Displays the US Population dashboard."""
    st.title("📊 US Population Dashboard (2010-2019)")

    # --- Sidebar Filters for Population ---
    st.sidebar.header("Population Filters")
    
    all_states = df['states'].unique()
    selected_states = st.sidebar.multiselect(
        "Select State(s) for Trend Line",
        options=all_states,
        default=['California', 'Texas', 'New York', 'Florida', 'Illinois']
    )

    # --- Charts ---
    st.header("Visualizations")
    
    # Population Trends (Line Chart)
    st.subheader("Population Trends for Selected States")
    trend_df = df[df['states'].isin(selected_states)]
    if trend_df.empty:
        st.warning("Please select at least one state to see the trend.")
    else:
        fig_trend = px.line(
            trend_df, 
            x='Year', 
            y='Population', 
            color='states',
            title="Population Trend (2010-2019)"
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("---")

    # 2019 Population by State (Choropleth Map)
    st.subheader("2019 Population by State")
    pop_2019 = df[df['Year'] == 2019]
    fig_map = px.choropleth(
        pop_2019,
        locations='states',       # Column with state names
        locationmode="USA-states",  # Use full state names
        color='Population',         # Column for color scale
        scope="usa",                # Limit map to USA
        color_continuous_scale="Viridis",
        title="2019 US Population by State"
    )
    st.plotly_chart(fig_map, use_container_width=True)

    # --- Raw Data ---
    if st.checkbox("Show Raw Population Data (Long Format)"):
        st.subheader("Raw Population Data")
        st.dataframe(df)

# --- Main App Logic ---

def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Choose a dashboard", ["Home", "Sales Data Analysis", "US Population Analysis"])

    if page == "Home":
        show_home_page()
        
    elif page == "Sales Data Analysis":
        sales_data = load_sales_data()
        if sales_data is not None:
            show_sales_dashboard(sales_data)
            
    elif page == "US Population Analysis":
        population_data = load_population_data()
        if population_data is not None:
            show_population_dashboard(population_data)

if __name__ == "__main__":
    main()