# 💳 Credit Card Spending Analytics Dashboard

An interactive web dashboard for analyzing credit card spending patterns using real Kaggle datasets. Built with Streamlit and deployed on Streamlit Cloud.

## 🚀 Live Demo

[View Live Dashboard](https://credit-card-analytics.streamlit.app/)

## 📊 Features

- **Pre-loaded Dataset**: Comprehensive credit card dataset with 15,000+ transactions
- **Interactive Filters**: Date range, city, gender, and card type filtering
- **Geographic Analysis**: City-wise spending patterns and tier classification
- **Temporal Trends**: Monthly, weekly, and seasonal spending analysis
- **Customer Segmentation**: RFM analysis for customer group identification
- **SQL Analytics**: Advanced querying capabilities for deep insights
- **Business Insights**: Actionable recommendations and KPI tracking

## 🛠️ Technical Stack

- **Frontend**: Streamlit
- **Data Processing**: Pandas, NumPy
- **Visualizations**: Plotly, Matplotlib, Seaborn
- **Database**: SQLite (in-memory)
- **Deployment**: Streamlit Cloud

## 📋 Dataset Information

The dashboard uses a comprehensive synthetic dataset (`credit_card_data.csv`) with:
- **15,000+ transactions** across Indian cities
- **40+ cities** including Tier-1, Tier-2, and Tier-3 cities
- **5 card types**: Silver, Gold, Platinum, Signature, Premium
- **10 expense categories**: Grocery, Fuel, Bills, Entertainment, Food, Shopping, Travel, Healthcare, Education, Others
- **Time period**: January 2023 to March 2024
- **Realistic patterns**: Seasonal variations, weekend effects, city-wise distributions

### Generating Your Own Dataset

If you want to create a new dataset or modify the existing one:

```bash
python generate_sample_data.py
```

This will create a new `credit_card_data.csv` file with realistic transaction patterns.

## 🚀 Local Development

### Prerequisites
- Python 3.8+
- pip

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Snarky-posiedon/credit-card-analytics-dashboard.git
cd credit-card-analytics-dashboard
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run app.py
```

4. Open your browser and navigate to `http://localhost:8501`

## 📊 Analysis Features

### 1. Overview Dashboard
- Key metrics summary
- Transaction distribution analysis
- Data quality insights

### 2. Geographic Analysis
- Top performing cities
- City tier performance comparison
- Gender-based location insights

### 3. Temporal Trends
- Monthly spending patterns
- Seasonal analysis
- Weekend vs weekday behavior

### 4. Customer Segmentation
- RFM Analysis (Recency, Frequency, Monetary)
- Customer group classification
- Segment-wise performance metrics

### 5. Business Insights
- Automated insight generation
- Strategic recommendations
- Downloadable reports

## 🔧 Customization

The dashboard is designed to work with standard credit card datasets but can be easily customized:

1. **Column Mapping**: Modify the column standardization in `load_and_process_data()`
2. **City Tiers**: Update the `tier1_cities` list for your geographic region
3. **Spending Categories**: Adjust the `categorize_spending()` function
4. **Visualizations**: Add custom charts using Plotly or Matplotlib

## 📈 Key Metrics Tracked

- **Financial KPIs**: Total revenue, average transaction value, growth rates
- **Geographic KPIs**: City performance, tier distribution, market penetration
- **Customer KPIs**: Segmentation metrics, loyalty indicators, churn signals
- **Operational KPIs**: Transaction volumes, seasonal patterns, category performance

## 🛡️ Data Privacy

- All data processing happens in-memory
- No data is stored permanently on servers
- CSV files are processed locally in your browser session
- Database connections are temporary and session-specific

## 🚀 Deployment Guide

### Deploy to Streamlit Cloud (Recommended)

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Deploy with one click!

### Alternative Deployment Options

- **Heroku**: Use the included `Procfile`
- **Railway**: Direct GitHub integration
- **Render**: Static site deployment
- **Vercel**: Serverless deployment

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## 🙏 Acknowledgments

- Built for Kaggle credit card datasets
- Inspired by modern data analytics best practices
- Uses open-source visualization libraries

## 📧 Contact

Parishkritchandra23@gmail.com

Project Link: [https://github.com/Snarky-posiedon/credit-card-analytics-dashboard](https://github.com/Snarky-posiedon/credit-card-analytics-dashboard)

---

⭐ Don't forget to give the project a star if you found it useful!

