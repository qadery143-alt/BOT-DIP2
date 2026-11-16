import os
import requests
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# استدعاء توكن البوت من متغيرات البيئة في Render بأمان
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# قاعدة بيانات وهمية أو هيكل لتخزين الحسابات الـ 36 والمصانع التابعة لها
game_accounts = [
    {"id": 1, "name": "REX.", "level": 94, "status": "نشط", "diamonds": "14,360", "cash": "415,692,967", "profit": "+114,551,704", "location": "Ürdün", "nationality": "فَالِيرِيَا | VALYRIA", "avatar": "👑", "color": "#22c55e"},
    {"id": 2, "name": "Rayzin.", "level": 88, "status": "نشط", "diamonds": "8,200", "cash": "210,400,000", "profit": "+52,100,000", "location": "Ürdün", "nationality": "فَالِيرِيَا | VALYRIA", "avatar": "🐺", "color": "#a0a6b8"},
    {"id": 3, "name": "NYXOR", "level": 75, "status": "متوقف", "diamonds": "5,100", "cash": "95,300,000", "profit": "+18,400,000", "location": "Ürdün", "nationality": "فَالِيرِيَا | VALYRIA", "avatar": "👤", "color": "#a0a6b8"},
    {"id": 4, "name": "STATHAM", "level": 62, "status": "نشط", "diamonds": "3,400", "cash": "45,100,000", "profit": "+9,200,000", "location": "Ürdün", "nationality": "فَالِيرِيَا | VALYRIA", "avatar": "⚓", "color": "#3b82f6"}
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DiplomaciaBOT</title>
    <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(15px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulseGlow {
            0% { box-shadow: 0 0 5px rgba(168, 85, 247, 0.4); }
            50% { box-shadow: 0 0 20px rgba(168, 85, 247, 0.8); }
            100% { box-shadow: 0 0 5px rgba(168, 85, 247, 0.4); }
        }
        body {
            background-color: #0f111a;
            color: #ffffff;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 15px;
            padding-bottom: 90px;
            animation: fadeIn 0.6s ease-out;
        }
        .header-card {
            background: #181b28;
            border-radius: 16px;
            padding: 15px;
            margin-bottom: 20px;
            border: 1px solid #2a2e43;
        }
        .bot-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .bot-title {
            font-size: 20px;
            font-weight: bold;
        }
        .bot-subtitle {
            font-size: 13px;
            color: #a0a6b8;
        }
        .bot-avatar {
            background: linear-gradient(135deg, #a855f7, #ec4899);
            width: 50px;
            height: 50px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 18px;
            animation: pulseGlow 3s infinite;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            background: #121520;
            padding: 12px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 20px;
        }
        .stat-item div:first-child {
            font-size: 12px;
            color: #a0a6b8;
        }
        .stat-item div:last-child {
            font-size: 15px;
            font-weight: bold;
            margin-top: 4px;
        }
        .search-bar {
            background: #181b28;
            border: 1px solid #2a2e43;
            border-radius: 12px;
            padding: 12px 15px;
            color: #a0a6b8;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .accounts-scroll {
            display: flex;
            gap: 12px;
            overflow-x: auto;
            padding-bottom: 10px;
            margin-bottom: 20px;
            scrollbar-width: none;
        }
        .accounts-scroll::-webkit-scrollbar {
            display: none;
        }
        .account-bubble {
            text-align: center;
            flex-shrink: 0;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .account-bubble:active {
            transform: scale(0.92);
        }
        .avatar-circle {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: #2a2e43;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            margin-bottom: 6px;
        }
        .account-name {
            font-size: 12px;
            color: #d1d5db;
        }
        .active-account-card {
            background: #181b28;
            border-radius: 16px;
            padding: 15px;
            border: 1px solid #2a2e43;
            animation: fadeIn 0.8s ease-out;
            margin-bottom: 15px;
        }
        .btn-run {
            background: #a855f7;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            font-size: 12px;
            margin-top: 10px;
            transition: background 0.2s;
        }
        .btn-run:hover {
            background: #9333ea;
        }
        .nav-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(18, 21, 32, 0.95);
            backdrop-filter: blur(10px);
            display: flex;
            justify-content: space-around;
            padding: 12px;
            border-top: 1px solid #2a2e43;
        }
        .nav-item {
            text-align: center;
            color: #a0a6b8;
            font-size: 12px;
            text-decoration: none;
            cursor: pointer;
        }
        .nav-item.active {
            color: #60a5fa;
        }
    </style>
</head>
<body>

    <div class="header-card">
        <div class="bot-info">
            <div>
                <div class="bot-title">DiplomaciaBOT</div>
                <div class="bot-subtitle">إدارة المصانع والحسابات</div>
            </div>
            <div class="bot-avatar">DB</div>
        </div>
        <div>
            <button style="background: #252838; border: none; border-radius: 10px; color: white; padding: 8px 15px; font-weight: bold; width: 100%; cursor: pointer;">تحكم جماعي</button>
        </div>
    </div>

    <div class="stats-grid">
        <div class="stat-item">
            <div>💎 إجمالي الماس</div>
            <div style="color: #60a5fa;">31,060</div>
        </div>
        <div class="stat-item">
            <div>💵 إجمالي النقد</div>
            <div style="color: #22c55e;">766,492,967</div>
        </div>
        <div class="stat-item">
            <div>📈 إجمالي الأرباح</div>
            <div style="color: #38bdf8;">+194,151,704</div>
        </div>
    </div>

    <div class="search-bar">
        <span>ابحث عن حساب (اسم أو رقم)...</span>
        <span>🔍</span>
    </div>

    <div style="font-size: 14px; font-weight: bold; margin-bottom: 10px; color: #a0a6b8;">حساباتك (36 حساب)</div>
    
    <div class="accounts-scroll">
        {% for acc in accounts %}
        <div class="account-bubble">
            <div class="avatar-circle" style="border: 2px solid {{ acc.color }};">
                <span style="font-size: 20px;">{{ acc.avatar }}</span>
            </div>
            <div class="account-name">{{ acc.name }}</div>
        </div>
        {% endfor %}
    </div>

    {% for acc in accounts %}
    <div class="active-account-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <span style="font-weight: bold;">حساب {{ acc.name }} — Lv.{{ acc.level }}</span>
            <span style="background: {% if acc.status == 'نشط' %}#14532d{% else %}#7f1d1d{% endif %}; color: {% if acc.status == 'نشط' %}#22c55e{% else %}#f87171{% endif %}; padding: 2px 8px; border-radius: 6px; font-size: 12px;">{{ acc.status }}</span>
        </div>
        <div style="font-size: 13px; color: #a0a6b8; margin-bottom: 5px;">الماس: {{ acc.diamonds }} | النقد: {{ acc.cash }}</div>
        <div style="font-size: 13px; display: flex; gap: 15px; margin-bottom: 8px;">
            <span>📍 موقعك: {{ acc.location }}</span>
            <span>🌍 الجنسية: {{ acc.nationality }}</span>
        </div>
        <button class="btn-run" onclick="triggerTask('{{ acc.name }}')">تشغيل مهام المصنع</button>
    </div>
    {% endfor %}

    <div class="nav-bar">
        <div class="nav-item active">
            <div>🏠</div>
            <div>الرئيسية</div>
        </div>
        <div class="nav-item">
            <div>💵</div>
            <div>إيداع</div>
        </div>
        <div class="nav-item">
            <div>⚙️</div>
            <div>الإعدادات</div>
        </div>
    </div>

    <script>
        function triggerTask(accountName) {
            fetch('/run-factory-task', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({account: accountName})
            })
            .then(res => res.json())
            .then(data => {
                alert(data.message);
            });
        }
    </script>

</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, accounts=game_accounts)

# مسار لتنفيذ مهمة المصنع وإرسال إشعار تليجرام عند الحاجة
@app.route("/run-factory-task", methods=["POST"])
def run_factory_task():
    data = request.json
    account_name = data.get("account", "الحساب")
    
    # هنا يتم استدعاء API اللعبة الحقيقي لتنفيذ عمل المصنع
    # مثال: requests.post("https://api.game.com/factory/work", json={"account": account_name})
    
    return jsonify({
        "status": "success",
        "message": f"تم بنجاح إرسال أمر بدء المصنع للحساب: {account_name} 🚀"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
