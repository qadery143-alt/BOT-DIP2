import os
from flask import Flask, jsonify, render_template_string, request
import requests

app = Flask(__name__)

# تخزين الحسابات (يمكنك إضافة الـ 36 حساباً هنا مع التوكن الخاص بكل حساب)
# مثال: {"Account 1": {"token": "eyJhbG...", "active": True}, ...}
ACCOUNTS = {
    "Account_1": {
        "name": "القائد الأول",
        "token": "ضع_التوكن_هنا_الذي_استخرجناه",
    },
    # "Account_2": {"name": "القائد الثاني", "token": "..."},
}

# تصميم واجهة الـ Mini App (تصميم داكن فاخر يناسب الألعاب الاستراتيجية)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Diplomaciia BOT Dashboard</title>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --accent-color: #38bdf8;
            --gold-color: #fbbf24;
            --text-color: #f8fafc;
            --text-muted: #94a3b8;
            --success-color: #22c55e;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 15px;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
        }
        h2 {
            text-align: center;
            color: var(--accent-color);
            margin-bottom: 20px;
        }
        .account-card {
            background-color: var(--card-bg);
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            border: 1px solid #334155;
        }
        .account-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: bold;
            font-size: 1.1em;
            margin-bottom: 10px;
            border-bottom: 1px solid #334155;
            padding-bottom: 8px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            font-size: 0.9em;
            margin-bottom: 12px;
        }
        .stat-item {
            background: #0f172a;
            padding: 8px 12px;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
        }
        .stat-value {
            color: var(--gold-color);
            font-weight: bold;
        }
        .btn {
            background-color: var(--accent-color);
            color: #0f172a;
            border: none;
            padding: 10px 15px;
            border-radius: 8px;
            font-weight: bold;
            width: 100%;
            cursor: pointer;
            transition: 0.2s;
        }
        .btn:hover {
            opacity: 0.9;
        }
        .global-actions {
            margin-top: 25px;
            display: flex;
            gap: 10px;
        }
        .btn-success {
            background-color: var(--success-color);
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>🚀 لوحة تحكم Diplomaciia BOT</h2>
        
        <div id="accounts-container">
            {% for acc_id, data in accounts.items() %}
            <div class="account-card" id="card-{{ acc_id }}">
                <div class="account-header">
                    <span>{{ data.name }} ({{ acc_id }})</span>
                    <span style="color: var(--success-color); font-size: 0.8em;">متصل</span>
                </div>
                <div class="stats-grid">
                    <div class="stat-item"><span>المستوى:</span> <span class="stat-value" id="lvl-{{ acc_id }}">--</span></div>
                    <div class="stat-item"><span>الماس:</span> <span class="stat-value" id="diamonds-{{ acc_id }}">--</span></div>
                    <div class="stat-item"><span>الأموال:</span> <span class="stat-value" id="cash-{{ acc_id }}">--</span></div>
                    <div class="stat-item"><span>حالة المصنع:</span> <span class="stat-value" id="work-{{ acc_id }}">جاهز</span></div>
                </div>
                <button class="btn" onclick="triggerWork('{{ acc_id }}')">تشغيل المصنع / المهام</button>
            </div>
            {% endfor %}
        </div>

        <div class="global-actions">
            <button class="btn btn-success" onclick="triggerAll()">تشغيل الكل دفعة واحدة</button>
        </div>
    </div>

    <script>
        function triggerWork(accId) {
            alert("جاري إرسال أمر العمل للحساب: " + accId);
            // سيتم ربطها بمسار الـ API لاحقاً
        }
        function triggerAll() {
            alert("جاري تشغيل المصانع لكل الحسابات الـ 36...");
        }
    </script>
</body>
</html>
"""


@app.route("/")
def index():
  return render_template_string(HTML_TEMPLATE, accounts=ACCOUNTS)


@app.route("/api/profile/<acc_id>")
def get_profile(acc_id):
  if acc_id not in ACCOUNTS:
    return jsonify({"error": "Account not found"}), 404

  token = ACCOUNTS[acc_id]["token"]
  headers = {
      "Authorization": f"Bearer {token}",
      "Content-Type": "application/json",
      "X-Client-Platform": "web",
      "X-App-Build": "2026111201",
  }

  try:
    response = requests.get(
        "https://diplomacia.com.tr/api/players/profile", headers=headers
    )
    if response.status_code == 200:
      return jsonify(response.json())
    return jsonify({"error": "Failed to fetch", "status": response.status_code})
  except Exception as e:
    return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
