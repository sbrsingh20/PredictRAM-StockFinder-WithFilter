import streamlit as st
import pandas as pd
import yfinance as yf
import ta
import io

# Function to fetch stock indicators
def fetch_indicators(stock):
    ticker = yf.Ticker(stock)
    data = ticker.history(period="1y")

    if data.empty:
        return {
            'RSI': None,
            'MACD': None,
            'MACD_Signal': None,
            'MACD_Hist': None,
            'Upper_BB': None,
            'Lower_BB': None,
            'Volatility': None,
            'Beta': None,
            'Close': None
        }

    # Calculate indicators
    data['RSI'] = ta.momentum.RSIIndicator(data['Close'], window=14).rsi()
    macd = ta.trend.MACD(data['Close'])
    data['MACD'] = macd.macd()
    data['MACD_Signal'] = macd.macd_signal()
    data['MACD_Hist'] = macd.macd_diff()
    bb = ta.volatility.BollingerBands(data['Close'], window=20, window_dev=2)
    data['Upper_BB'] = bb.bollinger_hband()
    data['Lower_BB'] = bb.bollinger_lband()
    data['Volatility'] = data['Close'].pct_change().rolling(window=21).std() * 100
    beta = ticker.info.get('beta', None)

    try:
        return {
            'RSI': data['RSI'].iloc[-1],
            'MACD': data['MACD'].iloc[-1],
            'MACD_Signal': data['MACD_Signal'].iloc[-1],
            'MACD_Hist': data['MACD_Hist'].iloc[-1],
            'Upper_BB': data['Upper_BB'].iloc[-1],
            'Lower_BB': data['Lower_BB'].iloc[-1],
            'Volatility': data['Volatility'].iloc[-1],
            'Beta': beta,
            'Close': data['Close'].iloc[-1]
        }
    except IndexError:
        return {
            'RSI': None,
            'MACD': None,
            'MACD_Signal': None,
            'MACD_Hist': None,
            'Upper_BB': None,
            'Lower_BB': None,
            'Volatility': None,
            'Beta': None,
            'Close': None
        }

# Function to score stocks based on indicators for different terms
def score_stock(indicators, term):
    score = 0

    if term == 'Short Term':
        if indicators['RSI'] is not None:
            if indicators['RSI'] < 30 or indicators['RSI'] > 70:
                score += 2  # Good
            if 30 <= indicators['RSI'] <= 40 or 60 <= indicators['RSI'] <= 70:
                score += 1  # Neutral

        if indicators['MACD'] is not None:
            if indicators['MACD'] > 0 and indicators['MACD'] > indicators['MACD_Signal']:
                score += 2  # Good

    elif term == 'Medium Term':
        if indicators['RSI'] is not None:
            if 40 <= indicators['RSI'] <= 60:
                score += 2  # Good

        if indicators['MACD'] is not None:
            if abs(indicators['MACD']) < 0.01:  # Close to zero
                score += 1  # Neutral

    elif term == 'Long Term':
        if indicators['RSI'] is not None:
            if 40 <= indicators['RSI'] <= 60:
                score += 2  # Good

        if indicators['Beta'] is not None:
            if 0.9 <= indicators['Beta'] <= 1.1:
                score += 2  # Good

    return score

