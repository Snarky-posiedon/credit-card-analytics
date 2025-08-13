import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# Page config
st.set_page_config(
    page_title="Credit Card Spending Analytics",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 10px;
    border-left: 5px solid #1f77b4;
}
.insight-box {
    background-color: #03233b;
    padding: 1rem;
    border-radius: 10px;
    border-left: 4px solid #0066cc;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_and_process_data():
    """Load and process the CSV file from repository"""
    try:
        df = pd.read_csv('credit_card_data.csv')
        
        # Standardize column names
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Data cleaning
        df = df.dropna(subset=['amount', 'date'])
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        df = df[df['amount'] > 0]
        
        # Standardize text fields
        text_columns = ['city', 'card_type', 'exp_type', 'gender']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.title().str.strip()
        
        # Feature engineering
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['quarter'] = df['date'].dt.quarter
        df['day_of_week'] = df['date'].dt.day_name()
        df['is_weekend'] = df['date'].dt.weekday >= 5
        df['month_name'] = df['date'].dt.month_name()
        
        # City tier classification
        tier1_cities = ['Greater Mumbai, India', 'Delhi, India', 'Bengaluru, India', 'Ahmedabad, India']
        df['city_tier'] = df['city'].apply(
            lambda x: 'Tier-1' if x in tier1_cities else 'Tier-2/3'
        )
        
        # Spending categories
        def categorize_spending(amount):
            if amount < 1000:
                return 'Low (₹0-1K)'
            elif amount < 5000:
                return 'Medium (₹1K-5K)'
            elif amount < 15000:
                return 'High (₹5K-15K)'
            else:
                return 'Premium (₹15K+)'
        
        df['spending_tier'] = df['amount'].apply(categorize_spending)
        
        # Create category from exp_type if available
        if 'exp_type' in df.columns:
            df['category'] = df['exp_type']
        
        return df
    except FileNotFoundError:
        st.error("❌ Credit card dataset not found. Please ensure 'credit_card_data.csv' exists in the repository.")
        return None
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        return None

def create_sql_analysis(df):
    """Create SQL database and run analysis queries"""
    conn = sqlite3.connect(':memory:')
    df.to_sql('transactions', conn, index=False, if_exists='replace')
    
    queries = {
        'city_analysis': """
        SELECT 
            city,
            city_tier,
            COUNT(*) as txn_count,
            ROUND(SUM(amount), 2) as total_spend,
            ROUND(AVG(amount), 2) as avg_spend,
            ROUND(SUM(amount) * 100.0 / (SELECT SUM(amount) FROM transactions), 2) as spend_percentage
        FROM transactions
        GROUP BY city, city_tier
        ORDER BY total_spend DESC
        LIMIT 15;
        """,
        
        'category_performance': """
        SELECT 
            category,
            COUNT(*) as transaction_count,
            ROUND(SUM(amount), 2) as total_revenue,
            ROUND(AVG(amount), 2) as avg_transaction_value
        FROM transactions
        WHERE category IS NOT NULL
        GROUP BY category
        ORDER BY total_revenue DESC;
        """,
        
        'gender_analysis': """
        SELECT 
            gender,
            city_tier,
            COUNT(*) as txn_count,
            ROUND(SUM(amount), 2) as total_spend,
            ROUND(AVG(amount), 2) as avg_spend
        FROM transactions
        GROUP BY gender, city_tier
        ORDER BY total_spend DESC;
        """,
        
        'monthly_trends': """
        SELECT 
            month,
            month_name,
            quarter,
            COUNT(*) as monthly_transactions,
            ROUND(SUM(amount), 2) as monthly_spend,
            ROUND(AVG(amount), 2) as avg_transaction
        FROM transactions
        GROUP BY month, month_name, quarter
        ORDER BY month;
        """
    }
    
    results = {}
    for name, query in queries.items():
        try:
            results[name] = pd.read_sql_query(query, conn)
        except Exception as e:
            st.error(f"Query {name} failed: {e}")
    
    conn.close()
    return results

def create_rfm_analysis(df):
    """Create RFM analysis using customer groups"""
    if df is None or len(df) == 0:
        return None
    
    # Create customer groups
    df['customer_group'] = df['city'].astype(str) + '_' + df['gender'].astype(str) + '_' + df['card_type'].astype(str)
    
    reference_date = df['date'].max()
    
    rfm = df.groupby('customer_group').agg({
        'date': lambda x: (reference_date - x.max()).days,
        'amount': ['count', 'sum']
    }).reset_index()
    
    rfm.columns = ['customer_group', 'Recency', 'Frequency', 'Monetary']
    
    # Calculate RFM scores
    rfm['R_Score'] = pd.qcut(rfm['Recency'], 5, labels=[5,4,3,2,1], duplicates='drop')
    rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1,2,3,4,5], duplicates='drop')
    rfm['M_Score'] = pd.qcut(rfm['Monetary'], 5, labels=[1,2,3,4,5], duplicates='drop')
    
    # Convert to int
    rfm['R_Score'] = rfm['R_Score'].astype(int)
    rfm['F_Score'] = rfm['F_Score'].astype(int)
    rfm['M_Score'] = rfm['M_Score'].astype(int)
    
    # Segmentation
    def segment_groups(row):
        if row['R_Score'] >= 4 and row['F_Score'] >= 4 and row['M_Score'] >= 4:
            return 'Champions'
        elif row['R_Score'] >= 3 and row['F_Score'] >= 3:
            return 'Loyal Groups'
        elif row['R_Score'] <= 2 and row['F_Score'] >= 3:
            return 'At Risk'
        elif row['R_Score'] <= 2 and row['F_Score'] <= 2:
            return 'Lost Groups'
        else:
            return 'Potential Loyalists'
    
    rfm['Segment'] = rfm.apply(segment_groups, axis=1)
    return rfm

