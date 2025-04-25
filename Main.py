from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ParseMode
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters,
    CallbackContext, CallbackQueryHandler, ConversationHandler
)
import random
from enum import Enum
from collections import defaultdict, deque
import time
import sqlite3
from datetime import datetime

# -------------------- تنظیمات پایه --------------------
TOKEN = "7854454220:AAHxBfkpUu6Gqt5LMtKHjSqAmvFW4hoZ2Bk"
DB_NAME = "games_bot.db"
ADMINS = [6961529186]  # آیدی ادمین‌ها
WARN_LIMIT = 3

# -------------------- انوم حالت‌ها --------------------
class GameMode(Enum):
    # بازی‌ها (همان 20 بازی قبلی)
    pass

# -------------------- کلاس مدیریت دیتابیس --------------------
class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        # جداول بازی‌ها
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_settings (
                chat_id INTEGER PRIMARY KEY,
                welcome_msg TEXT,
                rules TEXT,
                lang TEXT DEFAULT 'fa',
                warn_count INTEGER DEFAULT 0
            )
        """)
        # جداول مدیریتی
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_warns (
                user_id INTEGER,
                chat_id INTEGER,
                count INTEGER,
                PRIMARY KEY (user_id, chat_id)
            )
        """)
        self.conn.commit()

# -------------------- سیستم مدیریت گروه --------------------
class GroupManager:
    @staticmethod
    def is_admin(update: Update, context: CallbackContext):
        user = update.effective_user
        chat = update.effective_chat
        if user.id in ADMINS:
            return True
        member = chat.get_member(user.id)
        return member.status in ['administrator', 'creator']

    @staticmethod
    def ban_user(update: Update, context: CallbackContext):
        if not GroupManager.is_admin(update, context):
            update.message.reply_text("❌ فقط ادمین‌ها می‌توانند استفاده کنند!")
            return

        try:
            user_id = int(context.args[0]) if context.args else update.message.reply_to_message.from_user.id
            reason = " ".join(context.args[1:]) if len(context.args) > 1 else "بدون دلیل"
            
            context.bot.ban_chat_member(
                chat_id=update.effective_chat.id,
                user_id=user_id
            )
            update.message.reply_text(
                f"🚫 کاربر {user_id} مسدود شد!\nدلیل: {reason}",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            update.message.reply_text(f"❌ خطا: {str(e)}")

    @staticmethod
    def set_rules(update: Update, context: CallbackContext):
        if not GroupManager.is_admin(update, context):
            update.message.reply_text("❌ فقط ادمین‌ها می‌توانند استفاده کنند!")
            return

        rules = " ".join(context.args)
        db = Database()
        db.conn.execute(
            "INSERT OR REPLACE INTO group_settings (chat_id, rules) VALUES (?, ?)",
            (update.effective_chat.id, rules)
        )
        db.conn.commit()
        update.message.reply_text("✅ قوانین گروه با موفقیت به‌روزرسانی شد!")

# -------------------- کلاس‌های بازی‌ها (همان 20 بازی قبلی) --------------------
# ... (کدهای بازی‌ها بدون تغییر از پیام‌های قبلی)

# -------------------- دستورات مدیریتی --------------------
def setup_management_handlers(dispatcher):
    # دستورات مدیریتی
    dispatcher.add_handler(CommandHandler("ban", GroupManager.ban_user))
    dispatcher.add_handler(CommandHandler("unban", lambda u,c: GroupManager.ban_user(u,c, unban=True)))
    dispatcher.add_handler(CommandHandler("mute", mute_user))
    dispatcher.add_handler(CommandHandler("warn", warn_user))
    dispatcher.add_handler(CommandHandler("setrules", GroupManager.set_rules))
    dispatcher.add_handler(CommandHandler("rules", show_rules))
    dispatcher.add_handler(CommandHandler("clean", clean_messages))
    
    # دستورات اطلاعاتی
    dispatcher.add_handler(CommandHandler("info", user_info))
    dispatcher.add_handler(CommandHandler("mods", list_admins))
    dispatcher.add_handler(CommandHandler("stats", group_stats))

# -------------------- دستورات بازی‌ها --------------------
def setup_game_handlers(dispatcher):
    # دستورات بازی‌ها
    dispatcher.add_handler(CommandHandler("games", games_menu))
    dispatcher.add_handler(CallbackQueryHandler(game_selection_handler, pattern="^game_"))
    
    # هندلرهای مخصوص هر بازی
    dispatcher.add_handler(MessageHandler(
        Filters.text & ~Filters.command, 
        handle_game_actions
    ))

# -------------------- تابع اصلی --------------------
def main():
    # ایجاد دیتابیس و جداول
    db = Database()
    
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # تنظیم دستورات
    setup_management_handlers(dispatcher)
    setup_game_handlers(dispatcher)

    # دستورات پایه
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
