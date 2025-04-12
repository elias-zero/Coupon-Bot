import gspread
import os
import json
import time
from telegram import Bot, InputMediaPhoto
from telegram.error import TelegramError
from oauth2client.service_account import ServiceAccountCredentials

GCP_CREDS = json.loads(os.getenv('GCP_CREDS'))
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.metadata.readonly"
]

credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    GCP_CREDS,
    scope
)
client = gspread.authorize(credentials)

try:
    test_sheet = client.open("Coupons")
    print(f"تم الاتصال بنجاح! ID: {test_sheet.id}")
    print(f"الأوراق المتاحة: {[ws.title for ws in test_sheet.worksheets()]}")
except Exception as e:
    print(f"فشل الاتصال: {str(e)}")
    raise

bot = Bot(token=TELEGRAM_TOKEN)

def fetch_coupons():
    try:
        spreadsheet = client.open("Coupons")
        sheet = spreadsheet.sheet1
        
        headers = sheet.row_values(1)
        required = ['title','description','code','link','image','countries','note']
        if headers != required:
            raise ValueError(f"العناوين خاطئة\nالمطلوب: {required}\nالموجود: {headers}")
            
        data = sheet.get_all_records()
        print(f"تم جلب {len(data)} كوبون")
        return data
    except Exception as e:
        print(f"خطأ: {str(e)}")
        raise

def send_coupon(coupon):
    try:
        msg = (
            f"🎁 **{coupon['title']}**\n\n"
            f"{coupon['description']}\n"
            f"🔐 الكود: `{coupon['code']}`\n"
            f"🌍 الدول: {coupon['countries']}\n"
            f"📌 ملاحظة: {coupon.get('note','')}\n"
            f"🛒 [رابط الشراء]({coupon['link']})"
        )
        
        if coupon.get('image'):
            bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=coupon['image'],
                caption=msg,
                parse_mode='Markdown'
            )
        else:
            bot.send_message(
                chat_id=CHANNEL_ID,
                text=msg,
                parse_mode='Markdown'
            )
        print(f"تم إرسال: {coupon['title']}")
    except Exception as e:
        print(f"فشل إرسال {coupon['title']}: {str(e)}")

def publish_all():
    coupons = fetch_coupons()
    for idx, c in enumerate(coupons, 1):
        send_coupon(c)
        if idx < len(coupons):
            time.sleep(10)
    print(f"تم النشر: {len(coupons)} كوبون")

if __name__ == "__main__":
    publish_all()
