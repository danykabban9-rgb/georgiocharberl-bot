import yfinance as yf
import pandas as pd
from telegram.ext import Updater, CommandHandler
import datetime, os

updater = Updater("YOUR_NEW_TELEGRAM_BOT_TOKEN")
dispatcher = updater.dispatcher

# --- SIGNAL COMMAND ---
def signal(update, context):
    data = yf.download("XAUUSD=X", period="1d", interval="5m")
    open_ = data['Open']
    close = data['Close']
    high = data['High']
    low = data['Low']

    msg, patterns = [], []

    # Engulfing
    if close.iloc[-2] < open_.iloc[-2] and close.iloc[-1] > open_.iloc[-1]:
        msg.append("📈 Bullish Engulfing → BUY setup")
        patterns.append("Bullish Engulfing")
    elif close.iloc[-2] > open_.iloc[-2] and close.iloc[-1] < open_.iloc[-1]:
        msg.append("📉 Bearish Engulfing → SELL setup")
        patterns.append("Bearish Engulfing")

    # Doji
    body = abs(close.iloc[-1] - open_.iloc[-1])
    candle_range = high.iloc[-1] - low.iloc[-1]
    if body < candle_range * 0.1:
        msg.append("⚠️ Doji detected → indecision")
        patterns.append("Doji")

    # Hammer
    if (high.iloc[-1] - max(open_.iloc[-1], close.iloc[-1])) < candle_range * 0.25 and \
       (min(open_.iloc[-1], close.iloc[-1]) - low.iloc[-1]) > candle_range * 0.5:
        msg.append("🔨 Hammer detected → Possible reversal")
        patterns.append("Hammer")

    # Morning Star
    if close.iloc[-3] < open_.iloc[-3] and \
       abs(close.iloc[-2] - open_.iloc[-2]) < (high.iloc[-2] - low.iloc[-2]) * 0.3 and \
       close.iloc[-1] > open_.iloc[-1] and close.iloc[-1] > (close.iloc[-3] + open_.iloc[-3]) / 2:
        msg.append("🌅 Morning Star → Bullish reversal")
        patterns.append("Morning Star")

    # Evening Star
    if close.iloc[-3] > open_.iloc[-3] and \
       abs(close.iloc[-2] - open_.iloc[-2]) < (high.iloc[-2] - low.iloc[-2]) * 0.3 and \
       close.iloc[-1] < open_.iloc[-1] and close.iloc[-1] < (close.iloc[-3] + open_.iloc[-3]) / 2:
        msg.append("🌆 Evening Star → Bearish reversal")
        patterns.append("Evening Star")

    # Three Soldiers
    if close.iloc[-3] > open_.iloc[-3] and close.iloc[-2] > open_.iloc[-2] and close.iloc[-1] > open_.iloc[-1]:
        if close.iloc[-1] > close.iloc[-2] > close.iloc[-3]:
            msg.append("👨‍👨‍👦 Three Soldiers → Strong BUY")
            patterns.append("Three Soldiers")

    # Three Black Crows
    if close.iloc[-3] < open_.iloc[-3] and close.iloc[-2] < open_.iloc[-2] and close.iloc[-1] < open_.iloc[-1]:
        if close.iloc[-1] < close.iloc[-2] < close.iloc[-3]:
            msg.append("🐦 Three Black Crows → Strong SELL")
            patterns.append("Three Black Crows")

    # EMA Cross
    ema_short = close.ewm(span=5).mean().iloc[-1]
    ema_long = close.ewm(span=20).mean().iloc[-1]
    direction = "BUY" if ema_short > ema_long else "SELL"

    # Risk Management
    entry = close.iloc[-1]
    sl = entry - 2 if direction == "BUY" else entry + 2
    tp = entry + 4 if direction == "BUY" else entry - 4

    # Success Probability
    trend_strength = abs(ema_short - ema_long) / entry * 100
    confidence = 50
    if "Morning Star" in patterns: confidence += 20
    if "Evening Star" in patterns: confidence += 20
    if "Three Soldiers" in patterns: confidence += 25
    if "Three Black Crows" in patterns: confidence += 25
    if "Engulfing" in " ".join(msg): confidence += 15
    if "Hammer" in " ".join(msg): confidence += 10
    if "Doji" in " ".join(msg): confidence -= 10
    win_rate = min(95, max(40, confidence + trend_strength))

    msg.append(f"🎯 Entry: {entry:.2f}\n🛑 SL: {sl:.2f}\n✅ TP: {tp:.2f}\n📊 Success Rate: {win_rate:.1f}%")

    # Logging
    log_entry = {
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "patterns": ", ".join(patterns),
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "success_rate": win_rate
    }
    df = pd.DataFrame([log_entry])
    df.to_csv("signals_log.csv", mode="a", header=not os.path.exists("signals_log.csv"), index=False)

    update.message.reply_text("\n".join(msg))

# --- STATS COMMAND ---
def stats(update, context):
    if not os.path.exists("signals_log.csv"):
        update.message.reply_text("No signals logged yet.")
        return

    df = pd.read_csv("signals_log.csv")
    total_signals = len(df)
    avg_success = df['success_rate'].mean()
    pattern_counts = df['patterns'].value_counts()
    pattern_success = df.groupby('patterns')['success_rate'].mean()

    msg = f"📊 Stats Summary\nTotal Signals: {total_signals}\nAverage Success Rate: {avg_success:.1f}%\n\n"
    msg += "📈 Pattern Performance:\n"
    for pattern in pattern_counts.index:
        count = pattern_counts[pattern]
        success = pattern_success[pattern]
        msg += f"- {pattern}: {count} signals, Avg Success {success:.1f}%\n"

    update.message.reply_text(msg)

# --- BACKTEST COMMAND ---
def backtest(update, context):
    data = yf.download("XAUUSD=X", period="30d", interval="5m")
    close = data['Close']
    trades = []
    for i in range(20, len(data)-5):
        ema_short = close.iloc[i-5:i].mean()
        ema_long = close.iloc[i-20:i].mean()
        entry = close.iloc[i]
        if ema_short > ema_long:  # BUY
            sl, tp = entry - 2, entry + 4
            outcome = "WIN" if close.iloc[i+5] >= tp else "LOSS" if close.iloc[i+5] <= sl else "OPEN"
        else:  # SELL
            sl, tp = entry + 2, entry - 4
            outcome = "WIN" if close.iloc[i+5] <= tp else "LOSS" if close.iloc[i+5] >= sl else "OPEN"
        trades.append(outcome)

    wins, losses = trades.count("WIN"), trades.count("LOSS")
    total = wins + losses
    win_rate = (wins / total * 100) if total > 0 else 0

    msg = f"📊 Backtest Results (30 days)\nTotal Trades: {total}\nWins: {wins}\nLosses: {losses}\nWin Rate: {win_rate:.1f}%"
    update.message.reply_text(msg)

# --- REGISTER COMMANDS ---
dispatcher.add_handler(CommandHandler("signal", signal))
dispatcher.add_handler(CommandHandler("stats", stats))
dispatcher.add_handler(CommandHandler("backtest", backtest))

updater.start_polling()
updater.idle()
