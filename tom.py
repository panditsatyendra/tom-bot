import logging
import os
import json
import re
import asyncio
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ChatAction

# --- CONFIGURATION ---
BOT_TOKEN = "8566036790:AAEiTX8EI9NjyxvxZBQUOxlq0xnNieEX-sM"
ADMIN_ID = 6169350961 
USERS_FILE = "users_data.json"
BRANDING = "🛡️ *Powered by TOM Core*"

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

# --- PUBLIC COMMANDS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid_str = str(user.id)

    if user.id in data["banned"]:
        await update.message.reply_text("🚫 *Access Denied!*\nYou are permanently banned from using this bot.", parse_mode='Markdown')
        return

    # Check if user is new for Admin Notification
    is_new_user = uid_str not in data["users"]

    # Update database
    username_display = f"@{user.username}" if user.username else "None"
    data["users"][uid_str] = {"name": user.first_name, "username": username_display}
    save_data(data)

    # Notify Admin if it's a new user
    if is_new_user and user.id != ADMIN_ID:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID, 
                text=f"🔔 *NEW USER ALERT*\n👤 Name: {user.first_name}\n🆔 ID: `{user.id}`\n🔗 Username: {username_display}",
                parse_mode='Markdown'
            )
        except:
            pass

    welcome_text = (
        f"🚀 *SYSTEM ONLINE* 🤖\n\n"
        f"Hello *{user.first_name}*! Welcome to the official support bot. "
        f"Send me a direct message or use the buttons below to interact with the admin.\n\n"
        f"✨ *Available Commands:*\n"
        f"👤 /me - Check your profile status\n"
        f"🆘 /help - Get usage instructions\n"
        f"🏓 /ping - Check system latency\n\n"
        f"{BRANDING}"
    )
    
    keyboard = [[InlineKeyboardButton("👨‍💻 Contact Developer", url=f"tg://user?id={ADMIN_ID}")]]
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "❓ *HELP & SUPPORT MENU*\n\n"
        "• *Direct Chat:* Simply send any message, photo, or document here, and it will be securely forwarded to the admin.\n"
        "• */me:* Displays your unique ID and account standing.\n"
        "• */ping:* Checks the bot's response time.\n"
        "• */start:* Refreshes the bot interaction.\n\n"
        "⚠️ *Strict Policy:* Spamming or abusive messages will result in an immediate and permanent ban.\n\n"
        f"{BRANDING}"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    status = "Banned 🚫" if user.id in data["banned"] else "Active ✅"
    text = (
        f"✨ *YOUR ACCOUNT PROFILE* ✨\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📛 *Name:* {user.first_name}\n"
        f"🆔 *ID:* `{user.id}`\n"
        f"🚦 *Status:* {status}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"{BRANDING}"
    )
    await update.message.reply_text(text, parse_mode='Markdown')

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time = time.time()
    msg = await update.message.reply_text("🔄 Pinging system...", parse_mode='Markdown')
    end_time = time.time()
    ping_time = round((end_time - start_time) * 1000)
    await msg.edit_text(f"🏓 *Pong!*\nLatency: `{ping_time}ms`\n\n{BRANDING}", parse_mode='Markdown')

# --- ADMIN COMMANDS ---

async def maintenance_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    data["maintenance"] = True
    save_data(data)
    await update.message.reply_text("🚧 *Maintenance Mode:* `ON`\nUsers can no longer send messages.", parse_mode='Markdown')

