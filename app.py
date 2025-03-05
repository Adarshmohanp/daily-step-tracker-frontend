import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Backend API URL
API_URL = "http://127.0.0.1:5000"

# Title of the app
st.title("Daily Step Tracker Dashboard")

# User session state
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

# Sidebar for navigation
st.sidebar.title("Navigation")
if st.session_state['user_id'] is None:
    options = st.sidebar.radio("Choose an option", ["Login", "Register"])
else:
    options = st.sidebar.radio("Choose an option", ["Upload Data", "View Data", "Visualizations", "Predictions", "Logout"])

# User registration
if options == "Register":
    st.header("User Registration")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Register"):
        response = requests.post(f"{API_URL}/register", json={"username": username, "password": password})
        if response.status_code == 200:
            st.success("User registered successfully!")
        else:
            st.error(response.json()["message"])

# User login
elif options == "Login":
    st.header("User Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        response = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
        if response.status_code == 200:
            st.session_state['user_id'] = response.json()["user_id"]
            st.success("Login successful!")
        else:
            st.error("Invalid username or password!")

# Logout
elif options == "Logout":
    st.session_state['user_id'] = None
    st.success("Logged out successfully!")

# Upload step count data
elif options == "Upload Data":
    st.header("Upload Step Count Data")
    date = st.date_input("Date")
    step_count = st.number_input("Step Count", min_value=0)
    if st.button("Upload"):
        response = requests.post(
            f"{API_URL}/upload",
            json={
                "user_id": st.session_state['user_id'],
                "date": str(date),
                "step_count": step_count
            }
        )
        if response.status_code == 200:
            st.success("Data uploaded successfully!")
        else:
            st.error("Failed to upload data.")

# Fetch and display historical data
elif options == "View Data":
    st.header("Historical Data")
    if st.button("Fetch Data"):
        response = requests.get(f"{API_URL}/data", params={"user_id": st.session_state['user_id']})
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            if not df.empty:
                # Select only 'date' and 'step_count' columns
                df = df[['date', 'step_count']]
                st.write(df)
            else:
                st.warning("No data available. Please upload data first.")
        else:
            st.error("Failed to fetch data.")

# Data visualizations
elif options == "Visualizations":
    st.header("Data Visualizations")

    # Fetch data from the backend
    response = requests.get(f"{API_URL}/data", params={"user_id": st.session_state['user_id']})
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])  # Convert 'date' column to datetime

            # Daily Step Trends (Line Graph)
            st.subheader("Daily Step Trends")
            plt.figure(figsize=(10, 6))
            sns.lineplot(x='date', y='step_count', data=df, marker='o')
            plt.title("Daily Step Count Over Time")
            plt.xlabel("Date")
            plt.ylabel("Step Count")
            st.pyplot(plt)

            # Active vs. Inactive Days (Bar Chart and Pie Chart)
            st.subheader("Active vs. Inactive Days")
            df['activity'] = df['step_count'].apply(lambda x: "Active" if x > 5000 else "Inactive")
            activity_counts = df['activity'].value_counts()

            # Bar Chart
            plt.figure(figsize=(8, 5))
            sns.barplot(x=activity_counts.index, y=activity_counts.values, palette="Set2")
            plt.title("Active vs. Inactive Days")
            plt.xlabel("Activity")
            plt.ylabel("Number of Days")
            st.pyplot(plt)

            # Pie Chart
            plt.figure(figsize=(6, 6))
            plt.pie(activity_counts, labels=activity_counts.index, autopct='%1.1f%%', colors=['lightgreen', 'lightcoral'])
            plt.title("Activity Distribution")
            st.pyplot(plt)

            # Weekly and Monthly Averages (Bar Charts)
            st.subheader("Weekly and Monthly Averages")

            # Weekly Averages
            df['week'] = df['date'].dt.isocalendar().week  # Extract week number
            weekly_avg = df.groupby('week')['step_count'].mean()

            plt.figure(figsize=(10, 6))
            sns.barplot(x=weekly_avg.index, y=weekly_avg.values, palette="viridis")
            plt.title("Weekly Average Step Counts")
            plt.xlabel("Week")
            plt.ylabel("Average Step Count")
            st.pyplot(plt)

            # Monthly Averages
            df['month'] = df['date'].dt.to_period('M')  # Extract month
            monthly_avg = df.groupby('month')['step_count'].mean()

            plt.figure(figsize=(10, 6))
            sns.barplot(x=monthly_avg.index.astype(str), y=monthly_avg.values, palette="magma")
            plt.title("Monthly Average Step Counts")
            plt.xlabel("Month")
            plt.ylabel("Average Step Count")
            st.pyplot(plt)
        else:
            st.warning("No data available. Please upload data first.")
    else:
        st.error("Failed to fetch data for visualizations.")

# Generate predictions and recommendations
elif options == "Predictions":
    st.header("Step Count Predictions and Recommendations")

    if st.button("Generate Predictions and Recommendations"):
        # Fetch historical data
        response = requests.get(f"{API_URL}/data", params={"user_id": st.session_state['user_id']})
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])  # Convert 'date' column to datetime

                # Generate predictions
                response = requests.get(f"{API_URL}/predict", params={"user_id": st.session_state['user_id']})
                if response.status_code == 200:
                    predictions = response.json()["predictions"]
                    st.write("Predicted Step Counts for the Next 7 Days:")
                    for i, steps in enumerate(predictions, start=1):
                        st.write(f"Day {i}: {steps:.2f} steps")

                    # Plot the predictions
                    plt.figure(figsize=(10, 6))
                    plt.plot(range(1, 8), predictions, marker='o')
                    plt.title("Predicted Step Counts for the Next 7 Days")
                    plt.xlabel("Day")
                    plt.ylabel("Step Count")
                    st.pyplot(plt)

                    # Generate recommendations
                    st.subheader("Recommendations")

                    # Check weekend activity
                    df['day_of_week'] = df['date'].dt.day_name()
                    weekend_activity = df[df['day_of_week'].isin(['Saturday', 'Sunday'])]['step_count'].mean()
                    if weekend_activity < 5000:
                        st.write("📉 **You’ve been less active on weekends. Try to increase your activity on weekends!**")

                    # Compare current week to previous week
                    df['week'] = df['date'].dt.isocalendar().week
                    weekly_avg = df.groupby('week')['step_count'].mean()
                    if len(weekly_avg) > 1:
                        current_week = weekly_avg.iloc[-1]
                        previous_week = weekly_avg.iloc[-2]
                        if current_week < previous_week:
                            st.write("📉 **You’ve been less active this week compared to last week. Try to increase your activity!**")
                        else:
                            st.write("📈 **Great job! You’ve been more active this week compared to last week.**")

                    # Check overall activity
                    overall_avg = df['step_count'].mean()
                    if overall_avg < 5000:
                        st.write("📉 **Your overall activity is low. Try to increase your daily step count!**")
                    else:
                        st.write("📈 **Great job! Your overall activity is good. Keep it up!**")

                else:
                    st.error("Failed to generate predictions.")
            else:
                st.warning("No data available. Please upload data first.")
        else:
            st.error("Failed to fetch data for recommendations.")