# Function to generate recommendations based on different strategies
def generate_recommendations(indicators_list):
    recommendations = {
        'Short Term': [],
        'Medium Term': [],
        'Long Term': []
    }
    
    for stock, indicators in indicators_list.items():
        current_price = indicators['Close']
        
        if current_price is not None:
            lower_buy_range = current_price * 0.995  # 0.5% lower
            upper_buy_range = current_price * 1.005  # 0.5% higher
            short_stop_loss = current_price * (1 - 0.03)  # Max 3%
            short_target = current_price * (1 + 0.05)  # Min 5%
            medium_stop_loss = current_price * (1 - 0.04)  # Max 4%
            medium_target = current_price * (1 + 0.10)  # Min 10%
            long_stop_loss = current_price * (1 - 0.05)  # Max 5%
            long_target = current_price * (1 + 0.15)  # Min 15%

            short_score = score_stock(indicators, 'Short Term')
            medium_score = score_stock(indicators, 'Medium Term')
            long_score = score_stock(indicators, 'Long Term')

            if short_score > 0:
                recommendations['Short Term'].append({
                    'Stock': stock.replace('.NS', ''),  # Remove .NS
                    'Current Price': current_price,
                    'Lower Buy Range': lower_buy_range,
                    'Upper Buy Range': upper_buy_range,
                    'Stop Loss': short_stop_loss,
                    'Target Price': short_target,
                    'Score': short_score,
                    'RSI': indicators['RSI'],
                    'MACD': indicators['MACD'],
                    'MACD_Signal': indicators['MACD_Signal'],
                    'Upper_BB': indicators['Upper_BB'],
                    'Lower_BB': indicators['Lower_BB'],
                    'Volatility': indicators['Volatility'],
                    'Beta': indicators['Beta']
                })

            if medium_score > 0:
                recommendations['Medium Term'].append({
                    'Stock': stock.replace('.NS', ''),  # Remove .NS
                    'Current Price': current_price,
                    'Lower Buy Range': lower_buy_range,
                    'Upper Buy Range': upper_buy_range,
                    'Stop Loss': medium_stop_loss,
                    'Target Price': medium_target,
                    'Score': medium_score,
                    'RSI': indicators['RSI'],
                    'MACD': indicators['MACD'],
                    'MACD_Signal': indicators['MACD_Signal'],
                    'Upper_BB': indicators['Upper_BB'],
                    'Lower_BB': indicators['Lower_BB'],
                    'Volatility': indicators['Volatility'],
                    'Beta': indicators['Beta']
                })

            if long_score > 0:
                recommendations['Long Term'].append({
                    'Stock': stock.replace('.NS', ''),  # Remove .NS
                    'Current Price': current_price,
                    'Lower Buy Range': lower_buy_range,
                    'Upper Buy Range': upper_buy_range,
                    'Stop Loss': long_stop_loss,
                    'Target Price': long_target,
                    'Score': long_score,
                    'RSI': indicators['RSI'],
                    'MACD': indicators['MACD'],
                    'MACD_Signal': indicators['MACD_Signal'],
                    'Upper_BB': indicators['Upper_BB'],
                    'Lower_BB': indicators['Lower_BB'],
                    'Volatility': indicators['Volatility'],
                    'Beta': indicators['Beta']
                })

    return recommendations

# Function to check user credentials
def check_credentials(email, password):
    users_df = pd.read_excel('user.xlsx')
    for _, row in users_df.iterrows():
        if row['Email'] == email and row['Password'] == password:
            return True
    return False

# Streamlit app
st.image("png_2.3-removebg.png", width=400)
st.title("PredictRAM - Stock Analysis and Call Generator")

# User authentication
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'min_market_cap' not in st.session_state:
    st.session_state.min_market_cap = 117413688

if 'max_market_cap' not in st.session_state:
    st.session_state.max_market_cap = 20505738346496

if st.session_state.logged_in:
    # Display market cap sliders if logged in
    st.session_state.min_market_cap = st.slider("Select Minimum Market Cap", 117413688, 20505738346496, st.session_state.min_market_cap)
    st.session_state.max_market_cap = st.slider("Select Maximum Market Cap", st.session_state.min_market_cap, 20505738346496, st.session_state.max_market_cap)

    if st.button("Reset"):
        # Reset only the market cap selections
        st.session_state.min_market_cap = 117413688
        st.session_state.max_market_cap = 20505738346496

    # Fetch data if both sliders have values
    if st.session_state.min_market_cap is not None and st.session_state.max_market_cap is not None:
        st.info("Fetching data...")
        with st.spinner("Fetching stock indicators..."):
            try:
                stocks_df = pd.read_excel('stocks.xlsx')
                stocks = stocks_df['stocks'].tolist()
                market_caps = stocks_df['marketCap'].tolist()

                # Filter stocks based on selected market cap range
                filtered_stocks = [stock for stock, cap in zip(stocks, market_caps)
                                   if st.session_state.min_market_cap <= cap <= st.session_state.max_market_cap]

                # Fetch indicators...
                indicators_list = {stock: fetch_indicators(stock) for stock in filtered_stocks}
                st.success("Data fetched successfully!")

                # Display recommendations...
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
else:
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if check_credentials(email, password):
            st.session_state.logged_in = True
            st.success("Logged in successfully!")
        else:
            st.error("Invalid email or password.")
