"""
Special Agent - Telegram Gatekeeper & Automated Notification Gateway
Supports:
1. One-Shot Cron Mode (--cron) for GitHub Actions & Background Scheduled Runs.
2. Interactive Bot Mode (--bot) for Real-time Local/VPS 24/7 command execution.
"""

import os
import sys
import re
import json
import smtplib
import subprocess
import speech_recognition as sr

# Set UTF-8 encoding for Windows terminal
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# Ensure root dir is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.lead_hunter import (
    scan_all_real_sources,
    load_seen_ids,
    save_seen_ids,
    load_live_leads,
    save_live_leads,
    fetch_devpost_hackathons
)
from backend.pitch_engine import generate_pitch, OPERATOR_CONTEXT

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

SMTP_USER = os.getenv("GMAIL_USER") or os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("GMAIL_APP_PASSWORD") or os.getenv("SMTP_APP_PASSWORD", "")

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown") if TOKEN else None

def send_gmail(recipient: str, subject: str, body: str) -> bool:
    if not (SMTP_USER and SMTP_PASS and recipient):
        print("[Gmail] Missing credentials or recipient.")
        return False
    try:
        msg = MIMEMultipart()
        msg["From"] = f"{OPERATOR_CONTEXT['name']} <{SMTP_USER}>"
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        print(f"[Gmail] Successfully sent email to {recipient}")
        return True
    except Exception as e:
        print(f"[Gmail] Error sending email: {e}")
        return False

def format_telegram_card(lead: dict) -> tuple:
    source = lead.get("source", "Web")
    title = lead.get("title", "")
    budget = lead.get("budget_or_prize", "Negotiable")
    score = lead.get("match_score", 90)
    url = lead.get("url", "")
    email = lead.get("contact_email", "")
    summary = lead.get("bengali_summary", "ক্লায়েন্টের জন্য উপযুক্ত রিকয়ারমেন্ট।")
    pitch = lead.get("ai_pitch", "")
    lead_type = lead.get("type", "client_gig")

    if lead_type == "hackathon":
        header = f"🏆 **নতুন গ্লোবাল হ্যাকাথন! ({source})**"
        action_label = "🔗 হ্যাকাথন রেজিস্ট্রেশন লিংক"
    elif "reddit" in source.lower():
        header = f"🔥 **নতুন সরাসরি ক্লায়েন্ট গিগ! ({source})**"
        action_label = "🔗 ক্লায়েন্ট পোস্ট ও ডিএম লিংক"
    else:
        header = f"🚨 **নতুন রিমোট জব সুযোগ! ({source})**"
        action_label = "🔗 অফিসিয়াল জব পোস্ট / আবেদন"

    text = (
        f"{header}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📌 **শিরোনাম:** {title}\n"
        f"💰 **বাজেট/পুরস্কার:** `{budget}`\n"
        f"🎯 **ম্যাচ স্কোর:** `{score}%`\n"
        f"🏢 **উৎস:** `{lead.get('company', source)}`\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🇧🇩 **জুবায়েরের জন্য সারসংক্ষেপ:**\n"
        f"{summary}\n\n"
        f"📝 **রেডিমেড প্রপোজাল (ট্যাপ করে কপি করুন):**\n"
        f"```text\n{pitch}\n```\n\n"
        f"👉 ক্লায়েন্টকে দ্রুত ইনবক্স করতে নিচে চাপুন:"
    )

    markup = InlineKeyboardMarkup()
    buttons = [InlineKeyboardButton(text=action_label, url=url)]
    if email:
        buttons.append(InlineKeyboardButton(text=f"📧 ইমেইল পাঠান ({email})", url=f"mailto:{email}?subject=Regarding {title[:30]}&body={pitch[:300]}"))
    markup.add(*buttons)

    return text, markup

