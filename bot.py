import time
import requests
import pandas as pd
import pandas_ta as ta
import yfinance as yf

# ----------------- إعدادات الوكيل الثاني (OTC) -----------------
TELEGRAM_BOT_TOKEN = "7983033116:AAGbLkQZZp0VgLeudB9xF2nEL2Ln00cFJQo"  # يمكنك استخدام نفس البوت أو بوت جديد
TELEGRAM_CHAT_ID = "-1002873715505"     # يمكنك وضع Chat ID خاص بقناة الـ OTC

# أزواج الـ OTC الشهيرة المتاحة في ياهو فاينانس كمؤشرات بديلة أو أزواج مشابهة
PAIRS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X"]
# ----------------------------------------------------------------

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"خطأ في الاتصال: {e}")

def fetch_5m_candles(pair):
    """جلب بيانات سريعة لفريم 5 دقائق يناسب صفقات الـ OTC القصيرة"""
    try:
        data = yf.download(pair, interval="5m", period="1d", progress=False)
        if data.empty:
            return None
        return data
    except Exception as e:
        return None

def scan_otc_market():
    print("جاري فحص سوق الـ OTC للبحث عن فرص...")
    for pair in PAIRS:
        df = fetch_5m_candles(pair)
        if df is None or len(df) < 30:
            continue
            
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df['EMA_5'] = ta.ema(df['Close'], length=5)
        df['EMA_10'] = ta.ema(df['Close'], length=10)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        if len(df) < 3:
            continue
            
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        try:
            c_close = float(current['Close'])
            c_rsi = float(current['RSI'])
            p_ema5 = float(previous['EMA_5'])
            p_ema10 = float(previous['EMA_10'])
            c_ema5 = float(current['EMA_5'])
            c_ema10 = float(current['EMA_10'])
        except Exception:
            continue

        clean_pair = pair.replace("=X", "") + " (OTC / 5m)"

        # شروط صعود OTC سريعة
        if (p_ema5 <= p_ema10 and c_ema5 > c_ema10) and (c_rsi < 40):
            msg = (
                f"🚨 *فرصة OTC سريعة (صعود - CALL)*\n"
                f"💱 *الزوج:* {clean_pair}\n"
                f"⏳ *مدة الصفقة:* 5 دقائق\n"
                f"📊 *السعر:* {c_close:.5f} | *RSI:* {c_rsi:.2f}\n"
                f"⚠️ *تداول بحذر وإدارة صارمة لرأس المال*"
            )
            send_telegram_alert(msg)

        # شروط هبوط OTC سريعة
        elif (p_ema5 >= p_ema10 and c_ema5 < c_ema10) and (c_rsi > 60):
            msg = (
                f"🚨 *فرصة OTC سريعة (هبوط - PUT)*\n"
                f"💱 *الزوج:* {clean_pair}\n"
                f"⏳ *مدة الصفقة:* 5 دقائق\n"
                f"📊 *السعر:* {c_close:.5f} | *RSI:* {c_rsi:.2f}\n"
                f"⚠️ *تداول بحذر وإدارة صارمة لرأس المال*"
            )
            send_telegram_alert(msg)

if __name__ == "__main__":
    print("تم تفعيل وكيل الـ OTC بنجاح...")
    while True:
        scan_otc_market()
        time.sleep(120) # يفحص كل دقيقتين للفرص السريعة
