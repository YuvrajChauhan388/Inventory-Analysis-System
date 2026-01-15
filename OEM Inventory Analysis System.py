import pandas as pd
import numpy as np
import streamlit as st
from streamlit_lottie import st_lottie
import requests
import time
import matplotlib.pyplot as plt
import re

st.set_page_config(
    page_title="OEM Inventory Analysis System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inflation rates
INFLATION_RATES = {
    2021: 5.1, 2022: 6.7, 2023: 5.7,
    2024: 4.9, 2025: 3.16, 2026: 4.5, 2027: 4.5
}

def format_indian_number(num):
    try:
        num = float(num)
        if np.isnan(num):
            return "-"
        if abs(num) < 100000:
            return f"{num:,.2f}"
        elif abs(num) < 10000000:
            return f"{num/100000:.2f} Lakh"
        else:
            return f"{num/10000000:.2f} Crore"
    except:
        return str(num)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600&display=swap');
    :root {
        --primary: #2A5C99;
        --secondary: #4B8DF8;
        --accent: #FF6B6B;
    }
    * { font-family: 'Poppins', sans-serif; }
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    .header {
        color: var(--primary); text-align: center; padding: 1rem 0;
        border-bottom: 2px solid var(--secondary); margin-bottom: 2rem;
        background: rgba(255, 255, 255, 0.8); border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .card {
        background: white; border-radius: 15px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.1);
        padding: 1.5rem; margin-bottom: 1.5rem; transition: transform 0.3s ease;
    }
    .card:hover { transform: translateY(-5px); }
    .stButton button {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        color: white; border: none; border-radius: 30px;
        padding: 0.7rem 1.5rem; font-weight: 500; transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton button:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    .metric-value { font-size: 1.8rem; font-weight: 600; color: var(--primary); text-align: center; }
    .metric-label { font-size: 1rem; text-align: center; }
    .footer {
        text-align: center; padding: 1.5rem; margin-top: 2rem;
        background: rgba(255, 255, 255, 0.8); border-radius: 10px;
    }
    .upload-section {
        background: linear-gradient(135deg, #f0f7ff 0%, #e6f0ff 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

def load_lottie(url):
    try:
        r = requests.get(url, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def inflation_factor(base_year, target_year):
    factor = 1.0
    for year in range(base_year+1, target_year+1):
        rate = INFLATION_RATES.get(year, 4.5)
        factor *= (1 + rate/100)
    return factor

def calculate_equipment_lifetime(usage_years):
    """Calculate inventory lifetime based on usage gaps"""
    if len(usage_years) < 2:
        return None
    
    sorted_years = sorted(usage_years)
    gaps = []
    for i in range(1, len(sorted_years)):
        gap = sorted_years[i] - sorted_years[i-1]
        gaps.append(gap)
    
    if not gaps:
        return None
    
    # Use the maximum gap as lifetime indicator
    return max(gaps)

def predict_replenishment_events(historical_years, target_year):
    """Predict all replenishment events up to target year"""
    lifetime = calculate_equipment_lifetime(historical_years)
    if lifetime is None:
        return []
    
    last_usage = max(historical_years)
    events = []
    next_replenishment = last_usage + lifetime
    
    while next_replenishment <= target_year:
        events.append(next_replenishment)
        next_replenishment += lifetime
    
    return events

def detect_year_columns(df):
    """Detect year columns using regex pattern"""
    pattern = re.compile(r'^\d{4}$|^FY\d{2}$', re.IGNORECASE)
    year_cols = [col for col in df.columns if pattern.match(str(col).strip())]
    return sorted(year_cols, key=lambda x: int(re.search(r'\d{2,4}', str(x)).group()))

def convert_to_year(col_name):
    """Convert column name to year integer"""
    year_str = re.search(r'\d{2,4}', str(col_name)).group()
    if len(year_str) == 2:
        return 2000 + int(year_str) if int(year_str) < 50 else 1900 + int(year_str)
    return int(year_str)

def load_and_clean_data(uploaded_file):
    """Load and clean data from uploaded file"""
    try:
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        elif uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            st.error("Unsupported file format. Please upload XLSX or CSV.")
            return None
            
        # Clean column names
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        return None

def main():
    st.title("📊 OEM Inventory Analysis System")
    
    # File upload section
    with st.container():
        st.markdown("<div class='card upload-section'><h2>📂 Upload Your Inventory Data</h2></div>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload Excel or CSV file with inventory data",
            type=["xlsx", "csv"],
            key="file_uploader"
        )
        
        if uploaded_file is None:
            st.info("Please upload a data file to begin analysis")
            return
    
    # Load animation
    lottie_animation = load_lottie("https://assets9.lottiefiles.com/packages/lf20_sk5h1kfn.json")
    with st.container():
        col1, col2 = st.columns([1, 2])
        with col1:
            if lottie_animation:
                st_lottie(lottie_animation, height=150, key="header-animation")
        with col2:
            st.markdown("<div class='header'><h1>📈 Inventory Analysis System</h1></div>", unsafe_allow_html=True)
            st.caption("Predict prices and replenishment needs based on your data")
    
    # Load and process data
    with st.spinner("Processing data..."):
        df = load_and_clean_data(uploaded_file)
        if df is None:
            return
            
        required_cols = ["Material Discription", "Unit Price"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"Missing required columns: {', '.join(missing_cols)}")
            return
        
        # Detect year columns
        year_cols = detect_year_columns(df)
        if not year_cols:
            st.error("No year columns found in the data (e.g., 2021, FY21)")
            return
            
        st.success(f"Detected year columns: {', '.join(map(str, year_cols))}")
        
        # Filter and clean data
        df = df.dropna(subset=["Unit Price"])
        df["Unit Price"] = pd.to_numeric(df["Unit Price"], errors="coerce")
        df = df[df["Unit Price"] > 0]
        
        # Prepare results
        results = []
        for _, row in df.iterrows():
            material = row["Material Discription"]
            base_price = row["Unit Price"]
            record = {"Material": material, "Unit Price": base_price}
            last_year = None
            history_years = []
            
            # Process year columns
            for col in year_cols:
                year = convert_to_year(col)
                qty = pd.to_numeric(row[col], errors="coerce")
                if pd.notna(qty) and qty > 0:
                    record[f"{year} Units"] = qty
                    record[f"{year} Total"] = base_price * qty
                    last_year = year
                    history_years.append(year)
            
            # Only include equipment with valid data
            if last_year and history_years:
                record["_base"] = base_price
                record["_last_year"] = last_year
                record["_historical_years"] = history_years
                results.append(record)
        
        results_df = pd.DataFrame(results)

    # Custom price prediction
    with st.container():
        st.markdown("<div class='card'><h2>🔮 Custom Price Prediction</h2></div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            materials = results_df["Material"].unique()
            material_sel = st.selectbox("Select Inventory", materials, key="material_select")
        with col2:
            target_year = st.number_input("Target Year", min_value=2023, max_value=2100, value=2028, key="year_input")
        with col3:
            st.write("")
            predict_btn = st.button("Predict Unit Price", use_container_width=True)
        
        if predict_btn:
            material_data = results_df[results_df["Material"] == material_sel].iloc[0]
            base_price = material_data["_base"]
            last_year = material_data["_last_year"]
            
            if target_year <= last_year:
                st.error("Target year must be after last historical year")
            else:
                factor = inflation_factor(last_year, target_year)
                predicted_price = base_price * factor
                st.success(f"Predicted unit price for {target_year}: ₹{format_indian_number(predicted_price)}")

    # Replenishment prediction
    with st.container():
        st.markdown("<div class='card'><h2>⏳ Replenishment Prediction</h2></div>", unsafe_allow_html=True)
        col1, col2 = st.columns([2, 3])
        
        with col1:
            target_year_replenish = st.number_input("Target Year for Replenishment", min_value=2023, max_value=2100, value=2040, key="year_input_replenish")
            predict_all_btn = st.button("Predict All Replenishments", use_container_width=True)
        
        with col2:
            if predict_all_btn:
                with st.spinner('Analyzing inventory lifetimes...'):
                    time.sleep(0.5)
                    
                    # Prepare replenishment data
                    replenishment_data = []
                    for idx, row in results_df.iterrows():
                        material = row["Material"]
                        historical_years = row["_historical_years"]
                        
                        if len(historical_years) < 2:
                            continue
                            
                        events = predict_replenishment_events(
                            historical_years, 
                            target_year_replenish
                        )
                        
                        if events:
                            for event_year in events:
                                replenishment_data.append({
                                    "Inventory": material,
                                    "Last Usage": max(historical_years),
                                    "Replenishment Year": event_year,
                                    "Lifetime (years)": event_year - max(historical_years)
                                })
                    
                    if replenishment_data:
                        # Create DataFrame and sort
                        replenishment_df = pd.DataFrame(replenishment_data)
                        replenishment_df = replenishment_df.sort_values(by="Replenishment Year")
                        
                        # Display results
                        st.success(f"Found {len(replenishment_df)} replenishment events by {target_year_replenish}")
                        st.dataframe(
                            replenishment_df,
                            use_container_width=True,
                            height=400
                        )
                        
                        # Show timeline visualization
                        fig, ax = plt.subplots(figsize=(12, 6))
                        
                        # Group by year
                        year_counts = replenishment_df["Replenishment Year"].value_counts().sort_index()
                        
                        ax.bar(year_counts.index, year_counts.values, color='#4B8DF8')
                        ax.set_title(f'Replenishment Events by Year')
                        ax.set_xlabel('Year')
                        ax.set_ylabel('Number of Replenishments')
                        ax.grid(axis='y', linestyle='--', alpha=0.7)
                        st.pyplot(fig)
                    else:
                        st.info("No replenishment predicted for any inventory by the target year")

    # Data display section
    with st.container():
        st.markdown("<div class='card'><h2>📋 Inventory Usage History</h2></div>", unsafe_allow_html=True)
        
        # Dynamically create columns based on detected years
        column_order = ['Material', 'Unit Price']
        year_columns = [col for col in results_df.columns if re.match(r'\d{4} Units', col)]
        for col in year_columns:
            column_order.append(col)
            column_order.append(col.replace('Units', 'Total'))
        
        display_df = results_df[column_order].copy()
        # Apply Indian formatting to numeric columns
        for col in display_df.columns:
            if display_df[col].dtype in [np.float64, np.int64]:
                display_df[col] = display_df[col].apply(format_indian_number)
        st.dataframe(
            display_df,
            use_container_width=True,
            height=500
        )
    
    # Footer
    st.markdown(f"""
    <div class="footer">
        <p>OEM Inventory Analysis System • Data from: {uploaded_file.name}</p>
        <p>Analysis completed on {pd.Timestamp.now().strftime('%d-%m-%Y')}</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
