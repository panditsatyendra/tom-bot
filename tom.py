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

data = load_data()

def extract_id(text):
    if not text: return None
    match = re.search(r"ID:\s*(\d+)", text)
    return int(match.group(1)) if match else None

# --- COMMANDS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid_str = str(user.id)

    if user.id in data["banned"]:
        await update.message.reply_text("🚫 **Access Denied!**\nYou are banned.")
        return

    # Update database
    username_display = f"@{user.username}" if user.username else "None"
    data["users"][uid_str] = {"name": user.first_name, "username": username_display}
    save_data(data)

    welcome_text = (
        f"🚀 **TOM BOT ACTIVE** 🤖\n\n"
        f"Hi **{user.first_name}**, mere saath chat karne ke liye niche button pe click karein ya seedha message bhejein.\n\n"
        "✨ **User Menu:**\n"
        "👤 /me - Check My Profile\n"
        "🆘 /help - Get Help"
    )
    
    keyboard = [[InlineKeyboardButton("Developer 👨‍💻", url="tg://user?id=6169350961")]]
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "❓ **HELP MENU**\n\n"
        "• **Direct Chat:** Just send any message/photo, it will reach the admin.\n"
        "• **/me:** Shows your unique ID and account status.\n"
        "• **/start:** Restart the bot interaction.\n\n"
        "⚠️ *Note: Abusive messages will lead to a permanent ban.*"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    status = "Banned 🚫" if user.id in data["banned"] else "Active ✅"
    text = (
        f"✨ **YOUR ACCOUNT INFO** ✨\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📛 **Name:** {user.first_name}\n"
        f"🆔 **ID:** `{user.id}`\n"
        f"🚦 **Status:** {status}\n"
        f"━━━━━━━━━━━━━━━"
    )
    await update.message.reply_text(text, parse_mode='Markdown')

# --- ADMIN COMMANDS ---

async def maintenance_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    data["maintenance"] = True
    save_data(data)
    await update.message.reply_text("🚧 **Maintenance Mode: ON**")

async def maintenance_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    data["maintenance"] = False
    save_data(data)
    await update.message.reply_text("✅ **Maintenance Mode: OFF**")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    m_status = "ON 🚧" if data.get("maintenance") else "OFF ✅"
    total = len(data["users"])
    
    stats_text = (
        f"📊 **ADMIN DASHBOARD**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🛠 **M-Mode:** {m_status}\n"
        f"👥 **Total Users:** {total}\n"
        f"🚫 **Banned:** {len(data['banned'])}\n"
    )
    keyboard = [[InlineKeyboardButton("View All Users 📜", callback_data="get_list")]]
    await update.message.reply_text(stats_text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "get_list" and query.from_user.id == ADMIN_ID:
        user_list = "📜 **USER LIST:**\n\n"
        for uid, info in data["users"].items():
            status = "🚫" if int(uid) in data["banned"] else "✅"
            user_list += f"{status} `{uid}` | {info['name']}\n"
        await query.message.reply_text(user_list[:4096], parse_mode='Markdown')
    await query.answer()

async def send_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text("❌ Use: `/all Hello Everyone`", parse_mode='Markdown')
        return
    
    count = 0
    for uid in list(data["users"].keys()):
        try:
            if int(uid) not in data["banned"]:
                await context.bot.send_message(chat_id=int(uid), text=f"📢 **BROADCAST**\n\n{msg}", parse_mode='Markdown')
                count += 1
                await asyncio.sleep(0.05) # Flood avoid karne ke liye
        except: continue
    await update.message.reply_text(f"✅ Sent to {count} users.")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not update.message.reply_to_message: return
    target_id = extract_id(update.message.reply_to_message.text or update.message.reply_to_message.caption)
    if target_id and target_id not in data["banned"]:
        data["banned"].append(target_id)
        save_data(data)
        await update.message.reply_text(f"🚫 User `{target_id}` Banned.")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not update.message.reply_to_message: return
    target_id = extract_id(update.message.reply_to_message.text or update.message.reply_to_message.caption)
    if target_id and target_id in data["banned"]:
        data["banned"].remove(target_id)
        save_data(data)
        await update.message.reply_text(f"✅ User `{target_id}` Unbanned.")

# --- MAIN HANDLER ---
async def handle_incoming(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # 1. Ban Check
    if user.id in data["banned"] and user.id != ADMIN_ID:
        return

    # 2. Maintenance Check
    if data.get("maintenance") and user.id != ADMIN_ID:
        await update.message.reply_text("🛠 **Bot under maintenance.**")
        return

    # 3. Admin Reply Logic
    if user.id == ADMIN_ID:
        if update.message.reply_to_message:
            # If it's a command, let command handlers handle it
            if update.message.text and update.message.text.startswith("/"): return
            
            target_id = extract_id(update.message.reply_to_message.text or update.message.reply_to_message.caption)
            if target_id:
                try:
                    await update.message.copy(chat_id=target_id)
                    await update.message.reply_text("⚡ **Replied!**")
                    return
                except: pass
        return # Admin messages that are not replies won't be forwarded to anyone

    # 4. User Forwarding Logic (Only for non-admins)
    header = (
        f"📩 **NEW MSG**\n"
        f"👤 {user.first_name}\n"
        f"🆔 ID: `{user.id}`\n"
        f"⚡ [Link](tg://user?id={user.id})"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=header, parse_mode='Markdown')
    await update.message.copy(chat_id=ADMIN_ID)
    await update.message.reply_text("🚀 **Sent!** Owner will reply soon.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Commands (Sabse upar honi chahiye)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("me", me))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("all", send_all))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("maintenance_on", maintenance_on))
    app.add_handler(CommandHandler("maintenance_off", maintenance_off))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # Message Handler (Commands ke baad)
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_incoming))

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
