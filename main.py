import os
from flask import Flask, render_template_string

app = Flask(__name__)

# تصميم الواجهة مطابق لواجهة DiplomaciaBOT
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DiplomaciaBOT</title>
    <style>
        body {
            background-color: #0f111a;
            color: #ffffff;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 15px;
            padding-bottom: 80px;
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
        }
        .account-bubble {
            text-align: center;
            flex-shrink: 0;
        }
        .avatar-circle {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            border: 2px solid #22c55e;
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
        }
        .nav-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: #121520;
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
                <div class="bot-subtitle">أهلاً،</div>
            </div>
            <div class="bot-avatar">DB</div>
        </div>
        <div style="display: flex; gap: 10px; align-items: center;">
            <button style="background: #252838; border: none; border-radius: 10px; color: white; padding: 8px 15px; font-weight: bold; width: 100%;">تحكم جماعي</button>
        </div>
    </div>

    <div class="stats-grid">
        <div class="stat-item">
            <div>💎 الماس</div>
            <div style="color: #60a5fa;">14,360</div>
        </div>
        <div class="stat-item">
            <div>💵 النقد</div>
            <div style="color: #22c55e;">415,692,967</div>
        </div>
        <div class="stat-item">
            <div>📈 الأرباح</div>
            <div style="color: #38bdf8;">+114,551,704</div>
        </div>
    </div>

    <div class="search-bar">
        <span>ابحث عن حساب (اسم أو رقم)...</span>
        <span>🔍</span>
    </div>

    <div style="font-size: 14px; font-weight: bold; margin-bottom: 10px; color: #a0a6b8;">حساباتك (36)</div>
    
    <div class="accounts-scroll">
        <div class="account-bubble">
            <div class="avatar-circle" style="border-color: #22c55e;">
                <span style="font-size: 20px;">👑</span>
            </div>
            <div class="account-name">REX.</div>
        </div>
        <div class="account-bubble">
            <div class="avatar-circle" style="border-color: #a0a6b8;">
                <span style="font-size: 20px;">🐺</span>
            </div>
            <div class="account-name">Rayzin.</div>
        </div>
        <div class="account-bubble">
            <div class="avatar-circle" style="border-color: #a0a6b8;">
                <span style="font-size: 20px;">👤</span>
            </div>
            <div class="account-name">NYXOR</div>
        </div>
        <div class="account-bubble">
            <div class="avatar-circle" style="border-color: #3b82f6;">
                <span style="font-size: 20px;">⚓</span>
            </div>
            <div class="account-name">STATHAM</div>
        </div>
    </div>

    <div class="active-account-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <span style="font-weight: bold;">حساب 1 — Lv.94</span>
            <span style="background: #14532d; color: #22c55e; padding: 2px 8px; border-radius: 6px; font-size: 12px;">نشط</span>
        </div>
        <div style="font-size: 13px; color: #a0a6b8; margin-bottom: 5px;">ترقيات: 1048 | آخر: 19:25:33</div>
        <div style="font-size: 13px; display: flex; gap: 15px;">
            <span>📍 موقعك: Ürdün</span>
            <span>🌍 الجنسية: فَالِيرِيَا | VALYRIA</span>
        </div>
    </div>

    <div class="nav-bar">
        <a href="#" class="nav-item active">
            <div>🏠</div>
            <div>الرئيسية</div>
        </a>
        <a href="#" class="nav-item">
            <div>💵</div>
            <div>إيداع</div>
        </a>
        <a href="#" class="nav-item">
            <div>⚙️</div>
            <div>الإعدادات</div>
        </a>
    </div>

</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
