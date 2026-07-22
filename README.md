

<img src="assets/logo.png" alt="InsightFlow Logo" width="140"/>

# InsightFlow

### Enterprise Customer Journey & Growth Analytics Platform

Transform customer interactions into actionable business intelligence through executive dashboards, funnel analytics, marketing attribution, customer intelligence, and experimentation insights.

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red?style=for-the-badge&logo=streamlit)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-336791?style=for-the-badge&logo=postgresql)
![Plotly](https://img.shields.io/badge/Plotly-Interactive%20Charts-3F4F75?style=for-the-badge&logo=plotly)
![SQL](https://img.shields.io/badge/SQL-Analytics-green?style=for-the-badge)
![Pytest](https://img.shields.io/badge/Tested-71%20Tests-success?style=for-the-badge)

</div>

---

# Overview

InsightFlow is an enterprise-inspired customer journey and growth analytics platform designed to help organizations understand how users move through the acquisition funnel—from first interaction to successful conversion.

Using SQL analytics, PostgreSQL, Python, and interactive dashboards, the platform transforms customer events into meaningful business intelligence for marketing, product, and executive teams.

The project simulates a real-world fintech analytics ecosystem using a fictional company, **PaisaOne**, enabling end-to-end analysis of customer acquisition, marketing performance, conversion funnels, and experimentation.

---

# Dashboard Preview


## Executive Overview
<img width="1280" height="800" alt="Executive Overview" src="https://github.com/user-attachments/assets/f3a9a249-7f20-4184-b4a2-05ed67535866" />



---

## Funnel Analytics

<img width="1280" height="800" alt="Funnel Analytics" src="https://github.com/user-attachments/assets/24a4f904-1c32-457d-b8f8-596aee3a6235" />


---

## Marketing Attribution

<img width="1280" height="800" alt="Marketing Attribution" src="https://github.com/user-attachments/assets/10c156ec-8e6f-4045-a154-669eed620242" />


---

## Customer Intelligence

<img width="1280" height="800" alt="Customer Portfolio Analytics" src="https://github.com/user-attachments/assets/964753fb-604a-4a1b-96b3-94abefae8d44" />


---

## Experiment Analytics

<img width="1280" height="800" alt="Experiment Analytics" src="https://github.com/user-attachments/assets/15e038b9-5e05-45b7-94af-59ccdc4944c6" />


---

# Key Features

- Executive KPI dashboard
- Customer acquisition funnel analysis
- Marketing attribution analytics
- Customer intelligence dashboards
- Geographic performance analysis
- Interactive Plotly visualizations
- SQL-powered analytics layer
- PostgreSQL data warehouse
- Enterprise-inspired UI
- Dark theme interface
- Modular architecture
- Reusable analytics components
- Responsive layouts
- Cached analytics queries
- Automated testing

---

# Business Scenario

InsightFlow models the analytics infrastructure for **PaisaOne**, a fictional digital lending platform.

Business teams require visibility into:

- Customer acquisition performance
- Funnel conversion rates
- Marketing channel effectiveness
- Geographic trends
- Loan application behaviour
- Experiment performance
- Executive KPIs

Instead of relying on disconnected reports, InsightFlow consolidates these insights into a unified analytics platform.

---

# Architecture

![](docs/screenshots/architecture.png)

```
                    Synthetic Data
                          │
                          ▼
                PostgreSQL Data Warehouse
                          │
                          ▼
                 SQL Analytics Layer
                          │
                          ▼
                Analytics Service Layer
                          │
                          ▼
             Interactive Streamlit Dashboard
                          │
                          ▼
          Executive Business Intelligence
```

---

# Technology Stack

| Category | Technologies |
|----------|--------------|
| Programming | Python |
| Dashboard | Streamlit |
| Database | PostgreSQL |
| Query Layer | SQL |
| Visualization | Plotly |
| Data Processing | Pandas, NumPy |
| Testing | Pytest |
| Styling | HTML, CSS |
| Version Control | Git, GitHub |

---

# Project Structure

```
InsightFlow/

├── assets/
│   ├── logo.png
│   ├── india_map.png
│   └── styles.css
│
├── sql/
│   ├── attribution_queries.sql
│   └── funnel_queries.sql
│
├── src/
│   ├── components/
│   ├── database/
│   ├── pages/
│   ├── queries/
│   ├── services/
│   └── utils/
│
├── tests/
│
├── app.py
├── config.py
├── requirements.txt
└── README.md
```

---

# Dashboard Modules

### Executive Overview

Provides a consolidated view of business KPIs, customer growth, conversion metrics, and operational performance.

---

### Funnel Analytics

Visualizes customer movement across acquisition stages while identifying conversion bottlenecks and drop-off points.

---

### Marketing Attribution

Measures campaign effectiveness across acquisition channels using attribution metrics and channel-level performance indicators.

---

### Customer Intelligence

Analyzes customer demographics, behavioural patterns, geographic distribution, and engagement trends.

---

### Experiment Analytics

Tracks A/B experiments, compares performance metrics, and evaluates experiment outcomes.

---

# Installation

Clone the repository

```bash
git clone https://github.com/mohithkrishnaa/InsightFlow.git
```

Move into the project

```bash
cd InsightFlow
```

Install dependencies

```bash
pip install -r requirements.txt
```

Create your environment file

```text
cp .env.example .env
```

Configure PostgreSQL credentials inside `.env`.

Launch the application

```bash
streamlit run app.py
```

---

# Testing

Run all tests

```bash
pytest
```

The project includes automated tests covering analytics logic and database connectivity.

---

# Highlights

- Enterprise-inspired dashboard experience
- PostgreSQL-backed analytics
- Interactive business intelligence visualizations
- Modular software architecture
- SQL-driven analytics layer
- Automated testing
- Responsive interface
- Scalable code organization

---

# Future Roadmap

- Predictive analytics
- Machine learning integration
- Real-time event streaming
- User authentication
- Role-based access control
- Cloud deployment
- REST API
- Scheduled reporting
- Export to PDF and Excel

---

# About the Author

## Mohith Krishna

B.Tech Computer Science (AI & Data Engineering)

Passionate about Data Analytics, Product Analytics, Business Intelligence, and AI-powered decision systems.

- GitHub: https://github.com/mohithkrishnaa
- LinkedIn: https://www.linkedin.com/in/mohith-krishnaa/

---

# License

This project is licensed under the MIT License.

---

<div align="center">

### If you found this project useful, consider giving it a ⭐

**InsightFlow — Turning customer data into actionable business intelligence.**

</div>
