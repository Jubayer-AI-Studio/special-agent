"""
Special Agent - Jubayer Telegram Gateway
Connects Jubayer's smartphone to the AI Job Hunter with Human-In-The-Loop approval cards.
"""

import os
import asyncio
from typing import Optional, Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from backend.database.db import (
    get_dashboard_analytics,
    get_user_profile,
    get_application_with_job,
    update_application_status
)
from backend.gateway.email_sender import email_dispatcher

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8527137526:AAEEp--H13id9P-avLXS3xkhvJp1BYSwjgc")
OPERATOR_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

class TelegramGatekeeper:
    def __init__(self, token: Optional[str] = None):
        self.token = token or TELEGRAM_TOKEN
        self.app = None
        if self.token:
            self.app = Application.builder().token(self.token).build()
            self._register_handlers()

    def _register_handlers(self):
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("scan", self.cmd_scan))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_chat))

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        # Persist chat_id in environment
        os.environ["TELEGRAM_CHAT_ID"] = str(chat_id)
        
        profile = get_user_profile()
        name = profile.get("name", "Jubayer")
        title = profile.get("title", "AI Specialist")

        welcome_text = (
            f"👑 **স্বাগতম, {name} ভাই!**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"আমি আপনার পার্সোনাল **AI Job Hunter & Career Agent**।\n"
            f"📱 আপনার মোবাইল টেলিগ্রাম ব্রিজ সফলভাবে সংযুক্ত হয়েছে!\n"
            f"📌 আপনার চ্যাট আইডি (Chat ID): `{chat_id}`\n\n"
            f"💼 **অপারেটর প্রোফাইল:**\n"
            f"• পদবী: `{title}`\n"
            f"• পোর্টফোলিও: [Vercel Portfolio]({profile.get('portfolio_url')})\n"
            f"• গিটহাব: [GitHub Studio]({profile.get('github_url')})\n"
            f"• প্রেরক ইমেইল: `{profile.get('email')}`\n\n"
            f"🚀 **আমি আপনার জন্য কী করব?**\n"
            f"১. ২৪/৭ গ্লোবাল রিমোট জব ও ক্লায়েন্ট খুঁজব।\n"
            f"২. হার্মিস ব্রেইন দিয়ে আপনার পোর্টফোলিওসহ কভার লেটার লিখব।\n"
            f"৩. আপনার মোবাইলে নক দিয়ে অনুমতি চাইব।\n"
            f"৪. আপনি 'অনুমোদন' বাটনে চাপলে সরাসরি আপনার জিমেইল থেকে ইমেইল পাঠাব।\n\n"
            f"👉 নতুন চাকরির সন্ধান করতে চাপুন: `/scan`"
        )
        await update.message.reply_text(welcome_text, parse_mode="Markdown", disable_web_page_preview=True)

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        analytics = get_dashboard_analytics()
        text = (
            f"📊 **স্পেশাল এজেন্ট ড্যাশবোর্ড রিপোর্ট**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📡 সিস্টেম স্টেটাস: **সক্রিয় (Active 24/7)**\n"
            f"🎯 স্ক্যানকৃত মোট জব: `{analytics['total_jobs_scanned']}`\n"
            f"⏳ সিদ্ধান্তের অপেক্ষায় (Pending): `{analytics['pending_reviews']}`\n"
            f"✅ অনুমোদিত ও প্রস্তুত: `{analytics['approved_ready']}`\n"
            f"🚀 পাঠানো অ্যাপ্লিকেশন: `{analytics['applications_sent']}`\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"নতুন কাজ সার্চ করতে `/scan` লিখুন।"
        )
        await update.message.reply_text(text, parse_mode="Markdown")

    async def cmd_scan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🔍 গ্লোবাল রিমোট জব পোর্টালগুলোতে স্ক্যান শুরু হয়েছে... অনুগ্রহ করে অপেক্ষা করুন।")
        from backend.skills.job_radar import job_radar
        from backend.brain.hermes_brain import hermes_brain

        discovered_jobs = await job_radar.scan_all_sources()
        if not discovered_jobs:
            await update.message.reply_text("ℹ️ এই মুহূর্তে নতুন কোনো আনপ্রসেসড জব পাওয়া যায়নি। শীঘ্রই আবার স্ক্যান করা হবে।")
            return

        await update.message.reply_text(f"🎯 মোট {len(discovered_jobs)}টি নতুন প্রাসঙ্গিক রিমোট জব পাওয়া গেছে! হার্মিস ব্রেইন দিয়ে কভার লেটার তৈরি করে পাঠানো হচ্ছে...")
        
        for job in discovered_jobs[:3]: # Send top 3 immediately
            app_data = hermes_brain.draft_application(job)
            await self.send_approval_card(update.effective_chat.id, app_data)

    async def send_approval_card(self, chat_id: int, app_data: Dict[str, Any]):
        title = app_data.get("title", "Remote Developer")
        company = app_data.get("company_name", "Tech Client")
        recruiter = app_data.get("recruiter_email", "apply@company.com")
        salary = app_data.get("salary_range", "Competitive")
        location = app_data.get("location", "Worldwide Remote")
        subject = app_data.get("subject", "")
        body = app_data.get("email_body", "")
        app_id = app_data.get("application_id", 0)

        card_text = (
            f"🚨 **নতুন চাকরির সুযোগ পাওয়া গেছে!**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🏢 **কোম্পানি:** {company}\n"
            f"📌 **পদ:** {title}\n"
            f"💰 **বেতন:** {salary}\n"
            f"🌍 **লোকেশন:** {location}\n"
            f"✉️ **প্রাপক ইমেইল:** `{recruiter}`\n"
            f"🔗 [আবেদন বা কাজের মূল লিংক]({app_data.get('apply_url')})\n\n"
            f"📝 **হার্মিস ৩-এর প্রস্তুতকৃত ড্রাফট ইমেইল:**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"**বিষয়:** `{subject}`\n\n"
            f"{body}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"আপনি কি এই ইমেইলটি রিক্রুটারের কাছে পাঠাতে চান?"
        )

        keyboard = [
            [
                InlineKeyboardButton("✅ অনুমোদন করুন ও সেন্ড করুন", callback_data=f"send_app_{app_id}"),
                InlineKeyboardButton("❌ বাতিল করুন", callback_data=f"reject_app_{app_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if self.app:
            await self.app.bot.send_message(
                chat_id=chat_id,
                text=card_text,
                reply_markup=reply_markup,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        data = query.data
        if data.startswith("send_app_"):
            app_id = int(data.split("_")[2])
            app_info = get_application_with_job(app_id)
            if app_info:
                result = email_dispatcher.send_application_email(
                    application_id=app_id,
                    recipient_email=app_info.get("recruiter_email", "apply@client.com"),
                    subject=app_info.get("subject", "Application for Remote Role"),
                    body=app_info.get("email_body", "")
                )
                await query.edit_message_text(
                    text=f"{query.message.text}\n\n━━━━━━━━━━━━━━━━━━━\n✅ **অনুমোদিত ও সফলভাবে কার্যকর করা হয়েছে!**\n{result.get('message')}",
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
        elif data.startswith("reject_app_"):
            app_id = int(data.split("_")[2])
            update_application_status(app_id, "rejected")
            await query.edit_message_text(
                text=f"{query.message.text}\n\n━━━━━━━━━━━━━━━━━━━\n❌ **আবেদনটি বাতিল করা হয়েছে (Rejected)।**",
                parse_mode="Markdown",
                disable_web_page_preview=True
            )

    async def handle_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        await update.message.reply_text(
            f"🤖 জুবায়ের ভাই, আমি আপনার মেসেজ পেয়েছি: '{text}'।\n"
            f"কাজের খোঁজ পেতে `/scan` বা ড্যাশবোর্ড স্ট্যাটাস দেখতে `/status` চাপুন।"
        )

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📖 **কমান্ড লিস্ট:**\n"
            "• `/scan` - নতুন রিমোট জব সার্চ ও ড্রাফট তৈরি\n"
            "• `/status` - লাইভ ডাটাবেজ পরিসংখ্যান\n"
            "• `/start` - চ্যাট আইডি সিঙ্ক ও রিস্টার্ট"
        )

gatekeeper = TelegramGatekeeper()
