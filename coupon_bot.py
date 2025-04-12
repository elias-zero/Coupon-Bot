import gspread
import os
import json
import asyncio
import pytz
from datetime import datetime, timedelta
from telegram import Bot
from oauth2client.service_account import ServiceAccountCredentials

# إعدادات التوقيت الجزائري
ALGIERS_TZ = pytz.timezone('Africa/Algiers')

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

# تهيئة البوت
bot = Bot(token=TELEGRAM_TOKEN)

class CouponPublisher:
    def __init__(self):
        self.last_index = 0  # مؤشر آخر كوبون تم نشره
        self.max_per_day = 20  # الحد الأقصى اليومي
        
        # تحميل حالة النشر السابقة
        try:
            with open('state.json', 'r') as f:
                state = json.load(f)
                self.last_index = state.get('last_index', 0)
        except FileNotFoundError:
            pass

    async def fetch_coupons(self):
        """جلب جميع الكوبونات من الجدول"""
        try:
            spreadsheet = client.open("Coupons")
            sheet = spreadsheet.sheet1
            return sheet.get_all_records()
        except Exception as e:
            print(f"خطأ في قراءة البيانات: {str(e)}")
            return []

    async def send_coupon(self, coupon):
        """إرسال كوبون واحد"""
        try:
            message_lines = [
                f"**{coupon['title']}**",
                f"{coupon['description']}\n",
                f"الكوبون: `{coupon['code']}`"
            ]
            
            if coupon.get('countries'):
                message_lines.append(f"صالح لـ: {coupon['countries']")
                
            if coupon.get('note'):
                message_lines.append(f"ملاحظة: {coupon['note']")
            
            message_lines.append(f"رابط الشراء: [اضغط هنا]({coupon['link']})\n")
            message_lines.append("لمزيد من الكوبونات قم بزيارة موقعنا:\nhttps://www.discountcoupon.online")
            
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

    async def publish_daily_batch(self):
        """نشر الدفعة اليومية"""
        now = datetime.now(ALGIERS_TZ)
        print(f"بدء النشر اليومي - التوقيت الجزائري: {now.strftime('%Y-%m-%d %H:%M')}")
        
        coupons = await self.fetch_coupons()
        total_coupons = len(coupons)
        
        if total_coupons == 0:
            print("لا توجد كوبونات متاحة للنشر")
            return
        
        # حساب نطاق النشر
        start = self.last_index % total_coupons
        end = start + self.max_per_day
        
        # اختيار الكوبونات المطلوبة
        selected_coupons = coupons[start:end]
        
        # إذا تجاوزنا نهاية القائمة نكمل من البداية
        if end > total_coupons:
            selected_coupons += coupons[0:end - total_coupons]
        
        # النشر مع التأخير
        for idx, coupon in enumerate(selected_coupons, 1):
            await self.send_coupon(coupon)
            if idx < len(selected_coupons):
                await asyncio.sleep(3600)  # تأخير ساعة واحدة
                
        # تحديث المؤشر
        self.last_index = (self.last_index + len(selected_coupons)) % total_coupons
        
        # حفظ الحالة
        with open('state.json', 'w') as f:
            json.dump({'last_index': self.last_index}, f)
            
        print(f"تم نشر {len(selected_coupons)} كوبون اليوم")

async def main():
    publisher = CouponPublisher()
    await publisher.publish_daily_batch()

if __name__ == "__main__":
    asyncio.run(main())
