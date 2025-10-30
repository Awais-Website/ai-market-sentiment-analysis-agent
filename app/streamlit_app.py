import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_API_KEY", "")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

st.set_page_config(
    page_title="AI-Powered Market Sentiment Analysis Agent",
    layout="wide"
)

st.title("AI-Powered Market Sentiment Analysis Agent")
st.caption("(AI, Python, LangChain, SERP API)")

st.markdown(
    "This app collects context (industry, location, and market event) and demonstrates a placeholder market-sentiment analysis.\n"
    "Provide your API keys via a `.env` file for live LangChain + SERP API functionality."
)

with st.form("sentiment_form"):
    industry = st.text_input("Step 1 — Industry (e.g., Tech, Finance, Education):", "Apple")
    location = st.text_input("Step 2 — Location (e.g., US, Europe, APAC):", "US")
    scenario = st.text_input(
        "Step 3 — Market event or question (e.g., 'Should I buy Apple stock?')",
        "Should I buy Apple stock?"
    )
    submitted = st.form_submit_button("Run analysis")

if submitted:
    # Placeholder logic for demonstration. Replace with real LangChain and SERP API integration.
    st.subheader("Market Sentiment Report")
    st.write("Neutral: 80.00%")
    st.write("Positive: 20.00%")
    st.write("**Market sentiment is neutral. Mixed signals observed.**")

    st.divider()
    st.subheader("Top Financial News Articles")
    st.write("1. Magnificent Seven Stocks To Buy And Watch")
    st.write("2. Going Into Earnings, Is Apple Stock a Buy, a Sell, or Fairly Valued?")
    st.write("3. Is Apple a Buy, Sell, or Hold in 2025?")
    st.write("4. Should You Buy Apple Stock Before or After a New iPhone is Released?")
    st.write("5. Should I buy Apple shares for my ISA in February?")

    st.divider()
    st.caption("Note: This is a demo output. Connect LangChain + SERP API + LLM for live analysis.")
else:
    st.info("Fill in the fields above and click **Run analysis** to see the sentiment report.")
