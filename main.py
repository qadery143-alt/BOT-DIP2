import asyncio
from contextlib import suppress
import html
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
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# تحميل المتغيرات البيئية
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

router = Router()
app = Flask(__name__)

# ============================ إعدادات الحسابات والـ Mini App ============================

ACCOUNTS = {
    "Account_1": {
        "name": "القائد الأول",
        "token": "ضع_التوكن_هنا",
    },
    # يمكنك إضافة باقي الحسابات هنا حتى 36 حساباً
}

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
        .btn {
            background-color: var(--accent-color);
            color: #0f172a;
            border: none;
            padding: 10px 15px;
            border-radius: 8px;
            font-weight: bold;
            width: 100%;
            cursor: pointer;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>🚀 لوحة تحكم Diplomaciia BOT (36 حساب)</h2>
        <div id="accounts-container">
            {% for acc_id, data in accounts.items() %}
            <div class="account-card">
                <div class="account-header">
                    <span>{{ data.name }} ({{ acc_id }})</span>
                    <span style="color: var(--success-color);">متصل</span>
                </div>
                <button class="btn" onclick="triggerWork('{{ acc_id }}')">تشغيل المصنع / المهام</button>
            </div>
            {% endfor %}
        </div>
    </div>
    <script>
        function triggerWork(accId) {
            alert("جاري إرسال أمر العمل للحساب: " + accId);
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
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


# ============================ دوال وقوائم البوت (FSM & Handlers) ============================


class AdminStates(StatesGroup):
    waiting_broadcast = State()
    waiting_ban_id = State()


def main_menu(is_admin: bool = False):
    kb = [[InlineKeyboardButton(text="🎮 لوحة الألعاب / الحسابات", url="https://bot-dip2.onrender.com")]]
    if is_admin:
        kb.append([InlineKeyboardButton(text="🛠 لوحة الأدمن", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def admin_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton(text="📢 إذاعة", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="🚫 حظر مستخدم", callback_data="admin_ban")],
            [InlineKeyboardButton(text="✅ فك حظر", callback_data="admin_unban")],
            [InlineKeyboardButton(text="⬅️ القائمة الرئيسية", callback_data="back_main")],
        ]
    )


# دوال قاعدة البيانات (يمكنك ربطها بقاعدة البيانات الخاصة بك لاحقاً)
async def db_init():
    pass


async def db_stats():
    return (0, 0, 0)


async def db_all_user_ids(only_active=True):
    return []


async def db_set_ban(uid, banned):
    pass


async def db_is_banned(uid):
    return False


async def db_upsert_user(message):
    pass


async def db_log_message(message):
    pass


@router.callback_query(F.data == "back_main")
async def cb_back_main(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.answer()
    with suppress(TelegramBadRequest):
        await call.message.edit_text(
            "القائمة الرئيسية:",
            reply_markup=main_menu(call.from_user.id == ADMIN_ID),
        )


@router.callback_query(F.data == "admin")
async def cb_admin(call: CallbackQuery) -> None:
    if call.from_user.id != ADMIN_ID:
        await call.answer("غير مصرح", show_alert=True)
        return
    await call.answer()
    with suppress(TelegramBadRequest):
        await call.message.edit_text("🛠 <b>لوحة الأدمن</b>", reply_markup=admin_menu())


@router.callback_query(F.data == "admin_stats")
async def cb_stats(call: CallbackQuery) -> None:
    if call.from_user.id != ADMIN_ID:
        await call.answer("غير مصرح", show_alert=True)
        return
    total, banned, msgs = await db_stats()
    await call.answer()
    with suppress(TelegramBadRequest):
        await call.message.edit_text(
            f"📊 <b>الإحصائيات</b>\n\n👥 المستخدمون: <code>{total}</code>\n🚫 المحظورون: <code>{banned}</code>\n💬 الرسائل المسجلة: <code>{msgs}</code>",
            reply_markup=admin_menu(),
        )


@router.callback_query(F.data == "admin_broadcast")
async def cb_broadcast(call: CallbackQuery, state: FSMContext) -> None:
    if call.from_user.id != ADMIN_ID:
        await call.answer("غير مصرح", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_broadcast)
    await call.answer()
    await call.message.answer("📢 أرسل نص الرسالة التي تريد إذاعتها (أو /cancel للإلغاء):")


@router.callback_query(F.data == "admin_ban")
async def cb_ban(call: CallbackQuery, state: FSMContext) -> None:
    if call.from_user.id != ADMIN_ID:
        await call.answer("غير مصرح", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_ban_id)
    await call.answer()
    await call.message.answer("🚫 أرسل معرّف المستخدم المراد حظره:")


@router.callback_query(F.data == "admin_unban")
async def cb_unban(call: CallbackQuery, state: FSMContext) -> None:
    if call.from_user.id != ADMIN_ID:
        await call.answer("غير مصرح", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_ban_id)
    await state.update_data(unban=True)
    await call.answer()
    await call.message.answer("✅ أرسل معرّف المستخدم المراد فك الحظر عنه:")


@router.message(AdminStates.waiting_broadcast, Command("cancel"))
@router.message(AdminStates.waiting_ban_id, Command("cancel"))
async def fsm_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "تم الإلغاء.", reply_markup=main_menu(message.from_user.id == ADMIN_ID)
    )


@router.message(AdminStates.waiting_broadcast, F.text)
async def do_broadcast(message: Message, state: FSMContext, bot: Bot) -> None:
    await state.clear()
    text = message.html_text
    user_ids = await db_all_user_ids()
    sent = failed = 0
    status = await message.answer(f"⏳ جارٍ الإرسال إلى {len(user_ids)} مستخدم...")
    for uid in user_ids:
        try:
            await bot.send_message(uid, text)
            sent += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            failed += 1
        await asyncio.sleep(0.05)
    await status.edit_text(
        f"✅ اكتملت الإذاعة\n\nنجح: <code>{sent}</code>\nفشل: <code>{failed}</code>",
        reply_markup=main_menu(True),
    )


@router.message(AdminStates.waiting_ban_id, F.text)
async def do_ban(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    unban = data.get("unban", False)
    await state.clear()
    try:
        uid = int(message.text.strip())
    except ValueError:
        await message.answer("❌ معرّف غير صالح. أرسل رقماً فقط.")
        return
    await db_set_ban(uid, banned=not unban)
    action = "فك الحظر عن" if unban else "حظر"
    await message.answer(
        f"✅ تم {action} المستخدم <code>{uid}</code>", reply_markup=main_menu(True)
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    if message.from_user.id != ADMIN_ID:
        await message.answer("غير مصرح.")
        return
    await message.answer("🛠 <b>لوحة الأدمن</b>", reply_markup=admin_menu())


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if message.from_user.id != ADMIN_ID:
        return
    total, banned, msgs = await db_stats()
    await message.answer(
        f"📊 المستخدمون: <code>{total}</code>\n🚫 المحظورون: <code>{banned}</code>\n💬 الرسائل: <code>{msgs}</code>"
    )


@router.message(Command("users"))
async def cmd_users(message: Message) -> None:
    if message.from_user.id != ADMIN_ID:
        return
    ids = await db_all_user_ids(only_active=False)
    await message.answer(
        f"👥 إجمالي المستخدمين المسجلين: <code>{len(ids)}</code>"
    )


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, command: CommandObject) -> None:
    if message.from_user.id != ADMIN_ID:
        return
    if not command.args:
        await message.answer("الاستخدام: <code>/broadcast نص الرسالة</code>")
        return
    user_ids = await db_all_user_ids()
    sent = 0
    for uid in user_ids:
        with suppress(Exception):
            await message.bot.send_message(uid, command.args)
            sent += 1
        await asyncio.sleep(0.05)
    await message.answer(f"✅ أُرسلت إلى <code>{sent}</code> مستخدم.")


@router.message(Command("ban"))
async def cmd_ban(message: Message, command: CommandObject) -> None:
    if message.from_user.id != ADMIN_ID:
        return
    try:
        uid = int(command.args)
    except (TypeError, ValueError):
        await message.answer("الاستخدام: <code>/ban 123456789</code>")
        return
    await db_set_ban(uid, True)
    await message.answer(f"🚫 تم حظر <code>{uid}</code>")


@router.message(Command("unban"))
async def cmd_unban(message: Message, command: CommandObject) -> None:
    if message.from_user.id != ADMIN_ID:
        return
    try:
        uid = int(command.args)
    except (TypeError, ValueError):
        await message.answer("الاستخدام: <code>/unban 123456789</code>")
        return
    await db_set_ban(uid, False)
    await message.answer(f"✅ تم فك الحظر عن <code>{uid}</code>")


@router.message(F.text & ~F.text.startswith("/"))
async def echo(message: Message) -> None:
    if await db_is_banned(message.from_user.id):
        await message.answer("🚫 حسابك محظور من استخدام البوت.")
        return
    await db_upsert_user(message)
    await db_log_message(message)
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    await message.answer(
        f"استلمت رسالتك ✅\n\n<blockquote>{message.html_text}</blockquote>",
        reply_markup=main_menu(message.from_user.id == ADMIN_ID),
    )


# ============================ التشغيل الرئيسي ============================


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    if not BOT_TOKEN or not ADMIN_ID:
        raise SystemExit("ضع BOT_TOKEN و ADMIN_ID في ملف .env أو متغيرات Render")

    # تشغيل Flask في الخلفية
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logging.info("Flask Web App & Mini App started successfully in background.")

    await db_init()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    me = await bot.get_me()
    logging.info("Bot started: @%s", me.username)

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        asyncio.run(main())
