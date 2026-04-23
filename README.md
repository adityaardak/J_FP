# DriveIQ: BMW Sales Intelligence Studio 🏎️📊
An AI-Powered Business Intelligence System combining a **Streamlit web app**, **Microsoft Power BI** dashboards, a **CatBoost ML price-prediction model**, and a **Microsoft Copilot Studio** conversational agent — all built on 14 years of BMW global sales data (2010–2024).

## 🌟 Project Overview
DriveIQ is an intelligent reporting ecosystem that transforms 50,000+ rows of BMW global sales data into conversational, actionable insights. The project has two complementary interfaces:

- **Streamlit App (`app.py`)** — The primary interactive web application. It embeds live Power BI dashboards, renders custom analytics panels (model spotlight, regional demand, product mix), and hosts an AI price-prediction engine powered by CatBoost.
- **Static Web Portal (`index.html`)** — A standalone browser-based portal that uses SheetJS and Plotly.js for client-side analytics, embedding the same Power BI report without requiring a Python server.

By integrating Microsoft Copilot Studio (Gen-AI) with Power BI, the project also eliminates the "Insight Bottleneck," allowing stakeholders to query the dataset using natural language.

## Focus: Data Analytics & AI Integration

## 🚀 Key Features
1. **Conversational BI:** Ask questions like "Which model drives the most revenue in Asia?" and get instant text summaries via the embedded Copilot agent.
2. **AI Price Prediction:** Enter vehicle specifications (model year, region, fuel type, transmission, engine size, colour, etc.) and get an instant price estimate from a pre-trained CatBoost regression model with MAE, RMSE, and R² metrics shown.
3. **Interactive Filters:** Sidebar controls let users slice the data by Model, Manufacturing Year, Region, Fuel Type, Transmission, and Vehicle Type — all charts and KPIs update live.
4. **Multi-Page Strategic Dashboards (Power BI embed):**
   - Executive Overview: High-level KPIs ($19.01T Total Revenue).
   - Product Performance: Revenue contribution & model leadership.
   - Regional Market Analysis: Developed vs. Developing nation market share.
   - Customer Preference: Consumer choices and optimal production combinations.
   - Technology & Performance: Fuel Type adoption & Transmission trends.
5. **Custom Analytics Panels:** Model Spotlight (revenue, units, avg price per model), Regional Demand treemap, and Product Mix breakdown — all rendered with Plotly.
6. **95%+ Data Integrity:** Advanced ETL pipeline built with Power Query (removed 1,200+ duplicates, normalised currency, engineered `Revenue_Calculated` and `Vehicle_Type` features).

## 🛠️ Tech Stack
| Layer | Technology |
|---|---|
| Web App Framework | Streamlit ≥ 1.35 |
| Data Processing | Pandas ≥ 2.1, NumPy ≥ 1.26, OpenPyXL ≥ 3.1 |
| Visualisation | Plotly ≥ 5.20 |
| Machine Learning | CatBoost ≥ 1.2, scikit-learn ≥ 1.4 |
| BI Platform | Microsoft Power BI (DAX, Power Query) |
| Conversational AI | Microsoft Copilot Studio (grounded on Claude 3.5 Sonnet) |
| Static Portal | HTML5 / CSS3 / Vanilla JS, SheetJS, Plotly.js |
| Data Source | BMW Global Sales Dataset — Kaggle (2010–2024) |
| Design | Premium Dark Mode UI, Orbitron + Manrope typography |

## 🏗️ System Architecture
1. **Data Ingestion:** 50,000 rows of raw BMW sales data loaded from Excel.
2. **ETL Processing:** Cleaned with Power Query; engineered features include `Revenue_Calculated` and `Vehicle_Type`.
3. **ML Layer:** CatBoost regressor trained on 9 features (year, region, fuel type, transmission, engine size, vehicle type, mileage, development nation, colour); model is cached in `artifacts/bmw_price_catboost.cbm`.
4. **Visual Layer:** Interactive charts, decomposition trees, and regional maps in Power BI + custom Plotly panels in the Streamlit app.
5. **AI Layer:** Copilot Agent grounded on the cleaned dataset with custom system prompts to prevent hallucination.
6. **Output:** Seamless integration of AI-generated summaries within the Power BI interface and a standalone Streamlit dashboard.

## ⚙️ Installation & Running

### Prerequisites
- Python 3.10 or higher
- pip

### Setup
```bash
# 1. Clone the repository
git clone https://github.com/adityaardak/J_FP.git
cd J_FP

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the Streamlit app
streamlit run app.py
```

The app will open at `http://localhost:8501` in your browser.

### Static Portal
Open `index.html` directly in any modern browser — no server required.

## 📈 Key Insights
1. **Volume vs. Value:** The BMW 3 Series leads in sales volume, but the X5 SUV dominates revenue contribution (35%).
2. **Sustainability Surge:** Hybrid and Electric vehicle adoption increased by 150% post-2020 in developed markets.
3. **Optimal Config:** Data identifies **Blue | Hybrid | Automatic** as the most profitable combination for future production.

## 🎬 Demo Video
[Watch on Google Drive](https://drive.google.com/file/d/1vihDQZb_--Zcu0eMIMl6MW2mWv-erdq-/view?usp=drivesdk)

## 📁 Repository Structure
```
J_FP/
├── app.py                              # Streamlit web application (main entry point)
├── index.html                          # Standalone static web portal
├── styles.css                          # Styles for the static portal
├── script.js                           # Client-side analytics for the static portal
├── Dashboard.html                      # Alternate dashboard HTML page
├── requirements.txt                    # Python dependencies
├── EXCEL BMW sales data (2010-2024).xlsx  # Cleaned source dataset
├── artifacts/
│   └── bmw_price_catboost.cbm          # Pre-trained CatBoost price prediction model
├── Screenshots/
│   ├── Dashboard_Page_01 – 05          # Power BI dashboard page previews
│   ├── Agent_ss_01 – 04                # Copilot agent interface screenshots
│   └── Agent_Testing_01 – 08          # Agent Q&A testing screenshots
├── AICW ppt.pptx                       # Project presentation slides
├── Jyoti Pathak AICW Project Report.pdf  # Full project report
├── Project Synopsis Jyoti Pathak pdf.pdf # Project synopsis
└── README.md                           # Project overview (this file)
```

## 🧑‍💻 Author
**Jyoti Pathak** — Student at Graphic Era Deemed to Be University
