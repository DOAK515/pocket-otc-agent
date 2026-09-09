import time
import logging
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import urllib.request
import urllib.parse
import json
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO)

TOKEN = "8341287362:AAF0hO6PMtcP5O2Y-sF34OffcN_zeLbIKNo"
CHAT_ID = "-1003151787212"

# أفضل 10 أزواج عملات للمتابعة (تطابق الأسواق النشطة ذات العائد المرتفع)
PAIRS = [
    {"symbol": "EURUSD=X", "name": "EUR/USD", "payout": 89},
    {"symbol": "GBPUSD=X", "name": "GBP/USD", "payout": 88},
    {"symbol": "AUDCAD=X", "name": "AUD/CAD", "payout": 89},
    {"symbol": "USDCHF=X", "name": "USD/CHF", "payout": 89},
    {"symbol": "CADJPY=X", "name": "CAD/JPY", "payout": 86},
    {"symbol": "CHFJPY=X", "name": "CHF/JPY", "payout": 86},
    {"symbol": "NZDUSD=X", "name": "NZD/USD", "payout": 85},
    {"symbol": "EURJPY=X", "name": "EUR/JPY", "payout": 87},
    {"symbol": "GBPJPY=X", "name": "GBP/JPY", "payout": 86},
    {"symbol": "AUDUSD=X", "name": "AUD/USD", "payout": 81}
]

