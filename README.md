# 📊 Institutional Trade Surveillance & Analytics Platform

### A Full-Stack Python Application for Behavioral Risk Analysis
**Built with:** Python | Streamlit | Pandas | yfinance | Seaborn

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-ff4b4b)
![Status](https://img.shields.io/badge/Status-Active-success)

---

## 📖 Overview

This is not just a trading journal; it is an **Automated Trade Surveillance System**.

Most retail traders track P&L. Institutional traders track **process**. This application serves as a quantitative ETL (Extract, Transform, Load) pipeline that ingests raw trade data, enriches it with historical market context (VIX, Yields, SPY Trend), and performs counter-factual analysis to identify behavioral leaks in execution.

### 🚀 Key Capabilities

* **Automated Context Extraction (ETL):**
    * Instantly fetches the "Market Regime" (Bull/Bear), Volatility Index (VIX), and 10-Year Treasury Yields for every trade logged.
    * *Why?* To analyze if the user is forcing trades during high-risk macro conditions.

* **Behavioral "Counter-Factual" Engine:**
    * **The "Paper Hands" Metric:** Automatically checks price action **14 days post-exit** to calculate missed gains.
    * *Insight:* Quantifies the cost of selling too early vs. the benefit of dodging volatility.

* **Dynamic Performance Visualization:**
    * Real-time Equity Curve tracking using **Seaborn**.
    * Regime-based Win Rate analysis (e.g., "Win rate in Bear Markets vs. Bull Markets").

---

## 🛠️ Tech Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Frontend** | **Streamlit** | Interactive web dashboard with custom "Royal Amethyst" CSS theme. |
| **Backend** | **Python** | Logic for data validation, API calling, and state management. |
| **Data Processing** | **Pandas** | Time-series manipulation and cleaning of financial data. |
| **Market Data** | **yfinance** | API integration for historical price, volatility, and bond yield data. |
| **Visualization** | **Seaborn / Matplotlib** | Statistical plotting for performance trajectory. |
| **Storage** | **CSV** | Lightweight, portable persistence layer for trade logs. |

---

## 📂 Project Structure

```bash
├── app.py              # Frontend: Streamlit UI and Dashboard logic
├── backend.py          # ETL Pipeline: Data fetching and CSV writing
├── analytics.py        # Intelligence: Counter-factual analysis & Stats logic
├── trading_journal.csv # Database: Persistent storage (Auto-generated)
├── requirements.txt    # Dependencies
└── .streamlit/
    └── config.toml     # Theme configuration