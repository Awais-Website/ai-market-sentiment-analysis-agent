import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from serpapi.google_search import GoogleSearch
import feedparser
import yfinance as yfinance

# Load environment variables from .env if present
load_dotenv()

if "SERPAPI_API_KEY" in st.secrets:
    SERPAPI_KEY = st.secrets["SERPAPI_API_KEY"]
    OPENAI_KEY = st.secrets["OPENAI_API_KEY"]
else:
    from dotenv import load_dotenv
    import os
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
    "This app collects context (industry, location, and market event) and performs **real-time market-sentiment analysis** "
    "using SerpAPI to fetch financial news and OpenAI GPT-4 to analyze sentiment.\n\n"
#    "Provide your API keys via a `.env` file for live analysis."
)

# Forbes RSS helper
def fetch_forbes_news(keyword: str):
    """Fetch and filter Forbes real-time RSS feed by keyword. Returns top 5 entries."""
    try:
        feed = feedparser.parse("https://www.forbes.com/real-time/feed/")
        if not feed or not getattr(feed, "entries", None):
            return []
        keyword_l = (keyword or "").lower()
        filtered = [entry for entry in feed.entries if keyword_l in getattr(entry, "title", "").lower()]
        return filtered[:5]
    except Exception as e:
        st.error(f"Error fetching Forbes RSS: {str(e)}")
        return []

# Yahoo Finance helper
def fetch_stock_data(symbol: str):
    """Fetch last 5 days of OHLCV for the provided ticker symbol using yfinance."""
    try:
        if not symbol:
            return None
        data = yfinance.Ticker(symbol)
        hist = data.history(period="5d").tail(5)
        return hist
    except Exception as e:
        st.error(f"Error fetching stock data: {str(e)}")
        return None

# Helper function to fetch news from SerpAPI
def fetch_financial_news(industry, location, scenario, api_key):
    """Fetches financial news related to the user's query using SerpAPI."""
    query = f"{industry} {location} {scenario}"
    
    params = {
        "q": query,
        "tbm": "nws",  # News search mode
        "num": 5,  # Limit results to 5 articles (matching notebook)
        "api_key": api_key
    }
    
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "news_results" in results:
            return [article["title"] for article in results["news_results"]]
        else:
            return []
    except Exception as e:
        st.error(f"Error fetching news: {str(e)}")
        return []

# Helper function to analyze sentiment using OpenAI
def analyze_sentiment_gpt4(text, client):
    """Uses GPT-4 to classify sentiment as Positive, Negative, or Neutral."""
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Analyze the sentiment of the given financial news headline. Reply with only one word: Positive, Negative, or Neutral."
                },
                {"role": "user", "content": text}
            ],
            temperature=0,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error analyzing sentiment: {str(e)}")
        return "Neutral"

# Helper function to generate market summary
def generate_market_summary(sentiment_results):
    """Creates a market sentiment report based on sentiment distribution."""
    if not sentiment_results:
        return "No sentiment data available.", {}
    
    sentiment_values = list(sentiment_results.values())
    sentiment_counts = pd.Series(sentiment_values).value_counts(normalize=True) * 100
    
    # Create summary text
    summary = "📈 **Market Sentiment Report:**\n\n"
    
    # Display percentages for each sentiment
    for sentiment in ["Positive", "Negative", "Neutral"]:
        if sentiment in sentiment_counts:
            percentage = sentiment_counts[sentiment]
            summary += f"{sentiment}: {percentage:.2f}%\n"
    
    # Generate conclusion based on sentiment distribution
    # Ignore neutral - only compare positive vs negative
    negative_pct = sentiment_counts.get("Negative", 0)
    positive_pct = sentiment_counts.get("Positive", 0)
    
    # Compare only positive vs negative (ignore neutral)
    if positive_pct > negative_pct:
        conclusion = f"\n✅ **Overall Sentiment: POSITIVE** - Market sentiment is positive ({positive_pct:.1f}% positive vs {negative_pct:.1f}% negative). Growth opportunities ahead."
    elif negative_pct > positive_pct:
        conclusion = f"\n⚠️ **Overall Sentiment: NEGATIVE** - Market sentiment is negative ({negative_pct:.1f}% negative vs {positive_pct:.1f}% positive). High risk detected. Caution advised."
    else:
        # Positive and negative are equal
        conclusion = f"\n🔸 **Overall Sentiment: MIXED** - Mixed signals observed ({positive_pct:.1f}% positive, {negative_pct:.1f}% negative). Proceed with caution."
    
    summary += conclusion
    
    return summary, sentiment_counts.to_dict()

