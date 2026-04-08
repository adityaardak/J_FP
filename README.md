# DriveIQ: BMW Global Sales Insight Agent 🏎️📊
An AI-Powered Business Intelligence System using Microsoft Power BI & Copilot Studio

## 🌟 Project Overview
DriveIQ is an intelligent reporting ecosystem designed to transform 14 years of BMW global sales data (2010–2024) into conversational, actionable insights. By integrating Microsoft Copilot Studio (Gen-AI) with Power BI, this project eliminates the "Insight Bottleneck," allowing stakeholders to query 50,000+ rows of data using natural language.

## Focus: Data Analytics & AI Integration

## 🚀 Key Features
1. Conversational BI: Ask questions like "Which model drives the most revenue in Asia?" and get instant text summaries.
2. Role-Based Reporting: Automated report generation for Executives, Regional Managers, and Product Leads.
3. Multi-Page Strategic Dashboards:
     1. Executive Overview: High-level KPIs ($19.01T Total Revenue).
     2. Product Performance: Revenue contribution & model leadership.
     3. Regional Analysis: Developed vs. Developing nation market share.
     4. Technology & Performance: Deep-dive into Fuel Type adoption & Transmission trends.
4. 95%+ Data Integrity: Advanced ETL pipeline built with Power Query.

## 🛠️ Tech Stack
1. Analytics: Microsoft Power BI (DAX, Power Query).
2. Artificial Intelligence: Microsoft Copilot Studio (Grounded on Claude 3.5 Sonnet).
3. Data Source: BMW Global Sales Dataset (Kaggle).
4. Design: Premium Dark Mode UI with Montserrat typography.

## 🏗️ System Architecture
1. Data Ingestion: 50,000 rows of raw sales data.
2. ETL Processing: Removed 1,200+ duplicates, normalized currency, and engineered features (Revenue_Calculated, Vehicle_Type).
3. Visual Layer: Created interactive charts, decomposition trees, and regional maps.
4. AI Layer: Grounded a Copilot Agent on the cleaned dataset with custom system prompts to prevent hallucination.
5. Output: Seamless integration of AI-generated summaries within the Power BI interface.

## 📈 Key Insights
1. Volume vs. Value: The BMW 3 Series leads in sales volume, but the X5 SUV dominates revenue contribution (35%).
2. Sustainability Surge: Hybrid and Electric vehicle adoption increased by 150% post-2020 in developed markets.
3. Optimal Config: Data identifies Blue | Hybrid | Automatic as the most profitable combination for future production.

## 📁 Repository Structure
├── Data/                   # Cleaned Excel dataset

├── Dashboard/              # .PBIX Power BI file

├── Documentation/          # Project Report & Presentation

├── Screenshots/            # UI/UX previews of the dashboard & AI agent

└── README.md               # Project overview

## 🧑‍💻 Author
Jyoti Pathak, Student at Graphic Era Deemed to Be University 