def run_cron_cycle(max_notifications: int = 4):
    """
    Executed by GitHub Actions every 30 minutes or via `python backend/main.py --cron`.
    Scans real sources, crafts pitches, sends Telegram alerts, and saves live_leads.json.
    """
    print("=" * 60)
    print("🚀 [CRON] Starting Autonomous Lead Sweep & Telegram Gatekeeper...")
    print("=" * 60)

    seen = load_seen_ids()
    new_leads = scan_all_real_sources()

    unseen_leads = [l for l in new_leads if l.get("url") not in seen]
    print(f"[CRON] Unseen qualified leads to process: {len(unseen_leads)}")

    processed_leads = []
    notified_count = 0

    # Focus AI pitch generation on the top 15 highest-priority leads per sweep
    leads_to_process = unseen_leads[:15]
    print(f"[CRON] Processing top {len(leads_to_process)} prioritized leads...")

    for lead in leads_to_process:
        print(f"[CRON] Crafting Hermes 3 Pitch for: {lead['title'][:50]}...")
        b_summary, a_pitch = generate_pitch(lead)
        lead["bengali_summary"] = b_summary
        lead["ai_pitch"] = a_pitch
        processed_leads.append(lead)

        # Send Telegram notification if credentials exist and within notification quota
        if bot and CHAT_ID and notified_count < max_notifications:
            try:
                card_text, markup = format_telegram_card(lead)
                bot.send_message(CHAT_ID, card_text, reply_markup=markup)
                notified_count += 1
                print(f"[CRON] 📱 Sent Telegram alert #{notified_count} to Chat ID: {CHAT_ID}")
            except Exception as e:
                print(f"[CRON] Telegram send error: {e}")

        # Mark lead as seen
        seen.add(lead.get("url"))

    # Mark remaining unseen leads as seen so queue stays fresh
    for rem in unseen_leads[15:]:
        seen.add(rem.get("url"))


    # If all current leads were already seen, ensure existing live_leads has pitches
    if not processed_leads:
        existing = load_live_leads()
        if not existing:
            # First run seed
            for lead in new_leads[:15]:
                b_summary, a_pitch = generate_pitch(lead)
                lead["bengali_summary"] = b_summary
                lead["ai_pitch"] = a_pitch
                processed_leads.append(lead)
                seen.add(lead.get("url"))

    # Save to seen_ids.json and live_leads.json
    save_seen_ids(seen)
    final_live = save_live_leads(processed_leads)

    print("=" * 60)
    print(f"✅ [CRON] Sweep Complete! Processed: {len(processed_leads)}, Telegram Alerts: {notified_count}, Live Leads Saved: {len(final_live)}")
    print("=" * 60)
    return len(processed_leads)

