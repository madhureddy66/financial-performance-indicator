import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import calendar # For getting month names in order

# Set Streamlit page configuration
st.set_page_config(layout="wide", page_title="Financial Performance Dashboard")

st.title("📊 Financial Performance Dashboard")

# --- 1. File Uploader ---
st.sidebar.header("Upload your Data")
uploaded_file = st.sidebar.file_uploader("Choose your 'financial_data.csv' file", type="csv")

df = None # Initialize df outside the if block

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.sidebar.success("CSV loaded successfully!")
    except Exception as e:
        st.error(f"Error loading CSV file: {e}. Please ensure it's a valid CSV.")
        st.stop() # Stop execution if file cannot be read
else:
    st.info("Please upload a CSV file to view the dashboard.")
    st.stop() # Stop execution if no file is uploaded

# --- Data Preprocessing and Calculated Fields ---
if df is not None:
    # Ensure 'Date' column is in datetime format
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df.dropna(subset=['Date'], inplace=True) # Drop rows where date conversion failed

    # Ensure numerical columns are numeric
    numeric_cols = ['Units Sold', 'Manufacturing Price', 'Sale Price', 'Gross Sales', 'Discounts', 'Sales', 'COGS', 'Profit']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0) # Fill NaN with 0 for calculations

    if df.empty:
        st.error("DataFrame is empty after cleaning date and numerical columns. Please check your CSV data.")
        st.stop()

    # Create Time-based features
    df['Year'] = df['Date'].dt.year
    df['Month Number'] = df['Date'].dt.month
    df['Month Name'] = df['Date'].dt.month_name()
    df['Quarter'] = df['Date'].dt.quarter

    # Calculated Fields as per PDF
    # Profit Margin: SUM([Profit]) / SUM([Sales])
    # Total Discounts: SUM([Discounts]) (already a column)
    # Total Revenue (Gross Sales): (already a column)

    # --- Sidebar Filters ---
    st.sidebar.header("Filter Data")

    # Segment Filter
    all_segments = sorted(df['Segment'].unique().tolist())
    selected_segments = st.sidebar.multiselect("Select Segment(s)", all_segments, default=all_segments)

    # Country Filter
    all_countries = sorted(df['Country'].unique().tolist())
    selected_countries = st.sidebar.multiselect("Select Country(ies)", all_countries, default=all_countries)

    # Year Filter
    all_years = sorted(df['Year'].unique().tolist())
    selected_years = st.sidebar.multiselect("Select Year(s)", all_years, default=all_years)

    # Apply filters
    filtered_df = df[
        (df['Segment'].isin(selected_segments)) &
        (df['Country'].isin(selected_countries)) &
        (df['Year'].isin(selected_years))
    ].copy() # Use .copy() to avoid SettingWithCopyWarning

    if filtered_df.empty:
        st.warning("No data matches the selected filters. Please adjust your selections.")
        st.stop()

    # --- Reset Filters Button ---
    if st.sidebar.button("Reset All Filters"):
        # This will re-run the script with default selections
        st.experimental_rerun()

    # --- 2. Key Performance Indicators (KPIs) ---
    st.subheader("Key Performance Indicators")

    # Calculate KPIs from filtered data
    total_units_sold = filtered_df['Units Sold'].sum()
    total_gross_sale = filtered_df['Gross Sales'].sum()
    total_profit = filtered_df['Profit'].sum()
    # Calculate Profit Margin for the filtered data
    total_sales_for_margin = filtered_df['Sales'].sum()
    profit_margin = (total_profit / total_sales_for_margin * 100) if total_sales_for_margin > 0 else 0

    # Display KPIs using st.metric
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        st.metric("Total Units Sold", f"{total_units_sold:,.0f}")
    with kpi_col2:
        st.metric("Total Gross Sale", f"${total_gross_sale:,.2f}")
    with kpi_col3:
        st.metric("Total Profit", f"${total_profit:,.2f}")
    with kpi_col4:
        st.metric("Profit Margin", f"{profit_margin:,.2f}%")

    st.markdown("---")

    # --- 3. Charts ---

    # Row 1 of charts: Quarterly Profit and Monthly Profit
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Profit by Quarter (Clustered Bar Chart)")
        quarterly_profit = filtered_df.groupby(['Year', 'Quarter'])['Profit'].sum().reset_index()
        # Ensure proper sorting for plotting
        quarterly_profit['Quarter_Label'] = quarterly_profit['Year'].astype(str) + ' Q' + quarterly_profit['Quarter'].astype(str)
        # Sort by Year and Quarter for correct bar order
        quarterly_profit = quarterly_profit.sort_values(by=['Year', 'Quarter'])

        if quarterly_profit.empty:
            st.warning("No quarterly profit data based on current filters.")
        else:
            fig_quarter, ax_quarter = plt.subplots(figsize=(12, 6))
            sns.barplot(x='Quarter_Label', y='Profit', data=quarterly_profit, ax=ax_quarter, palette='viridis')
            ax_quarter.set_title('Profit by Quarter')
            ax_quarter.set_xlabel('Quarter')
            ax_quarter.set_ylabel('Total Profit ($)')
            ax_quarter.tick_params(axis='x', rotation=45)
            ax_quarter.grid(axis='y', linestyle='--')
            plt.tight_layout()
            st.pyplot(fig_quarter)
            plt.close(fig_quarter)

    with chart_col2:
        st.subheader("Profit by Month (Area Chart)")
        # Group by Month Number and Month Name to ensure correct chronological order
        monthly_profit = filtered_df.groupby(['Year', 'Month Number', 'Month Name'])['Profit'].sum().reset_index()
        monthly_profit = monthly_profit.sort_values(by=['Year', 'Month Number'])

        if monthly_profit.empty:
            st.warning("No monthly profit data based on current filters.")
        else:
            fig_month, ax_month = plt.subplots(figsize=(12, 6))
            # Use 'Month Name' for x-axis, but ensure order is by 'Month Number'
            sns.lineplot(x='Month Name', y='Profit', hue='Year', data=monthly_profit, marker='o', ax=ax_month, palette='magma', errorbar=None)
            ax_month.set_title('Profit by Month')
            ax_month.set_xlabel('Month')
            ax_month.set_ylabel('Total Profit ($)')
            ax_month.tick_params(axis='x', rotation=45)
            ax_month.grid(True, linestyle='--')
            # Set x-axis labels to be in calendar order
            ax_month.set_xticks(range(len(all_months)))
            ax_month.set_xticklabels([calendar.month_name[i] for i in range(1, 13)])
            plt.tight_layout()
            st.pyplot(fig_month)
            plt.close(fig_month)

    st.markdown("---")

    # Row 2 of charts: Sales/Profit by Segment and Country (additional relevant plots)
    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        st.subheader("Total Sales by Segment")
        sales_by_segment = filtered_df.groupby('Segment')['Sales'].sum().sort_values(ascending=False).reset_index()
        if sales_by_segment.empty:
            st.warning("No sales by segment data based on current filters.")
        else:
            fig_segment, ax_segment = plt.subplots(figsize=(10, 6))
            sns.barplot(x='Sales', y='Segment', data=sales_by_segment, palette='crest', ax=ax_segment)
            ax_segment.set_title('Total Sales by Segment')
            ax_segment.set_xlabel('Total Sales ($)')
            ax_segment.set_ylabel('Segment')
            ax_segment.grid(axis='x', linestyle='--')
            plt.tight_layout()
            st.pyplot(fig_segment)
            plt.close(fig_segment)

    with chart_col4:
        st.subheader("Total Profit by Country")
        profit_by_country = filtered_df.groupby('Country')['Profit'].sum().sort_values(ascending=False).reset_index()
        if profit_by_country.empty:
            st.warning("No profit by country data based on current filters.")
        else:
            fig_country, ax_country = plt.subplots(figsize=(10, 6))
            sns.barplot(x='Profit', y='Country', data=profit_by_country, palette='rocket', ax=ax_country)
            ax_country.set_title('Total Profit by Country')
            ax_country.set_xlabel('Total Profit ($)')
            ax_country.set_ylabel('Country')
            ax_country.grid(axis='x', linestyle='--')
            plt.tight_layout()
            st.pyplot(fig_country)
            plt.close(fig_country)


st.sidebar.markdown("---")
st.sidebar.info("Dashboard created using Streamlit, Pandas, Matplotlib, and Seaborn.")
