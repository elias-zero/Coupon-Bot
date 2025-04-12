import gspread
import os
import json
import asyncio
from datetime import datetime
from telegram import Bot
from oauth2client.service_account import ServiceAccountCredentials

# إعدادات الثوابت
MAX_DAILY = 20
DELAY_HOURS = 1
START_DATE = datetime(2024, 1, 1)  # تاريخ بدء التشغيل

# تهيئة البيانات
GCP_CREDS = json.loads(os.getenv('GCP_CREDS'))
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')

# إعداد اتصال Google Sheets
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file"  # ← التعديل هنا
]

credentials = ServiceAccountCredentials.from_json_keyfile_dict(GCP_CREDS, scope)
client = gspread.authorize(credentials)
bot = Bot(token=TELEGRAM_TOKEN)

def get_batch_number():
    """حساب رقم الدفعة بناءً على الأيام منذ تاريخ البدء"""
    delta = datetime.utcnow() - START_DATE
    return delta.days

async def publish_daily():
    coupons = await get_coupons()
    total = len(coupons)
    
    if not coupons:
        print("لا يوجد كوبونات للنشر اليوم")
        return

    batch = get_batch_number()
    start = (batch * MAX_DAILY) % total
    end = start + MAX_DAILY
    
    # تحديد الكوبونات المطلوبة
    selected = coupons[start:end] if end <= total else coupons[start:]
    
    print(f"الدفعة: {batch+1} | النطاق: {start+1}-{start+len(selected)}")
    
    for idx, coupon in enumerate(selected, 1):
        await send_coupon(coupon)
        if idx < len(selected):
            await asyncio.sleep(DELAY_HOURS * 3600)

async def get_coupons():
    """جلب الكوبونات من الجدول"""
    try:
        sheet = client.open("Coupons").sheet1
        return sheet.get_all_records()
    except Exception as e:
        print(f"خطأ في قراءة البيانات: {str(e)}")
        return []

async def send_coupon(coupon):
    """إرسال كوبون واحد"""
    try:
        message = (
            f"**{coupon['title']}**\n"
            f"{coupon['description']}\n\n"
            f"الكوبون: `{coupon['code']}`\n"
            f"صالح لـ: {coupon['countries']}\n"
            f"{'ملاحظة: ' + coupon['note'] if coupon.get('note') else ''}\n"
            f"رابط الشراء: [اضغط هنا]({coupon['link']})\n\n"
            "لمزيد من الكوبونات: https://www.discountcoupon.online"
        )
        
        if coupon.get('image'):
            await bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=coupon['image'],
                caption=message,
                parse_mode='Markdown'
            )
        else:
            await bot.send_message(
                chat_id=CHANNEL_ID,
                text=message,
                parse_mode='Markdown'
            )
        print(f"تم بنجاح: {coupon['title']}")
    except Exception as e:
        print(f"فشل إرسال {coupon['title']}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(publish_daily())
