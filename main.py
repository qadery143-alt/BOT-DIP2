import asyncio
from contextlib import suppress
import logging
import os
import threading

import aiosqlite
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template_string, request
import requests

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatAction, ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

router = Router()
app = Flask(__name__)

DB_NAME = "bot_database.db"

# ============================ إدارة قاعدة البيانات للحسابات المستقلة ============================


async def db_init():
  async with aiosqlite.connect(DB_NAME) as db:
    # جدول الحسابات: لكل حساب بياناته، اسم المستخدم، كلمة المرور/التوكن الخاص به حصرياً
    await db.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                account_id TEXT PRIMARY KEY,
                name TEXT,
                username TEXT,
                password TEXT,
                token TEXT,
                level INTEGER DEFAULT 1,
                diamonds INTEGER DEFAULT 0,
                cash INTEGER DEFAULT 0,
                status TEXT DEFAULT 'جاهز'
            )
        """)
    # جدول المستخدمين الخاص بالبوت
    await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                banned INTEGER DEFAULT 0
            )
        """)
    await db.commit()


async def get_all_accounts():
  async with aiosqlite.connect(DB_NAME) as db:
    db.row_factory = aiosqlite.Row
    async with db.execute("SELECT * FROM accounts") as cursor:
      rows = await cursor.fetchall()
      return [dict(row) for row in rows]


async def get_account(account_id):
  async with aiosqlite.connect(DB_NAME) as db:
    db.row_factory = aiosqlite.Row
    async with db.execute(
        "SELECT * FROM accounts WHERE account_id = ?", (account_id,)
    ) as cursor:
      row = await cursor.fetchone()
      return dict(row) if row else None


# ============================ واجهة الـ Mini App ============================

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
            --success-color: #22c55e;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 15px;
        }
        .container { max-width: 600px; margin: 0 auto; }
        h2 { text-align: center; color: var(--accent-color); }
        .account-card {
            background-color: var(--card-bg);
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 15px;
            border: 1px solid #334155;
        }
        .account-header {
            display: flex;
            justify-content: space-between;
            font-weight: bold;
            margin-bottom: 10px;
            border-bottom: 1px solid #334155;
            padding-bottom: 8px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
            font-size: 0.9em;
            margin-bottom: 10px;
        }
        .stat-item {
            background: #0f172a;
            padding: 6px 10px;
            border-radius: 6px;
            display: flex;
            justify-content: space-between;
        }
        .stat-value { color: var(--gold-color); font-weight: bold; }
        .btn {
            background-color: var(--accent-color);
            color: #0f172a;
            border: none;
            padding: 10px;
            border-radius: 8px;
            font-weight: bold;
            width: 100%;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>🚀 إدارة الحسابات المستقلة (36 حساب)</h2>
        <div id="accounts-container">
            {% for acc in accounts %}
            <div class="account-card">
                <div class="account-header">
                    <span>{{ acc.name }} ({{ acc.username }})</span>
                    <span style="color: var(--success-color);">متصل</span>
                </div>
                <div class="stats-grid">
                    <div class="stat-item"><span>المستوى:</span> <span class="stat-value">{{ acc.level }}</span></div>
                    <div class="stat-item"><span>الماس:</span> <span class="stat-value">{{ acc.diamonds }}</span></div>
                    <div class="stat-item"><span>الأموال:</span> <span class="stat-value">{{ acc.cash }}</span></div>
                    <div class="stat-item"><span>الحالة:</span> <span class="stat-value">{{ acc.status }}</span></div>
                </div>
                <button class="btn" onclick="triggerWork('{{ acc.account_id }}')">تشغيل المصنع / المهام</button>
            </div>
            {% endfor %}
        </div>
    </div>
    <script>
        function triggerWork(accId) {
            alert("جاري تنفيذ المهام للحساب المستقل ID: " + accId);
        }
    </script>
</body>
</html>
"""


@app.route("/")
def index():
  # جلب الحسابات من قاعدة البيانات بشكل متزامن بسيط
  import sqlite3

  conn = sqlite3.connect(DB_NAME)
  conn.row_factory = sqlite3.Row
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM accounts")
  accounts = [dict(row) for row in cursor.fetchall()]
  conn.close()
  return render_template_string(HTML_TEMPLATE, accounts=accounts)


@app.route("/api/profile/<acc_id>")
def get_profile(acc_id):
  import sqlite3

  conn = sqlite3.connect(DB_NAME)
  conn.row_factory = sqlite3.Row
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM accounts WHERE account_id = ?", (acc_id,))
  acc = cursor.fetchone()
  conn.close()

  if not acc:
    return jsonify({"error": "Account not found"}), 404

  token = acc["token"]
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
    return jsonify(response.json()), response.status_code
  except Exception as e:
    return jsonify({"error": str(e)}), 500


def run_flask():
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


# ============================ دوال البوت وتليجرام ============================


def main_menu(is_admin: bool = False):
  kb = [[
      InlineKeyboardButton(
          text="🎮 لوحة الحسابات المستقلة", url="https://bot-dip2.onrender.com"
      )
  ]]
  if is_admin:
    kb.append([InlineKeyboardButton(text="🛠 لوحة الأدمن", callback_data="admin")])
  return InlineKeyboardMarkup(inline_keyboard=kb)


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
  if message.from_user.id != ADMIN_ID:
    await message.answer("غير مصرح.")
    return
  await message.answer("🛠 <b>لوحة الأدمن</b>")


@router.message(F.text & ~F.text.startswith("/"))
async def echo(message: Message) -> None:
  await message.answer(
      "مرحباً بك في نظام إدارة الحسابات المستقلة ✅",
      reply_markup=main_menu(message.from_user.id == ADMIN_ID),
  )


async def main() -> None:
  logging.basicConfig(level=logging.INFO)
  if not BOT_TOKEN or not ADMIN_ID:
    raise SystemExit("ضع BOT_TOKEN و ADMIN_ID في متغيرات البيئة")

  # إنشاء الجداول وقاعدة البيانات
  await db_init()

  # تشغيل الـ Flask في الخلفية
  flask_thread = threading.Thread(target=run_flask, daemon=True)
  flask_thread.start()

  bot = Bot(
      token=BOT_TOKEN,
      default=DefaultBotProperties(parse_mode=ParseMode.HTML),
  )
  dp = Dispatcher(storage=MemoryStorage())
  dp.include_router(router)

  me = await bot.get_me()
  logging.info("Bot started: @%s", me.username)

  try:
    await dp.start_polling(bot)
  finally:
    await bot.session.close()


if __name__ == "__main__":
  with suppress(KeyboardInterrupt):
    asyncio.run(main())
