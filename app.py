import streamlit as st
import pandas as pd
import yfinance as yf
import ta
import io

# Function to fetch stock indicators
def fetch_indicators(stock):
    ticker = yf.Ticker(stock)
    try:
        data = ticker.history(period="1y")
        if data.empty:
            return None
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
    except Exception as e:
        st.error(f"Error fetching data for {stock}: {e}")
        return None

# Function to score stocks based on indicators
def score_stock(indicators, term):
    score = 0
    if term == 'Short Term':
        if indicators['RSI'] is not None:
            if indicators['RSI'] < 30 or indicators['RSI'] > 70:
                score += 2
            if 30 <= indicators['RSI'] <= 40 or 60 <= indicators['RSI'] <= 70:
                score += 1
        if indicators['MACD'] is not None:
            if indicators['MACD'] > 0 and indicators['MACD'] > indicators['MACD_Signal']:
                score += 2
    elif term == 'Medium Term':
        if indicators['RSI'] is not None:
            if 40 <= indicators['RSI'] <= 60:
                score += 2
    elif term == 'Long Term':
        if indicators['RSI'] is not None:
            if 40 <= indicators['RSI'] <= 60:
                score += 2
        if indicators['Beta'] is not None:
            if 0.9 <= indicators['Beta'] <= 1.1:
                score += 2
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
            lower_buy_range = current_price * 0.995
            upper_buy_range = current_price * 1.005
            short_stop_loss = current_price * (1 - 0.03)
            short_target = current_price * (1 + 0.05)

            short_score = score_stock(indicators, 'Short Term')

            if short_score > 0:
                recommendations['Short Term'].append({
                    'Stock': stock.replace('.NS', ''),
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

    return recommendations

# Streamlit app
st.image("png_2.3-removebg.png", width=400)  # Your logo
st.title("PredictRAM - Stock Analysis and Call Generator")

# Slider for market cap selection
min_market_cap = st.slider("Select Minimum Market Cap", 117413688, 20505738346496, 117413688)
max_market_cap = st.slider("Select Maximum Market Cap", min_market_cap, 20505738346496, 20505738346496)

if st.button("Fetch Data"):
    st.info("Fetching data...")
    with st.spinner("Fetching stock indicators..."):
        try:
            stocks_df = pd.read_excel('stocks.xlsx')
            filtered_stocks = stocks_df[(stocks_df['marketCap'] >= min_market_cap) & 
                                         (stocks_df['marketCap'] <= max_market_cap)]['stocks'].tolist()

            indicators_list = {}
            for stock in filtered_stocks:
                indicators = fetch_indicators(stock)
                if indicators:
                    indicators_list[stock] = indicators

            if indicators_list:
                st.success("Data fetched successfully!")
                recommendations = generate_recommendations(indicators_list)

                # Display top recommendations
                st.subheader("Top Short Term Trades")
                short_term_df = pd.DataFrame(recommendations['Short Term']).sort_values(by='Score', ascending=False).head(20)
                st.table(short_term_df)

                # Export to Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    short_term_df.to_excel(writer, sheet_name='Short Term', index=False)
                output.seek(0)

                st.download_button(
                    label="Download Recommendations",
                    data=output,
                    file_name="stock_recommendations.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("No valid data fetched.")
        except Exception as e:
            st.error(f"An error occurred: {e}")