with st.form("sentiment_form"):
    industry = st.text_input("Step 1 — Industry (e.g., Tech, Finance, Education):", "Apple")
    location = st.text_input("Step 2 — Location (e.g., US, Europe, APAC):", "US")
    scenario = st.text_input(
        "Step 3 — Market event or question (e.g., 'Should I buy Apple stock?')",
        "Should I buy Apple stock?"
    )
    stock_symbol = st.text_input("Optional — Stock symbol for Yahoo Finance (e.g., AAPL, MSFT):", "AAPL")
    submitted = st.form_submit_button("Run analysis")

if submitted:
    # Validate API keys
    if not SERPAPI_KEY:
        st.error("⚠️ SERPAPI_API_KEY not found in .env file. Please add your SerpAPI key.")
        st.stop()
    
    if not OPENAI_KEY:
        st.error("⚠️ OPENAI_API_KEY not found in .env file. Please add your OpenAI API key.")
        st.stop()
    
    # Show loading state
    with st.spinner("Fetching financial news and analyzing sentiment..."):
        # Fetch news from SerpAPI (matching notebook approach)
        news_headlines = fetch_financial_news(industry, location, scenario, SERPAPI_KEY)
        
        if not news_headlines or len(news_headlines) == 0:
            st.warning("No news articles found. Please try different search terms.")
            st.stop()
        
        # Initialize OpenAI client
        client = OpenAI(api_key=OPENAI_KEY)
        
        # Analyze sentiment for each headline (matching notebook structure)
        sentiment_results = {}
        progress_bar = st.progress(0)
        total_articles = len(news_headlines)
        
        for i, headline in enumerate(news_headlines):
            if headline and headline != "No relevant news found.":
                sentiment = analyze_sentiment_gpt4(headline, client)
                sentiment_results[headline] = sentiment
            progress_bar.progress((i + 1) / total_articles)
        
        progress_bar.empty()
        
        # Generate market summary
        summary_text, sentiment_stats = generate_market_summary(sentiment_results)
    
    # Display results
    st.subheader("Market Sentiment Report")
    st.markdown(summary_text)

    st.divider()
    st.subheader("Top Financial News Articles Analyzed")
    
    # Display articles with their sentiment
    for idx, (headline, sentiment) in enumerate(sentiment_results.items(), 1):
        # Color code based on sentiment
        if sentiment == "Positive":
            sentiment_emoji = "✅"
        elif sentiment == "Negative":
            sentiment_emoji = "⚠️"
        else:
            sentiment_emoji = "🔸"
        
        st.write(f"{idx}. {sentiment_emoji} **{sentiment}**: {headline}")

    st.divider()
    # Forbes RSS section
    st.subheader("Forbes Real-Time News (Filtered)")
    forbes_items = fetch_forbes_news(industry)
    if not forbes_items:
        st.write("No Forbes articles matched your industry filter.")
    else:
        for i, entry in enumerate(forbes_items, start=1):
            title = getattr(entry, "title", "Untitled")
            link = getattr(entry, "link", None)
            published = getattr(entry, "published", "")
            if link:
                st.markdown(f"{i}. [{title}]({link})  ")
            else:
                st.write(f"{i}. {title}")
            if published:
                st.caption(published)

    st.divider()
    # Yahoo Finance section
    st.subheader("Latest Stock Data (Yahoo Finance)")
    stock_df = fetch_stock_data(stock_symbol)
    if stock_df is None or stock_df.empty:
        st.write("No stock data available. Please check the symbol.")
    else:
        st.dataframe(stock_df)
        try:
            st.line_chart(stock_df["Close"], use_container_width=True)
        except Exception:
            pass

    st.caption("✅ Analysis completed using real-time API data from SerpAPI, OpenAI GPT-4, Forbes RSS, and Yahoo Finance.")
else:
    st.info("Fill in the fields above and click **Run analysis** to see the sentiment report.")
