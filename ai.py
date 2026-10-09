import requests
import json

API_KEY = "XS-WIcdhIrSDuyRdzsBnV7NRFc-MSzOL6aHQnhd0aiU-2WpUKm33C3IFWaQZEX7j"
headers = {"X-API-KEY": API_KEY}
endpoint_url = "https://api.ferdowsi.cloud/api/v1/ai/vision/" 

with open("1.png", "rb") as image_file:
    # تغییر کلید از file_ref به استاندارد OpenAI یعنی file
    files = {
        "file": image_file 
    }
    data = {
        "model": "gemma4",
        "content": "این تصویر را به دقت تحلیل کن."
    }

    response = requests.post(endpoint_url, headers=headers, files=files, data=data)
    print(json.dumps(response.json(), indent=4, ensure_ascii=False))