import requests
import json

API_KEY = "XS-WIcdhIrSDuyRdzsBnV7NRFc-MSzOL6aHQnhd0aiU-2WpUKm33C3IFWaQZEX7j"
FILE_PATH = "1.png"  # فایل خود را اینجا مسیردهی کنید
MODEL_NAME = "gemma4"       # یا qwen3.6

# =======================================================
# مرحله اول: ارسال فایل به OCR و دریافت شناسه مکالمه (UUID)
# =======================================================
ocr_url = "https://api.ferdowsi.cloud/api/v1/ai/ocr/"
headers_ocr = {
    "X-API-KEY": API_KEY
    # نیازی به Content-Type نیست، requests خودش multipart تنظیم می‌کند
}

try:
    with open(FILE_PATH, "rb") as file:
        files = {"file_ref": file}
        print("۱. در حال ارسال فایل به سرور...")
        
        response_ocr = requests.post(ocr_url, headers=headers_ocr, files=files)
        response_ocr.raise_for_status()
        
        result_ocr = response_ocr.json()
        
        # استخراج UUID از پاسخ سرور (طبق داکیومنت کلید conversation_uuid برمی‌گردد)
        conversation_uuid = result_ocr.get("conversation_uuid")
        
        if not conversation_uuid:
            print("خطا: UUID در پاسخ یافت نشد! خروجی خام سرور:")
            print(result_ocr)
            exit()
            
        print(f"✅ فایل با موفقیت پردازش شد. شناسه مکالمه: {conversation_uuid}")

except FileNotFoundError:
    print(f"فایل در مسیر {FILE_PATH} پیدا نشد.")
    exit()
except requests.exceptions.RequestException as e:
    print(f"خطا در مرحله آپلود: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(e.response.text)
    exit()

# =======================================================
# مرحله دوم: ادامه مکالمه با همان UUID و پرسیدن سوال
# =======================================================
# قرار دادن شناسه مکالمه در انتهای آدرس
llm_url = f"https://api.ferdowsi.cloud/api/v1/ai/llm/{conversation_uuid}"

headers_llm = {
    "X-API-KEY": API_KEY,
    "Content-Type": "application/json"
}

payload_llm = {
    "content": "با توجه به فایلی که بررسی کردی، لطفاً مهم‌ترین نکات آن را برای من خلاصه کن.",
    "model": MODEL_NAME
}

print("\n۲. در حال پرسیدن سوال از هوش مصنوعی در ادامه همان مکالمه...")

try:
    response_llm = requests.post(llm_url, headers=headers_llm, data=json.dumps(payload_llm))
    response_llm.raise_for_status()
    
    result_llm = response_llm.json()
    
    print("\n--- پاسخ هوش مصنوعی ---")
    print(result_llm["choices"][0]["message"]["content"])

except requests.exceptions.RequestException as e:
    print(f"خطا در مرحله پرسش: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(e.response.text)


'''

# OCR - Document To Text
curl -X POST "https://api.ferdowsi.cloud/api/v1/ai/ocr/" \
  -H "X-API-KEY: XS-WIcdhIrSDuyRdzsBnV7NRFc-MSzOL6aHQnhd0aiU-2WpUKm33C3IFWaQZEX7j" \
  -F "file_ref=@document.pdf"

'''