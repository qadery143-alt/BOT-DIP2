import os
import requests
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# هيكل بيانات موسع لـ 36 حساباً (يمكنك إضافة أو تعديل الحسابات هنا بسهولة)
# تم إعداد أول 4 حسابات كمثال رئيسي، والبقية يتم توليدها أو إضافتها بنفس الطريقة
game_accounts = [
    {"id": i, "name": f"Account_{i}" if i > 4 else ["REX.", "Rayzin.", "NYXOR", "STATHAM"][i-1], 
     "level": 90 - i, 
     "status": "نشط" if i % 2 == 0 else "متوقف", 
     "diamonds": f"{15000 - (i*100):,}", 
     "cash": f"{400000000 - (i*1000000):,}", 
     "profit": f"+{110000000 - (i*500000):,}", 
     "location": "Ürdün", 
     "nationality": "فَالِيرِيَا | VALYRIA", 
     "avatar": "👑" if i == 1 else "🐺" if i == 2 else "👤", 
     "color": "#22c55e" if i % 2 == 0 else "#a0a6b8"}
    for i in range(1, 37) # إنشاء قائمة بـ 36 حساباً تلقائياً لتوفير الوقت
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DiplomaciaBOT - لوحة التحكم</title>
    <style>
        @keyframes fadeIn { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
        body { background-color: #0f111a; color: #ffffff; font-family: sans-serif; margin: 0; padding: 15px; padding-bottom: 90px; animation: fadeIn 0.6s ease-out; }
        .header-card { background: #181b28; border-radius: 16px; padding: 15px; margin-bottom: 20px; border: 1px solid #2a2e43; }
        .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; background: #121520; padding: 12px; border-radius: 12px; text-align: center; margin-bottom: 20px; }
        .accounts-scroll { display: flex; gap: 12px; overflow-x: auto; padding-bottom: 10px; margin-bottom: 20px; scrollbar-width: none; }
        .accounts-scroll::-webkit-scrollbar { display: none; }
        .account-bubble { text-align: center; flex-shrink: 0; cursor: pointer; }
        .avatar-circle { width: 60px; height: 60px; border-radius: 50%; background: #2a2e43; display: flex; align-items: center; justify-content: center; overflow: hidden; margin-bottom: 6px; }
        .active-account-card { background: #181b28; border-radius: 16px; padding: 15px; border: 1px solid #2a2e43; margin-bottom: 15px; }
        .btn-run { background: #a855f7; color: white; border: none; padding: 8px 12px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 12px; margin-top: 10px; }
        .nav-bar { position: fixed; bottom: 0; left: 0; right: 0; background: rgba(18, 21, 32, 0.95); display: flex; justify-content: space-around; padding: 12px; border-top: 1px solid #2a2e43; }
        .nav-item { text-align: center; color: #a0a6b8; font-size: 12px; cursor: pointer; }
        .nav-item.active { color: #60a5fa; }
    </style>
</head>
<body>

    <div class="header-card">
        <div style="font-size: 20px; font-weight: bold;">DiplomaciaBOT</div>
        <div style="font-size: 13px; color: #a0a6b8;">إدارة 36 حساباً والمصانع النشطة</div>
    </div>

    <div class="stats-grid">
        <div><div>💎 الحسابات</div><div style="color: #60a5fa; font-weight: bold;">36 حساب</div></div>
        <div><div>💵 الحالة العامة</div><div style="color: #22c55e; font-weight: bold;">متصل تلقائي</div></div>
        <div><div>📈 الأتمتة</div><div style="color: #38bdf8; font-weight: bold;">مفعلة</div></div>
    </div>

    <div style="font-size: 14px; font-weight: bold; margin-bottom: 10px; color: #a0a6b8;">جميع الحسابات (36)</div>
    
    <div class="accounts-scroll">
        {% for acc in accounts %}
        <div class="account-bubble">
            <div class="avatar-circle" style="border: 2px solid {{ acc.color }};">
                <span style="font-size: 18px;">{{ acc.avatar }}</span>
            </div>
            <div style="font-size: 11px; color: #d1d5db; width: 60px; overflow: hidden; text-overflow: ellipsis;">{{ acc.name }}</div>
        </div>
        {% endfor %}
    </div>

    {% for acc in accounts %}
    <div class="active-account-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <span style="font-weight: bold;">{{ acc.name }} — Lv.{{ acc.level }}</span>
            <span style="background: {% if acc.status == 'نشط' %}#14532d{% else %}#7f1d1d{% endif %}; color: {% if acc.status == 'نشط' %}#22c55e{% else %}#f87171{% endif %}; padding: 2px 8px; border-radius: 6px; font-size: 12px;">{{ acc.status }}</span>
        </div>
        <div style="font-size: 13px; color: #a0a6b8; margin-bottom: 5px;">الماس: {{ acc.diamonds }} | النقد: {{ acc.cash }}</div>
        <button class="btn-run" onclick="runAutomation('{{ acc.name }}')">تشغيل أتمتة المصنع</button>
    </div>
    {% endfor %}

    <div class="nav-bar">
        <div class="nav-item active">🏠 الرئيسية</div>
        <div class="nav-item">💵 إيداع</div>
        <div class="nav-item">⚙️ الإعدادات</div>
    </div>

    <script>
        function runAutomation(accountName) {
            fetch('/automate-task', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({account: accountName})
            })
            .then(res => res.json())
            .then(data => alert(data.message));
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, accounts=game_accounts)

@app.route("/automate-task", methods=["POST"])
def automate_task():
    data = request.json
    account_name = data.get("account", "الحساب")
    
    # هنا يتم تنفيذ أوامر الأتمتة وإرسال طلبات الـ API الخاصة باللعبة للحساب المختار
    # مثال إرسال إشعار تيليجرام تفاعلي أو إعادة تشغيل المصنع:
    
    return jsonify({
        "status": "success",
        "message": f"تم تفعيل الأتمتة وبدء مهام المصنع بنجاح للحساب: {account_name} ⚙️🚀"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
