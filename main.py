import os
import requests
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# بيانات البوت والـ API (يمكنك ربطها بمتغيرات البيئة Environment Variables)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")

# تخزين مؤقت للمهام والحسابات (يمكن استبداله بقاعدة بيانات لاحقاً)
game_tasks = [
    {"id": 1, "name": "مصنع الماس (DIAMOND EMPIRE)", "status": "نشط", "yield": "+114,551,704"},
    {"id": 2, "name": "خط الإنتاج العسكري", "status": "متوقف", "yield": "0"}
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DiplomaciaBOT - إدارة المهام</title>
    <style>
        body { background-color: #0f111a; color: #ffffff; font-family: sans-serif; margin: 0; padding: 15px; }
        .card { background: #181b28; border-radius: 16px; padding: 15px; margin-bottom: 15px; border: 1px solid #2a2e43; }
        .task-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #2a2e43; }
        .btn { background: #a855f7; color: white; border: none; padding: 8px 15px; border-radius: 8px; cursor: pointer; font-weight: bold; }
    </style>
</head>
<body>
    <h2>إدارة مهام المصانع - DiplomaciaBOT</h2>
    
    <div class="card">
        <h3>المهام النشطة حالياً</h3>
        <div id="tasks-container">
            {% for task in tasks %}
            <div class="task-item">
                <div>
                    <b>{{ task.name }}</b><br>
                    <small style="color: #a0a6b8;">العائد: {{ task.yield }} | الحالة: {{ task.status }}</small>
                </div>
                <button class="btn" onclick="executeTask({{ task.id }})">تشغيل المهمة</button>
            </div>
            {% endfor %}
        </div>
    </div>

    <script>
        function executeTask(taskId) {
            fetch('/run-task/' + taskId, { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    location.reload();
                });
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, tasks=game_tasks)

# مسار خاص لتنفيذ المهمة عندما يضغط المستخدم عليها
@app.route("/run-task/<int:task_id>", methods=["POST"])
def run_task(task_id):
    # هنا يتم وضع منطق التواصل مع API اللعبة لتنفيذ المهمة (مثل العمل في المصنع أو نقل الأموال)
    for task in game_tasks:
        if task["id"] == task_id:
            task["status"] = "قيد التنفيذ..."
            # مثال لطلب خارجي لـ API اللعبة:
            # requests.post(f"https://api.game.com/factory/{task_id}/start")
            
            return jsonify({"status": "success", "message": f"تم بدء تنفيذ المهمة: {task['name']} بنجاح!"})
    
    return jsonify({"status": "error", "message": "المهمة غير موجودة"}), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