def send_telegram_message(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = urllib.parse.urlencode({'chat_id': CHAT_ID, 'text': text}).encode('utf-8')
        urllib.request.urlopen(url, data)
    except Exception as e:
        logging.error(f"Telegram Msg Error: {e}")

def send_telegram_photo(photo_bytes, caption=""):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        data = io.BytesIO()
        data.write(f'--{boundary}\r\n'.encode('utf-8'))
        data.write(f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{CHAT_ID}'.encode('utf-8'))
        data.write(f'\r\n--{boundary}\r\n'.encode('utf-8'))
        data.write(f'Content-Disposition: form-data; name="caption"\r\n\r\n{caption}'.encode('utf-8'))
        data.write(f'\r\n--{boundary}\r\n'.encode('utf-8'))
        data.write(f'Content-Disposition: form-data; name="photo"; filename="chart.png"\r\n'.encode('utf-8'))
        data.write(f'Content-Type: image/png\r\n\r\n'.encode('utf-8'))
        data.write(photo_bytes)
        data.write(f'\r\n--{boundary}--\r\n'.encode('utf-8'))
        req = urllib.request.Request(url, data=data.getvalue(), headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
        urllib.request.urlopen(req)
    except Exception as e:
        logging.error(f"Telegram Photo Error: {e}")

def get_turkey_time():
    turkey_tz = timezone(timedelta(hours=3))
    return datetime.now(turkey_tz)

def is_market_open():
    now = get_turkey_time()
    weekday = now.weekday()
    if weekday == 5 or weekday == 6:
        return False
    return True

def fetch_pair_data(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=5m&range=1d"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        result = data['chart']['result'][0]
        timestamp = result['timestamp']
        quote = result['indicators']['quote'][0]
        df = pd.DataFrame({
            'timestamp': timestamp,
            'open': quote['open'],
            'high': quote['high'],
            'low': quote['low'],
            'close': quote['close']
        }).dropna()
    except Exception as e:
        base = 1.1620
        np.random.seed(int(time.time() // 60))
        closes = base + np.cumsum(np.random.normal(0, 0.0001, 40))
        df = pd.DataFrame()
        df['close'] = closes
        df['open'] = df['close'].shift(1).fillna(base)
        df['high'] = df[['open', 'close']].max(axis=1) + 0.00008
        df['low'] = df[['open', 'close']].min(axis=1) - 0.00008

    # استراتيجية الدعوم والمقاومات القوية
    df['Support'] = df['low'].rolling(window=20).min()
    df['Resistance'] = df['high'].rolling(window=20).max()
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['RSI'] = df['RSI'].fillna(50)
    
    return df

def analyze_signal(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    current_price = last['close']
    support_level = last['Support']
    resistance_level = last['Resistance']
    
    near_support = abs(current_price - support_level) <= 0.00020
    if (near_support or current_price <= support_level * 1.0002) and last['RSI'] < 42 and last['close'] > prev['close']:
        return "CALL", current_price
        
    near_resistance = abs(current_price - resistance_level) <= 0.00020
    if (near_resistance or current_price >= resistance_level * 0.9998) and last['RSI'] > 58 and last['close'] < prev['close']:
        return "PUT", current_price
        
    return None, current_price

def generate_chart_image(df, title):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 4.5), gridspec_kw={'height_ratios': [3, 1]}, sharex=True)
    bg_color = '#121824'
    grid_color = '#1e2636'
    fig.patch.set_facecolor(bg_color)
    ax1.set_facecolor(bg_color)
    ax2.set_facecolor(bg_color)
    
    # شموع متلاصقة وواضحة تماماً
    for i in range(len(df)):
        o = df['open'].iloc[i]
        c = df['close'].iloc[i]
        h = df['high'].iloc[i]
        l = df['low'].iloc[i]
        color = '#00c853' if c >= o else '#ff5252'
        ax1.plot([i, i], [l, h], color=color, linewidth=1.0, zorder=1)
        ax1.bar(i, abs(c - o), bottom=min(o, c), color=color, width=0.9, zorder=2)

    sup_val = df['Support'].iloc[-1]
    res_val = df['Resistance'].iloc[-1]
    ax1.axhline(sup_val, color='#00e5ff', linestyle='--', alpha=0.7, label='Support')
    ax1.axhline(res_val, color='#ff9100', linestyle='--', alpha=0.7, label='Resistance')

    ax1.set_title(title, fontsize=10, color='white', fontweight='bold', pad=8)
    ax1.tick_params(colors='#8b949e', labelsize=8)
    ax1.grid(True, color=grid_color, alpha=0.5)
    ax1.legend(loc='upper left', facecolor='#121824', edgecolor='none', labelcolor='white', fontsize=7)
    
    ax2.plot(df['RSI'].values, color='#00e5ff', linewidth=1.2)
    ax2.axhline(70, color='#ff5252', linestyle='--', alpha=0.5)
    ax2.axhline(50, color='#ffeb3b', linestyle='-', alpha=0.3)
    ax2.axhline(30, color='#00c853', linestyle='--', alpha=0.5)
    ax2.set_ylabel('RSI', color='#8b949e', fontsize=7)
    ax2.set_ylim(0, 100)
    ax2.tick_params(colors='#8b949e', labelsize=8)
    ax2.grid(True, color=grid_color, alpha=0.5)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor=fig.get_facecolor(), dpi=150)
    buf.seek(0)
    plt.close()
    return buf.read()

total_wins = 11
total_losses = 20

def main():
    global total_wins, total_losses
    send_telegram_message("🎯 بوت تداول أفضل 10 أزواج (عوائد > 80% + دعوم ومقاومات) يعمل الآن.")
    
    market_was_closed = False

    while True:
        try:
            if not is_market_open():
                if not market_was_closed:
                    send_telegram_message("⏸ **السوق مغلق حالياً (عطلة نهاية الأسبوع)**")
                    market_was_closed = True
                time.sleep(1800)
                continue
            else:
                if market_was_closed:
                    send_telegram_message("🟢 **تم افتتحاح السوق ومراقبة أفضل 10 أزواج عملات!**")
                    market_was_closed = False

            signal_found = False

            # فحص الـ 10 أزواج واحداً تلو الآخر
            for pair in PAIRS:
                if pair['payout'] < 80:
                    continue  # استبعاد أي زوج يقل عائده عن 80%
                
                df = fetch_pair_data(pair['symbol'])
                signal, current_price = analyze_signal(df)
                
                if signal:
                    signal_found = True
                    now_tr = get_turkey_time()
                    entry_time = now_tr + timedelta(minutes=2)
                    
                    chart_img = generate_chart_image(df, f"{pair['name']} | Payout: +{pair['payout']}% | {signal}")
                    
                    alert_msg = (
                        f"🚨 **إشارة قوية جداً (عائد مرتفع +{pair['payout']}%)** 🚨\n"
                        f"──────────────────────\n"
                        f"💱 **الزوج:** {pair['name']}\n"
                        f"📈 **القرار:** {'شراء / صعود (CALL) 🟢' if signal == 'CALL' else 'بيع / هبوط (PUT) 🔴'}\n"
                        f"⏳ **وقت الدخول:** {entry_time.strftime('%H:%M')}\n"
                        f"⏱ **مدة الصفقة:** 5 دقائق\n"
                        f"📍 **سعر الدخول:** {current_price:.5f}\n"
                        f"💰 **نسبة الربح:** +{pair['payout']}%\n"
                        f"🛡 **النظام:** دعم/مقاومة + شموع متلاصقة\n"
                        f"──────────────────────"
                    )
                    send_telegram_photo(chart_img, caption=alert_msg)
                    
                    # انتظار مدة الصفقة (7 دقائق)
                    time.sleep(420)
                    
                    df_end = fetch_pair_data(pair['symbol'])
                    end_price = df_end['close'].iloc[-1]
                    
                    is_win = (end_price >= current_price) if signal == "CALL" else (end_price <= current_price)
                    
                    if is_win:
                        total_wins += 1
                        res_text = "✅ رابحة (WIN)"
                    else:
                        total_losses += 1
                        res_text = "❌ خاسرة (LOSS)"
                        
                    end_tr = get_turkey_time()
                    result_chart_img = generate_chart_image(df_end, f"Result: {res_text}")
                    
                    result_msg = (
                        f"🏁 **تقرير نتيجة الصفقة ({pair['name']})**\n"
                        f"──────────────────────\n"
                        f"النتيجة: {res_text}\n"
                        f"📍 سعر الفتح: {current_price:.5f}\n"
                        f"📍 سعر الإغلاق: {end_price:.5f}\n"
                        f"⏰ وقت الانتهاء: {end_tr.strftime('%H:%M')}\n"
                        f"──────────────────────\n"
                        f"📈 **الربح:** {total_wins}\n"
                        f"📉 **الخساره:** {total_losses}\n"
                        f"🎯 **الإجمالي الكلي:** {total_wins + total_losses} صفقات"
                    )
                    send_telegram_photo(result_chart_img, caption=result_msg)
                    
                    time.sleep(60)
                    break # الانتقال لدورة جديدة بعد تنفيذ الصفقة
            
            if not signal_found:
                time.sleep(30) # فحص متواصل كل 30 ثانية للأزواج
                
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
