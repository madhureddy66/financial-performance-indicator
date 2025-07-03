import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import calendar # For getting month names in order
import re # For regular expressions to clean strings

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
        # --- DIAGNOSTIC LINE (COMMENT OUT AFTER FIXING ALL ISSUES) ---
        # st.write("Columns in your uploaded CSV:", df.columns.tolist())
        # --- END OF DIAGNOSTIC LINE ---
        st.sidebar.success("CSV loaded successfully!")
    except Exception as e:
        st.error(f"Error loading CSV file: {e}. Please ensure it's a valid CSV.")
        st.stop() # Stop execution if file cannot be read
else:
    st.info("Please upload a CSV file to view the dashboard.")
    st.stop() # Stop execution if no file is uploaded

# --- Data Preprocessing and Calculated Fields ---
if df is not None:
    # --- Date Column Handling ---
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df.dropna(subset=['Date'], inplace=True) # Drop rows where date conversion failed
    else:
        st.error("Error: 'Date' column not found in the uploaded CSV. Please ensure your CSV has a 'Date' column.")
        st.stop()

    if df.empty:
        st.error("DataFrame is empty after cleaning 'Date' column. Please check your CSV data.")
        st.stop()

    # Define columns expected to be numeric
    # These names exactly match your CSV's headers, including leading/trailing spaces,
    # as identified from your diagnostic output.
    expected_numeric_cols = [
        " Units Sold ",
        " Manufacturing Price ",
        " Sale Price ",
        " Gross Sales ",
        " Discounts ",
        "  Sales ", # This column specifically has two leading spaces
        " COGS ",
        " Profit "
    ]

    # Convert expected numeric columns to numeric, handling missing columns gracefully
    # And cleaning non-numeric characters from the strings
    for col in expected_numeric_cols:
        if col in df.columns:
            # Convert to string first to apply string methods, and strip any surrounding whitespace from cell values
            df[col] = df[col].astype(str).str.strip()
            
            # Handle negative numbers in parentheses: $(X.XX) -> -X.XX
            df[col] = df[col].replace(r'\$\(([\d,\.]+)\)', r'-\1', regex=True)
            
            # Handle '$-' or just '-' as 0
            df[col] = df[col].replace(r'^\$\-+$', '0', regex=True) # Matches exactly '$-' or '---' etc.
            
            # Remove dollar signs, commas, and quotes
            df[col] = df[col].str.replace('$', '', regex=False)\
                             .str.replace(',', '', regex=False)\
                             .str.replace('"', '', regex=False)
            
            # Convert to numeric, coercing errors to NaN and then filling with 0
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            st.warning(f"Warning: Column '{col}' not found in your CSV. It will be skipped for numerical calculations.")

    # --- Ensure essential columns for core dashboard calculations exist ---
    # These names exactly match your CSV's headers, including leading/trailing spaces.
    required_cols_for_dashboard = [" Gross Sales ", "  Sales ", " Profit ", " Units Sold ", " Discounts ", " COGS "]
    for col in required_cols_for_dashboard:
        if col not in df.columns:
            st.error(f"Error: Required column '{col}' is missing or named differently in your CSV. Please correct your CSV or adjust the `required_cols_for_dashboard` list in the code to match.")
            st.stop()

    # Create Time-based features
    df['Year'] = df['Date'].dt.year
    df['Month Number'] = df['Date'].dt.month
    df[' Month Name '] = df['Date'].dt.month_name() # Has spaces in header name
    df['Quarter'] = df['Date'].dt.quarter

    # --- Sidebar Filters ---
    st.sidebar.header("Filter Data")

    # Segment Filter - 'Segment' is clean based on your output
    if 'Segment' in df.columns:
        all_segments = sorted(df['Segment'].unique().tolist())
        selected_segments = st.sidebar.multiselect("Select Segment(s)", all_segments, default=all_segments)
    else:
        st.sidebar.warning("Column 'Segment' not found for filtering.")
        selected_segments = [] # No segments to filter if column is missing

    # Country Filter - 'Country' is clean based on your output
    if 'Country' in df.columns:
        all_countries = sorted(df['Country'].unique().tolist())
        selected_countries = st.sidebar.multiselect("Select Country(ies)", all_countries, default=all_countries)
    else:
        st.sidebar.warning("Column 'Country' not found for filtering.")
        selected_countries = [] # No countries to filter if column is missing

    # Year Filter
    all_years = sorted(df['Year'].unique().tolist())
    selected_years = st.sidebar.multiselect("Select Year(s)", all_years, default=all_years)

    # --- NEW FILTERS ---
    # Product Filter
    if ' Product ' in df.columns: # Note: ' Product ' has a leading and trailing space based on your CSV
        all_products = sorted(df[' Product '].unique().tolist())
        selected_products = st.sidebar.multiselect("Select Product(s)", all_products, default=all_products)
    else:
        st.sidebar.warning("Column ' Product ' not found for filtering.")
        selected_products = []

    # Discount Band Filter
    if ' Discount Band ' in df.columns: # Note: ' Discount Band ' has a leading and trailing space based on your CSV
        all_discount_bands = sorted(df[' Discount Band '].unique().tolist())
        selected_discount_bands = st.sidebar.multiselect("Select Discount Band(s)", all_discount_bands, default=all_discount_bands)
    else:
        st.sidebar.warning("Column ' Discount Band ' not found for filtering.")
        selected_discount_bands = []
    # --- END NEW FILTERS ---

    # Apply filters
    filtered_df = df[
        (df['Year'].isin(selected_years))
    ].copy() # Use .copy() to avoid SettingWithCopyWarning

    # Conditionally apply segment and country filters only if the columns exist and selections are made
    if 'Segment' in df.columns and selected_segments:
        filtered_df = filtered_df[filtered_df['Segment'].isin(selected_segments)]
    if 'Country' in df.columns and selected_countries:
        filtered_df = filtered_df[filtered_df['Country'].isin(selected_countries)]
    
    # --- APPLY NEW FILTERS ---
    if ' Product ' in df.columns and selected_products:
        filtered_df = filtered_df[filtered_df[' Product '].isin(selected_products)]
    if ' Discount Band ' in df.columns and selected_discount_bands:
        filtered_df = filtered_df[filtered_df[' Discount Band '].isin(selected_discount_bands)]
    # --- END APPLY NEW FILTERS ---

    if filtered_df.empty:
        st.warning("No data matches the selected filters. Please adjust your selections.")
        st.stop()

    # --- Reset Filters Button ---
    if st.sidebar.button("Reset All Filters"):
        st.experimental_rerun() # This will re-run the script with default selections

    # --- 2. Key Performance Indicators (KPIs) ---
    st.subheader("Key Performance Indicators")

    # Calculate KPIs from filtered data (using the adjusted column names)
    total_units_sold = filtered_df[" Units Sold "].sum() if " Units Sold " in filtered_df.columns else 0
    total_gross_sale = filtered_df[" Gross Sales "].sum() if " Gross Sales " in filtered_df.columns else 0
    total_profit = filtered_df[" Profit "].sum() if " Profit " in filtered_df.columns else 0
    total_sales_for_margin = filtered_df["  Sales "].sum() if "  Sales " in filtered_df.columns else 0

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

    # --- NEW: Profit and Loss Statement Summary ---
    st.subheader("Profit and Loss Statement Summary")

    # Calculate P&L line items
    # Ensure columns exist before summing, though required_cols_for_dashboard already checks
    gross_sales_summary = filtered_df[" Gross Sales "].sum()
    discounts_summary = filtered_df[" Discounts "].sum()
    sales_summary = filtered_df["  Sales "].sum() # Note: two spaces
    cogs_summary = filtered_df[" COGS "].sum()
    profit_summary = filtered_df[" Profit "].sum()

    # Create a DataFrame for display
    pnl_data = {
        "Metric": ["Gross Sales", "Discounts", "Net Sales", "Cost of Goods Sold (COGS)", "Profit"],
        "Amount": [
            gross_sales_summary,
            discounts_summary,
            sales_summary,
            cogs_summary,
            profit_summary
        ]
    }
    pnl_df = pd.DataFrame(pnl_data)

    # Format the 'Amount' column as currency
    pnl_df['Amount'] = pnl_df['Amount'].apply(lambda x: f"${x:,.2f}")

    st.table(pnl_df) # Using st.table for a static, neat summary
    
    st.markdown("---")
    # --- END NEW: Profit and Loss Statement Summary ---


    # --- 3. Charts ---

    # Row 1 of charts: Quarterly Profit and Monthly Profit
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Profit by Quarter (Clustered Bar Chart)")
        if 'Quarter' in filtered_df.columns and " Profit " in filtered_df.columns and not filtered_df.empty:
            quarterly_profit = filtered_df.groupby(['Year', 'Quarter'])[" Profit "].sum().reset_index()
            # Ensure proper sorting for plotting
            quarterly_profit['Quarter_Label'] = quarterly_profit['Year'].astype(str) + ' Q' + quarterly_profit['Quarter'].astype(str)
            # Sort by Year and Quarter for correct bar order
            quarterly_profit = quarterly_profit.sort_values(by=['Year', 'Quarter'])

            if quarterly_profit.empty:
                st.warning("No quarterly profit data based on current filters.")
            else:
                fig_quarter, ax_quarter = plt.subplots(figsize=(12, 6))
                sns.barplot(x='Quarter_Label', y=" Profit ", data=quarterly_profit, ax=ax_quarter, palette='viridis')
                ax_quarter.set_title('Profit by Quarter')
                ax_quarter.set_xlabel('Quarter')
                ax_quarter.set_ylabel('Total Profit ($)')
                ax_quarter.tick_params(axis='x', rotation=45)
                ax_quarter.grid(axis='y', linestyle='--')
                plt.tight_layout()
                st.pyplot(fig_quarter)
                plt.close(fig_quarter)
        else:
            st.warning("Cannot generate Quarterly Profit chart: Required columns ('Quarter', ' Profit ') missing or no data.")


    with chart_col2:
        st.subheader("Profit by Month (Area Chart)")
        if 'Month Number' in filtered_df.columns and " Month Name " in filtered_df.columns and " Profit " in filtered_df.columns and not filtered_df.empty:
            # Group by Year, Month Number, and Month Name to ensure correct chronological order
            monthly_profit = filtered_df.groupby(['Year', 'Month Number', " Month Name "])[" Profit "].sum().reset_index()
            monthly_profit = monthly_
       