# Main App
def main():
    st.markdown('<h1 class="main-header">💳 Credit Card Spending Analytics Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("🔧 Dashboard Controls")
    st.sidebar.markdown("### 📊 Dataset Information")
    st.sidebar.info("This dashboard uses a pre-loaded credit card spending dataset for analysis.")
    
    # Add filters in sidebar (we'll populate these after loading data)
    st.sidebar.markdown("### 🎛️ Filters")
    
    # Load and process data automatically
    with st.spinner("🔄 Loading credit card dataset..."):
        df = load_and_process_data()
    
    if df is None:
        st.error("❌ Unable to load the dataset. Please check if 'credit_card_data.csv' exists in the repository.")
        st.markdown("""
        ### Expected CSV Format:
        The dataset should contain these columns:
        - **date**: Transaction date
        - **amount**: Transaction amount  
        - **city**: City name
        - **gender**: Gender
        - **card_type**: Type of card
        - **exp_type**: Expense/Category type
        """)
        return
    
    # Add sidebar filters after data is loaded
    st.sidebar.markdown("---")
    
    # Date range filter
    if not df.empty:
        date_min = df['date'].min().date()
        date_max = df['date'].max().date()
        
        date_range = st.sidebar.date_input(
            "📅 Select Date Range",
            value=(date_min, date_max),
            min_value=date_min,
            max_value=date_max
        )
        
        # City filter
        cities = ['All Cities'] + sorted(df['city'].unique().tolist())
        selected_city = st.sidebar.selectbox("🏙️ Select City", cities)
        
        # Gender filter  
        genders = ['All Genders'] + sorted(df['gender'].unique().tolist())
        selected_gender = st.sidebar.selectbox("👤 Select Gender", genders)
        
        # Card type filter
        card_types = ['All Card Types'] + sorted(df['card_type'].unique().tolist())
        selected_card_type = st.sidebar.selectbox("💳 Select Card Type", card_types)
        
        # Apply filters
        filtered_df = df.copy()
        
        # Date filter
        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df = filtered_df[
                (filtered_df['date'].dt.date >= start_date) & 
                (filtered_df['date'].dt.date <= end_date)
            ]
        
        # Other filters
        if selected_city != 'All Cities':
            filtered_df = filtered_df[filtered_df['city'] == selected_city]
        if selected_gender != 'All Genders':
            filtered_df = filtered_df[filtered_df['gender'] == selected_gender]
        if selected_card_type != 'All Card Types':
            filtered_df = filtered_df[filtered_df['card_type'] == selected_card_type]
        
        # Update df to filtered version
        df = filtered_df
        
        # Show filter summary
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 Filtered Data Summary")
        st.sidebar.metric("Transactions", f"{len(df):,}")
        st.sidebar.metric("Total Value", f"₹{df['amount'].sum():,.0f}")
    
    # Dataset overview
    st.success(f"✅ Dataset loaded successfully! Shape: {df.shape}")
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Revenue", f"₹{df['amount'].sum():,.0f}")
    with col2:
        st.metric("Total Transactions", f"{len(df):,}")
    with col3:
        st.metric("Average Transaction", f"₹{df['amount'].mean():.0f}")
    with col4:
        st.metric("Cities Covered", f"{df['city'].nunique()}")
    
    # Tabs for different analyses
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "🏙️ Geographic", "📈 Trends", "👥 Customer Segmentation", "💡 Insights"])
    
    with tab1:
        st.subheader("📊 Dataset Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Data Summary:**")
            st.write(f"- Date Range: {df['date'].min().date()} to {df['date'].max().date()}")
            st.write(f"- Number of Cities: {df['city'].nunique()}")
            st.write(f"- Card Types: {df['card_type'].nunique() if 'card_type' in df.columns else 'N/A'}")
            
            # Top categories
            if 'category' in df.columns:
                st.write("**Top Expense Categories:**")
                top_categories = df['category'].value_counts().head()
                for cat, count in top_categories.items():
                    st.write(f"- {cat}: {count:,} transactions")
        
        with col2:
            # Amount distribution
            fig = px.histogram(df, x='amount', nbins=50, title='Transaction Amount Distribution')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("🏙️ Geographic Analysis")
        
        # SQL Analysis
        sql_results = create_sql_analysis(df)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'city_analysis' in sql_results:
                st.write("**Top Cities by Revenue:**")
                city_data = sql_results['city_analysis'].head(10)
                fig = px.bar(city_data, x='city', y='total_spend', 
                           title='Top 10 Cities by Revenue',
                           color='city_tier')
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # City tier distribution
            city_tier_spend = df.groupby('city_tier')['amount'].sum().reset_index()
            fig = px.pie(city_tier_spend, values='amount', names='city_tier', 
                        title='Revenue Distribution by City Tier')
            st.plotly_chart(fig, use_container_width=True)
        
        # Gender analysis
        if 'gender_analysis' in sql_results:
            st.write("**Gender & Location Analysis:**")
            gender_data = sql_results['gender_analysis']
            fig = px.bar(gender_data, x='gender', y='total_spend', 
                        color='city_tier', barmode='group',
                        title='Spending by Gender & City Tier')
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("📈 Spending Trends")
        
        if 'monthly_trends' in sql_results:
            monthly_data = sql_results['monthly_trends']
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Monthly spending trend
                fig = px.line(monthly_data, x='month', y='monthly_spend',
                             title='Monthly Spending Trends', markers=True)
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Monthly transaction count
                fig = px.bar(monthly_data, x='month_name', y='monthly_transactions',
                           title='Monthly Transaction Count')
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
        
        # Weekend vs Weekday analysis
        weekend_data = df.groupby('is_weekend').agg({
            'amount': ['sum', 'count', 'mean']
        }).round(2)
        weekend_data.columns = ['Total_Spend', 'Transaction_Count', 'Avg_Spend']
        weekend_data.index = ['Weekday', 'Weekend']
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(x=weekend_data.index, y=weekend_data['Total_Spend'],
                        title='Weekend vs Weekday Spending')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Day of week pattern
            dow_data = df.groupby('day_of_week')['amount'].sum().reindex([
                'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
            ])
            fig = px.bar(x=dow_data.index, y=dow_data.values,
                        title='Spending by Day of Week')
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.subheader("👥 Customer Segmentation (RFM Analysis)")
        
        rfm_results = create_rfm_analysis(df)
        
        if rfm_results is not None:
            col1, col2 = st.columns(2)
            
            with col1:
                # Segment distribution
                segment_counts = rfm_results['Segment'].value_counts()
                fig = px.pie(values=segment_counts.values, names=segment_counts.index,
                           title='Customer Group Segments')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Segment value
                segment_value = rfm_results.groupby('Segment')['Monetary'].mean().reset_index()
                fig = px.bar(segment_value, x='Segment', y='Monetary',
                           title='Average Monetary Value by Segment')
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
            
            st.write("**Segment Summary:**")
            segment_summary = rfm_results.groupby('Segment').agg({
                'customer_group': 'count',
                'Monetary': 'mean',
                'Frequency': 'mean',
                'Recency': 'mean'
            }).round(2)
            segment_summary.columns = ['Count', 'Avg_Monetary', 'Avg_Frequency', 'Avg_Recency']
            st.dataframe(segment_summary)
    
    with tab5:
        st.subheader("💡 Business Insights & Recommendations")
        
        # Key insights
        total_revenue = df['amount'].sum()
        top_city = df.groupby('city')['amount'].sum().idxmax()
        best_month = df.groupby('month_name')['amount'].sum().idxmax()
        
        st.markdown(f"""
        <div class="insight-box">
        <h4>🎯 Key Findings:</h4>
        <ul>
        <li><strong>Top Performing City:</strong> {top_city} generates the highest revenue</li>
        <li><strong>Peak Season:</strong> {best_month} shows highest spending activity</li>
        <li><strong>Total Market Size:</strong> ₹{total_revenue:,.0f} across {df['city'].nunique()} cities</li>
        <li><strong>Transaction Pattern:</strong> {len(df):,} transactions with ₹{df['amount'].mean():.0f} average ticket size</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Recommendations
        st.markdown("""
        ### 🚀 Strategic Recommendations:
        
        1. **🎯 Geographic Focus**: Prioritize marketing investments in top-performing cities
        2. **🏙️ Tier-2/3 Expansion**: Untapped potential in smaller cities
        3. **👫 Gender-Specific Strategies**: Develop targeted campaigns based on spending patterns
        4. **📅 Seasonal Planning**: Optimize promotional activities during peak months
        5. **💳 Card Portfolio**: Optimize card types based on performance data
        6. **🔄 Customer Retention**: Focus on 'At Risk' and 'Lost Groups' segments
        7. **📱 Digital Engagement**: Implement location-based mobile marketing
        8. **📊 Predictive Analytics**: Use transaction patterns for forecasting
        """)
        
        # Download insights
        if st.button("📥 Download Full Analysis Report"):
            # Create summary dataframe
            summary_data = {
                'Metric': ['Total Revenue', 'Total Transactions', 'Average Transaction', 'Cities Covered', 'Top City', 'Peak Month'],
                'Value': [f"₹{total_revenue:,.0f}", f"{len(df):,}", f"₹{df['amount'].mean():.0f}", 
                         f"{df['city'].nunique()}", top_city, best_month]
            }
            summary_df = pd.DataFrame(summary_data)
            
            csv = summary_df.to_csv(index=False)
            st.download_button(
                label="Download Summary CSV",
                data=csv,
                file_name='credit_card_analysis_summary.csv',
                mime='text/csv'
            )

if __name__ == "__main__":
    main()