async def maintenance_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    data["maintenance"] = False
    save_data(data)
    await update.message.reply_text("✅ *Maintenance Mode:* `OFF`\nSystem is fully operational.", parse_mode='Markdown')

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    m_status = "ON 🚧" if data.get("maintenance") else "OFF ✅"
    total = len(data["users"])
    
    stats_text = (
        f"📊 *ADMIN DASHBOARD*\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛠 *Maintenance:* {m_status}\n"
        f"👥 *Total Users:* {total}\n"
        f"🚫 *Banned Users:* {len(data['banned'])}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"{BRANDING}"
    )
    keyboard = [[InlineKeyboardButton("📜 View All Users", callback_data="get_list")]]
    await update.message.reply_text(stats_text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def userinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not context.args:
        await update.message.reply_text("❌ *Usage:* `/userinfo <ID>`", parse_mode='Markdown')
        return
    
    target_id = context.args[0]
    if target_id in data["users"]:
        u_data = data["users"][target_id]
        status = "Banned 🚫" if int(target_id) in data["banned"] else "Active ✅"
        await update.message.reply_text(
            f"🔍 *USER LOOKUP*\n"
            f"🆔 ID: `{target_id}`\n"
            f"📛 Name: {u_data['name']}\n"
            f"🔗 Username: {u_data['username']}\n"
            f"🚦 Status: {status}", 
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ User not found in database.", parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "get_list" and query.from_user.id == ADMIN_ID:
        user_list = "📜 *USER LIST:*\n\n"
        for uid, info in data["users"].items():
            status = "🚫" if int(uid) in data["banned"] else "✅"
            user_list += f"{status} `{uid}` | {info['name']}\n"
        await query.message.reply_text(user_list[:4096], parse_mode='Markdown')
    await query.answer()

async def send_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    
    is_reply = bool(update.message.reply_to_message)
    msg_text = " ".join(context.args)

    if not is_reply and not msg_text:
        await update.message.reply_text("❌ *Usage:* Reply to a message with `/all` OR type `/all <message>`", parse_mode='Markdown')
        return
    
    count = 0
    await update.message.reply_text("⏳ *Broadcasting message...*")
    
    for uid in list(data["users"].keys()):
        if int(uid) not in data["banned"]:
            try:
                if is_reply:
                    await update.message.reply_to_message.copy(chat_id=int(uid))
                else:
                    await context.bot.send_message(chat_id=int(uid), text=f"📢 *BROADCAST*\n\n{msg_text}\n\n{BRANDING}", parse_mode='Markdown')
                count += 1
                await asyncio.sleep(0.05) # To avoid Telegram API rate limits
            except Exception as e:
                continue
                
    await update.message.reply_text(f"✅ *Broadcast Complete!*\nSuccessfully sent to `{count}` users.", parse_mode='Markdown')

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not update.message.reply_to_message: 
        await update.message.reply_text("❌ Please reply to the user's message to ban them.")
        return
        
    target_id = extract_id(update.message.reply_to_message.text or update.message.reply_to_message.caption)
    if target_id and target_id not in data["banned"]:
        data["banned"].append(target_id)
        save_data(data)
        await update.message.reply_text(f"🚫 User `{target_id}` has been banned.", parse_mode='Markdown')
        try:
            await context.bot.send_message(chat_id=target_id, text="🚫 *You have been banned by the Admin.*", parse_mode='Markdown')
        except: pass

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not update.message.reply_to_message: return
    
    target_id = extract_id(update.message.reply_to_message.text or update.message.reply_to_message.caption)
    if target_id and target_id in data["banned"]:
        data["banned"].remove(target_id)
        save_data(data)
        await update.message.reply_text(f"✅ User `{target_id}` has been unbanned.", parse_mode='Markdown')
        try:
            await context.bot.send_message(chat_id=target_id, text="✅ *You have been unbanned by the Admin. You can use the bot again.*", parse_mode='Markdown')
        except: pass

# --- MAIN INCOMING MESSAGE HANDLER ---
async def handle_incoming(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # 1. Ban Check
    if user.id in data["banned"] and user.id != ADMIN_ID:
        return

    # 2. Maintenance Check
    if data.get("maintenance") and user.id != ADMIN_ID:
        await update.message.reply_text("🚧 *System is currently under maintenance. Please try again later.*", parse_mode='Markdown')
        return

    # Show typing action while processing
    await context.bot.send_chat_action(chat_id=user.id, action=ChatAction.TYPING)

    # 3. Admin Reply Logic
    if user.id == ADMIN_ID:
        if update.message.reply_to_message:
            # Ignore command replies to prevent breaking logic
            if update.message.text and update.message.text.startswith("/"): return
            
            target_id = extract_id(update.message.reply_to_message.text or update.message.reply_to_message.caption)
            if target_id:
                try:
                    await update.message.copy(chat_id=target_id)
                    await update.message.reply_text("⚡ *Message delivered successfully!*", parse_mode='Markdown')
                    return
                except Exception as e:
                    await update.message.reply_text(f"❌ *Delivery failed.* User might have blocked the bot.", parse_mode='Markdown')
        return # Standard admin messages (non-replies) are ignored

    # 4. User Forwarding Logic (Only for non-admins)
    header = (
        f"📩 *NEW SUPPORT TICKET*\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *From:* {user.first_name}\n"
        f"🆔 *ID:* `{user.id}`\n"
        f"⚡ *Profile:* [Click Here](tg://user?id={user.id})\n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )
    
    # Send user info header to admin, then copy the actual message content
    await context.bot.send_message(chat_id=ADMIN_ID, text=header, parse_mode='Markdown')
    await update.message.copy(chat_id=ADMIN_ID)
    await update.message.reply_text("🚀 *Message sent!* The Admin will reply to you shortly.", parse_mode='Markdown')

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Register Commands (Must be at the top)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("me", me))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ping", ping))
    
    # Admin Commands
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("userinfo", userinfo))
    app.add_handler(CommandHandler("all", send_all))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("maintenance_on", maintenance_on))
    app.add_handler(CommandHandler("maintenance_off", maintenance_off))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # Message Handler (Must be after commands)
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_incoming))

    print("🛡️ TOM Core System is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
