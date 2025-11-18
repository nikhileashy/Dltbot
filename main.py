#Credits @sathan_of_telegram

import asyncio
import re
import time
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient
from pyrogram.enums import ParseMode
from pyrogram import Client, filters
from pyrogram.errors import MessageDeleteForbidden, RPCError, FloodWait
from pyrogram.types import ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from config import (
    API_ID, API_HASH, BOT_TOKEN, ADMIN_ID, OWNER_USERNAME,
    MONGO_URI, DB_NAME, GROUP_DELETE_AFTER, BANNED_WORDS,
    MAX_MESSAGE_LENGTH, PREVIEW_URL
)

# ===== MongoDB Connection =====
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
users_col = db["users"]

# ===== Pyrogram Client =====
app = Client("autodelete-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ========= Emoji Regex =========
emoji_pattern = re.compile(
    "[\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002500-\U00002BEF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+"
)

# ====== Generate Start Text ======
def get_start_text(is_admin: bool):
    if is_admin:
        text = (
            f"🤖 𝗪𝗲𝗹𝗰𝗼𝗺𝗲! | 👑 <b>𝗕𝗼𝘁 𝗢𝘄𝗻𝗲𝗿: {OWNER_USERNAME}</b>\n\n"
            f"⚙️ <b>𝗖𝘂𝗿𝗿𝗲𝗻𝘁 𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀:</b>\n"
            f"• Auto-delete: <code>{GROUP_DELETE_AFTER}s</code>\n"
            f"• Max msg length: <code>{MAX_MESSAGE_LENGTH}</code>\n"
            f"• Punishment: 🔇 2 hour mute"
        )
    else:
        text = (
            f"🤖 𝗪𝗲𝗹𝗰𝗼𝗺𝗲! | 👑 <b>𝗕𝗼𝘁 𝗢𝘄𝗻𝗲𝗿: {OWNER_USERNAME}</b>\n\n"
            f"✨ I am an 𝗦𝗽𝗮𝗺-𝗗𝗲𝘁𝗲𝗰𝘁𝗶𝗼𝗻 Bot created to keep groups clean.\n\n"
            f"📌 𝗙𝗲𝗮𝘁𝘂𝗿𝗲𝘀:\n"
            f"• 𝘈𝘶𝘵𝘰-𝘥𝗲𝗹𝗲𝘁𝗲 messages after <code>{GROUP_DELETE_AFTER}s</code>\n"
            f"• Delete links, forwards, usernames, long msgs, emojis\n"
            f"• Mute rule violators for 2 hours\n\n"
            f"✅ Add me to your group & give <b>𝗗𝗲𝗹𝗲𝘁𝗲 & 𝗕𝗮𝗻</b> permissions!\n\n"
            f"📖 Tap the \"𝗛𝗲𝗹𝗽\" button below for more details."
        )
    return text

# ====== Buttons ======
start_buttons = InlineKeyboardMarkup(
    [[
        InlineKeyboardButton("📖 𝗛𝗲𝗹𝗽", callback_data="help"),
        InlineKeyboardButton("👑 𝗢𝘄𝗻𝗲𝗿", url=f"https://t.me/{OWNER_USERNAME.strip('@')}")
    ]]
)

# ====== Add User to DB ======
def add_user(user_id: int, name: str):
    if not users_col.find_one({"_id": user_id}):
        users_col.insert_one({"_id": user_id, "name": name, "joined": datetime.utcnow()})

# ====== /start ======
@app.on_message(filters.command("start") & filters.private)
async def start_private(client, message):
    # Resolve primary admin (ADMIN_ID may be list or single int)
    primary_admin = ADMIN_ID[0] if isinstance(ADMIN_ID, (list, tuple)) else ADMIN_ID
    is_admin = message.from_user.id == primary_admin
    user_id = message.from_user.id
    name = message.from_user.first_name

    # add to db
    add_user(user_id, name)

    # notify admin (if configured)
    if primary_admin:
        try:
            await client.send_message(
                primary_admin,
                f"🆕 <b>New User Started Bot</b>\n\n"
                f"👤 Name: {message.from_user.mention}\n"
                f"🆔 ID: <code>{user_id}</code>",
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass

    # build start text
    start_text = get_start_text(is_admin)

    # If you want a big quoted-style preview card at top WITHOUT showing the link:
    # use a zero-width char wrapped in an <a href="..."> link. Telegram will detect
    # the URL and render the preview, but the link itself stays invisible.
    if PREVIEW_URL:
        try:
            ZWC = "&#8203;"  # zero-width char (invisible)
            hidden_preview_link = f"<a href=\"{PREVIEW_URL}\">{ZWC}</a>"
            full_text = hidden_preview_link + "\n" + start_text

            await client.send_message(
                chat_id=message.chat.id,
                text=full_text,
                parse_mode=ParseMode.HTML,
                reply_markup=start_buttons,
                disable_web_page_preview=False  # must be False to show preview
            )
            return
        except Exception as e:
            # fallback to photo or plain text if preview send fails
            print("Hidden preview send failed:", e)

    # If PREVIEW_URL not set or preview send failed, fallback to sending a photo (if url is image)
    if PREVIEW_URL:
        try:
            await client.send_photo(
                chat_id=message.chat.id,
                photo=PREVIEW_URL,
                caption=start_text,
                parse_mode=ParseMode.HTML,
                reply_markup=start_buttons
            )
            return
        except Exception as e:
            print("Photo send fallback failed:", e)

    # Final fallback: plain text (no preview)
    await client.send_message(
        chat_id=message.chat.id,
        text=start_text,
        parse_mode=ParseMode.HTML,
        reply_markup=start_buttons,
        disable_web_page_preview=True
    )

# ====== Help Callback ======
@app.on_callback_query(filters.regex("help"))
async def help_menu(client, callback_query):
    help_text = (
        f"🤖 𝗛𝗲𝗹𝗽 𝗠𝗲𝗻𝘂 | 👑 <b>𝗕𝗼𝘁 𝗢𝘄𝗻𝗲𝗿: {OWNER_USERNAME}</b>\n\n"
        f"📌 How to use this bot:\n"
        f"• Add me to your group and give <b>Delete & Ban</b> permissions\n"
        f"• Messages auto-delete after <code>{GROUP_DELETE_AFTER}s</code>\n"
        f"• Links, forwards, usernames, long msgs, and emojis are deleted instantly\n"
        f"• Violators are muted for 2 hours 🚫\n\n"
        f"⚡ <b>Punishment Mode:</b>\n"
        f"✅ ON → If admins give <b>Ban Users</b> permission\n"
        f"❌ OFF → If no Ban Users permission\n\n"
        f"📖 <b>Admins Commands:</b>\n"
        f"• /ping → Check bot speed\n"
        f"• /alive → Bot alive status\n"
        f"• /setgroup <seconds> → Change delete timer\n"
        f"• /delall <chat_id> → Delete last 500 messages\n"
        f"• /broadcast <msg> → Send message to all users\n"
        f"• /totalusers → Show total users\n\n"
        f"🙏 Thanks for using @{client.me.username}"
    )

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("👑 𝗢𝘄𝗻𝗲𝗿", url=f"https://t.me/{OWNER_USERNAME.strip('@')}")],
        [InlineKeyboardButton("⬅ Back", callback_data="back_start")]
    ])

    # Answer callback to remove spinner quickly
    try:
        await callback_query.answer()
    except:
        pass

    # Try to edit the message body; if it's media (photo/video) edit the caption instead.
    try:
        # prefer editing text if the message is a text message
        if not callback_query.message.media:
            await callback_query.message.edit_text(help_text, reply_markup=buttons, parse_mode=ParseMode.HTML)
            return
    except Exception:
        # fall through to try editing caption
        pass

    # If message has media or edit_text failed, try editing caption
    try:
        await callback_query.message.edit_caption(help_text, reply_markup=buttons, parse_mode=ParseMode.HTML)
        return
    except Exception:
        # If editing the original message fails (permissions or unsupported), send a new message
        try:
            await callback_query.message.reply_text(help_text, reply_markup=buttons, parse_mode=ParseMode.HTML)
            # optionally remove old inline keyboard to avoid duplicate actions
            try:
                await callback_query.message.edit_reply_markup(None)
            except:
                pass
            return
        except Exception:
            # last resort: notify user via popup
            await callback_query.answer("Unable to open help.", show_alert=False)
            return

