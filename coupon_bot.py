import gspread
import os
import json
import time
import asyncio
from telegram import Bot, InputMediaPhoto
from telegram.error import TelegramError
from oauth2client.service_account import ServiceAccountCredentials

# تهيئة بيانات الاعتماد
GCP_CREDS = json.loads(os.getenv('GCP_CREDS'))
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# إعداد اتصال Google Sheets
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.metadata.readonly"
]

credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    GCP_CREDS,
    scope
)
client = gspread.authorize(credentials)

# تهيئة البوت بشكل صحيح
bot = Bot(token=TELEGRAM_TOKEN)

async def fetch_coupons():
    """جلب البيانات من الجدول"""
    try:
        spreadsheet = client.open("Coupons")
        sheet = spreadsheet.sheet1
        
        # التحقق من العناوين
        headers = sheet.row_values(1)
        required = ['title','description','code','link','image','countries','note']
        if headers != required:
            raise ValueError(f"خطأ في العناوين!\nالمطلوب: {required}\nالموجود: {headers}")
            
        return sheet.get_all_records()
    except Exception as e:
        print(f"خطأ في قراءة البيانات: {str(e)}")
        raise

async def send_coupon(coupon):
    """إرسال كوبون واحد"""
    try:
        # بناء الرسالة الجديدة
        message_lines = [
            f"**{coupon['title']}**",
            f"{coupon['description']}\n"
        ]
        
        # إضافة العناصر الأساسية
        message_lines.append(f"الكوبون : `{coupon['code']}`")
        
        if coupon.get('countries'):
            message_lines.append(f"صالح لـ : {coupon['countries']}")
            
        if coupon.get('note'):
            message_lines.append(f"ملاحظة : {coupon['note']}")
        
        # رابط الشراء
        message_lines.append(f"رابط الشراء : [اضغط هنا]({coupon['link']})\n")
        
        # الرابط الثابت
        message_lines.append("لمزيد من الكوبونات قم بزيارة موقعنا :\nhttps://www.discountcoupon.online")
        
        # دمج كل السطور
        full_message = "\n".join(message_lines)
        
        if coupon.get('image'):
            await bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=coupon['image'],
                caption=full_message,
                parse_mode='Markdown'
            )
        else:
            await bot.send_message(
                chat_id=CHANNEL_ID,
                text=full_message,
                parse_mode='Markdown'
            )
            
        print(f"تم الإرسال: {coupon['title']}")
        
    except Exception as e:
        print(f"فشل إرسال {coupon['title']}: {str(e)}")

async def publish_all():
    """النشر الرئيسي"""
    try:
        coupons = await fetch_coupons()
        for idx, coupon in enumerate(coupons, 1):
            await send_coupon(coupon)
            if idx < len(coupons):
                await asyncio.sleep(10)  # تأخير بين الإرسالات
        print(f"تم نشر {len(coupons)} كوبون بنجاح")
    except Exception as e:
        print(f"فشل النشر: {str(e)}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(publish_all())
