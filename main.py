import requests

# 1. رابط الـ API الخاص بالخدمة أو اللعبة
api_url = "https://api.example.com/get_user_data"

# 2. إرسال الطلب (إذا كان الـ API يحتاج مفتاح حماية أو توكن)
headers = {
    "Authorization": "Bearer YOUR_API_KEY"
}

try:
    response = requests.get(api_url, headers=headers)
    
    # 3. التحقق أن الطلب نجح (رقم 200 يعني نجاح الاتصال)
    if response.status_code == 200:
        data = response.json() # تحويل الرد إلى بيانات تفهمها بايثون (Dictionary)
        
        # استخراج البيانات واستخدامها
        diamonds = data.get("diamonds")
        print(f"رصيد الماس هو: {diamonds}")
    else:
        print("فشل الاتصال بالـ API")

except Exception as e:
    print("حدث خطأ:", e)
