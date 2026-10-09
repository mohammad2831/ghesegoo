import requests
import json

def text_generate(prompt):
    # کلید API خود را اینجا قرار دهید
    api_key = "XS-WIcdhIrSDuyRdzsBnV7NRFc-MSzOL6aHQnhd0aiU-2WpUKm33C3IFWaQZEX7j"
    
    # آدرس اندپوینت چت متنی[cite: 1]
    url = "https://api.ferdowsi.cloud/api/v1/ai/llm/"
    
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    
    # ساختار درخواست طبق داکیومنت[cite: 1]
    payload = {
        "model": "gemma4",
        "content": prompt
    }
    
    try:
        # ارسال درخواست به سرور
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        
        # استخراج پاسخ خام JSON
        result = response.json()
        
        # استخراج فقط متنِ خالصِ پاسخ از داخل ساختار[cite: 2]
        clean_text = result["choices"][0]["message"]["content"]
        
        # چاپ کردن متن بدون هیچ چیز اضافه‌ای
        print(clean_text)
        
    except requests.exceptions.RequestException as e:
        print(f"خطا در ارتباط با سرور: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"جزئیات خطا: {e.response.text}")


my_prompt = "سلام، یک داستان خیلی کوتاه درباره یک برنامه‌نویس بنویس."
text_generate(my_prompt)