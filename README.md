# Personal Expense Tracker

A simple and intuitive Personal Expense Tracker built using Python, Streamlit, and SQLite. This app allows users to track their expenses, set budgets, and visualize spending patterns.

## Features
- Multi-user authentication with hashed passwords.
- User-specific expense tracking and budget management.
- Receipt photo uploads along with expense.
- Dashboard visualizations for spending trends and category breakdowns.
- Gruvbox dark theme for a modern UI.

## Prerequisites
- Python 3.8 or higher
- Streamlit
- SQLite

## Installation
1. Clone the repository:
   ```zsh
   git clone https://github.com/shubhpsd/expense-tracker.git
   ```
2. Navigate to the project directory:
   ```zsh
   cd expense-tracker
   ```
3. Install the required dependencies:
   ```zsh
   pip install -r requirements.txt
   ```

## Usage
1. Run the application locally:
   ```zsh
   streamlit run app.py
   ```
2. Open the URL provided by Streamlit (usually `http://localhost:8501`) in your browser.

## App Link

You can access the app here: [Personal Expense Tracker](https://track-expense.streamlit.app/)

## Notes
- SQLite `.db` files are used for local storage. Changes made during runtime will not persist across app restarts if deployed on Streamlit Community Cloud.
- For multi-user scalability, will use a cloud database in future when financially worry free.
