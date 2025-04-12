import gspread
import os
import json
import time
from telegram import Bot, InputMediaPhoto
from telegram.error import TelegramError
from oauth2client.service_account import ServiceAccountCredentials

# تهيئة بيانات الاعتماد من متغيرات البيئة
GCP_CREDS = json.loads(os.getenv('GCP_CREDS'))
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# إعداد اتصال Google Sheets
credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    GCP_CREDS,
    ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
)
client = gspread.authorize(credentials)

# تهيئة بوت التليجرام
bot = Bot(token=TELEGRAM_TOKEN)

def fetch_coupons():
    """جلب بيانات الكوبونات من الجدول"""
    try:
        spreadsheet = client.open("coupons")
        sheet = spreadsheet.sheet1
        return sheet.get_all_records()
    except Exception as e:
        print(f"خطأ في قراءة البيانات: {e}")
        return []

def send_coupon(coupon):
    """إرسال كوبون واحد إلى القناة"""
    try:
        message = (
            f"🎁 **{coupon['title']}** 🎁\n\n"
            f"{coupon['description']}\n\n"
            f"🔐 الكود: `{coupon['code']}`\n"
            f"🌍 الدول: {coupon['countries']}\n"
            f"📌 ملاحظة: {coupon.get('note', '')}\n"
            f"🛒 [رابط الشراء]({coupon['link']})"
        )
        
        if coupon.get('image'):
            bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=coupon['image'],
                caption=message,
                parse_mode='Markdown'
            )
        else:
            bot.send_message(
                chat_id=CHANNEL_ID,
                text=message,
                parse_mode='Markdown'
            )
        print(f"تم إرسال الكوبون: {coupon['title']}")
    except TelegramError as e:
        print(f"خطأ في الإرسال: {e}")

def publish_all_coupons():
    """نشر جميع الكوبونات دفعة واحدة"""
    coupons = fetch_coupons()
    for idx, coupon in enumerate(coupons, 1):
        send_coupon(coupon)
        if idx < len(coupons):  # تأخير 10 ثواني بين الإرسالات ما عدا الأخير
            time.sleep(10)
    print(f"تم نشر جميع الكوبونات ({len(coupons)} منشور)")

if __name__ == "__main__":
    publish_all_coupons()  # التشغيل الفوري بدون جدولة