def run_interactive_bot():
    """
    Interactive 24/7 long-polling Telegram bot for local PC or persistent VPS.
    """
    if not bot:
        print("[Bot] TELEGRAM_BOT_TOKEN missing. Cannot run interactive bot.")
        return

    print(f"🤖 [Bot] Interactive Telegram Gatekeeper started for @Jubayer_agent_bot...")

    @bot.message_handler(commands=["start", "help"])
    def cmd_start(message):
        welcome = (
            f"👑 **সালাম {message.from_user.first_name} ভাই!**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"আমি আপনার পার্সোনাল **24/7 AI Client, Gig & Hackathon Hunter**।\n"
            f"আমি প্রতি ৩০ মিনিটে Reddit, RemoteOK, WeWorkRemotely ও Devpost থেকে আসল সুযোগ খুঁজে আপনার জন্য উইনিং পিচ লিখে রাখি।\n\n"
            f"🚀 **উপলব্ধ কমান্ডসমূহ:**\n"
            f"• `/scan` - তাৎক্ষণিক ৪টি সোর্স থেকে নতুন লিড স্ক্যান করুন\n"
            f"• `/hackathons` - চলমান ওপেন গ্লোবাল হ্যাকাথন ও প্রপোজাল দেখুন\n"
            f"• `/status` - স্ক্যান পরিসংখ্যান ও ড্যাশবোর্ড রিপোর্ট\n\n"
            f"🌐 **লাইভ মিশন কন্ট্রোল ড্যাশবোর্ড:**\n"
            f"https://jubayer-ai-studio.github.io/special-agent/"
        )
        bot.reply_to(message, welcome)

    @bot.message_handler(commands=["status"])
    def cmd_status(message):
        seen = load_seen_ids()
        leads = load_live_leads()
        gigs = sum(1 for l in leads if l.get("type") == "client_gig")
        hacks = sum(1 for l in leads if l.get("type") == "hackathon")
        jobs = sum(1 for l in leads if l.get("type") == "remote_job")

        stat_msg = (
            f"📊 **স্পেশাল এজেন্ট মিশন কন্ট্রোল রিপোর্ট**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📡 সিস্টেম স্টেটাস: **সক্রিয় (24/7 Cloud Automated)**\n"
            f"🎯 ড্যাশবোর্ডে সক্রিয় লিড: `{len(leads)}টি`\n"
            f"💼 সরাসরি Reddit ক্লায়েন্ট গিগ: `{gigs}টি`\n"
            f"🏆 Devpost গ্লোবাল হ্যাকাথন: `{hacks}টি`\n"
            f"🌍 রিমোট প্রোগ্রামিং জব: `{jobs}টি`\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"নতুন কাজ সার্চ করতে চাপুন: `/scan`"
        )
        bot.reply_to(message, stat_msg)

    # In-memory session tracking for active conversation
    user_cached_leads = {}

    def send_numbered_leads_summary(chat_id):
        leads = load_live_leads()
        if not leads:
            leads = scan_all_real_sources()[:5]
            save_live_leads(leads)
        
        # Prioritize beginner-friendly micro gigs & regional tasks
        selected = leads[:5]
        user_cached_leads[chat_id] = selected
        
        summary_text = (
            f"👑 **সালাম জুবায়ের ভাই!**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"আমি আপনার জন্য বর্তমানের শীর্ষ ৫টি সহজ ও প্র্যাকটিক্যাল কাজের তালিকা তৈরি করেছি:\n\n"
        )
        
        for idx, l in enumerate(selected, 1):
            title = l.get("title", "")[:55]
            budget = l.get("budget_or_prize", "আলোচনা সাপেক্ষ")
            # If budget in USD, add approximate BDT conversion for beginner clarity
            if "$" in budget:
                nums = re.findall(r'\d+', budget.replace(",", ""))
                if nums:
                    val = int(nums[0])
                    bdt_val = val * 122
                    budget = f"{budget} (প্রায় ৳{bdt_val:,})"
            source = l.get("source", "Web")
            summary_text += f"📌 **{idx}. {title}**\n💰 বাজেট: `{budget}` | উৎস: `{source}`\n\n"
            
        summary_text += (
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👉 **কোন কাজটি নিয়ে বিস্তারিত জানতে চান?**\n"
            f"শুধু **১**, **২**, **৩** বা কাজের নম্বর লিখে রিপ্লাই দিন।\n"
            f"আমি আপনাকে ক্লায়েন্টের শর্ত, কাজটি কীভাবে করবেন এবং ক্লায়েন্টকে পাঠানোর রেডিমেড ইনবক্স মেসেজ বুঝিয়ে দিচ্ছি!"
        )
        bot.send_message(chat_id, summary_text)

    def explain_selected_lead(chat_id, index):
        cached = user_cached_leads.get(chat_id, [])
        if not cached:
            cached = load_live_leads()[:5]
            user_cached_leads[chat_id] = cached
            
        if not (1 <= index <= len(cached)):
            bot.send_message(chat_id, f"⚠️ দুঃখিত জুবায়ের ভাই, ১ থেকে {len(cached)}-এর মধ্যে যেকোনো একটি নম্বর বেছে নিন।")
            return
            
        lead = cached[index - 1]
        title = lead.get("title", "")
        desc = lead.get("description", "")
        budget = lead.get("budget_or_prize", "আলোচনা সাপেক্ষ")
        if "$" in budget:
            nums = re.findall(r'\d+', budget.replace(",", ""))
            if nums:
                val = int(nums[0])
                budget = f"{budget} (প্রায় ৳{val*122:,})"
                
        source = lead.get("source", "Web")
        url = lead.get("url", "")
        b_summary = lead.get("bengali_summary") or "ক্লায়েন্টের জন্য উপযুক্ত প্রজেক্ট।"
        pitch = lead.get("ai_pitch") or ""
        
        explanation = (
            f"🎯 **কাজের বিশ্লেষণ (নম্বর {index}):**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📌 **কাজের নাম:** {title}\n"
            f"💰 **বাজেট:** `{budget}`\n"
            f"🏢 **উৎস:** `{source}`\n\n"
            f"🇧🇩 **ক্লায়েন্ট আসলে কী চাইছে (সহজ বাংলায়):**\n"
            f"{b_summary}\n\n"
            f"🛠️ **জুবায়ের ভাই কীভাবে কাজটি শুরু করবেন:**\n"
            f"১. ক্লায়েন্টের চাহিদা অনুযায়ী মূল রিকোয়ারমেন্ট বুঝুন।\n"
            f"২. জটিল কোডিং ছাড়া সহজ লজিক বা রেডিমেড প্লাগইন/স্ক্রিপ্ট ব্যবহার করুন।\n"
            f"৩. নিচে দেওয়া ইনবক্স প্রপোজালটি কপি করে ক্লায়েন্টকে ইনবক্স বা হোয়াটসঅ্যাপে পাঠিয়ে দিন।\n\n"
            f"✉️ **ক্লায়েন্টকে পাঠানোর রেডিমেড মেসেজ (ট্যাপ করে কপি করুন):**\n"
            f"```text\n{pitch if pitch else 'সালাম ভাই, আপনার পোস্টটি দেখলাম। আমি আপনার কাজটি আজকেই সফলভাবে কমপ্লিট করে দিতে পারব। আপনি ফ্রি থাকলে ইনবক্সে বিস্তারিত আলোচনা করতে পারি।'}\n```\n\n"
            f"🔗 **মূল পোস্টের লিংক:**\n{url}\n\n"
            f"💡 *টিপস: কোনো ফর্ম পূরণ করতে হলে বা ফেসবুক পোস্টের স্ক্রিনশট থাকলে আমাকে দিন, আমি পুরো উত্তর লিখে দেব!*"
        )
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text="🔗 মূল পোস্ট ও ক্লায়েন্ট ইনবক্স লিংক", url=url))
        bot.send_message(chat_id, explanation, reply_markup=markup)

    @bot.message_handler(commands=["scan"])
    def cmd_scan(message):
        bot.reply_to(message, "🔍 নতুন লোকাল ও বিগিনার-বান্ধব কাজগুলো খোঁজা হচ্ছে... অনুগ্রহ করে একটু অপেক্ষা করুন।")
        send_numbered_leads_summary(message.chat.id)

    @bot.message_handler(func=lambda m: True)
    def handle_chat(message):
        chat_id = message.chat.id
        text = message.text.strip()
        text_lower = text.lower()
        print(f"📩 [Telegram Message]: {text[:60]}")
        
        # Check if user typed a lead number (1, 2, 3, 4, 5 or Bengali ১, ২, ৩, ৪, ৫)
        bengali_digits = {'১': 1, '২': 2, '৩': 3, '৪': 4, '৫': 5}
        target_num = None
        
        if text.isdigit() and 1 <= int(text) <= 10:
            target_num = int(text)
        elif text in bengali_digits:
            target_num = bengali_digits[text]
        elif any(w in text_lower for w in ["১ নম্বর", "১ নাম্বার", "১নং", "1 number", "number 1"]):
            target_num = 1
        elif any(w in text_lower for w in ["২ নম্বর", "২ নাম্বার", "২নং", "2 number", "number 2"]):
            target_num = 2
        elif any(w in text_lower for w in ["৩ নম্বর", "৩ নাম্বার", "৩নং", "3 number", "number 3"]):
            target_num = 3
        elif any(w in text_lower for w in ["৪ নম্বর", "৪ নাম্বার", "৪নং", "4 number", "number 4"]):
            target_num = 4
        elif any(w in text_lower for w in ["৫ নম্বর", "৫ নাম্বার", "৫নং", "5 number", "number 5"]):
            target_num = 5
            
        if target_num is not None:
            explain_selected_lead(chat_id, target_num)
            return

        # Check if user is asking for jobs or summary
        job_inquiry_keywords = ["কাজ", "অর্ডার", "স্ক্যান", "scan", "list", "তালিকা", "নতুন কাজ", "কি আছে", "কি কি কাজ"]
        if any(k in text_lower for k in job_inquiry_keywords):
            send_numbered_leads_summary(chat_id)
            return

        # Conversational & Wingman Mode via Hermes Brain (Calibrated to Jubayer's exact preference)
        bot.send_chat_action(chat_id, "typing")
        try:
            from backend.brain.hermes_brain import hermes_brain
            prompt = (
                f"Operator: Jubayer Ahmad (Full Stack Developer & AI Specialist in Bangladesh).\n"
                f"User Message: '{text}'.\n\n"
                f"Your Persona & Strict Rules:\n"
                f"1. Identity: You are Jubayer's sharp, loyal, respectful junior assistant and technical wingman (জুবায়ের ভাইয়ের চটপটে ছোট ভাই ও ডানহাত)। Address him respectfully as 'জুবায়ের ভাই' when needed, but never call yourself 'বড় ভাই'.\n"
                f"2. Strict Conciseness: Jump STRAIGHT to the answer. NO filler words, NO unnecessary greetings like 'হ্যালো', 'কেমন আছেন', 'আশা করি ভালো আছেন' or fluff. Be 100% to-the-point.\n"
                f"3. Default Length: Keep normal answers short, crisp, and direct (1-3 sentences). ONLY provide long, detailed, step-by-step breakdowns if Jubayer explicitly asks ('বিস্তারিত বলো', 'ভেঙ্গে বলো', 'ডিটেইলস দাও').\n"
                f"4. Language: Jubayer may talk in Banglish (e.g., 'kemon acho', 'kaj dekhao'), casual Bengali, or English. Understand everything effortlessly and reply in clean, natural Bengali or Banglish as appropriate.\n"
                f"5. Tasks & Forms: If Jubayer shares a client post, requirement, or form question, instantly give him the exact copy-paste inbox DM or form answers without any intro."
            )
            reply = hermes_brain.chat(prompt, user_name="Jubayer")
            bot.reply_to(message, reply)
        except Exception as e:
            fallback = f"জুবায়ের ভাই, সিস্টেমের একটি ছোট নোটিশ এসেছে। কাজ দেখতে `/scan` লিখুন।"
            bot.reply_to(message, fallback)

    @bot.message_handler(content_types=['voice', 'audio'])
    def handle_voice(message):
        chat_id = message.chat.id
        print(f"🎙️ [Voice received from chat {chat_id}]")
        bot.send_chat_action(chat_id, "record_audio")
        try:
            file_info = bot.get_file(message.voice.file_id if message.voice else message.audio.file_id)
            downloaded = bot.download_file(file_info.file_path)

            temp_dir = os.path.join(root_dir, "data", "temp_voice")
            os.makedirs(temp_dir, exist_ok=True)
            ogg_path = os.path.join(temp_dir, f"voice_{message.message_id}.ogg")
            wav_path = os.path.join(temp_dir, f"voice_{message.message_id}.wav")

            with open(ogg_path, "wb") as f:
                f.write(downloaded)

            # Convert audio to 16kHz mono WAV via ffmpeg
            cmd = ["ffmpeg", "-y", "-i", ogg_path, "-ar", "16000", "-ac", "1", wav_path]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio_data = recognizer.record(source)
                try:
                    # Recognize Bengali first
                    transcribed = recognizer.recognize_google(audio_data, language="bn-BD")
                except Exception:
                    # Fallback to English
                    transcribed = recognizer.recognize_google(audio_data, language="en-US")

            # Clean temporary files
            for p in [ogg_path, wav_path]:
                if os.path.exists(p):
                    try: os.remove(p)
                    except: pass

            if transcribed and transcribed.strip():
                bot.reply_to(message, f"🎙️ *শুনেছি:* \"{transcribed}\"")
                message.text = transcribed
                handle_chat(message)
            else:
                bot.reply_to(message, "🎙️ ভাই, ভয়েস স্পষ্টভাবে বোঝা যায়নি। আরেকবার বলবেন কি?")
        except Exception as e:
            bot.reply_to(message, f"🎙️ ভয়েস প্রসেস করতে একটি নোটিশ এসেছে: {str(e)[:100]}। অনুগ্রহ করে লিখে পাঠান।")

    bot.infinity_polling(timeout=20, long_polling_timeout=10)

if __name__ == "__main__":
    if "--cron" in sys.argv:
        run_cron_cycle()
    elif "--bot" in sys.argv:
        run_interactive_bot()
    else:
        # Default single sweep
        run_cron_cycle()