# ====== Back to Start Handler ======
@app.on_callback_query(filters.regex("back_start"))
async def back_to_start(client, callback_query):

    # Remove loading spinner
    try:
        await callback_query.answer()
    except:
        pass

    # Delete the help menu message (ignore failure)
    try:
        await callback_query.message.delete()
    except:
        pass

    # Create a fake message object to reuse start_private logic
    fake = type("FakeMessage", (), {})()
    fake.chat = callback_query.message.chat
    fake.from_user = callback_query.from_user
    fake.text = "/start"

    # Call /start handler to re-send the start screen
    try:
        await start_private(client, fake)
    except Exception as e:
        # fallback: send a plain start text if something fails
        try:
            primary_admin = ADMIN_ID[0] if isinstance(ADMIN_ID, (list, tuple)) else ADMIN_ID
            is_admin = callback_query.from_user.id == primary_admin
            start_text = get_start_text(is_admin)
            await client.send_message(
                callback_query.message.chat.id,
                start_text,
                parse_mode=ParseMode.HTML,
                reply_markup=start_buttons,
                disable_web_page_preview=True
            )
        except:
            await callback_query.answer("Couldn't open start.", show_alert=True)

# ====== Broadcast ======
@app.on_message(filters.command("broadcast") & filters.private)
async def broadcast_message(client, message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply_text("🚫 Only admin can use broadcast.")

    if len(message.command) < 2:
        return await message.reply_text("⚠️ Usage: `/broadcast your message`")

    text = message.text.split(" ", 1)[1]
    sent, failed = 0, 0

    await message.reply_text("📢 Broadcast started...")

    users = users_col.find()
    for user in users:
        uid = user["_id"]
        try:
            await client.send_message(uid, text)
            sent += 1
            await asyncio.sleep(0.05)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            continue
        except Exception:
            failed += 1
            users_col.delete_one({"_id": uid})  # remove inactive user

    await client.send_message(
        ADMIN_ID,
        f"✅ Broadcast completed!\n\n📨 Sent: {sent}\n❌ Failed: {failed}"
    )

# ====== /setgroup ======
@app.on_message(filters.command("setgroup") & filters.private)
async def set_group_timer(client, message):
    global GROUP_DELETE_AFTER
    if message.from_user.id != ADMIN_ID:
        return await message.reply_text("🚫 Only admin can change group auto-delete time.")
    try:
        secs = int(message.text.split()[1])
        GROUP_DELETE_AFTER = secs
        await message.reply_text(f"✅ Group auto-delete updated → {secs} seconds.")
    except (IndexError, ValueError):
        await message.reply_text("⚠️ Usage: `/setgroup 20`", quote=True)

# ====== /alive ======
@app.on_message(filters.command("alive") & filters.group)
async def alive_group(client, message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status in ["administrator", "creator"]:
        sent = await message.reply_text(f"🤖 Alive!\n🕒 Delete timer: {GROUP_DELETE_AFTER}s")
        await asyncio.sleep(5)
        try:
            await sent.delete()
        except:
            pass

# ====== /ping ======
@app.on_message(filters.command("ping"))
async def ping(client, message):
    start = time.time()
    sent = await message.reply_text("🏓 Pinging...")
    end = time.time()
    await sent.edit_text(f"🏓 Pong!\n⚡ {round((end-start)*1000)} ms")

# ====== /delall ======
@app.on_message(filters.command("delall") & filters.private)
async def delete_all_in_group(client, message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply_text("🚫 Only admin can use this command.")
    try:
        chat_id = int(message.text.split()[1])
    except (IndexError, ValueError):
        return await message.reply_text("⚠️ Usage: `/delall <chat_id>`")
    await message.reply_text(f"🧹 Deleting last 500 messages in `{chat_id}`...")
    try:
        for i in range(1, 501, 100):
            try:
                await client.delete_messages(chat_id, list(range(i, i+100)))
            except Exception:
                continue
        await message.reply_text("✅ Deleted last 500 messages.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

# ====== Auto Delete + Punishment ======
@app.on_message(filters.group)
async def auto_delete_group(client, message):
    text = message.text or message.caption or ""
    if (
        message.forward_from or message.forward_from_chat or
        "http://" in text or "https://" in text or "t.me/" in text or
        re.search(r"@\w+", text) or
        any(word.lower() in text.lower() for word in BANNED_WORDS) or
        len(text) > MAX_MESSAGE_LENGTH or
        emoji_pattern.search(text)
    ):
        try:
            await message.delete()
            until_date = datetime.now(timezone.utc) + timedelta(hours=2)
            await client.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=message.from_user.id,
                permissions=ChatPermissions(),
                until_date=until_date
            )
            warn = await message.reply_text(
                f"🚫 {message.from_user.mention} muted for 2 hours (rule violation)."
            )
            await asyncio.sleep(5)
            await warn.delete()
        except (MessageDeleteForbidden, RPCError):
            pass
        return
    asyncio.create_task(delete_later(message, GROUP_DELETE_AFTER))

async def delete_later(message, delay):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except (MessageDeleteForbidden, RPCError):
        pass

# ====== Total Users ======
@app.on_message(filters.command("totalusers") & filters.private)
async def total_users(client, message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply_text("🚫 Only admin can use this command.")
    
    total = users_col.count_documents({})
    await message.reply_text(f"👥 Total Users: {total}")

# ====== Start Bot ======
print("🤖 Auto Delete Bot with Punishment + MongoDB started...")
app.run()
