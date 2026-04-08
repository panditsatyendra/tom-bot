import logging
import os
import json
import re
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- CONFIGURATION ---
BOT_TOKEN = "8566036790:AAEiTX8EI9NjyxvxZBQUOxlq0xnNieEX-sM"
ADMIN_ID = 6169350961 
USERS_FILE = "users_data.json"

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DATA MANAGEMENT ---
def load_data():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                content = json.load(f)
                content["banned"] = [int(i) for i in content.get("banned", [])]
                if "users" not in content: content["users"] = {}
                if "maintenance" not in content: content["maintenance"] = False
                return content
        except Exception as e:
            logger.error(f"Error loading JSON: {e}")
    return {"users": {}, "banned": [], "maintenance": False}

def save_data(data_to_save):
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(data_to_save, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving JSON: {e}")

# Global data variable for faster access
data = load_data()

def extract_id(text):
    if not text: return None
    match = re.search(r"ID:\s*(\d+)", text)
    return int(match.group(1)) if match else None

# --- DECORATORS / HELPERS ---
def is_admin(user_id):
    return user_id == ADMIN_ID

# --- COMMANDS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid_str = str(user.id)

    if user.id in data["banned"]:
        await update.message.reply_text("🚫 **Access Denied!**\nYou are permanently banned.")
        return

    if data.get("maintenance") and not is_admin(user.id):
        await update.message.reply_text("🛠 **Maintenance Mode**\nHum kuch naya update kar rahe hain. Jaldi wapas aayenge! 😎")
        return

    # User registration
    username_display = f"@{user.username}" if user.username else "None"
    data["users"][uid_str] = {"name": user.first_name, "username": username_display}
    save_data(data)

    welcome_text = (
        f"👋 **Hello {user.first_name}!**\n\n"
        "Welcome to the **TOM Bot 🤖**\n"
        "Aap mujhe koi bhi message bhej sakte hain, "
        "Admin aapko jaldi reply karega.\n\n"
        "✨ **Available Commands:**\n"
        "👤 /me - Meri details\n"
        "🆘 /help - Help mangne ke liye"
    )
    
    keyboard = [[InlineKeyboardButton("Support 💬", url="https://t.me/your_username_here")]] # Apna link daal sakte hain
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    status = "Banned 🚫" if user.id in data["banned"] else "Active ✅"
    text = (
        f"👤 **USER PROFILE**\n\n"
        f"📛 **Name:** {user.first_name}\n"
        f"🆔 **ID:** `{user.id}`\n"
        f"🔗 **Username:** @{user.username}\n"
        f"🚦 **Status:** {status}"
    )
    await update.message.reply_text(text, parse_mode='Markdown')

async def maintenance_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    data["maintenance"] = True
    save_data(data)
    await update.message.reply_text("🚧 **Maintenance Mode: [ON]**\nAb sirf admin bot use kar sakta hai.")

async def maintenance_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    data["maintenance"] = False
    save_data(data)
    await update.message.reply_text("✅ **Maintenance Mode: [OFF]**\nSabhi users ke liye bot open hai.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    m_status = "ON 🚧" if data.get("maintenance") else "OFF ✅"
    total_users = len(data["users"])
    banned_users = len(data["banned"])
    
    stats_text = (
        f"📊 **BOT STATISTICS**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🛠 **Maintenance:** {m_status}\n"
        f"👥 **Total Users:** {total_users}\n"
        f"🚫 **Banned:** {banned_users}\n"
        f"🟢 **Active:** {total_users - banned_users}\n"
    )
    
    # Inline button for detailed user list to avoid long messages
    keyboard = [[InlineKeyboardButton("Get User List 📜", callback_data="get_list")]]
    await update.message.reply_text(stats_text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "get_list" and is_admin(query.from_user.id):
        user_list = "📜 **USER LIST:**\n\n"
        for uid, info in data["users"].items():
            status = "🚫" if int(uid) in data["banned"] else "✅"
            user_list += f"{status} `{uid}` | {info['name']}\n"
        await query.message.reply_text(user_list[:4096], parse_mode='Markdown')

async def send_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text("❌ Format: `/all Your message here`", parse_mode='Markdown')
        return
    
    status_msg = await update.message.reply_text("🚀 Sending announcement...")
    count = 0
    
    for uid in list(data["users"].keys()):
        try:
            if int(uid) not in data["banned"]:
                await context.bot.send_message(chat_id=int(uid), text=f"📢 **ANNOUNCEMENT**\n\n{msg}", parse_mode='Markdown')
                count += 1
                if count % 10 == 0: # Update status every 10 users to avoid lag
                    await status_msg.edit_text(f"🚀 Sending... ({count} users reached)")
        except Exception: continue
    
    await status_msg.edit_text(f"✅ **Success!**\nMessage delivered to {count} users.")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Reply to an admin log to ban the user.")
        return
    
    target_id = extract_id(update.message.reply_to_message.text or update.message.reply_to_message.caption)
    if target_id:
        if target_id not in data["banned"]:
            data["banned"].append(target_id)
            save_data(data)
            try: await context.bot.send_message(chat_id=target_id, text="🚫 **You have been banned by the admin.**")
            except: pass
        await update.message.reply_text(f"🚫 User `{target_id}` is now BANNED.", parse_mode='Markdown')

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Reply to an admin log to unban.")
        return
    
    target_id = extract_id(update.message.reply_to_message.text or update.message.reply_to_message.caption)
    if target_id and target_id in data["banned"]:
        data["banned"].remove(target_id)
        save_data(data)
        try: await context.bot.send_message(chat_id=target_id, text="✅ **Good news! You have been unbanned.**")
        except: pass
        await update.message.reply_text(f"✅ User `{target_id}` is now UNBANNED.", parse_mode='Markdown')

# --- MESSAGE HANDLER ---
async def handle_incoming(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if user.id in data["banned"] and not is_admin(user.id):
        return # Ignore banned users silently or send reply

    if data.get("maintenance") and not is_admin(user.id):
        await update.message.reply_text("🛠 Under Maintenance.")
        return

    # Admin Reply Logic
    if is_admin(user.id):
        if update.message.reply_to_message:
            # Skip if admin is trying to use a command on a reply
            if update.message.text and update.message.text.startswith("/"): return
            
            target_id = extract_id(update.message.reply_to_message.text or update.message.reply_to_message.caption)
            if target_id:
                try:
                    await update.message.copy(chat_id=target_id)
                    await update.message.reply_text("🚀 **Replied Successfully!**", parse_mode='Markdown')
                except Exception as e:
                    await update.message.reply_text(f"❌ Failed to send: {e}")
        return

    # Forwarding to Admin
    uid_str = str(user.id)
    username_disp = f"@{user.username}" if user.username else "None"
    
    # Update data in memory
    data["users"][uid_str] = {"name": user.first_name, "username": username_disp}
    
    header = (
        f"📩 **NEW MESSAGE RECEIVED**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 **Name:** {user.first_name}\n"
        f"🆔 **ID:** `{user.id}`\n"
        f"🔗 **User:** {username_disp}\n"
        f"⚡ [Open Profile](tg://user?id={user.id})\n"
        f"━━━━━━━━━━━━━━━"
    )
    
    # Send header then the content
    await context.bot.send_message(chat_id=ADMIN_ID, text=header, parse_mode='Markdown')
    await update.message.copy(chat_id=ADMIN_ID)
    await update.message.reply_text("✅ **Sent!** Admin ko aapka message mil gaya hai.")

def main():
    PORT = int(os.environ.get('PORT', 8443))
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("me", me))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("all", send_all))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("maintenance_on", maintenance_on))
    app.add_handler(CommandHandler("maintenance_off", maintenance_off))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_incoming))

    # Notification to Admin that bot started
    async def on_startup(application):
        try: await application.bot.send_message(chat_id=ADMIN_ID, text="🚀 **Bot has been restarted and is now ONLINE!**")
        except: pass

    RENDER_URL = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if RENDER_URL:
        app.run_webhook(listen="0.0.0.0", port=PORT, url_path=BOT_TOKEN, webhook_url=f"https://{RENDER_URL}/{BOT_TOKEN}")
    else: 
        logger.info("Bot started via Polling...")
        app.run_polling()

if __name__ == '__main__':
    main()
