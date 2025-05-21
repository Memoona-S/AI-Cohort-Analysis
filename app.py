# Import necessary libraries
import streamlit as st                          # For creating interactive web app UI
import pandas as pd                             # For data handling and analysis
import matplotlib.pyplot as plt                 # For plotting graphs
import seaborn as sns                           # For making beautiful heatmap visuals
import os                                       # For accessing environment variables
from openai import OpenAI                       # <-- Updated to OpenAI API (new line)
from dotenv import load_dotenv                  # For securely loading API keys
from operator import attrgetter                 # For date calculations

# Load API key securely from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")    # <-- Updated variable name (new line)

# Check if the API key exists, stop app if not found
if not OPENAI_API_KEY:
    st.error("🚨 API Key is missing! Set it in Streamlit Secrets or a .env file.")
    st.stop()

# Streamlit App UI: Title and instructions
st.title("🤖 FP&A AI Agent - SaaS Cohort Analysis")
st.write("Upload an Excel file, analyze retention rates, and get AI-generated FP&A insights!")

# File uploader widget for user input (Excel files only)
uploaded_file = st.file_uploader("📂 Upload your cohort data (Excel format)", type=["xlsx"])

if uploaded_file:
    # Read the uploaded Excel file into a pandas DataFrame
    sales_data = pd.read_excel(uploaded_file)

    # Convert "Date" column to a proper datetime format
    sales_data['Date'] = pd.to_datetime(sales_data['Date'])

    # Extract first month of purchase (cohort month) for each unique customer
    sales_data['CohortMonth'] = sales_data.groupby('Customer_ID')['Date'].transform('min').dt.to_period('M')

    # Calculate the month difference (CohortIndex) between purchase date and cohort month
    sales_data['PurchaseMonth'] = sales_data['Date'].dt.to_period('M')
    sales_data['CohortIndex'] = (sales_data['PurchaseMonth'] - sales_data['CohortMonth']).apply(attrgetter('n'))

    # Pivot data to create cohort analysis table: counts unique customers in each cohort-month pair
    cohort_counts = sales_data.pivot_table(
        index='CohortMonth',
        columns='CohortIndex',
        values='Customer_ID',
        aggfunc='nunique'
    )

    # Calculate retention rates (percentages retained each month)
    cohort_sizes = cohort_counts.iloc[:, 0]
    retention_rate = cohort_counts.divide(cohort_sizes, axis=0)

    # Display a preview of the data to the user
    st.subheader("📊 Data Preview")
    st.dataframe(sales_data.head())

    # Plot and display retention rate heatmap
    st.subheader("🔥 Retention Rate Heatmap")
    plt.figure(figsize=(16, 9))  # Set plot size
    sns.heatmap(retention_rate, annot=True, fmt=".0%", cmap="YlGnBu", linewidths=0.5)  # Create heatmap
    plt.title('Cohort Analysis - Retention Rate', fontsize=16)
    plt.xlabel('Months Since First Purchase', fontsize=12)
    plt.ylabel('Cohort Month', fontsize=12)
    plt.tight_layout()  # Adjust layout for clear visuals
    st.pyplot(plt)  # Display plot in Streamlit

    # Prepare text summary of cohort analysis to send to AI
    cohort_summary = f"""
    📌 **Cohort Analysis Summary**:
    - Number of Cohorts: {len(cohort_counts)}
    - Retention Rate Breakdown:
    {retention_rate.to_string()}
    """

    # Streamlit section for AI commentary
    st.subheader("🤖 AI Agent - FP&A Commentary")

    # User input text area for custom prompts/questions
    user_prompt = st.text_area(
        "📝 Enter your question for the AI:",
        "Analyze the cohort retention data and provide key FP&A insights."
    )

    # Button to trigger AI commentary generation
    if st.button("🚀 Generate AI Commentary"):

        # Initialize OpenAI API client (updated section)
        client = OpenAI(OPENAI_API_KEY)  # <-- Updated client initialization

        # Send the cohort summary and user prompt to OpenAI GPT-4o model
        response = client.chat.completions.create(
            model="gpt-4o",   # <-- Updated to GPT-4o
            messages=[
                {"role": "system",
                 "content": "You are an expert FP&A analyst providing detailed financial insights."},
                {"role": "user",
                 "content": f"The cohort retention analysis is summarized below:\n{cohort_summary}\n\n{user_prompt}"}
            ]
        )

        # Extract AI-generated commentary from OpenAI response
        ai_commentary = response.choices[0].message.content

        # Display AI-generated insights clearly to user
        st.subheader("💡 AI-Generated FP&A Insights")
        st.write(ai_commentary)
