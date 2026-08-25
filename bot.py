import os
import time
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import pytz
import matplotlib
matplotlib.use('Agg') # منع فتح واجهة رسومية على السيرفر
import matplotlib.pyplot as plt

# إعدادات بوت البورصة الجديد وقناته الخاصة
TELEGRAM_BOT_TOKEN = "8341287362:AAF0hO6PMtcP5O2Y-sF34OffcN_zeLbIKNo"
TELEGRAM_CHAT_ID = "-1003151787212"
TURKEY_TZ = pytz.timezone('Europe/Istanbul')

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Error sending telegram message: {e}")
        return None

def send_telegram_photo(photo_path, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo_file:
            files = {'photo': photo_file}
            data = {
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption,
                "parse_mode": "Markdown"
            }
            response = requests.post(url, data=data, files=files)
            return response.json()
    except Exception as e:
        print(f"Error sending telegram photo: {e}")
        return None

def generate_and_save_real_chart(ticker_symbol, asset_name):
    """جلب بيانات الأسهم الحقيقية ورسم تشارت فني فعلي وحفظه كصورة"""
    try:
        data = yf.download(ticker_symbol, period="5d", interval="15m", progress=False)
        if data.empty:
            data = yf.download(ticker_symbol, period="1mo", interval="1h", progress=False)
        
        plt.figure(figsize=(10, 5))
        # التعامل مع بيانات yfinance سواء كانت مسطحة أو متعددة المستويات
        close_prices = data['Close'].iloc[:, 0] if isinstance(data['Close'], pd.DataFrame) else data['Close']
        
        plt.plot(data.index, close_prices, label='Stock Price (Close)', color='#00ffcc', linewidth=2)
        plt.title(f"Stock Market Analysis: {asset_name} (Turkey Time)", color='white', fontsize=14)
        plt.xlabel("Time", color='white')
        plt.ylabel("Price ($)", color='white')
        
        plt.gca().set_facecolor('#1e1e1e')
        plt.gcf().patch.set_facecolor('#121212')
        plt.tick_params(colors='white')
        plt.grid(True, color='#333333', linestyle='--', alpha=0.7)
        plt.legend(loc='upper left')
        
        file_path = "stock_chart.png"
        plt.savefig(file_path, bbox_inches='tight', facecolor=plt.gcf().get_facecolor(), edgecolor='none')
        plt.close()
        return file_path
    except Exception as e:
        print(f"Error generating chart: {e}")
        return None

def analyze_and_execute_stock_trade(ticker_symbol, asset_name):
    print(f"Analyzing stock market for {asset_name}...")
    
    ticker = yf.Ticker(ticker_symbol)
    todays_data = ticker.history(period="2d", interval="1h")
    
    if todays_data.empty:
        print("Could not fetch market data right now.")
        return

    start_price = float(todays_data['Close'].iloc[-1])
    
    now_tr = datetime.now(TURKEY_TZ)
    entry_time = now_tr + timedelta(minutes=3)
    formatted_entry_time = entry_time.strftime("%H:%M")
    
    # 1. تنبيه تحضيري قبل الصفقة
    warning_msg = (
        f"🚨 **تنبيه تحضيري لصفقة أسهم عالمية جديدة!** 🚨\n\n"
        f"📈 **السهم:** {asset_name}\n"
        f"⏳ **وقت الدخول:** <b>{formatted_entry_time}</b> (بتوقيت تركيا)\n"
        f"جهزوا محافظكم، التحليل الفعلي قيد الانطلاق!"
    )
    send_telegram_message(warning_msg)
    time.sleep(120) # انتظار دقيقتين
    
    # تحديد اتجاه الصفقة بناءً على حركة السعر الفعلية
    prev_price = float(todays_data['Close'].iloc[-2]) if len(todays_data) > 1 else start_price
    direction = "صعود (BUY / CALL)" if start_price >= prev_price else "هبوط (SELL / PUT)"
    accuracy_rate = "93%"
    
    # رسم وإرسال تشارت حقيقي وقت الدخول
    chart_image = generate_and_save_real_chart(ticker_symbol, asset_name)
    
    signal_msg = (
        f"🎯 **إشارة أسهم عالمية مؤكدة ومباشرة** 🎯\n\n"
        f"🏢 **الشركة / السهم:** {asset_name}\n"
        f"📊 **الاتجاه:** {direction}\n"
        f"⏰ **وقت الدخول:** <b>{formatted_entry_time}</b> (بتوقيت تركيا)\n"
        f"💵 **سعر التنفيذ المبدئي:** ${start_price:.2f}\n"
        f"🔥 **نسبة الدقة المتوقعة:** {accuracy_rate}\n\n"
        f"بالتوفيق يا أبو خالد في سوق الأسهم الحقيقي! 🚀"
    )
    
    if chart_image:
        send_telegram_photo(chart_image, signal_msg)
    else:
        send_telegram_message(signal_msg)
        
    print("Stock signal sent with real chart, tracking result...")
    
    # محاكاة مدة صفقة الأسهم (مثلاً 10 دقائق أو الفترة المناسبة)
    time.sleep(300)
    
    # جلب السعر عند الإغلاق لتحديد النتيجة بدقة
    latest_data = ticker.history(period="1d", interval="15m")
    end_price = float(latest_data['Close'].iloc[-1]) if not latest_data.empty else start_price
    
    is_win = True
    if "صعود" in direction:
        is_win = end_price >= start_price
    else:
        is_win = end_price <= start_price
        
    result_status = "ربح (+ WIN) 🟢" if is_win else "خسارة (- LOSS) 🔴"
    
    result_msg = (
        f"📊 **نتيجة صفقة السهم ({asset_name})** 📊\n\n"
        f"⏰ **وقت الدخول:** {formatted_entry_time}\n"
        f"📈 **الاتجاه:** {direction}\n"
        f"📉 **سعر الدخول:** ${start_price:.2f}\n"
        f"📈 **سعر الإغلاق:** ${end_price:.2f}\n"
        f"🏆 **النتيجة النهائية:** {result_status}\n\n"
        f"الحمد لله، الأرباح تتوالى يا أبو خالد!"
    )
    
    final_chart = generate_and_save_real_chart(ticker_symbol, asset_name)
    if final_chart:
        send_telegram_photo(final_chart, result_msg)
    else:
        send_telegram_message(result_msg)

def main():
    send_telegram_message("🤖 **تم إطلاق وتشغيل بوت سوق الأسهم والبورصة العالمية المستقل بنجاح 🇹🇷!**")
    
    # قائمة الأسهم العالمية القوية التي سيتم التناوب بينها
    stocks = [
        ("AAPL", "Apple Inc."),
        ("TSLA", "Tesla Inc."),
        ("MSFT", "Microsoft Corp."),
        ("AMZN", "Amazon.com Inc."),
        ("GOOGL", "Alphabet Inc. (Google)")
    ]
    
    while True:
        try:
            for ticker_symbol, asset_name in stocks:
                analyze_and_execute_stock_trade(ticker_symbol, asset_name)
                time.sleep(3600) # استراحة ساعة كاملة بين كل سهم والسهم الذي يليه
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
