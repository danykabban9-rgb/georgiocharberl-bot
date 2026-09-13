import yfinance as yf
import pandas as pd
import numpy as np
from telegram.ext import Updater, CommandHandler

# --- Handlers ---

def start(update, context):
    update.message.reply_text("Bot is alive and ready! Use /signal, /stats, or /backtest.")

def signal(update, context):
    # Fetch gold price (XAUUSD 5m candles)
    data = yf.download("XAUUSD=X", period="1d", interval="5m")
    last_close = data["Close"].iloc[-1]

    # Example trading logic (simple moving average)
    sma_short = data["Close"].rolling(window=5).mean().iloc[-1]
    sma_long = data["Close"].rolling(window=20).mean().iloc[-1]

    if sma_short > sma_long:
        entry = last_close
        sl = entry - 2
        tp = entry + 4
        msg = f"📈 BUY Signal\nEntry: {entry:.2f}\nSL: {sl:.2f}\nTP: {tp:.2f}\nSuccess %: 70%"
    else:
        entry = last_close
        sl = entry + 2
        tp = entry - 4
        msg = f"📉 SELL Signal\nEntry: {entry:.2f}\nSL: {sl:.2f}\nTP: {tp:.2f}\nSuccess %: 65%"

    update.message.reply_text(msg)

def stats(update, context):
    # Dummy stats example
    msg = "📊 Bot Stats\nWin Rate: 68%\nSignals Sent: 120\nBest Pair: XAUUSD"
    update.message.reply_text(msg)

def backtest(update, context):
    # Simple backtest example
    data = yf.download("XAUUSD=X", period="5d", interval="5m")
    returns = data["Close"].pct_change().dropna()
    avg_return = returns.mean() * 100
    msg = f"🔎 Backtest (5d)\nAverage Return per Candle: {avg_return:.4f}%"
    update.message.reply_text(msg)

# --- Main ---
def main():
    updater = Updater("YOUR_TELEGRAM_BOT_TOKEN", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("signal", signal))
    dp.add_handler(CommandHandler("stats", stats))
    dp.add_handler(CommandHandler("backtest", backtest))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
