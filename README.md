# Smartspend_prototype
# SmartSpend — Prototype

Small Streamlit prototype for SmartSpend — AI-driven UPI expense tracker.

## How to run (local)
1. Install Python 3.10+
2. Create venv (optional) and activate it.
3. Install dependencies:
   pip install -r requirements.txt
4. Run:
   streamlit run app.py

## Features
- Add expenses (simulate UPI)
- Auto-categorization (keyword-based)
- Set monthly budgets and receive alerts
- Dashboard with pie chart showing spending by category
- Offline P2P payment (simulated)

## Files
- app.py — main application
- requirements.txt — Python packages
- expenses.csv — stored transactions (created automatically)
- budgets.json — stored budgets (created automatically)

## Notes
This is a prototype for hackathon submission. Real app would integrate bank/UPI APIs, stronger ML categorization, and secure offline transfer via device APIs.
