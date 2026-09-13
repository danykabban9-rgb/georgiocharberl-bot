import yfinance as yf
import pandas as pd
import numpy as np
from telegram.ext import Updater, CommandHandler

# === CONFIG ===
TOKEN = "YOUR_NEW_BOTFATHER_TOKEN"

# === INDICATORS ===
def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    return true_range.rolling(period).mean()

# === PATTERN DETECTION ===
def detect_double_top(df, lookback=50):
    highs = df['High'].tail(lookback)
    max1 = highs.idxmax()
    max2 = highs.drop(max1).idxmax()
    if abs(df['High'][max1] - df['High'][max2]) < 1.0:
        return True
    return False

def detect_double_bottom(df, lookback=50):
    lows = df['Low'].tail(lookback)
    min1 = lows.idxmin()
    min2 = lows.drop(min1).idxmin()
    if abs(df['Low'][min1] - df['Low'][min2]) < 1.0:
        return True
    return False

def detect_candlestick_patterns(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    # Bullish Engulfing
    if last['Close'] > last['Open'] and prev['Close'] < prev['Open'] and last['Close'] > prev['Open'] and last['Open'] < prev['Close']:
        return "Bullish Engulfing"

    # Bearish Engulfing
    if last['Close'] < last['Open'] and prev['Close'] > prev['Open'] and last['Open'] > prev['Close'] and last['Close'] < prev['Open']:
        return "Bearish Engulfing"

    # Doji
    if abs(last['Close'] - last['Open']) <= (last['High'] - last['Low']) * 0.1:
        return "Doji"

    # Pin Bar
    body = abs(last['Close'] - last['Open'])
    upper_wick = last['High'] - max(last['Close'], last['Open'])
    lower_wick = min(last['Close'], last['Open']) - last['Low']
    if upper_wick > body * 2:
        return "Pin Bar (Bearish)"
    if lower_wick > body * 2:
        return "Pin Bar (Bullish)"

    return None

# === SIGNAL ENGINE ===
def generate_signal():
    daily = yf.download("XAUUSD=X", interval="1d", period="6mo")
    intraday = yf.download("XAUUSD=X", interval="5m", period="5d")

    # Daily trend
    daily['EMA50'] = ema(daily['Close'], 50)
    daily['EMA200'] = ema(daily['Close'], 200)
    trend = "Bullish" if daily['EMA50'].iloc[-1] > daily['EMA200'].iloc[-1] else "Bearish"

    # Intraday signals
    intraday['EMA9'] = ema(intraday['Close'], 9)
    intraday['EMA21'] = ema(intraday['Close'], 21)
    intraday['RSI'] = rsi(intraday['Close'])
    intraday['ATR'] = atr(intraday)

    last = intraday.iloc[-1]

    # Base signal
    if last['EMA9'] > last['EMA21'] and last['RSI'] < 70:
        signal_type = "BUY"
        confidence = 70
    elif last['EMA9'] < last['EMA21'] and last['RSI'] > 30:
        signal_type = "SELL"
        confidence = 70
    else:
        signal_type = "NO TRADE"
        confidence = 50

    # Pattern boosts
    pattern = detect_candlestick_patterns(intraday)
    if pattern == "Bullish Engulfing" or pattern == "Pin Bar (Bullish)":
        signal_type = "BUY"
        confidence += 15
    elif pattern == "Bearish Engulfing" or pattern == "Pin Bar (Bearish)":
        signal_type = "SELL"
        confidence += 15
    elif pattern == "Doji":
        confidence -= 10

    if detect_double_top(intraday):
        signal_type = "SELL"
        confidence += 10
    if detect_double_bottom(intraday):
        signal_type = "BUY"
        confidence += 10

    # ATR-based scalping SL/TP
    atr_value = last['ATR']
    entry = last['Close']
    if signal_type == "BUY":
        sl = entry - (atr_value * 0.5)
        tp = entry + (atr_value * 1.0)
    elif signal_type == "SELL":
        sl = entry + (atr_value * 0.5)
        tp = entry - (atr_value * 1.0)
    else:
        sl, tp = entry, entry

    return f"""
⚡ GOLD SCALPING SIGNAL
Type: {signal_type}
Pattern: {pattern if pattern else "None"}
Trend: {trend}
Entry: {entry:.2f}
SL: {sl:.2f}
TP: {tp:.2f}
Winning Rate: {confidence}%
ATR(5m): {atr_value:.2f}
"""

# === TELEGRAM COMMAND ===
def signal(update, context):
    msg = generate_signal()
    update.message.reply_text(msg)

updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher
dp.add_handler(CommandHandler("signal", signal))

updater.start_polling()
updater.idle()
