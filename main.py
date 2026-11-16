import asyncio
import html
import logging
import os
from contextlib import suppress

import aiosqlite
from dotenv import load_dotenv

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

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DB_PATH = "diplomaciia.db"

router = Router()


# ============================ قاعدة البيانات ============================

async def db_init() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                full_name   TEXT,
                joined_at   TEXT DEFAULT CURRENT_TIMESTAMP,
                is_banned   INTEGER DEFAULT 0,
                msg_count   INTEGER DEFAULT 0
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS messages_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER,
                text       TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.commit()


async def db_upsert_user(message: Message) -> None:
    u = message.from_user
    if u is None:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (user_id, username, full_name)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username  = excluded.username,
                full_name = excluded.full_name
            """,
            (u.id, u.username, u.full_name),
        )
        await db.commit()


async def db_is_banned(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT is_banned FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
    return bool(row and row[0])


async def db_set_ban(user_id: int, banned: bool) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_banned = ? WHERE user_id = ?",
            (1 if banned else 0, user_id),
        )
        await db.commit()


async def db_stats() -> tuple[int, int, int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            total = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1") as cur:
            banned = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM messages_log") as cur:
            msgs = (await cur.fetchone())[0]
    return total, banned, msgs


async def db_all_user_ids(only_active: bool = True) -> list[int]:
    query = "SELECT user_id FROM users"
    if only_active:
        query += " WHERE is_banned = 0"
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(query) as cur:
            rows = await cur.fetchall()
    return [r[0] for r in rows]


async def db_log_message(message: Message) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages_log (user_id, text) VALUES (?, ?)",
            (message.from_user.id, message.text),
        )
        await db.execute(
            "UPDATE users SET msg_count = msg_count + 1 WHERE user_id = ?",
            (message.from_user.id,),
        )
        await db.commit()


# ============================ الحالات (FSM) ============================

class AdminStates(StatesGroup):
    waiting_broadcast = State()
    waiting_ban_id = State()


# ============================ لوحات المفاتيح ============================

def main_menu(is_admin: bool) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="ℹ️ عن البوت", callback_data="about")],
        [InlineKeyboardButton(text="🆔 معرّفي", callback_data="myid")],
    ]
    if is_admin:
        rows.append([InlineKeyboardButton(text="🛠 لوحة الأدمن", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton(text="📢 إذاعة رسالة", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="🚫 حظر مستخدم", callback_data="admin_ban")],
            [InlineKeyboardButton(text="✅ فك الحظر", callback_data="admin_unban")],
            [InlineKeyboardButton(text="⬅️ رجوع", callback_data="back_main")],
        ]
    )


# ============================ الأوامر العامة ============================

@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject) -> None:
    await db_upsert_user(message)
    name = html.escape(message.from_user.full_name)
    payload = f"\n\n🔗 وصلت عبر: <code>{html.escape(command.args)}</code>" if command.args else ""
    await message.answer(
        f"أهلاً بك <b>{name}</b> في <b>DiplomaciiaBOT</b> 👋\n\n"
        f"استخدم الأزرار بالأسفل أو الأوامر:\n"
        f"/help — قائمة الأوامر\n"
        f"/id — معرّف حسابك{payload}",
        reply_markup=main_menu(message.from_user.id == ADMIN_ID),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await db_upsert_user(message)
    text = (
        "<b>الأوامر المتاحة</b>\n\n"
        "/start — تشغيل البوت\n"
        "/help — هذه القائمة\n"
        "/id — معرّف حسابك\n"
        "/about — معلومات عن البوت\n"
    )
    if message.from_user.id == ADMIN_ID:
        text += (
            "\n<b>أوامر الأدمن</b>\n"
            "/admin — لوحة التحكم\n"
            "/stats — الإحصائيات\n"
            "/broadcast — إذاعة رسالة\n"
            "/ban &lt;id&gt; — حظر مستخدم\n"
            "/unban &lt;id&gt; — فك الحظر\n"
            "/users — عدد المستخدمين\n"
        )
    await message.answer(text)


@router.message(Command("about"))
async def cmd_about(message: Message) -> None:
    await message.answer(
        "<b>DiplomaciiaBOT</b>\n"
        "بوت تيليجرام مبني بـ Python + aiogram 3\n"
        f"الإصدار: <code>1.0.0</code>"
    )


@router.message(Command("id"))
async def cmd_id(message: Message) -> None:
    u = message.from_user
    await message.answer(
        f"🆔 معرّفك: <code>{u.id}</code>\n"
        f"👤 اليوزر: @{u.username if u.username else 'لا يوجد'}\n"
        f"💬 معرّف المحادثة: <code>{message.chat.id}</code>"
    )


# ============================ معالجات الأزرار ============================

@router.callback_query(F.data == "about")
async def cb_about(call: CallbackQuery) -> None:
    await call.answer()
    await call.message.answer(
        "<b>DiplomaciiaBOT</b>\nبوت تيليجرام مبني بـ Python + aiogram 3."
    )


@router.callback_query(F.data == "myid")
async def cb_myid(call: CallbackQuery) -> None:
    await call.answer(f"معرّفك: {call.from_user.id}", show_alert=True)


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
            f"📊 <b>الإحصائيات</b>\n\n"
            f"👥 المستخدمون: <code>{total}</code>\n"
            f"🚫 المحظورون: <code>{banned}</code>\n"
            f"💬 الرسائل المسجلة: <code>{msgs}</code>",
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


# ============================ أحداث FSM ============================

@router.message(AdminStates.waiting_broadcast, Command("cancel"))
@router.message(AdminStates.waiting_ban_id, Command("cancel"))
async def fsm_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("تم الإلغاء.", reply_markup=main_menu(message.from_user.id == ADMIN_ID))


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
        await asyncio.sleep(0.05)  # احترام حدود Telegram API

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
        f"✅ تم {action} المستخدم <code>{uid}</code>",
        reply_markup=main_menu(True),
    )


# ============================ أوامر الأدمن النصية ============================

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
        f"📊 المستخدمون: <code>{total}</code>\n"
        f"🚫 المحظورون: <code>{banned}</code>\n"
        f"💬 الرسائل: <code>{msgs}</code>"
    )


@router.message(Command("users"))
async def cmd_users(message: Message) -> None:
    if message.from_user.id != ADMIN_ID:
        return
    ids = await db_all_user_ids(only_active=False)
    await message.answer(f"👥 إجمالي المستخدمين المسجلين: <code>{len(ids)}</code>")


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


# ============================ الرسائل العامة ============================

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


# ============================ التشغيل ============================

async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    if not BOT_TOKEN or not ADMIN_ID:
        raise SystemExit("ضع BOT_TOKEN و ADMIN_ID في ملف .env")

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
    
