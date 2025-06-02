import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import os
import io
import matplotlib.pyplot as plt
import hashlib
from PIL import Image
import base64

# Gruvbox theme colors
GRUVOX_DARK = {
    "bg": "#282828",
    "fg": "#ebdbb2",
    "red": "#cc241d",
    "green": "#98971a",
    "yellow": "#d79921",
    "blue": "#458588",
    "purple": "#b16286",
    "aqua": "#689d6a",
    "gray": "#a89984",
    "orange": "#d65d0e",
}

# Helper functions (Database, Auth, etc.)
# User Authentication
USER_DB = 'users.db'

def init_user_db():
    if not os.path.exists(USER_DB):
        with sqlite3.connect(USER_DB) as conn:
            conn.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
            ''')
            conn.commit()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    return stored_password == hash_password(provided_password)

def signup_user(username, password):
    try:
        with sqlite3.connect(USER_DB) as conn:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hash_password(password)))
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_user(username, password):
    with sqlite3.connect(USER_DB) as conn:
        cursor = conn.execute('SELECT password FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        if result and verify_password(result[0], password):
            return True
    return False

# Expense and Budget Database Operations
def init_db(db_file):
    if not os.path.exists(db_file):
        with sqlite3.connect(db_file) as conn:
            conn.execute('''
            CREATE TABLE expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                amount REAL NOT NULL,
                receipt_photo TEXT
            )
            ''')
            # Also create budget_goals table
            conn.execute('''
            CREATE TABLE IF NOT EXISTS budget_goals (
                category TEXT PRIMARY KEY,
                monthly_limit REAL NOT NULL
            )
            ''')
            conn.commit()
    else: # If DB exists, ensure budget_goals table is there
        with sqlite3.connect(db_file) as conn:
            conn.execute('''
            CREATE TABLE IF NOT EXISTS budget_goals (
                category TEXT PRIMARY KEY,
                monthly_limit REAL NOT NULL
            )
            ''')
            conn.commit()

def add_expense(db_file, date, category, description, amount, receipt_photo=None):
    with sqlite3.connect(db_file) as conn:
        conn.execute('''
        INSERT INTO expenses (date, category, description, amount, receipt_photo)
        VALUES (?, ?, ?, ?, ?)
        ''', (date, category, description, amount, receipt_photo))
        conn.commit()

def get_expenses(db_file):
    with sqlite3.connect(db_file) as conn:
        df = pd.read_sql_query('SELECT * FROM expenses ORDER BY date DESC', conn)
    return df

def delete_expense(db_file, expense_id):
    with sqlite3.connect(db_file) as conn:
        conn.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
        conn.commit()

def set_budget_goal(db_file, category, monthly_limit):
    with sqlite3.connect(db_file) as conn:
        conn.execute('''
        INSERT INTO budget_goals (category, monthly_limit)
        VALUES (?, ?)
        ON CONFLICT(category) DO UPDATE SET monthly_limit = excluded.monthly_limit
        ''', (category, monthly_limit))
        conn.commit()

def get_budget_goals(db_file):
    with sqlite3.connect(db_file) as conn:
        df = pd.read_sql_query('SELECT * FROM budget_goals', conn)
    return df

def delete_budget_goal(db_file, category):
    with sqlite3.connect(db_file) as conn:
        conn.execute('DELETE FROM budget_goals WHERE category = ?', (category,))
        conn.commit()

def delete_user_account(username):
    try:
        # Connect to the users database
        conn = sqlite3.connect('users.db')
        conn.execute('DELETE FROM users WHERE username = ?', (username,))
        conn.commit()
        conn.close()

        # Delete the user's expense database file
        user_db_file = f'expenses_{username}.db'
        if os.path.exists(user_db_file):
            os.remove(user_db_file)

        return True
    except Exception as e:
        return False

# Main app
def main():
    # Apply dark mode theme directly
    current_theme_colors = GRUVOX_DARK

    # Inject CSS for dark mode only
    css = f"""
    <style>
      /* Base styles */
      .stApp {{
        background-color: {current_theme_colors['bg']} !important;
        color: {current_theme_colors['fg']} !important;
      }}

      /* Remove default link styling */
      a {{
        color: inherit !important;
        text-decoration: none !important;
      }}

      /* Fix logout button styling */
      .logout-button {{
        background-color: {current_theme_colors['gray']};
        color: {current_theme_colors['bg']} !important;
        border: 1px solid {current_theme_colors['gray']};
        border-radius: 6px;
        padding: 0.4rem 0.75rem;
        font-size: 14px;
        height: 38px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s ease;
      }}

      .logout-button:hover {{
        background-color: {current_theme_colors['orange']};
        border-color: {current_theme_colors['orange']};
        color: {current_theme_colors['bg']} !important;
      }}

      /* Specifically target budget tab row */
      [data-testid="stHorizontalBlock"] {{
        display: flex !important;
        align-items: flex-end !important;
        gap: 1rem;
      }}

      /* Column containers in budget tab */
      [data-testid="stHorizontalBlock"] > div {{
        flex: 1;
        margin-bottom: 1rem !important;
      }}

      /* Label styling for consistent height */
      .stSelectbox label,
      .stNumberInput label {{
        margin-bottom: 0.5rem !important;
        display: block !important;
      }}

      /* Common height for all interactive elements */
      .stSelectbox > div,
      .stNumberInput > div,
      .stTextInput > div,
      .stButton > button {{
        height: 38px !important;
      }}

      /* Selectbox specific styling */
      .stSelectbox [data-baseweb="select"] {{
        border: none !important;
      }}

      .stSelectbox > div > div {{
        background-color: {current_theme_colors['bg']};
        border: 1px solid {current_theme_colors['gray']};
        border-radius: 6px;
        height: 38px !important;
      }}

      .stSelectbox [role="button"] {{
        display: flex;
        align-items: center;
        height: 100%;
      }}

      .stSelectbox [role="button"] > div:first-child {{
        padding: 6px 8px;
        flex: 1;
        color: {current_theme_colors['fg']};
      }}

      .stSelectbox [role="button"] > div:last-child {{
        padding-right: 8px;
      }}

      /* Number input styling */
      .stNumberInput input {{
        height: 38px !important;
        background-color: {current_theme_colors['bg']} !important;
        color: {current_theme_colors['fg']} !important;
        border: 1px solid {current_theme_colors['gray']} !important;
        border-radius: 6px !important;
        padding: 0.4rem 0.6rem !important;
        box-sizing: border-box !important;
      }}

      /* Button styling */
      .stButton > button {{
        width: 100% !important;
        height: 38px !important;
        background-color: {current_theme_colors['gray']};
        color: {current_theme_colors['bg']};
        border: 1px solid {current_theme_colors['gray']};
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
      }}

      .stButton > button:hover {{
        background-color: {current_theme_colors['orange']};
        border-color: {current_theme_colors['orange']};
      }}

      /* Logout button */
      .logout-button {{
        background-color: {current_theme_colors['gray']};
        color: {current_theme_colors['bg']};
        border: 1px solid {current_theme_colors['gray']};
        border-radius: 6px;
        padding: 0.4rem 0.75rem;
        text-decoration: none;
        font-size: 14px;
        height: 38px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
      }}

      .logout-button:hover {{
        background-color: {current_theme_colors['orange']};
        border-color: {current_theme_colors['orange']};
      }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

    # Initialize user DB and session state
    init_user_db()
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = ''

    # --- Centered Login/Signup ---
    if not st.session_state.authenticated:
        st.title("Welcome to Personal Expense Tracker")
        tab_login, tab_signup = st.tabs(["Login", "Sign Up"])
        with tab_login:
            with st.form("login_form"):
                user = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    if authenticate_user(user, password):
                        st.session_state.authenticated = True
                        st.session_state.username = user
                        # Clear any URL parameters (like logout=true) on login
                        st.query_params.clear()
                    else:
                        st.error("Invalid credentials")
        with tab_signup:
            with st.form("signup_form"):
                new_user = st.text_input("New Username")
                new_pass = st.text_input("New Password", type="password")
                confirm_pass = st.text_input("Confirm Password", type="password")
                if st.form_submit_button("Sign Up"):
                    if new_pass != confirm_pass:
                        st.error("Passwords do not match")
                    elif signup_user(new_user, new_pass):
                        st.success("Registration successful! Please log in.")
                    else:
                        st.error("Username already exists")
        # Stop rendering further until authenticated
        return

    # Main app after authentication
    # Title and Logout aligned in one row
    # Header with custom HTML logout button that won't have extra space
    st.markdown(
        f'''
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <h3>Expense Tracker: {st.session_state.username}</h3>
            <a href="?logout=true" class="logout-button" target="_self">
                Logout
            </a>
        </div>
        ''', 
        unsafe_allow_html=True
    )
    
    # Check if logout was clicked
    if st.query_params.get("logout") == "true":
        st.session_state.authenticated = False
        st.session_state.username = ''
        st.query_params.clear()
        st.success("Logged out")
        return

    # Per-user DB setup
    username = st.session_state.username
    db_file = f"expenses_{username}.db"
    init_db(db_file)

    tab_add, tab_dashboard, tab_budget = st.tabs(["Add New Expense", "View Dashboard", "Budget Management"])
    
    with tab_add:
        d = st.date_input('Date', date.today())
        cat = st.selectbox('Category', ['Food', 'Transport', 'Utilities', 'Entertainment', 'Health', 'Other'])
        desc = st.text_input('Description')
        amt = st.number_input('Amount', min_value=0.0, step=100.0, format='%.2f')
        
        # Receipt photo upload
        st.write("📷 **Receipt Photo (Optional)**")
        uploaded_file = st.file_uploader("Upload receipt image", type=['png', 'jpg', 'jpeg'], help="Upload a photo of your receipt for record keeping")
        
        # Show preview if image is uploaded
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Receipt Preview", width=300)
        
        if st.button('Add Expense'):
            # Process uploaded image
            receipt_data = None
            if uploaded_file is not None:
                # Convert image to bytes for storage
                img_bytes = uploaded_file.getvalue()
                receipt_data = base64.b64encode(img_bytes).decode()
            
            add_expense(db_file, d.isoformat(), cat, desc, amt, receipt_data)
            st.success('Expense added successfully!')
            if uploaded_file is not None:
                st.success('Receipt photo saved! 📸')

    with tab_dashboard:
        df = get_expenses(db_file)
        if df.empty:
            st.info('No expenses recorded yet.')
        else:
            df['date'] = pd.to_datetime(df['date'])
            
            # Filtering options
            st.subheader("Filter Expenses")
            col1, col2, col3 = st.columns(3)
            with col1:
                start_date = st.date_input("From Date", value=df['date'].min().date())
            with col2:
                end_date = st.date_input("To Date", value=df['date'].max().date())
            with col3:
                available_categories = ['All'] + list(df['category'].unique())
                selected_category = st.selectbox("Category", available_categories)
            
            # Apply filters
            mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)
            if selected_category != 'All':
                mask = mask & (df['category'] == selected_category)
            filtered_df = df.loc[mask].copy()
            
            if filtered_df.empty:
                filter_msg = f"No expenses found between {start_date} and {end_date}"
                if selected_category != 'All':
                    filter_msg += f" for category '{selected_category}'"
                st.warning(filter_msg)
            else:
                # Display filterable data table with delete option
                st.subheader('All Expenses')
                
                # Add column headers
                header_cols = st.columns([0.15, 0.2, 0.25, 0.18, 0.12, 0.1])
                with header_cols[0]:
                    st.write("**Date**")
                with header_cols[1]:
                    st.write("**Category**")
                with header_cols[2]:
                    st.write("**Description**")
                with header_cols[3]:
                    st.write("**Amount**")
                with header_cols[4]:
                    st.write("**Receipt**")
                with header_cols[5]:
                    st.write("**Actions**")
                
                st.divider()
                
                with st.container():
                    for i, row in filtered_df.iterrows():
                        # Main expense row
                        cols = st.columns([0.15, 0.2, 0.25, 0.18, 0.12, 0.1])
                        with cols[0]:
                            st.write(row['date'].strftime('%Y-%m-%d'))
                        with cols[1]:
                            st.write(row['category'])
                        with cols[2]:
                            st.write(row['description'])
                        with cols[3]:
                            st.write(f"₹{row['amount']:.2f}")
                        with cols[4]:
                            # Receipt photo button
                            has_receipt = row.get('receipt_photo') is not None
                            if has_receipt:
                                if st.button("📷", key=f"view_{row['id']}", help="View receipt"):
                                    st.session_state[f"show_receipt_{row['id']}"] = not st.session_state.get(f"show_receipt_{row['id']}", False)
                            else:
                                st.write("📋")  # No receipt indicator
                        with cols[5]:
                            if st.button("🗑️", key=f"del_{row['id']}", help="Delete expense"):
                                delete_expense(db_file, row['id'])
                                st.success("Expense deleted!")
                                st.rerun()
                        
                        # Show receipt image if button was clicked
                        if has_receipt and st.session_state.get(f"show_receipt_{row['id']}", False):
                            try:
                                # Decode base64 image
                                img_data = base64.b64decode(row['receipt_photo'])
                                image = Image.open(io.BytesIO(img_data))
                                st.image(image, caption=f"Receipt for {row['description']}", width=400)
                            except Exception as e:
                                st.error(f"Error loading receipt image: {str(e)}")
                        
                        st.divider()  # Add separator between expenses
             
                # Charts
                st.subheader('Spending Over Time')
                df_indexed = filtered_df.set_index('date')
                daily = df_indexed.resample('D').sum()
                st.line_chart(daily['amount'])

                st.subheader('Category Breakdown')
                breakdown = filtered_df.groupby('category')['amount'].sum()
                # Pie chart
                fig, ax = plt.subplots()
                ax.pie(breakdown, labels=breakdown.index, autopct='%1.1f%%')
                ax.set_title('Category Breakdown')
                st.pyplot(fig)
                
                # Download Excel
                towrite = io.BytesIO()
                with pd.ExcelWriter(towrite, engine='openpyxl') as writer:
                    filtered_df.to_excel(writer, sheet_name='Expenses', index=False)
                st.download_button(
                    label='Download data as Excel',
                    data=towrite.getvalue(),
                    file_name=f'expenses_{username}_{start_date}_{end_date}.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )

    with tab_budget:
        df = get_expenses(db_file)
        budget_df = get_budget_goals(db_file)
        
        st.subheader("Set Monthly Budget Goals")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            budget_cat = st.selectbox("Category", ['Food', 'Transport', 'Utilities', 'Entertainment', 'Health', 'Other'], key="budget_cat")
        with col2:
            cat_limit = st.number_input("Monthly Limit (₹)", min_value=0.0, step=100.0, format="%.2f", key="budget_amt")
        with col3:
            if st.button("Set Budget"):
                set_budget_goal(db_file, budget_cat, cat_limit)
                st.success(f"Budget goal set for {budget_cat}")
                st.rerun()
        
        if not budget_df.empty:
            st.subheader("Current Budget Goals")
            # Create a container for budget goals
            with st.container():
                for _, budget_row in budget_df.iterrows():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"**{budget_row['category']}**: ₹{budget_row['monthly_limit']:.2f}")
                    with col2:
                        if st.button("🗑️", key=f"del_budget_{budget_row['category']}", help=f"Remove budget for {budget_row['category']}"):
                            delete_budget_goal(db_file, budget_row['category'])
                            st.success(f"Budget for {budget_row['category']} removed!")
                            st.rerun()

            if budget_df.empty:
                st.info("No budget goals set yet.")
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            
            # Current month's spending by category
            today = date.today()
            month_start = date(today.year, today.month, 1)
            month_mask = (df['date'].dt.date >= month_start) & (df['date'].dt.date <= today)
            month_df = df.loc[month_mask].copy()
            month_totals = month_df.groupby('category')['amount'].sum().reset_index()
            
            if not budget_df.empty:
                st.subheader("Budget Progress (Current Month)")
                for _, budget_row in budget_df.iterrows():
                    cat = budget_row['category']
                    limit = budget_row['monthly_limit']
                    
                    # Find actual spending
                    cat_total = month_totals.loc[month_totals['category'] == cat, 'amount'].sum() if cat in month_totals['category'].values else 0
                    
                    # Calculate percentage
                    percentage = min((cat_total / limit) * 100, 100) if limit > 0 else 0
                    
                    # Determine color based on percentage
                    if percentage >= 100:
                        color = "#ff4b4b"  # Red for over budget
                        status_emoji = "🔴"
                    elif percentage >= 80:
                        color = "#ffa500"  # Orange/Yellow for warning
                        status_emoji = "🟡"
                    else:
                        color = "#00ff00"  # Green for safe
                        status_emoji = "🟢"
                    
                    # Display category info with status emoji
                    st.write(f"{status_emoji} **{cat}**: ₹{cat_total:.2f} of ₹{limit:.2f} ({percentage:.1f}%)")
                    
                    # Custom colored progress bar using HTML
                    progress_html = f"""
                    <div style="background-color: #e0e0e0; border-radius: 10px; padding: 2px; margin: 5px 0;">
                        <div style="background-color: {color}; width: {min(percentage, 100)}%; height: 20px; border-radius: 8px; 
                                    display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 12px;">
                            {percentage:.1f}%
                        </div>
                    </div>
                    """
                    st.markdown(progress_html, unsafe_allow_html=True)
                    
                    # Status messages
                    if cat_total > limit:
                        st.error(f"⚠️ Over budget by ₹{cat_total - limit:.2f} in {cat}")
                    elif percentage > 80:
                        st.warning(f"💡 You've used {percentage:.1f}% of your {cat} budget")
                    elif percentage > 0:
                        st.success(f"✅ {cat} spending is on track!")
        else:
            st.info("No expenses recorded yet. Add some expenses to see budget progress.")

    # Add UI for deleting user account
    st.markdown("---")
    st.markdown("### Delete Account")
    username_to_delete = st.text_input("Enter your username to delete your account:")
    if st.button("Delete Account"):
        if username_to_delete:
            if delete_user_account(username_to_delete):
                st.success("Account deleted successfully!")
            else:
                st.error("Failed to delete account. Please try again.")
        else:
            st.error("Please enter a username.")

    st.markdown("---")
    st.markdown("**GitHub Repository:** [Personal Expense Tracker](https://github.com/shubhpsd/expense-tracker)")
    st.markdown("**Made by:** Shubham Prasad")

if __name__ == '__main__':
    main()
