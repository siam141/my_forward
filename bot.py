# ============================================================
#  🎙️ ALPHAPOST STUDIO PRO v16 — PREMIUM EDITION
#  No-Edit Mode · Multi-Bot · Userbot · 2GB · Bengali · Premium
# ============================================================

import asyncio, logging, re, json, io, os, base64, random, time
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import quote
from typing import Optional

import aiosqlite, aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (Message, CallbackQuery, BufferedInputFile,
    InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto)

from pyrogram import Client as PyroClient
from pyrogram.errors import (SessionPasswordNeeded, PhoneCodeInvalid,
    PhoneCodeExpired, PasswordHashInvalid)

# ============================================================
#  CONFIGURATION
# ============================================================
TOKEN       = "8948573487:AAHA5F84xxLXx0C4RB_AWmMCOYhisBGZve0"
ADMIN_ID    = 8530165612
TIMEZONE    = ZoneInfo("Asia/Dhaka")
DB_PATH     = "studio.db"
SESSION_DIR = "sessions"
TMP_DIR     = os.path.join(SESSION_DIR, "tmp_downloads")
os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs(TMP_DIR, exist_ok=True)
BOT_API_MAX_MB = 48
POLL_INTERVAL  = 10

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("studio")
logging.getLogger("pyrogram").setLevel(logging.WARNING)

bot = Bot(token=TOKEN)
dp  = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)
scheduler = AsyncIOScheduler(timezone=TIMEZONE)

WEEKDAYS    = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
WEEKDAYS_BN = ["Som", "Mongol", "Budh", "Briho", "Shukro", "Shoni", "Robi"]

_bot_cache       = {}
_bot_pollers     = {}
_userbot_clients = {}
_login_clients   = {}

# ============================================================
#  PRESETS & CONSTANTS
# ============================================================
SIZE_PRESETS = {
    "square": (1080, 1080), "portrait": (1080, 1350),
    "story": (1080, 1920), "wide": (1200, 630), "landscape": (1920, 1080)}

SIZE_LABELS = {
    "square": "◼  Square  ·  1:1", "portrait": "▯  Portrait  ·  4:5",
    "story": "▮  Story  ·  9:16", "wide": "▭  Wide  ·  16:9",
    "landscape": "▬  Landscape  ·  Full HD"}

TEMPLATE_LABELS = {
    "bottom_bar": "◼  Bottom Bar", "top_ribbon": "🔖  Top Ribbon",
    "side_ribbon": "🎗  Side Ribbon", "magazine": "📰  Magazine",
    "minimal_center": "◯  Minimal Center", "news_card": "📺  News Card",
    "gradient_fade": "🌈  Gradient Fade", "corner_badge": "🎖  Corner Badge",
    "glass_card": "💎  Glass Card", "neon_glow": "✨  Neon Glow",
    "split_screen": "⬒  Split Screen", "bold_stripe": "🟨  Bold Stripe"}

COLOR_THEMES = {
    "gold": "#ffce00", "blue": "#3b82f6", "red": "#ef4444",
    "green": "#22c55e", "purple": "#a855f7", "cyan": "#06b6d4",
    "pink": "#ec4899", "black": "#1c1a15", "orange": "#f97316",
    "teal": "#14b8a6"}

COLOR_LABELS = {
    "gold": "🟡  Gold", "blue": "🔵  Blue", "red": "🔴  Red",
    "green": "🟢  Green", "purple": "🟣  Purple", "cyan": "🔷  Cyan",
    "pink": "🩷  Pink", "black": "⚫  Black", "orange": "🟠  Orange",
    "teal": "🟦  Teal"}

IMAGE_SOURCES = {
    "pollinations": "🤖  AI Generated  ·  Pollinations",
    "picsum":       "📷  Random Stock  ·  Picsum",
    "loremflickr":  "🖼  Keyword Photo  ·  LoremFlickr",
    "cascade":      "🔄  Smart Fallback  ·  Try All"}

PROVIDER_DEFS = [
    {"type":"groq","name":"Groq","caps":["text"],"base":"https://api.groq.com/openai","model":"llama-3.3-70b-versatile"},
    {"type":"cerebras","name":"Cerebras","caps":["text"],"base":"https://api.cerebras.ai/v1","model":"llama-3.3-70b"},
    {"type":"sambanova","name":"SambaNova","caps":["text"],"base":"https://api.sambanova.ai/v1","model":"Meta-Llama-3.3-70B-Instruct"},
    {"type":"nvidia","name":"NVIDIA NIM","caps":["text"],"base":"https://integrate.api.nvidia.com/v1","model":"meta/llama-3.3-70b-instruct"},
    {"type":"mistral","name":"Mistral","caps":["text"],"base":"https://api.mistral.ai","model":"mistral-large-latest"},
    {"type":"llm7","name":"LLM7 (No Key)","caps":["text"],"base":"https://api.llm7.io/v1","model":"deepseek-r1","nokey":True},
    {"type":"uncloseai","name":"UncloseAI","caps":["text"],"base":"https://hermes.ai.unturf.com/v1","model":"hermes","nokey":True},
    {"type":"openrouter","name":"OpenRouter","caps":["text"],"base":"https://openrouter.ai/api/v1","model":"openai/gpt-4o-mini"},
    {"type":"gemini","name":"Gemini","caps":["text","image"],"base":"https://generativelanguage.googleapis.com","model":"gemini-2.0-flash"},
    {"type":"openai","name":"OpenAI","caps":["text","image"],"base":"https://api.openai.com","model":"gpt-4o-mini"},
    {"type":"deepseek","name":"DeepSeek","caps":["text"],"base":"https://api.deepseek.com","model":"deepseek-chat"}]

KNOWN_MODELS = {
    "groq": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
    "cerebras": ["llama-3.3-70b", "llama3.1-8b"],
    "sambanova": ["Meta-Llama-3.3-70B-Instruct"],
    "nvidia": ["meta/llama-3.3-70b-instruct"],
    "mistral": ["mistral-large-latest", "mistral-medium-latest"],
    "llm7": ["deepseek-r1", "gpt-4o-mini"],
    "uncloseai": ["hermes"],
    "openrouter": ["openai/gpt-4o-mini", "google/gemini-flash-1.5"],
    "gemini": ["gemini-2.0-flash", "gemini-2.5-flash"],
    "openai": ["gpt-4o-mini", "gpt-4o"],
    "deepseek": ["deepseek-chat"]}

# ============================================================
#  PREMIUM PLANS CONFIG
# ============================================================
PLANS = {
    "free": {
        "name": "Free", "emoji": "🎁", "price": 0,
        "duration_days": 0, "tagline": "For getting started",
        "features": ["1 destination account", "2 automations", "2 watchers",
                     "50 posts/month", "Basic image templates"],
        "limits": {"accounts": 1, "automations": 2, "watchers": 2,
                   "userbots": 0, "posts_per_month": 50,
                   "ai_rewrite": False, "ai_compose": False,
                   "all_templates": False}},
    "premium": {
        "name": "Premium", "emoji": "⭐", "price": 599,
        "duration_days": 30, "tagline": "For serious creators",
        "features": ["5 destination accounts", "10 automations", "10 watchers",
                     "1 userbot (2GB)", "Unlimited posts",
                     "All 12 templates", "AI rewrite (EN + BN)"],
        "limits": {"accounts": 5, "automations": 10, "watchers": 10,
                   "userbots": 1, "posts_per_month": -1,
                   "ai_rewrite": True, "ai_compose": True,
                   "all_templates": True}},
    "pro": {
        "name": "Pro", "emoji": "💎", "price": 1499,
        "duration_days": 30, "tagline": "For agencies & teams",
        "features": ["Unlimited accounts", "Unlimited automations",
                     "Unlimited watchers", "5 userbots", "Unlimited posts",
                     "Priority support", "All templates + custom"],
        "limits": {"accounts": -1, "automations": -1, "watchers": -1,
                   "userbots": 5, "posts_per_month": -1,
                   "ai_rewrite": True, "ai_compose": True,
                   "all_templates": True}},
    "starter_yearly": {
        "name": "Starter Yearly", "emoji": "🎯", "price": 4999,
        "duration_days": 365, "tagline": "Premium · billed yearly",
        "features": ["Everything in Premium", "Save ৳2,189 (30% off)",
                     "Priority rendering", "Priority queue",
                     "Free upgrades for 1 year"],
        "limits": {"accounts": 5, "automations": 10, "watchers": 10,
                   "userbots": 2, "posts_per_month": -1,
                   "ai_rewrite": True, "ai_compose": True,
                   "all_templates": True}}}

PAYMENT_METHODS = {
    "bkash": {"name": "bKash", "emoji": "📱", "number": "+8801XXXXXXXXX",
              "instruction": (
                  "1. Open bKash app or dial *247#\n"
                  "2. Choose 'Send Money'\n"
                  "3. Enter number: +8801XXXXXXXXX\n"
                  "4. Enter the amount above\n"
                  "5. Reference: ALPHAPOST\n"
                  "6. Copy the TrxID from confirmation")},
    "nagad": {"name": "Nagad", "emoji": "📲", "number": "+8801XXXXXXXXX",
              "instruction": (
                  "1. Open Nagad app or dial *167#\n"
                  "2. Choose 'Send Money'\n"
                  "3. Enter number: +8801XXXXXXXXX\n"
                  "4. Enter the amount above\n"
                  "5. Copy the TrxID from confirmation")},
    "rocket": {"name": "Rocket", "emoji": "🚀", "number": "+8801XXXXXXXXX-1",
               "instruction": (
                   "1. Dial *322# from your phone\n"
                   "2. Choose 'Send Money'\n"
                   "3. Enter Rocket number: +8801XXXXXXXXX-1\n"
                   "4. Enter the amount above\n"
                   "5. Copy the TrxID from confirmation")}}

# ============================================================
#  TEXT STYLING HELPERS
# ============================================================
_SC = str.maketrans({
    'a':'ᴀ','b':'ʙ','c':'ᴄ','d':'ᴅ','e':'ᴇ','f':'ꜰ','g':'ɢ','h':'ʜ','i':'ɪ',
    'j':'ᴊ','k':'ᴋ','l':'ʟ','m':'ᴍ','n':'ɴ','o':'ᴏ','p':'ᴘ','q':'ǫ','r':'ʀ',
    's':'ꜱ','t':'ᴛ','u':'ᴜ','v':'ᴠ','w':'ᴡ','x':'x','y':'ʏ','z':'ᴢ',
    'A':'ᴀ','B':'ʙ','C':'ᴄ','D':'ᴅ','E':'ᴇ','F':'ꜰ','G':'ɢ','H':'ʜ','I':'ɪ',
    'J':'ᴊ','K':'ᴋ','L':'ʟ','M':'ᴍ','N':'ɴ','O':'ᴏ','P':'ᴘ','Q':'ǫ','R':'ʀ',
    'S':'ꜱ','T':'ᴛ','U':'ᴜ','V':'ᴠ','W':'ᴡ','X':'x','Y':'ʏ','Z':'ᴢ'})

def sc(t): return str(t or "").translate(_SC)
def divider(label=""):
    return f"◈─ {sc(label)} ─◈" if label else "━━━━━━━━━━━━━━━━━━━━━━━━"
def progress_bar(pct, length=12, filled="▰", empty="▱"):
    pct = max(0, min(100, pct)); n = int(length * pct / 100)
    return filled * n + empty * (length - n)

def human_time(ts):
    if not ts: return "—"
    try:
        dt = datetime.fromtimestamp(int(ts)); delta = datetime.now() - dt
        if delta.total_seconds() < 60: return "just now"
        if delta.total_seconds() < 3600: return f"{int(delta.total_seconds() // 60)}m ago"
        if delta.total_seconds() < 86400: return f"{int(delta.total_seconds() // 3600)}h ago"
        if delta.days == 1: return "yesterday"
        if delta.days < 7: return f"{delta.days}d ago"
        return dt.strftime("%d %b")
    except Exception: return "—"

def human_size(n):
    try:
        n = int(n)
        for u in ["B", "KB", "MB", "GB"]:
            if n < 1024: return f"{n:.1f}{u}"
            n /= 1024
        return f"{n:.1f}TB"
    except Exception: return "?"

def clean_text(t):
    if not t: return ""
    s = str(t)
    s = re.sub(r"^\s*[-=_*]{3,}\s*$", "", s, flags=re.M)
    s = re.sub(r"\*\*([^*\n]+?)\*\*", r"\1", s)
    s = re.sub(r"__([^_\n]+?)__", r"\1", s)
    s = re.sub(r"```([\s\S]*?)```", r"\1", s)
    s = re.sub(r"`([^`\n]+?)`", r"\1", s)
    s = re.sub(r"^\s*#{1,6}\s+", "", s, flags=re.M)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", s)
    s = re.sub(r"^(\s*)[-*+]\s+", r"\1• ", s, flags=re.M)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def strip_md_stars(t):
    return re.sub(r"\*([^*\n]+?)\*", r"\1", t) if t else t

def mask_key(k):
    if not k: return "—"
    return k[:6] + "…" + k[-4:] if len(k) > 12 else "•" * len(k)

def mask_phone(p):
    return p[:4] + "•" * (len(p) - 6) + p[-2:] if p and len(p) >= 5 else p

def parse_labeled(text):
    out = {"headline":"","hook":"","body":"","cta":"","hashtags":"","keywords":""}
    mapping = {"headline":["headline","title"],"hook":["hook"],
        "body":["body","post"],"cta":["cta","call to action"],
        "hashtags":["hashtags","tags"],"keywords":["keywords"]}
    cur = None
    for ln in str(text).split("\n"):
        m = re.match(r"^\s*([A-Za-z][A-Za-z ]{2,20}):\s*(.*)$", ln)
        if m:
            key = m.group(1).lower().strip()
            field = next((f for f, al in mapping.items()
                          if any(key == a or key in a for a in al)), None)
            if field:
                cur = field
                out[cur] = (out[cur] + "\n" + m.group(2)) if out[cur] else m.group(2)
                continue
        if cur: out[cur] += "\n" + ln
    for k in out: out[k] = clean_text(out[k])
    if not out["body"]: out["body"] = clean_text(str(text))
    return out

def _has_keywords(text, kw_csv):
    if not kw_csv or not str(kw_csv).strip(): return True
    kws = [k.strip().lower() for k in str(kw_csv).split(",") if k.strip()]
    if not kws: return True
    return any(k in (text or "").lower() for k in kws)

def _has_blockwords(text, bw_csv):
    if not bw_csv or not str(bw_csv).strip(): return False
    kws = [k.strip().lower() for k in str(bw_csv).split(",") if k.strip()]
    return any(k in (text or "").lower() for k in kws)

def _length_ok(text, ml):
    try: ml = int(ml or 0)
    except Exception: ml = 0
    return ml <= 0 or len((text or "").strip()) >= ml

# ── SENDING HELPERS ──
async def send_safe(chat_id, text, reply_markup=None, disable_preview=True):
    try:
        return await bot.send_message(chat_id, text, reply_markup=reply_markup,
            parse_mode="Markdown", disable_web_page_preview=disable_preview)
    except Exception:
        try:
            return await bot.send_message(chat_id, strip_md_stars(text),
                reply_markup=reply_markup, disable_web_page_preview=disable_preview)
        except Exception as e:
            logger.warning(f"send_safe: {e}"); return None

async def edit_safe(msg, text, reply_markup=None):
    try:
        chat_id = msg.chat.id; old_id = msg.message_id
    except Exception: return None
    try: await bot.delete_message(chat_id, old_id)
    except Exception: pass
    return await send_safe(chat_id, text, reply_markup=reply_markup)

async def http_json(url, method="GET", headers=None, json_body=None, timeout=60):
    async with aiohttp.ClientSession() as s:
        try:
            async with s.request(method, url, headers=headers or {}, json=json_body,
                timeout=aiohttp.ClientTimeout(total=timeout)) as r:
                txt = await r.text()
                try: return r.status, json.loads(txt)
                except Exception: return r.status, {"_raw": txt[:400]}
        except Exception as e:
            return 0, {"_err": str(e)}

# ============================================================
#  DATABASE
# ============================================================
async def db_init():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT)")
        await db.execute("""CREATE TABLE IF NOT EXISTS providers(
            id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, name TEXT, api_key TEXT,
            base_url TEXT, model TEXT, caps TEXT, priority INTEGER DEFAULT 99,
            enabled INTEGER DEFAULT 1, last_working_model TEXT)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS accounts(
            id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER,
            platform TEXT DEFAULT 'telegram', name TEXT, bot_token TEXT, chat_id TEXT,
            status TEXT DEFAULT 'connected', created_at INTEGER, last_post INTEGER,
            post_count INTEGER DEFAULT 0)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS userbots(
            id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER, name TEXT, phone TEXT,
            api_id INTEGER, api_hash TEXT, session_string TEXT, status TEXT DEFAULT 'active',
            created_at INTEGER, last_used INTEGER, forward_count INTEGER DEFAULT 0)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS bots(
            id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER, name TEXT,
            token TEXT UNIQUE, bot_id INTEGER, bot_username TEXT,
            created_at INTEGER, status TEXT DEFAULT 'active')""")
        await db.execute("""CREATE TABLE IF NOT EXISTS automations(
            id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER, name TEXT,
            content_source TEXT DEFAULT 'ai', topic TEXT, language TEXT DEFAULT 'English',
            post_length TEXT DEFAULT 'medium', image_size TEXT DEFAULT 'square',
            image_template TEXT DEFAULT 'bottom_bar', image_source TEXT DEFAULT 'cascade',
            color_theme TEXT DEFAULT 'gold', headline_on_image INTEGER DEFAULT 1,
            num_images INTEGER DEFAULT 1, inline_buttons TEXT DEFAULT '',
            posts_per_day INTEGER DEFAULT 2, post_from TEXT DEFAULT '08:00',
            post_until TEXT DEFAULT '22:00', days TEXT DEFAULT '0,1,2,3,4,5,6',
            account_ids TEXT, generate_image INTEGER DEFAULT 1,
            image_style TEXT DEFAULT 'real', use_hashtags INTEGER DEFAULT 1,
            hashtag_group TEXT DEFAULT '', link TEXT DEFAULT '',
            text_before_link TEXT DEFAULT '', mode TEXT DEFAULT 'auto',
            active INTEGER DEFAULT 1, created_at INTEGER, last_run INTEGER,
            run_count INTEGER DEFAULT 0, success_count INTEGER DEFAULT 0,
            fail_count INTEGER DEFAULT 0)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS history(
            id INTEGER PRIMARY KEY AUTOINCREMENT, account_id INTEGER DEFAULT 0,
            automation_id INTEGER DEFAULT 0, status TEXT, error TEXT, ts INTEGER)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS hashtag_groups(
            id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER, name TEXT,
            tags TEXT, created_at INTEGER)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS watchers(
            id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER,
            source_chat TEXT, source_title TEXT,
            source_type TEXT DEFAULT 'bot', userbot_id INTEGER DEFAULT 0,
            source_bot_db_id INTEGER DEFAULT 0, source_bot_token TEXT DEFAULT '',
            source_username TEXT DEFAULT '', source_chat_id TEXT DEFAULT '',
            last_seen_msg_id INTEGER DEFAULT 0,
            mode TEXT DEFAULT 'ai_rewrite', brand_template TEXT DEFAULT 'bottom_bar',
            brand_color TEXT DEFAULT '#ffce00',
            keyword_filter TEXT DEFAULT '', block_words TEXT DEFAULT '',
            min_length INTEGER DEFAULT 0, media_filter TEXT DEFAULT 'any',
            footer TEXT DEFAULT '', delay_seconds INTEGER DEFAULT 3,
            rewrite_language TEXT DEFAULT 'English',
            active INTEGER DEFAULT 1, created_at INTEGER,
            processed_count INTEGER DEFAULT 0)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS watcher_destinations(
            id INTEGER PRIMARY KEY AUTOINCREMENT, watcher_id INTEGER, account_id INTEGER)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS processed_posts(
            id INTEGER PRIMARY KEY AUTOINCREMENT, watcher_id INTEGER, source_chat TEXT,
            source_msg_id INTEGER, ts INTEGER,
            UNIQUE(watcher_id, source_chat, source_msg_id))""")
        await db.execute("""CREATE TABLE IF NOT EXISTS watcher_logs(
            id INTEGER PRIMARY KEY AUTOINCREMENT, watcher_id INTEGER, source_msg_id INTEGER,
            dest_account_id INTEGER, mode TEXT, status TEXT, error TEXT, ts INTEGER)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS seen_chats(
            id INTEGER PRIMARY KEY AUTOINCREMENT, userbot_id INTEGER, chat_id TEXT,
            chat_title TEXT, chat_username TEXT, chat_type TEXT, last_seen INTEGER,
            UNIQUE(userbot_id, chat_id))""")
        # ── PREMIUM TABLES ──
        await db.execute("""CREATE TABLE IF NOT EXISTS app_users(
            user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
            plan TEXT DEFAULT 'free', plan_started INTEGER DEFAULT 0,
            plan_expires INTEGER DEFAULT 0, total_paid INTEGER DEFAULT 0,
            created_at INTEGER, last_seen INTEGER)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS payments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, username TEXT, plan TEXT, amount INTEGER,
            method TEXT, trx_id TEXT, status TEXT DEFAULT 'pending',
            submitted_at INTEGER, reviewed_at INTEGER,
            reviewer_id INTEGER, note TEXT)""")
        await db.commit()

        migrations = [
            ("watchers","source_bot_db_id","INTEGER DEFAULT 0"),
            ("watchers","source_bot_token","TEXT DEFAULT ''"),
            ("watchers","source_type","TEXT DEFAULT 'bot'"),
            ("watchers","userbot_id","INTEGER DEFAULT 0"),
            ("watchers","source_username","TEXT DEFAULT ''"),
            ("watchers","source_chat_id","TEXT DEFAULT ''"),
            ("watchers","last_seen_msg_id","INTEGER DEFAULT 0"),
            ("automations","content_source","TEXT DEFAULT 'ai'"),
            ("automations","image_size","TEXT DEFAULT 'square'"),
            ("automations","image_template","TEXT DEFAULT 'bottom_bar'"),
            ("automations","image_source","TEXT DEFAULT 'cascade'"),
            ("automations","color_theme","TEXT DEFAULT 'gold'"),
            ("automations","headline_on_image","INTEGER DEFAULT 1"),
            ("automations","num_images","INTEGER DEFAULT 1"),
            ("automations","inline_buttons","TEXT DEFAULT ''"),
            ("automations","hashtag_group","TEXT DEFAULT ''"),
            ("automations","success_count","INTEGER DEFAULT 0"),
            ("automations","fail_count","INTEGER DEFAULT 0"),
            ("automations","account_ids","TEXT")]
        for tbl, col, coldef in migrations:
            try:
                await db.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {coldef}")
                await db.commit()
            except Exception: pass

        defaults = {"imgbb_key": "", "brand_name": "My Channel",
            "brand_handle": "@mychannel", "brand_website": "example.com",
            "brand_color": "#ffce00"}
        for k, v in defaults.items():
            await db.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (k, v))
        await db.commit()

async def get_setting(key, default=""):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT value FROM settings WHERE key=?", (key,))
        r = await cur.fetchone()
        return r[0] if r else default

async def set_setting(key, value):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)",
                         (key, str(value)))
        await db.commit()

async def db_add_provider(d):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""INSERT INTO providers(type,name,api_key,base_url,
            model,caps,priority,enabled) VALUES(?,?,?,?,?,?,?,1)""",
            (d["type"], d["name"], d["api_key"], d["base_url"], d["model"],
             ",".join(d["caps"]), d.get("priority", 99)))
        await db.commit(); return cur.lastrowid

async def db_list_providers():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM providers ORDER BY priority ASC, id ASC")
        return await cur.fetchall()

async def db_update_provider(pid, **f):
    if not f: return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE providers SET " + ", ".join(f"{k}=?" for k in f) +
                         " WHERE id=?", list(f.values()) + [pid])
        await db.commit()

async def db_add_account(d):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""INSERT INTO accounts(owner_id,platform,name,
            bot_token,chat_id,status,created_at) VALUES(?,?,?,?,?,?,?)""",
            (d["owner_id"], d.get("platform", "telegram"), d["name"],
             d.get("bot_token", ""), d.get("chat_id", ""),
             d.get("status", "connected"), int(datetime.now().timestamp())))
        await db.commit(); return cur.lastrowid

async def db_list_accounts(owner):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM accounts WHERE owner_id=? ORDER BY created_at DESC", (owner,))
        return await cur.fetchall()

async def db_get_account(aid):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM accounts WHERE id=?", (aid,))
        return await cur.fetchone()

async def db_del_account(aid, owner):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM accounts WHERE id=? AND owner_id=?", (aid, owner))
        await db.execute("DELETE FROM watcher_destinations WHERE account_id=?", (aid,))
        await db.commit()

async def db_bump_account_post(aid):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""UPDATE accounts SET last_post=?,
            post_count=post_count+1 WHERE id=?""",
            (int(datetime.now().timestamp()), aid))
        await db.commit()

async def db_add_userbot(d):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""INSERT INTO userbots(owner_id,name,phone,api_id,
            api_hash,session_string,status,created_at)
            VALUES(?,?,?,?,?,?,'active',?)""",
            (d["owner_id"], d["name"], d["phone"], d["api_id"], d["api_hash"],
             d["session_string"], int(datetime.now().timestamp())))
        await db.commit(); return cur.lastrowid

async def db_list_userbots(owner):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM userbots WHERE owner_id=? ORDER BY id DESC", (owner,))
        return await cur.fetchall()

async def db_get_userbot(u):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM userbots WHERE id=?", (u,))
        return await cur.fetchone()

async def db_del_userbot(u, owner):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM userbots WHERE id=? AND owner_id=?", (u, owner))
        await db.commit()

async def db_bump_userbot(u):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""UPDATE userbots SET last_used=?,
            forward_count=forward_count+1 WHERE id=?""",
            (int(datetime.now().timestamp()), u))
        await db.commit()

async def db_add_bot(d):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""INSERT INTO bots(owner_id,name,token,bot_id,
            bot_username,status,created_at) VALUES(?,?,?,?,?,'active',?)""",
            (d["owner_id"], d["name"], d["token"], d.get("bot_id", 0),
             d.get("bot_username", ""), int(datetime.now().timestamp())))
        await db.commit(); return cur.lastrowid

async def db_list_bots(owner):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM bots WHERE owner_id=? ORDER BY id DESC", (owner,))
        return await cur.fetchall()

async def db_get_bot(bid):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM bots WHERE id=?", (bid,))
        return await cur.fetchone()

async def db_get_bot_by_token(tok):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM bots WHERE token=?", (tok,))
        return await cur.fetchone()

async def db_del_bot(bid, owner):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM bots WHERE id=? AND owner_id=?", (bid, owner))
        await db.commit()

async def db_add_automation(d):
    cols = ["owner_id","name","content_source","topic","language","post_length",
            "image_size","image_template","image_source","color_theme",
            "headline_on_image","num_images","inline_buttons","posts_per_day",
            "post_from","post_until","days","account_ids","generate_image",
            "image_style","use_hashtags","hashtag_group","link","text_before_link",
            "mode","active","created_at"]
    vals = [d["owner_id"], d["name"], d.get("content_source", "ai"), d["topic"],
            d["language"], d["post_length"], d.get("image_size", "square"),
            d.get("image_template", "bottom_bar"),
            d.get("image_source", "cascade"), d.get("color_theme", "gold"),
            d.get("headline_on_image", 1), d.get("num_images", 1),
            d.get("inline_buttons", ""), d["posts_per_day"],
            d["post_from"], d["post_until"], d["days"], d["account_ids"],
            d.get("generate_image", 1), d.get("image_style", "real"),
            d.get("use_hashtags", 1), d.get("hashtag_group", ""),
            d.get("link", ""), d.get("text_before_link", ""), d["mode"], 1,
            int(datetime.now().timestamp())]
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            f"INSERT INTO automations({','.join(cols)}) VALUES({','.join('?'*len(cols))})",
            vals)
        await db.commit(); return cur.lastrowid

async def db_list_automations(owner):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM automations WHERE owner_id=? ORDER BY id DESC", (owner,))
        return await cur.fetchall()

async def db_get_automation(aid):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM automations WHERE id=?", (aid,))
        return await cur.fetchone()

async def db_del_automation(aid, owner):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM automations WHERE id=? AND owner_id=?", (aid, owner))
        await db.commit()

async def db_toggle_automation(aid, owner, active):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE automations SET active=? WHERE id=? AND owner_id=?",
                         (1 if active else 0, aid, owner))
        await db.commit()

async def db_update_automation_run(aid, success=True):
    async with aiosqlite.connect(DB_PATH) as db:
        if success:
            await db.execute("""UPDATE automations SET last_run=?,
                run_count=run_count+1, success_count=success_count+1 WHERE id=?""",
                (int(datetime.now().timestamp()), aid))
        else:
            await db.execute("""UPDATE automations SET last_run=?,
                run_count=run_count+1, fail_count=fail_count+1 WHERE id=?""",
                (int(datetime.now().timestamp()), aid))
        await db.commit()

async def db_log(acc_id, status, err="", automation_id=None):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""INSERT INTO history(account_id,automation_id,
                status,error,ts) VALUES(?,?,?,?,?)""",
                (acc_id or 0, automation_id or 0, status, err,
                 int(datetime.now().timestamp())))
            await db.commit()
    except Exception as e: logger.warning(f"db_log: {e}")

async def db_add_hashtags(owner, name, tags):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""INSERT INTO hashtag_groups(owner_id,name,tags,
            created_at) VALUES(?,?,?,?)""",
            (owner, name, tags, int(datetime.now().timestamp())))
        await db.commit(); return cur.lastrowid

async def db_list_hashtags(owner):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM hashtag_groups WHERE owner_id=?", (owner,))
        return await cur.fetchall()

async def db_get_hashtags(hid):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM hashtag_groups WHERE id=?", (hid,))
        return await cur.fetchone()

async def db_del_hashtags(hid, owner):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM hashtag_groups WHERE id=? AND owner_id=?",
                         (hid, owner))
        await db.commit()

async def db_add_watcher(d):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""INSERT INTO watchers(owner_id,source_chat,
            source_title,source_type,userbot_id,source_bot_db_id,source_bot_token,
            mode,brand_template,brand_color,keyword_filter,block_words,min_length,
            media_filter,footer,delay_seconds,rewrite_language,active,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1,?)""",
            (d["owner_id"], d["source_chat"], d.get("source_title", ""),
             d.get("source_type", "bot"), d.get("userbot_id", 0),
             d.get("source_bot_db_id", 0), d.get("source_bot_token", ""),
             d.get("mode", "ai_rewrite"), d.get("brand_template", "bottom_bar"),
             d.get("brand_color", "#ffce00"), d.get("keyword_filter", ""),
             d.get("block_words", ""), d.get("min_length", 0),
             d.get("media_filter", "any"), d.get("footer", ""),
             d.get("delay_seconds", 3), d.get("rewrite_language", "English"),
             int(datetime.now().timestamp())))
        await db.commit(); return cur.lastrowid

async def db_add_watcher_dest(w, a):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""INSERT INTO watcher_destinations(watcher_id,account_id)
            VALUES(?,?)""", (w, a))
        await db.commit()

async def db_list_watchers(owner):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM watchers WHERE owner_id=? ORDER BY id DESC", (owner,))
        return await cur.fetchall()

async def db_list_all_active_userbot_watchers():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""SELECT * FROM watchers
            WHERE active=1 AND source_type='userbot'""")
        return await cur.fetchall()

async def db_get_watcher(wid):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM watchers WHERE id=?", (wid,))
        return await cur.fetchone()

async def db_get_watcher_dests(wid):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""SELECT wd.id as wd_id, wd.watcher_id,
            wd.account_id, a.name, a.chat_id, a.bot_token
            FROM watcher_destinations wd JOIN accounts a ON a.id = wd.account_id
            WHERE wd.watcher_id=?""", (wid,))
        return await cur.fetchall()

async def db_del_watcher(wid, owner):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM watchers WHERE id=? AND owner_id=?", (wid, owner))
        await db.execute("DELETE FROM watcher_destinations WHERE watcher_id=?", (wid,))
        await db.commit()

async def db_toggle_watcher(wid, owner, active):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE watchers SET active=? WHERE id=? AND owner_id=?",
                         (1 if active else 0, wid, owner))
        await db.commit()

async def db_bump_watcher_count(wid):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE watchers SET processed_count=processed_count+1 WHERE id=?", (wid,))
        await db.commit()

async def db_update_last_seen(wid, msg_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE watchers SET last_seen_msg_id=? WHERE id=?", (msg_id, wid))
        await db.commit()

async def db_log_watcher(wid, src_msg_id, dest_acc, mode, status, err=""):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""INSERT INTO watcher_logs(watcher_id,source_msg_id,
                dest_account_id,mode,status,error,ts) VALUES(?,?,?,?,?,?,?)""",
                (wid, src_msg_id, dest_acc, mode, status, err,
                 int(datetime.now().timestamp())))
            await db.commit()
    except Exception as e: logger.warning(f"log_watcher: {e}")

async def db_mark_processed(wid, source_chat, source_msg_id):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""INSERT OR IGNORE INTO processed_posts(watcher_id,
                source_chat,source_msg_id,ts) VALUES(?,?,?,?)""",
                (wid, source_chat, source_msg_id, int(datetime.now().timestamp())))
            await db.commit(); return True
    except Exception: return False

async def db_is_processed(wid, source_chat, source_msg_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""SELECT 1 FROM processed_posts
            WHERE watcher_id=? AND source_chat=? AND source_msg_id=?""",
            (wid, source_chat, source_msg_id))
        return (await cur.fetchone()) is not None

async def db_upsert_seen_chat(ub, cid, t, u, ct):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""INSERT INTO seen_chats(userbot_id,chat_id,chat_title,
                chat_username,chat_type,last_seen) VALUES(?,?,?,?,?,?)
                ON CONFLICT(userbot_id,chat_id) DO UPDATE SET
                chat_title=excluded.chat_title, chat_username=excluded.chat_username,
                chat_type=excluded.chat_type, last_seen=excluded.last_seen""",
                (ub, str(cid), t or "", u or "", ct or "",
                 int(datetime.now().timestamp())))
            await db.commit()
    except Exception as e: logger.warning(f"upsert seen: {e}")

async def db_list_seen_chats(owner_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""SELECT sc.*, ub.name as ub_name FROM seen_chats sc
            JOIN userbots ub ON ub.id = sc.userbot_id WHERE ub.owner_id=?
            ORDER BY sc.last_seen DESC LIMIT 50""", (owner_id,))
        return await cur.fetchall()

def _normalize_username(u): return (u or "").strip().lower().lstrip("@")

def _normalize_id(i):
    s = str(i or "").strip()
    if not s: return ""
    if s.startswith("-100"): return s[4:]
    if s.startswith("-"): return s[1:]
    return s

def _chat_matches(w, inc_id, inc_uname):
    try:
        stored = (w["source_chat"] or "").strip()
        stored_id = (w["source_chat_id"] if "source_chat_id" in w.keys() else "") or ""
        stored_uname = _normalize_username(
            w["source_username"] if "source_username" in w.keys() else "")
    except Exception: return False
    stored_clean = stored.lower().lstrip("@")
    inc_id_s = str(inc_id or "").strip()
    inc_uname_n = _normalize_username(inc_uname)
    if stored == inc_id_s: return True
    if stored_id and inc_id_s and stored_id == inc_id_s: return True
    if stored_id and inc_id_s:
        if _normalize_id(stored_id) == _normalize_id(inc_id_s): return True
    if inc_uname_n:
        if stored_clean == inc_uname_n: return True
        if stored_uname == inc_uname_n: return True
    if stored.lstrip("-").isdigit() and inc_id_s:
        if _normalize_id(stored) == _normalize_id(inc_id_s): return True
    return False

async def db_find_watchers_bot(c, u="", bot_db_id=0):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""SELECT * FROM watchers WHERE active=1
            AND source_type='bot' AND source_bot_db_id=?""", (bot_db_id,))
        rows = await cur.fetchall()
    return [w for w in rows if _chat_matches(w, c, u)]

async def db_find_watchers_userbot(ub, c, u=""):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""SELECT * FROM watchers WHERE active=1
            AND source_type='userbot' AND userbot_id=?""", (ub,))
        rows = await cur.fetchall()
    return [w for w in rows if _chat_matches(w, c, u)]

# ============================================================
#  PREMIUM DB LAYER
# ============================================================
async def register_user(user):
    now = int(time.time())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO app_users(user_id, username, first_name, created_at, last_seen)
            VALUES(?,?,?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_seen = excluded.last_seen""",
            (user.id, user.username or "", user.first_name or "", now, now))
        await db.commit()

async def get_user_plan(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM app_users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
    if not row:
        return {"user_id": user_id, "plan": "free", "plan_obj": PLANS["free"],
                "expires": 0, "is_premium": False, "total_paid": 0,
                "username": "", "first_name": ""}
    plan_key = row["plan"] or "free"
    expires = row["plan_expires"] or 0
    now = int(time.time())
    if plan_key != "free" and expires > 0 and now > expires:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE app_users SET plan='free', plan_expires=0 WHERE user_id=?",
                (user_id,))
            await db.commit()
        plan_key = "free"; expires = 0
    return {"user_id": user_id, "username": row["username"] or "",
            "first_name": row["first_name"] or "", "plan": plan_key,
            "plan_obj": PLANS.get(plan_key, PLANS["free"]), "expires": expires,
            "is_premium": plan_key != "free", "total_paid": row["total_paid"] or 0}

async def check_limit(user_id, resource):
    info = await get_user_plan(user_id)
    plan_key = info["plan"]
    max_val = PLANS[plan_key]["limits"].get(resource, 0)
    if max_val == -1: return True, 0, -1, plan_key
    async with aiosqlite.connect(DB_PATH) as db:
        table_map = {"accounts": "accounts", "automations": "automations",
                     "watchers": "watchers", "userbots": "userbots"}
        table = table_map.get(resource)
        if not table: return True, 0, 0, plan_key
        cur = await db.execute(f"SELECT COUNT(*) FROM {table} WHERE owner_id=?",
                                (user_id,))
        row = await cur.fetchone(); current = row[0] if row else 0
    return current < max_val, current, max_val, plan_key

async def has_feature(user_id, feature):
    info = await get_user_plan(user_id)
    return bool(PLANS[info["plan"]]["limits"].get(feature, False))

async def check_all_expirations():
    now = int(time.time())
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""UPDATE app_users SET plan='free', plan_expires=0
            WHERE plan != 'free' AND plan_expires > 0 AND plan_expires < ?""", (now,))
        await db.commit()
        if cur.rowcount: logger.info(f"Downgraded {cur.rowcount} expired users")

async def create_payment(user_id, username, plan_key, amount, method, trx_id):
    now = int(time.time())
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""INSERT INTO payments(user_id, username, plan,
            amount, method, trx_id, status, submitted_at)
            VALUES(?,?,?,?,?,?,'pending',?)""",
            (user_id, username, plan_key, amount, method, trx_id, now))
        await db.commit(); return cur.lastrowid

async def get_payment(pid):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM payments WHERE id=?", (pid,))
        return await cur.fetchone()

async def list_pending_payments():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM payments WHERE status='pending' ORDER BY id DESC LIMIT 20")
        return await cur.fetchall()

async def approve_payment(pid, reviewer_id):
    pay = await get_payment(pid)
    if not pay or pay["status"] != "pending": return None
    plan = PLANS.get(pay["plan"])
    if not plan: return None
    now = int(time.time())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""UPDATE payments SET status='approved',
            reviewed_at=?, reviewer_id=? WHERE id=?""", (now, reviewer_id, pid))
        cur = await db.execute(
            "SELECT plan_expires FROM app_users WHERE user_id=?", (pay["user_id"],))
        row = await cur.fetchone()
        cur_exp = row[0] if row and row[0] else 0
        base = cur_exp if cur_exp > now else now
        new_exp = base + plan["duration_days"] * 86400
        await db.execute("""INSERT INTO app_users(user_id, username, first_name,
            created_at, last_seen) VALUES(?,?,?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET plan=excluded.plan""",
            (pay["user_id"], pay["username"] or "", "", now, now))
        await db.execute("""UPDATE app_users SET plan=?, plan_started=?,
            plan_expires=?, total_paid = total_paid + ? WHERE user_id=?""",
            (pay["plan"], now, new_exp, pay["amount"], pay["user_id"]))
        await db.commit()
    return dict(pay)

async def reject_payment(pid, reviewer_id, note=""):
    pay = await get_payment(pid)
    if not pay or pay["status"] != "pending": return None
    now = int(time.time())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""UPDATE payments SET status='rejected',
            reviewed_at=?, reviewer_id=?, note=? WHERE id=?""",
            (now, reviewer_id, note, pid))
        await db.commit()
    return dict(pay)

async def grant_plan(user_id, plan_key, days=None):
    plan = PLANS.get(plan_key)
    if not plan: return False
    now = int(time.time())
    dur = (days if days else plan["duration_days"]) * 86400
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""INSERT INTO app_users(user_id, username, first_name,
            created_at, last_seen) VALUES(?,?,?,?,?)
            ON CONFLICT(user_id) DO NOTHING""", (user_id, "", "", now, now))
        cur = await db.execute(
            "SELECT plan_expires FROM app_users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        cur_exp = row[0] if row and row[0] else 0
        base = cur_exp if cur_exp > now else now
        await db.execute("""UPDATE app_users SET plan=?, plan_started=?,
            plan_expires=? WHERE user_id=?""",
            (plan_key, now, base + dur, user_id))
        await db.commit()
    return True

async def revoke_plan(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE app_users SET plan='free', plan_expires=0 WHERE user_id=?",
            (user_id,))
        await db.commit()
    return True

async def get_premium_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT COUNT(*) FROM app_users")
        total = (await cur.fetchone())[0]
        cur = await db.execute("SELECT COUNT(*) FROM app_users WHERE plan != 'free'")
        premium = (await cur.fetchone())[0]
        cur = await db.execute(
            "SELECT COALESCE(SUM(amount),0) FROM payments WHERE status='approved'")
        revenue = (await cur.fetchone())[0]
        cur = await db.execute("SELECT COUNT(*) FROM payments WHERE status='pending'")
        pending = (await cur.fetchone())[0]
        cur = await db.execute("SELECT COUNT(*) FROM payments WHERE status='approved'")
        approved = (await cur.fetchone())[0]
    return {"total": total, "premium": premium, "revenue": revenue,
            "pending": pending, "approved": approved}

def fmt_date(ts):
    if not ts: return "—"
    try: return datetime.fromtimestamp(ts).strftime("%d %b %Y")
    except Exception: return "—"

def fmt_remaining(ts):
    if not ts: return "—"
    rem = ts - int(time.time())
    if rem <= 0: return "expired"
    days = rem // 86400; hours = (rem % 86400) // 3600
    return f"{days}d {hours}h" if days else f"{hours}h"

def fmt_num(n): return "∞" if n == -1 else str(n)

# ============================================================
#  AI TEXT GENERATION
# ============================================================
async def ai_generate_text(prompt, system=None):
    providers = await db_list_providers()
    errors = []
    for p in providers:
        if not p["enabled"]: continue
        api_key = p["api_key"] or ""
        ptype = p["type"]
        defn = next((d for d in PROVIDER_DEFS if d["type"] == ptype), None)
        if not defn: continue
        if not defn.get("nokey") and not api_key: continue
        models = [p["model"]] if p["model"] else []
        models += [m for m in KNOWN_MODELS.get(ptype, []) if m not in models]
        if p["last_working_model"] and p["last_working_model"] not in models:
            models.insert(0, p["last_working_model"])
        for model in models[:4]:
            try:
                if ptype == "gemini":
                    base = p["base_url"] or "https://generativelanguage.googleapis.com"
                    url = f"{base}/v1beta/models/{model}:generateContent?key={api_key}"
                    body = {"contents": [{"parts": [{"text": prompt}]}],
                            "generationConfig": {"temperature": 0.9, "maxOutputTokens": 2500}}
                    if system: body["systemInstruction"] = {"parts": [{"text": system}]}
                    status, j = await http_json(url, "POST",
                        {"Content-Type": "application/json"}, body)
                    if status == 200:
                        parts = j.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                        txt = "".join(x.get("text", "") for x in parts)
                        if txt:
                            await db_update_provider(p["id"], last_working_model=model)
                            return {"ok": True, "text": txt,
                                    "provider": p["name"], "model": model}
                    errors.append(f"{p['name']}/{model}: HTTP {status}")
                else:
                    base = (p["base_url"] or defn["base"]).rstrip("/")
                    if not base.endswith("/v1") and "generativelanguage" not in base:
                        base += "/v1"
                    url = f"{base}/chat/completions"
                    headers = {"Content-Type": "application/json"}
                    if api_key: headers["Authorization"] = f"Bearer {api_key}"
                    msgs = ([{"role": "system", "content": system}] if system else []) + \
                           [{"role": "user", "content": prompt}]
                    body = {"model": model, "messages": msgs,
                            "temperature": 0.9, "max_tokens": 2500}
                    status, j = await http_json(url, "POST", headers, body)
                    if status == 200 and "choices" in j:
                        txt = j["choices"][0]["message"]["content"]
                        await db_update_provider(p["id"], last_working_model=model)
                        return {"ok": True, "text": txt,
                                "provider": p["name"], "model": model}
                    errors.append(f"{p['name']}/{model}: HTTP {status}")
            except Exception as e:
                errors.append(f"{p['name']}/{model}: {e}")
    return {"ok": False, "errors": errors or ["No AI provider configured."]}

# ============================================================
#  IMAGE FETCHING
# ============================================================
async def _fetch_pollinations(prompt, w, h):
    url = (f"https://image.pollinations.ai/prompt/{quote(prompt[:180], safe='')}"
           f"?width={w}&height={h}&nologo=true&seed={int(datetime.now().timestamp())}")
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=90)) as r:
                if r.status == 200:
                    d = await r.read()
                    if len(d) > 1000: return d
    except Exception as e: logger.warning(f"Pollinations: {e}")
    return None

async def _fetch_picsum(prompt, w, h):
    seed = int(datetime.now().timestamp() * 1000) % 1000000
    url = f"https://picsum.photos/seed/{seed}/{w}/{h}"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=30),
                             allow_redirects=True) as r:
                if r.status == 200:
                    d = await r.read()
                    if len(d) > 1000: return d
    except Exception as e: logger.warning(f"Picsum: {e}")
    return None

async def _fetch_loremflickr(prompt, w, h):
    kw = ",".join([x for x in re.split(r"[\s,]+", prompt) if x][:3]) or "abstract"
    seed = int(datetime.now().timestamp() * 1000) % 1000000
    url = f"https://loremflickr.com/{w}/{h}/{quote(kw, safe=',')}?random={seed}"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=30),
                             allow_redirects=True) as r:
                if r.status == 200:
                    d = await r.read()
                    if len(d) > 1000: return d
    except Exception as e: logger.warning(f"LoremFlickr: {e}")
    return None

async def generate_ai_image(prompt, width=1080, height=1080, source="cascade"):
    if source == "pollinations": return await _fetch_pollinations(prompt, width, height)
    if source == "picsum": return await _fetch_picsum(prompt, width, height)
    if source == "loremflickr": return await _fetch_loremflickr(prompt, width, height)
    for fn in [_fetch_pollinations, _fetch_loremflickr, _fetch_picsum]:
        d = await fn(prompt, width, height)
        if d: return d
    return None

async def upload_to_imgbb(image_bytes, name=None):
    key = await get_setting("imgbb_key", "")
    if not key: return {"ok": False, "error": "No ImgBB key."}
    b64 = base64.b64encode(image_bytes).decode()
    data = {"key": key, "image": b64}
    if name: data["name"] = name[:60]
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post("https://api.imgbb.com/1/upload", data=data,
                timeout=aiohttp.ClientTimeout(total=90)) as r:
                j = await r.json()
                if j.get("success") and j.get("data"):
                    return {"ok": True, "url": j["data"]["url"]}
                return {"ok": False, "error": str(j)[:200]}
    except Exception as e: return {"ok": False, "error": str(e)}

# ============================================================
#  IMAGE COMPOSER (unchanged from original)
# ============================================================
async def compose_image(photo_bytes, headline="", template="bottom_bar",
    color_hex="#ffce00", brand_name=None, brand_handle=None, brand_website=None):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError: return photo_bytes
    if not brand_name: brand_name = await get_setting("brand_name", "My Channel")
    if not brand_handle: brand_handle = await get_setting("brand_handle", "")
    if not brand_website: brand_website = await get_setting("brand_website", "")
    try: img = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
    except Exception: return photo_bytes
    W, H = img.size; draw = ImageDraw.Draw(img); scale = W / 1080
    try:
        cr = int(color_hex[1:3], 16); cg = int(color_hex[3:5], 16); cb = int(color_hex[5:7], 16)
    except Exception: cr, cg, cb = 255, 206, 0
    def _has_bn(s): return bool(re.search(r"[\u0980-\u09FF]", str(s or "")))
    _FONT_CACHE = {}
    def load_font(size, bold=True, bengali=False):
        key = (int(size), bold, bengali)
        if key in _FONT_CACHE: return _FONT_CACHE[key]
        size = int(size)
        if bengali:
            candidates = ["/usr/share/fonts/truetype/noto/NotoSansBengali-Bold.ttf" if bold
                else "/usr/share/fonts/truetype/noto/NotoSansBengali-Regular.ttf",
                "/usr/share/fonts/truetype/kalpurush/Kalpurush.ttf",
                "/usr/share/fonts/truetype/lohit-bengali/Lohit-Bengali.ttf",
                "/usr/share/fonts/truetype/solaimanlipi/SolaimanLipi.ttf",
                "/usr/share/fonts/truetype/mukti/MuktiNarrowBold.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"]
        else:
            candidates = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
                else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold
                else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"]
        for p in candidates:
            try:
                f = ImageFont.truetype(p, size); _FONT_CACHE[key] = f; return f
            except Exception: continue
        f = ImageFont.load_default(); _FONT_CACHE[key] = f; return f
    def pick_font(size, bold, *texts):
        return load_font(size, bold, bengali=any(_has_bn(t) for t in texts if t))
    def wrap_text(text, font, max_w):
        words = str(text).split(); lines, cur = [], ""
        for w in words:
            test = (cur + " " + w).strip()
            try: tw = draw.textlength(test, font=font)
            except Exception: tw = len(test) * 15
            if tw <= max_w: cur = test
            else:
                if cur: lines.append(cur)
                cur = w
        if cur: lines.append(cur)
        return lines

    def draw_bottom_bar():
        bar_h = int(H * 0.11)
        ov = Image.new("RGBA", (W, bar_h), (0, 0, 0, 215)); img.paste(ov, (0, H - bar_h), ov)
        draw.rectangle([0, H - bar_h, W, H - bar_h + 6], fill=(cr, cg, cb))
        f_big = pick_font(42 * scale, True, brand_name)
        f_sm = pick_font(28 * scale, False, brand_handle, brand_website)
        pad = int(W * 0.045)
        draw.text((pad, H - bar_h + int(bar_h * 0.16)), brand_name or "",
                  fill=(255, 255, 255), font=f_big)
        meta = "  •  ".join(x for x in [brand_website, brand_handle] if x)
        if meta:
            draw.text((pad, H - bar_h + int(bar_h * 0.62)), meta,
                      fill=(cr, cg, cb), font=f_sm)
    def draw_top_ribbon():
        rh = int(H * 0.11)
        ov = Image.new("RGBA", (W, rh), (0, 0, 0, 215)); img.paste(ov, (0, 0), ov)
        draw.rectangle([0, rh, W, rh + 6], fill=(cr, cg, cb))
        f_big = pick_font(42 * scale, True, brand_name)
        f_sm = pick_font(28 * scale, False, brand_handle, brand_website)
        pad = int(W * 0.045)
        draw.text((pad, int(rh * 0.2)), brand_name or "",
                  fill=(255, 255, 255), font=f_big)
        meta = "  •  ".join(x for x in [brand_website, brand_handle] if x)
        if meta:
            try: tw = draw.textlength(meta, font=f_sm)
            except Exception: tw = len(meta) * 15
            draw.text((W - pad - tw, int(rh * 0.2)), meta, fill=(cr, cg, cb), font=f_sm)
    def draw_side_ribbon():
        rw = int(W * 0.13)
        ov = Image.new("RGBA", (rw, H), (0, 0, 0, 215)); img.paste(ov, (0, 0), ov)
        draw.rectangle([rw, 0, rw + 6, H], fill=(cr, cg, cb))
        ti = Image.new("RGBA", (H, rw), (0, 0, 0, 0)); td = ImageDraw.Draw(ti)
        f = pick_font(44 * scale, True, brand_name); nm = (brand_name or "")[:20]
        try: tw = td.textlength(nm, font=f)
        except Exception: tw = len(nm) * 24
        td.text((H // 2 - tw // 2, int(rw * 0.15)), nm, fill=(255, 255, 255), font=f)
        ti = ti.rotate(-90, expand=True); img.paste(ti, (0, 0), ti)
    def draw_magazine():
        mh = int(H * 0.22)
        draw.rectangle([0, H - mh, W, H], fill=(cr, cg, cb))
        f_huge = pick_font(96 * scale, True, brand_name)
        f_sm = pick_font(30 * scale, False, brand_handle, brand_website)
        pad = int(W * 0.05); nm = (brand_name or "")[:12].upper()
        tc = (28, 26, 21) if (cr + cg + cb) > 400 else (255, 255, 255)
        draw.text((pad, H - mh + int(mh * 0.18)), nm, fill=tc, font=f_huge)
        meta = "  •  ".join(x for x in [brand_website, brand_handle] if x)
        if meta: draw.text((pad, H - mh + int(mh * 0.72)), meta, fill=tc, font=f_sm)
    def draw_minimal_center():
        f_big = pick_font(58 * scale, True, brand_name); nm = brand_name or ""
        try: tw = draw.textlength(nm, font=f_big)
        except Exception: tw = len(nm) * 30
        cx = W // 2 - tw // 2; cy = H - int(H * 0.16)
        draw.text((cx + 3, cy + 3), nm, fill=(0, 0, 0), font=f_big)
        draw.text((cx, cy), nm, fill=(255, 255, 255), font=f_big)
        bar_y = cy + int(f_big.size * 1.3); bw = int(W * 0.2)
        draw.rectangle([W // 2 - bw // 2, bar_y, W // 2 + bw // 2, bar_y + 6], fill=(cr, cg, cb))
    def draw_gradient_fade():
        gH = int(H * 0.4); grad = Image.new("RGBA", (W, gH), (0, 0, 0, 0))
        gd = ImageDraw.Draw(grad)
        for y in range(gH):
            a = int(220 * (y / gH)); gd.rectangle([0, y, W, y + 1], fill=(0, 0, 0, a))
        img.paste(grad, (0, H - gH), grad)
        f_big = pick_font(48 * scale, True, brand_name); pad = int(W * 0.05)
        draw.rectangle([pad, H - int(H * 0.14), pad + 90, H - int(H * 0.14) + 6],
                       fill=(cr, cg, cb))
        draw.text((pad, H - int(H * 0.12)), brand_name or "",
                  fill=(255, 255, 255), font=f_big)
    def draw_corner_badge():
        bs = int(190 * scale)
        draw.polygon([(W, 0), (W - bs, 0), (W, bs)], fill=(cr, cg, cb))
        f = pick_font(60 * scale, True, brand_name)
        init = (brand_name or "A").strip()[0].upper()
        try: tw = draw.textlength(init, font=f)
        except Exception: tw = 30
        draw.text((W - int(bs * 0.55) - tw // 2, int(bs * 0.15)),
                  init, fill=(255, 255, 255), font=f)
        bh = int(H * 0.1); ov = Image.new("RGBA", (W, bh), (0, 0, 0, 215))
        img.paste(ov, (0, H - bh), ov)
        draw.rectangle([0, H - bh, W, H - bh + 6], fill=(cr, cg, cb))
        f_big = pick_font(38 * scale, True, brand_name); pad = int(W * 0.045)
        draw.text((pad, H - bh + int(bh * 0.2)), brand_name or "",
                  fill=(255, 255, 255), font=f_big)
    def draw_news_card():
        hh = int(H * 0.13); draw.rectangle([0, 0, W, hh], fill=(cr, cg, cb))
        tc = (28, 26, 21) if (cr + cg + cb) > 400 else (255, 255, 255)
        f_tag = pick_font(36 * scale, True, "NEWS"); pad = int(W * 0.05)
        draw.text((pad, int(hh * 0.2)), "● NEWS", fill=tc, font=f_tag)
        dt = datetime.now().strftime("%d %b %Y · %H:%M")
        f_sm = pick_font(22 * scale, False, dt)
        try: dw = draw.textlength(dt, font=f_sm)
        except Exception: dw = len(dt) * 12
        draw.text((W - pad - dw, int(hh * 0.35)), dt, fill=tc, font=f_sm)
        bh = int(H * 0.2); ov = Image.new("RGBA", (W, bh), (0, 0, 0, 230))
        img.paste(ov, (0, H - bh), ov)
        draw.rectangle([0, H - bh, W, H - bh + 6], fill=(cr, cg, cb))
        if headline:
            f_head = pick_font(44 * scale, True, headline)
            lines = wrap_text(headline, f_head, W - pad * 2)[:3]
            y = H - bh + int(bh * 0.15)
            for ln in lines:
                draw.text((pad, y), ln, fill=(255, 255, 255), font=f_head)
                y += int(f_head.size * 1.15)
        else:
            f_big = pick_font(44 * scale, True, brand_name)
            draw.text((pad, H - bh + int(bh * 0.3)), brand_name or "",
                      fill=(255, 255, 255), font=f_big)
    def draw_glass_card():
        cw, ch = int(W * 0.86), int(H * 0.22)
        cx, cy = (W - cw) // 2, H - ch - int(H * 0.06)
        card = Image.new("RGBA", (cw, ch), (255, 255, 255, 35))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([0, 0, cw, ch], radius=int(28 * scale),
            fill=(255, 255, 255, 30), outline=(255, 255, 255, 80), width=2)
        img.paste(card, (cx, cy), card)
        draw.rounded_rectangle([cx + int(cw * 0.04), cy + int(ch * 0.15),
            cx + int(cw * 0.04) + int(6 * scale), cy + int(ch * 0.85)],
            radius=3, fill=(cr, cg, cb))
        f_big = pick_font(46 * scale, True, brand_name); pad = int(cw * 0.09)
        draw.text((cx + pad, cy + int(ch * 0.18)), brand_name or "",
                  fill=(255, 255, 255), font=f_big)
    def draw_neon_glow():
        try: from PIL import ImageFilter as IF
        except Exception: IF = None
        bh = int(H * 0.13)
        glow = Image.new("RGBA", (W, bh + int(60 * scale)), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.rounded_rectangle([int(W * 0.03), int(30 * scale),
            W - int(W * 0.03), bh + int(30 * scale)],
            radius=int(20 * scale), fill=(cr, cg, cb, 200))
        if IF: glow = glow.filter(IF.GaussianBlur(int(20 * scale)))
        img.paste(glow, (0, H - bh - int(60 * scale)), glow)
        ov = Image.new("RGBA", (W, bh), (0, 0, 0, 220))
        img.paste(ov, (0, H - bh), ov)
        draw.rectangle([0, H - bh, W, H - bh + 4], fill=(cr, cg, cb))
        f_big = pick_font(42 * scale, True, brand_name); pad = int(W * 0.05)
        draw.text((pad, H - bh + int(bh * 0.15)), brand_name or "",
                  fill=(255, 255, 255), font=f_big)
    def draw_split_screen():
        pw = int(W * 0.32)
        panel = Image.new("RGBA", (pw, H), (0, 0, 0, 220))
        img.paste(panel, (0, 0), panel)
        draw.rectangle([pw, 0, pw + 6, H], fill=(cr, cg, cb))
        f_init = pick_font(140 * scale, True, brand_name)
        init = (brand_name or "A").strip()[0].upper()
        try: tw = draw.textlength(init, font=f_init)
        except Exception: tw = 80
        draw.text((pw // 2 - tw // 2, int(H * 0.08)), init, fill=(cr, cg, cb), font=f_init)
        f_big = pick_font(40 * scale, True, brand_name); nm = (brand_name or "")[:16]
        ti = Image.new("RGBA", (H, pw), (0, 0, 0, 0)); td = ImageDraw.Draw(ti)
        try: tw2 = td.textlength(nm, font=f_big)
        except Exception: tw2 = len(nm) * 22
        td.text((H // 2 - tw2 // 2, int(pw * 0.5)), nm, fill=(255, 255, 255), font=f_big)
        ti = ti.rotate(-90, expand=True); img.paste(ti, (0, 0), ti)
    def draw_bold_stripe():
        sh = int(H * 0.18)
        draw.polygon([(0, H - sh), (W, H - sh - int(40 * scale)), (W, H), (0, H)],
                     fill=(cr, cg, cb))
        f_big = pick_font(56 * scale, True, brand_name); pad = int(W * 0.05)
        tc = (28, 26, 21) if (cr + cg + cb) > 400 else (255, 255, 255)
        draw.text((pad, H - int(sh * 0.75)), brand_name or "", fill=tc, font=f_big)

    try:
        drawer = {"bottom_bar": draw_bottom_bar, "top_ribbon": draw_top_ribbon,
            "side_ribbon": draw_side_ribbon, "magazine": draw_magazine,
            "minimal_center": draw_minimal_center, "gradient_fade": draw_gradient_fade,
            "corner_badge": draw_corner_badge, "news_card": draw_news_card,
            "glass_card": draw_glass_card, "neon_glow": draw_neon_glow,
            "split_screen": draw_split_screen, "bold_stripe": draw_bold_stripe}
        (drawer.get(template) or draw_bottom_bar)()
    except Exception as e: logger.error(f"compose: {e}")

    if headline and template != "news_card":
        try:
            f_head = pick_font(50 * scale, True, headline); max_w = W - int(W * 0.1)
            lines = wrap_text(headline, f_head, max_w)[:3]
            line_h = int(f_head.size * 1.2)
            block_h = line_h * len(lines) + int(40 * scale); block_y = int(H * 0.08)
            ov = Image.new("RGBA", (W, block_h), (0, 0, 0, 155))
            img.paste(ov, (0, block_y), ov)
            draw.rectangle([0, block_y, int(8 * scale), block_y + block_h], fill=(cr, cg, cb))
            y = block_y + int(20 * scale)
            for ln in lines:
                draw.text((int(W * 0.05) + 2, y + 2), ln, fill=(0, 0, 0), font=f_head)
                draw.text((int(W * 0.05), y), ln, fill=(255, 255, 255), font=f_head)
                y += int(line_h)
        except Exception as e: logger.warning(f"hl: {e}")

    out = io.BytesIO()
    img.save(out, format="JPEG", quality=90, optimize=True)
    return out.getvalue()

# ============================================================
#  RSS FEEDS
# ============================================================
RSS_FEEDS = [
    ("Prothom Alo", "https://www.prothomalo.com/feed", "bn"),
    ("BDNews24", "https://bangla.bdnews24.com/rss.xml", "bn"),
    ("Kaler Kantho", "https://www.kalerkantho.com/rss.xml", "bn"),
    ("Jugantor", "https://www.jugantor.com/rss.xml", "bn"),
    ("Samakal", "https://samakal.com/rss.xml", "bn"),
    ("Dhaka Post", "https://www.dhakapost.com/rss.xml", "bn"),
    ("The Daily Star", "https://www.thedailystar.net/frontpage/rss.xml", "en"),
    ("BBC News", "https://feeds.bbci.co.uk/news/rss.xml", "en"),
    ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml", "en"),
    ("The Guardian", "https://www.theguardian.com/world/rss", "en"),
    ("TechCrunch", "https://techcrunch.com/feed/", "en"),
    ("The Verge", "https://www.theverge.com/rss/index.xml", "en")]

async def fetch_rss_article(topic):
    clean = re.sub(r"\b(news|latest|breaking|today)\b", "",
                   (topic or "").lower(), flags=re.I).strip()
    words = [w for w in clean.split() if len(w) > 2]
    is_bn = bool(re.search(r"[\u0980-\u09FF]", topic or ""))
    feeds = list(RSS_FEEDS)
    if is_bn: feeds.sort(key=lambda f: 0 if f[2] == "bn" else 1)
    all_items = []
    for name, url, lang in feeds[:10]:
        r2j = "https://api.rss2json.com/v1/api.json?rss_url=" + quote(url, safe="")
        status, j = await http_json(r2j, timeout=15)
        if status == 200 and j.get("status") == "ok":
            for it in j.get("items", []):
                img = it.get("thumbnail") or ""
                if not img:
                    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']',
                                  it.get("description", ""))
                    if m: img = m.group(1)
                desc = re.sub(r"<[^>]+>", " ", it.get("description", ""))[:2000]
                all_items.append({"title": it.get("title", ""), "image": img,
                    "desc": re.sub(r"\s+", " ", desc).strip(), "source": name})
    if not all_items: return {"ok": False, "error": "No RSS items found."}
    def score(item):
        sc_v = 0; t = item["title"].lower(); d = (item["desc"] or "").lower()
        if item["image"]: sc_v += 100
        for w in words:
            if w in t: sc_v += 20
            if w in d: sc_v += 8
        return sc_v
    all_items.sort(key=score, reverse=True)
    for cand in all_items[:8]:
        if not cand["image"]: continue
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(cand["image"],
                    timeout=aiohttp.ClientTimeout(total=20)) as r:
                    if r.status == 200 and r.headers.get("Content-Type","").startswith("image/"):
                        ib = await r.read()
                        if len(ib) > 3000:
                            return {"ok": True, "title": cand["title"],
                                    "desc": cand["desc"], "source": cand["source"],
                                    "image_bytes": ib, "image_url": cand["image"]}
        except Exception: continue
    best = all_items[0]
    return {"ok": True, "title": best["title"], "desc": best["desc"],
            "source": best["source"], "image_bytes": None, "image_url": None}

# ============================================================
#  SEND HELPERS
# ============================================================
def get_bot_for_token(token):
    if not token or token == TOKEN: return bot
    if token not in _bot_cache: _bot_cache[token] = Bot(token=token)
    return _bot_cache[token]

async def send_photo_to(account, caption, image_url=None,
                        image_bytes=None, buttons=None):
    token = account["bot_token"] if "bot_token" in account.keys() else ""
    chat_id = account["chat_id"] if "chat_id" in account.keys() else ""
    if not chat_id: return False, "No chat_id configured."
    b = get_bot_for_token(token or TOKEN)
    if image_url:
        try:
            await b.send_photo(chat_id, image_url,
                               caption=caption[:1024], reply_markup=buttons)
            return True, ""
        except Exception as e: logger.warning(f"URL photo: {e}")
    if image_bytes:
        try:
            await b.send_photo(chat_id,
                BufferedInputFile(image_bytes, filename="post.jpg"),
                caption=caption[:1024], reply_markup=buttons)
            return True, ""
        except Exception as e: return False, str(e)
    try:
        await b.send_message(chat_id, caption[:4096], reply_markup=buttons)
        return True, ""
    except Exception as e: return False, str(e)

async def send_media_group_to(account, image_list, caption="", buttons=None):
    token = account["bot_token"] if "bot_token" in account.keys() else ""
    chat_id = account["chat_id"] if "chat_id" in account.keys() else ""
    if not chat_id: return False, "No chat_id configured."
    b = get_bot_for_token(token or TOKEN)
    if len(image_list) < 2:
        return await send_photo_to(account, caption,
            image_bytes=image_list[0] if image_list else None, buttons=buttons)
    try:
        media = [InputMediaPhoto(
                    media=BufferedInputFile(d, filename=f"img{i}.jpg"),
                    caption=caption[:1024] if i == 0 else None)
                 for i, d in enumerate(image_list[:10])]
        await b.send_media_group(chat_id, media=media)
        if buttons: await b.send_message(chat_id, "⬇", reply_markup=buttons)
        return True, ""
    except Exception as e: return False, str(e)

async def send_text_to(account, text, buttons=None):
    token = account["bot_token"] if "bot_token" in account.keys() else ""
    chat_id = account["chat_id"] if "chat_id" in account.keys() else ""
    if not chat_id: return False, "No chat_id configured."
    b = get_bot_for_token(token or TOKEN)
    try:
        await b.send_message(chat_id, text[:4096], reply_markup=buttons)
        return True, ""
    except Exception as e: return False, str(e)

async def send_file_to(account, ctype, file_id, caption="", buttons=None):
    token = account["bot_token"] if "bot_token" in account.keys() else ""
    chat_id = account["chat_id"] if "chat_id" in account.keys() else ""
    if not chat_id: return False, "No chat_id configured."
    b = get_bot_for_token(token or TOKEN)
    try:
        if ctype == "photo": await b.send_photo(chat_id, file_id, caption=caption[:1024], reply_markup=buttons)
        elif ctype == "video": await b.send_video(chat_id, file_id, caption=caption[:1024], reply_markup=buttons)
        elif ctype == "document": await b.send_document(chat_id, file_id, caption=caption[:1024], reply_markup=buttons)
        elif ctype == "audio": await b.send_audio(chat_id, file_id, caption=caption[:1024], reply_markup=buttons)
        elif ctype == "voice": await b.send_voice(chat_id, file_id, caption=caption[:1024], reply_markup=buttons)
        else: await b.send_message(chat_id, caption[:4096], reply_markup=buttons)
        return True, ""
    except Exception as e: return False, str(e)

async def _send_ai_rewrite(account, rewritten, *, image_bytes=None, video_bytes=None,
                           video_name="video.mp4", doc_bytes=None, doc_name="file.bin"):
    MAX_CAP = 1024
    rewritten = rewritten or ""
    cap = rewritten[:MAX_CAP]
    overflow = rewritten[MAX_CAP:] if len(rewritten) > MAX_CAP else ""
    token = account["bot_token"] if "bot_token" in account.keys() else ""
    chat_id = account["chat_id"] if "chat_id" in account.keys() else ""
    if not chat_id: return False, "No chat_id configured."
    b = get_bot_for_token(token or TOKEN)
    try:
        if image_bytes:
            await b.send_photo(chat_id,
                BufferedInputFile(image_bytes, filename="post.jpg"),
                caption=cap or None)
        elif video_bytes:
            await b.send_video(chat_id,
                BufferedInputFile(video_bytes, filename=video_name),
                caption=cap or None)
        elif doc_bytes:
            await b.send_document(chat_id,
                BufferedInputFile(doc_bytes, filename=doc_name),
                caption=cap or None)
        elif rewritten:
            await b.send_message(chat_id, rewritten[:4096]); return True, ""
        else: return False, "nothing to send"
        if overflow:
            try: await b.send_message(chat_id, overflow[:4096])
            except Exception: pass
        return True, ""
    except Exception as e:
        logger.error(f"_send_ai_rewrite: {e}")
        if rewritten:
            try:
                await b.send_message(chat_id, rewritten[:4096]); return True, ""
            except Exception as e2: return False, str(e2)
        return False, str(e)

def build_inline_buttons(buttons_str):
    if not buttons_str: return None
    try:
        rows = []
        for pair in buttons_str.split(";"):
            pair = pair.strip()
            if not pair: continue
            if "|" in pair:
                lbl, url = pair.split("|", 1)
                rows.append([InlineKeyboardButton(text=lbl.strip()[:40], url=url.strip())])
        return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None
    except Exception: return None

# ============================================================
#  SCHEDULER
# ============================================================
def auto_slot_times(posts_per_day, from_str, until_str):
    try:
        fh = int(from_str.split(":")[0]); fm = int(from_str.split(":")[1]) if ":" in from_str else 0
        uh = int(until_str.split(":")[0]); um = int(until_str.split(":")[1]) if ":" in until_str else 0
    except Exception: fh, fm, uh, um = 8, 0, 22, 0
    s = fh * 60 + fm; e = uh * 60 + um; span = e - s
    if span <= 0: span = 60
    n = max(1, min(24, posts_per_day))
    if n == 1: minutes = [s + span // 2]
    else:
        step = span / (n - 1); minutes = [int(s + step * i) for i in range(n)]
    return [(m // 60, m % 60) for m in minutes]

def register_automation_jobs(auto):
    aid = auto["id"]
    for i in range(24):
        try: scheduler.remove_job(f"auto_{aid}_{i}")
        except Exception: pass
    if not auto["active"]: return
    slots = auto_slot_times(auto["posts_per_day"], auto["post_from"], auto["post_until"])
    days = [int(d) for d in str(auto["days"]).split(",") if d.strip().isdigit()]
    if not days: days = [0, 1, 2, 3, 4, 5, 6]
    dow = ",".join(map(str, days))
    for idx, (hh, mm) in enumerate(slots):
        try:
            trig = CronTrigger(day_of_week=dow, hour=hh, minute=mm, timezone=TIMEZONE)
            scheduler.add_job(run_automation, trigger=trig, args=[aid, idx],
                id=f"auto_{aid}_{idx}", replace_existing=True, misfire_grace_time=300)
        except Exception as e: logger.error(f"register: {e}")

async def run_automation(aid, slot_idx, dry_run=False):
    auto = await db_get_automation(aid)
    if not auto or (not auto["active"] and not dry_run): return None
    def sg(k, d=None): return auto[k] if k in auto.keys() else d
    topic = auto["topic"]; lang = auto["language"]
    content_source = sg("content_source", "ai"); image_size = sg("image_size", "square")
    image_template = sg("image_template", "bottom_bar"); image_source = sg("image_source", "cascade")
    color_theme = sg("color_theme", "gold"); headline_on_image = sg("headline_on_image", 1)
    num_images = sg("num_images", 1); inline_buttons = sg("inline_buttons", "")
    hashtag_group_id = sg("hashtag_group", "")

    rss_article = None
    if content_source == "rss":
        rss_article = await fetch_rss_article(topic)
        if not rss_article.get("ok"): rss_article = None
    len_map = {"short": "30-60 words", "medium": "60-120 words", "long": "120-200 words"}
    len_hint = len_map.get(auto["post_length"], "60-120 words")

    if rss_article:
        prompt = (f"Rewrite this news in {lang} with completely fresh words.\n\n"
                  f"TITLE: {rss_article['title']}\nSOURCE: {rss_article['source']}\n"
                  f"CONTENT: {rss_article['desc'][:1500]}\n\n"
                  f"RULES: unique, preserve facts, no markdown.\nLength: {len_hint}\n\n"
                  f"Return EXACTLY:\nHeadline: ...\nHook: ...\nBody: ...\nCTA: ...\nHashtags: ...")
        system_msg = "Senior journalist."
    else:
        angles = ["practical benefits", "surprising fact", "story-driven", "3 tips",
                  "question+answer", "myths vs facts", "real example", "step-by-step",
                  "common mistake", "explain why", "inspirational", "data insight"]
        angle = random.choice(angles)
        prompt = (f"Write a fresh social post in {lang} about: {topic}\n"
                  f"Style: {angle}\nLength: {len_hint}\nNo markdown.\n"
                  f"Return EXACTLY:\nHeadline: ...\nHook: ...\nBody: ...\nCTA: ...\nHashtags: ...")
        system_msg = "Social copywriter."

    ai = await ai_generate_text(prompt, system=system_msg)
    if not ai.get("ok"):
        await db_log(0, "fail", str(ai.get("errors"))[:200], automation_id=aid)
        await db_update_automation_run(aid, False); return {"ok": False}

    parsed = parse_labeled(ai["text"])
    if not parsed["headline"]:
        parsed["headline"] = (rss_article["title"] if rss_article else topic)[:80]
    text = strip_md_stars(clean_text(
        f"{parsed['headline']}\n\n{parsed['hook']}\n\n{parsed['body']}\n\n{parsed['cta']}"))
    if auto["use_hashtags"]:
        if hashtag_group_id:
            try:
                grp = await db_get_hashtags(int(hashtag_group_id))
                if grp and grp["tags"]: text += f"\n\n{grp['tags']}"
                elif parsed["hashtags"]: text += f"\n\n{parsed['hashtags']}"
            except Exception:
                if parsed["hashtags"]: text += f"\n\n{parsed['hashtags']}"
        elif parsed["hashtags"]: text += f"\n\n{parsed['hashtags']}"
    if auto["link"]:
        if auto["text_before_link"]: text += f"\n\n{auto['text_before_link']} {auto['link']}"
        else: text += f"\n\n{auto['link']}"
    if rss_article: text += f"\n\n📰 {rss_article['source']}"

    reply_markup = build_inline_buttons(inline_buttons)
    W, H = SIZE_PRESETS.get(image_size, (1080, 1080))
    color_hex = COLOR_THEMES.get(color_theme, "#ffce00")
    images = []
    if rss_article and rss_article.get("image_bytes"):
        composed = await compose_image(rss_article["image_bytes"],
            headline=parsed["headline"] if headline_on_image else "",
            template=image_template, color_hex=color_hex)
        images.append(composed)
    elif auto["generate_image"]:
        base_prompt = f"{parsed['headline']}. {parsed['hook'][:100]}"
        for i in range(min(num_images, 10)):
            vp = base_prompt if i == 0 else f"{base_prompt}, variant {i+1}"
            raw = await generate_ai_image(vp, W, H, source=image_source)
            if raw:
                composed = await compose_image(raw,
                    headline=parsed["headline"] if headline_on_image else "",
                    template=image_template, color_hex=color_hex)
                images.append(composed)
            await asyncio.sleep(0.5)

    acc_ids = [int(x) for x in str(sg("account_ids", "") or "").split(",") if x.strip()]
    if not acc_ids: return {"ok": False, "error": "No accounts configured."}
    if dry_run: return {"ok": True, "text": text, "images": images}

    sent, fail = 0, 0
    for acc_id in acc_ids:
        account = await db_get_account(acc_id)
        if not account: continue
        if len(images) > 1:
            ok, err = await send_media_group_to(account, images, caption=text, buttons=reply_markup)
        elif images:
            ok, err = await send_photo_to(account, text, image_bytes=images[0], buttons=reply_markup)
        else:
            ok, err = await send_text_to(account, text, buttons=reply_markup)
        if ok:
            sent += 1; await db_bump_account_post(acc_id); await db_log(acc_id, "ok", automation_id=aid)
        else:
            fail += 1; await db_log(acc_id, "fail", err, automation_id=aid)
    await db_update_automation_run(aid, success=(sent > 0))
    try:
        await send_safe(auto["owner_id"],
            f"⚡  *{sc('Auto Post Complete')}*\n{divider()}\n"
            f"  📛  Automation     `#{aid}`\n  ✅  Delivered      `{sent}`\n  ❌  Failed         `{fail}`")
    except Exception: pass
    return {"ok": True}

async def load_all_jobs():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM automations WHERE active=1")
        autos = await cur.fetchall()
    for a in autos: register_automation_jobs(a)
    logger.info(f"Loaded {len(autos)} active automations.")

# ============================================================
#  USERBOT MANAGER
# ============================================================
async def start_userbot_from_db(row):
    ub_id = row["id"]
    if ub_id in _userbot_clients:
        try: await _userbot_clients[ub_id].stop()
        except Exception: pass
        del _userbot_clients[ub_id]
    try:
        session_name = os.path.join(SESSION_DIR, f"ub_{ub_id}")
        client = PyroClient(name=session_name, api_id=int(row["api_id"]),
            api_hash=row["api_hash"], session_string=row["session_string"] or None,
            in_memory=False)
        @client.on_message()
        async def _on_msg(c, msg):
            try: await on_userbot_message(ub_id, msg)
            except Exception as e: logger.error(f"ub handler {ub_id}: {e}")
        await client.start()
        _userbot_clients[ub_id] = client
        me = await client.get_me()
        uname = me.username or me.first_name
        logger.info(f"✅ Userbot #{ub_id} started: {uname}")
        try: await client.get_dialogs()
        except Exception as e: logger.debug(f"dialogs prime: {e}")
        return True, uname
    except Exception as e:
        logger.error(f"ub start {ub_id}: {e}"); return False, str(e)

async def stop_userbot(ub_id):
    if ub_id in _userbot_clients:
        try: await _userbot_clients[ub_id].stop()
        except Exception: pass
        del _userbot_clients[ub_id]

async def start_all_userbots():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM userbots WHERE status='active'")
        rows = await cur.fetchall()
    for r in rows:
        ok, info = await start_userbot_from_db(r)
        if not ok: logger.warning(f"Userbot #{r['id']}: {info}")

def _get_file_meta(msg):
    try:
        if msg.document: return (getattr(msg.document, "file_name", None) or "file.bin", "document")
        if msg.video: return (getattr(msg.video, "file_name", None) or "video.mp4", "video")
        if msg.animation: return (getattr(msg.animation, "file_name", None) or "animation.mp4", "video")
        if msg.audio: return (getattr(msg.audio, "file_name", None) or "audio.mp3", "audio")
        if msg.voice: return ("voice.ogg", "voice")
        if msg.photo: return ("photo.jpg", "photo")
        if msg.sticker: return ("sticker.webm", "document")
    except Exception: pass
    return ("file.bin", "document")

def _has_media(msg):
    return bool(msg.photo or msg.video or msg.document or msg.audio
                or msg.voice or msg.animation or msg.sticker)

async def _download_pyro_media(client, msg):
    if not client: return None, None, None
    filename, kind = _get_file_meta(msg)
    try:
        result = await client.download_media(msg, in_memory=True)
        if result is not None:
            if hasattr(result, "getvalue"): data = result.getvalue()
            elif hasattr(result, "read"): data = result.read()
            else: data = bytes(result) if result else None
            if data and len(data) > 0:
                logger.info(f"✅ in-memory: {kind} ({human_size(len(data))})")
                return data, filename, kind
    except Exception as e: logger.warning(f"in-memory failed: {e}")
    for attempt in range(2):
        try:
            os.makedirs(TMP_DIR, exist_ok=True)
            safe = re.sub(r"[^\w.\-]", "_", filename) or "file.bin"
            full_path = os.path.join(TMP_DIR, f"{int(datetime.now().timestamp()*1000)}_{safe}")
            result = await client.download_media(msg, file_name=full_path)
            if result:
                p = str(result)
                if os.path.exists(p) and os.path.getsize(p) > 0:
                    with open(p, "rb") as f: data = f.read()
                    try: os.remove(p)
                    except Exception: pass
                    logger.info(f"✅ disk: {kind} ({human_size(len(data))})")
                    return data, filename, kind
            if attempt == 0: await asyncio.sleep(1)
        except Exception as e:
            logger.warning(f"disk try {attempt+1}: {e}")
            if attempt == 0: await asyncio.sleep(1)
    return None, None, None

async def try_resolve_chat(client, chat_id_str):
    if not client: return None
    s = str(chat_id_str).strip()
    try:
        if s.lstrip("-").isdigit():
            cid = int(s)
            try: return await client.get_chat(cid)
            except Exception:
                try:
                    await client.get_dialogs()
                    return await client.get_chat(cid)
                except Exception: return None
        else: return await client.get_chat(s)
    except Exception as e:
        logger.debug(f"resolve chat {chat_id_str}: {e}"); return None

async def on_userbot_message(ub_id, msg):
    try:
        chat = msg.chat
        if not chat: return
        source_chat_id = chat.id
        source_username = getattr(chat, "username", "") or ""
        try:
            await db_upsert_seen_chat(ub_id, chat.id,
                getattr(chat, "title", None) or getattr(chat, "first_name", "") or "",
                source_username, str(getattr(chat, "type", "unknown")))
        except Exception: pass
        watchers = await db_find_watchers_userbot(ub_id, source_chat_id, source_username)
        if not watchers: return
        src_text = msg.text or msg.caption or ""
        if not (src_text or _has_media(msg)): return
        logger.info(f"✅ UB watcher(s) {[w['id'] for w in watchers]} ← msg {msg.id}")
        for w in watchers:
            ok, reason = should_process_pyro(msg, w)
            if not ok:
                logger.info(f"UB watcher #{w['id']} skip: {reason}"); continue
            if await db_is_processed(w["id"], str(source_chat_id), msg.id): continue
            await db_mark_processed(w["id"], str(source_chat_id), msg.id)
            await db_update_last_seen(w["id"], msg.id)
            await process_watcher_pyro(ub_id, msg, w)
            await db_bump_watcher_count(w["id"])
            await db_bump_userbot(ub_id)
    except Exception as e: logger.error(f"on_userbot_message: {e}")

def should_process_pyro(msg, watcher):
    text = (msg.text or msg.caption or "")
    if not _has_keywords(text, watcher["keyword_filter"]): return False, "keyword"
    if _has_blockwords(text, watcher["block_words"]): return False, "blockword"
    mf = watcher["media_filter"]
    has_photo = bool(msg.photo); has_video = bool(msg.video or msg.animation)
    has_doc = bool(msg.document); has_audio = bool(msg.audio); has_voice = bool(msg.voice)
    has_media = has_photo or has_video or has_doc or has_audio or has_voice
    if mf == "text" and has_media: return False, "text only"
    if mf == "photo" and not has_photo: return False, "photo only"
    if mf == "video" and not has_video: return False, "video only"
    if mf == "document" and not has_doc: return False, "document only"
    if mf == "media" and not has_media: return False, "media only"
    if not _length_ok(text, watcher["min_length"]): return False, "too short"
    return True, ""

async def _send_to_dest(dest, ub_id, msg, src_text, downloaded):
    tb = get_bot_for_token(dest["bot_token"] or TOKEN)
    chat_id = dest["chat_id"]
    caption = (src_text or "")[:1024] if src_text else None
    data, filename, kind = downloaded if downloaded else (None, None, None)
    if data is None and _has_media(msg):
        data, filename, kind = await _download_pyro_media(_userbot_clients.get(ub_id), msg)
    try:
        if kind == "photo" and data:
            await tb.send_photo(chat_id,
                BufferedInputFile(data, filename=filename or "photo.jpg"), caption=caption)
            return True, ""
        if kind == "video" and data:
            if len(data) > BOT_API_MAX_MB * 1024 * 1024:
                await tb.send_message(chat_id, f"{src_text[:400] or '⚠️ Video too large'}")
                return False, f"too large {human_size(len(data))}"
            try:
                await tb.send_video(chat_id,
                    BufferedInputFile(data, filename=filename or "video.mp4"), caption=caption)
                return True, ""
            except Exception:
                await tb.send_document(chat_id,
                    BufferedInputFile(data, filename=filename or "video.mp4"), caption=caption)
                return True, ""
        if kind == "document" and data:
            if len(data) > BOT_API_MAX_MB * 1024 * 1024:
                await tb.send_message(chat_id, f"{src_text[:400] or '⚠️ File too large'}")
                return False, f"too large {human_size(len(data))}"
            await tb.send_document(chat_id,
                BufferedInputFile(data, filename=filename or "file.bin"), caption=caption)
            return True, ""
        if kind == "audio" and data:
            try:
                await tb.send_audio(chat_id,
                    BufferedInputFile(data, filename=filename or "audio.mp3"), caption=caption)
                return True, ""
            except Exception:
                await tb.send_document(chat_id,
                    BufferedInputFile(data, filename=filename or "audio.mp3"), caption=caption)
                return True, ""
        if kind == "voice" and data:
            try:
                await tb.send_voice(chat_id,
                    BufferedInputFile(data, filename=filename or "voice.ogg"), caption=caption)
                return True, ""
            except Exception:
                await tb.send_document(chat_id,
                    BufferedInputFile(data, filename=filename or "voice.ogg"), caption=caption)
                return True, ""
        if src_text:
            await tb.send_message(chat_id, src_text[:4096]); return True, ""
        return False, "no content"
    except Exception as e:
        logger.error(f"send to dest #{dest['wd_id']}: {e}"); return False, str(e)

async def _direct_forward(ub_id, msg, w, mode):
    client = _userbot_clients.get(ub_id)
    if not client:
        logger.error(f"Watcher #{w['id']}: no userbot"); return
    dests = await db_get_watcher_dests(w["id"])
    delay = int(w["delay_seconds"] or 3)
    for d in dests:
        dest_chat = d["chat_id"]
        try:
            dest_id = int(dest_chat) if str(dest_chat).lstrip("-").isdigit() else dest_chat
        except Exception: dest_id = dest_chat
        try:
            if mode == "direct_forward":
                await client.forward_messages(dest_id, msg.chat.id, msg.id)
            else:
                await client.copy_message(dest_id, msg.chat.id, msg.id)
            await db_log_watcher(w["id"], msg.id, d["account_id"], mode, "ok")
            logger.info(f"🚀 UB {mode} #{w['id']} → {d['name']}")
        except Exception as e:
            err = str(e); logger.warning(f"❌ UB {mode} #{w['id']}: {err}")
            await db_log_watcher(w["id"], msg.id, d["account_id"], mode, "fail", err)
        await asyncio.sleep(delay)

async def process_watcher_pyro(ub_id, msg, w):
    mode = w["mode"]
    dests = await db_get_watcher_dests(w["id"])
    if not dests:
        logger.warning(f"UB Watcher #{w['id']}: no destinations"); return
    delay = int(w["delay_seconds"] or 3)
    src_text = msg.text or msg.caption or ""
    if mode in ("direct_forward", "direct_copy"):
        await _direct_forward(ub_id, msg, w, mode); return
    if mode in ("forward", "copy"):
        pre_dl = None
        if _has_media(msg):
            pre_dl = await _download_pyro_media(_userbot_clients.get(ub_id), msg)
        for d in dests:
            try:
                ok, err = await _send_to_dest(d, ub_id, msg, src_text, pre_dl)
                await db_log_watcher(w["id"], msg.id, d["account_id"], mode,
                    "ok" if ok else "fail", err)
                if ok: logger.info(f"✅ UB watcher #{w['id']} → {d['name']}")
            except Exception as e:
                await db_log_watcher(w["id"], msg.id, d["account_id"], mode, "fail", str(e))
            await asyncio.sleep(delay)
        return
    if mode in ("ai_rewrite", "ai_rewrite_image"):
        has_media = _has_media(msg); base_text = src_text.strip()
        if not base_text and not has_media:
            logger.info(f"UB watcher #{w['id']}: skip"); return
        logger.info(f"UB watcher #{w['id']}: AI rewrite START ({mode})")
        rewritten = ""
        if base_text:
            prompt = (f"Rewrite this post in {w['rewrite_language'] or 'English'} "
                      f"with completely fresh wording.\n\nORIGINAL:\n{base_text[:2000]}\n\n"
                      f"RULES: unique wording, keep all facts, no markdown, output ONLY the rewritten content.")
            r = await ai_generate_text(prompt, system="You are a professional journalist.")
            if not r.get("ok"):
                errs = "; ".join(r.get("errors", []))[:400]
                logger.error(f"UB #{w['id']}: AI FAILED — {errs}")
                for d in dests:
                    await db_log_watcher(w["id"], msg.id, d["account_id"], mode,
                        "fail", f"AI: {errs}")
                return
            rewritten = strip_md_stars(clean_text(r["text"]))
            if not rewritten.strip(): return
            logger.info(f"UB #{w['id']}: AI OK via {r['provider']}")
        footer = w["footer"] if "footer" in w.keys() else ""
        if footer:
            rewritten = (rewritten + "\n\n" + footer).strip() if rewritten else footer
        media_data, media_name, media_kind = (None, None, None)
        if has_media:
            media_data, media_name, media_kind = await _download_pyro_media(
                _userbot_clients.get(ub_id), msg)
        branded_bytes = None
        if mode == "ai_rewrite_image" and media_kind == "photo" and media_data:
            try:
                color_hex = w["brand_color"] if "brand_color" in w.keys() else "#ffce00"
                template = w["brand_template"] if "brand_template" in w.keys() else "bottom_bar"
                branded_bytes = await compose_image(media_data, headline="",
                    template=template, color_hex=color_hex)
            except Exception as e: logger.error(f"brand #{w['id']}: {e}")
        send_photo = branded_bytes; send_video = None; send_vdoc = None; vname = None
        if not send_photo:
            if media_kind == "photo" and media_data: send_photo = media_data
            elif media_kind == "video" and media_data:
                send_video = media_data; vname = media_name or "video.mp4"
            elif media_kind in ("document", "audio", "voice") and media_data:
                send_vdoc = media_data; vname = media_name or "file.bin"
        sent_any = 0
        for d in dests:
            acc_id = d["account_id"]; acc = await db_get_account(acc_id)
            if not acc:
                await db_log_watcher(w["id"], msg.id, acc_id, mode,
                    "fail", f"account #{acc_id} missing"); continue
            try:
                ok, err = await _send_ai_rewrite(acc, rewritten,
                    image_bytes=send_photo, video_bytes=send_video,
                    video_name=vname or "video.mp4", doc_bytes=send_vdoc,
                    doc_name=vname or "file.bin")
                await db_log_watcher(w["id"], msg.id, acc_id, mode,
                    "ok" if ok else "fail", err)
                if ok:
                    sent_any += 1
                    logger.info(f"✅ UB AI #{w['id']} → {d['name']}")
            except Exception as e:
                await db_log_watcher(w["id"], msg.id, acc_id, mode, "fail", str(e))
            await asyncio.sleep(delay)
        logger.info(f"UB #{w['id']}: DONE — {sent_any}/{len(dests)}")

async def poll_single_watcher(w):
    ub_id = w["userbot_id"]; client = _userbot_clients.get(ub_id)
    if not client: return
    source = (w["source_chat"] or "").strip()
    if not source: return
    chat = await try_resolve_chat(client, source)
    if not chat:
        sid = w["source_chat_id"] if "source_chat_id" in w.keys() else ""
        if sid: chat = await try_resolve_chat(client, sid)
    if not chat: return
    chat_id = chat.id
    last_seen = w["last_seen_msg_id"] if "last_seen_msg_id" in w.keys() else 0
    if last_seen is None: last_seen = 0
    try:
        if last_seen == 0:
            async for msg in client.get_chat_history(chat_id, limit=3):
                last_seen = max(last_seen, msg.id); break
            if last_seen:
                await db_update_last_seen(w["id"], last_seen); return
            return
        new_msgs = []
        async for msg in client.get_chat_history(chat_id, limit=15):
            if msg.id > last_seen: new_msgs.append(msg)
        if not new_msgs: return
        new_msgs.sort(key=lambda m: m.id); max_seen = last_seen
        for msg in new_msgs:
            max_seen = max(max_seen, msg.id)
            src_text = msg.text or msg.caption or ""
            if not (src_text or _has_media(msg)): continue
            if await db_is_processed(w["id"], str(chat_id), msg.id): continue
            ok, _ = should_process_pyro(msg, w)
            if not ok: continue
            await db_mark_processed(w["id"], str(chat_id), msg.id)
            await process_watcher_pyro(ub_id, msg, w)
            await db_bump_watcher_count(w["id"])
            await db_bump_userbot(ub_id)
        await db_update_last_seen(w["id"], max_seen)
    except Exception as e: logger.debug(f"poll #{w['id']}: {e}")

async def poll_userbot_watchers_loop():
    await asyncio.sleep(8)
    while True:
        try:
            watchers = await db_list_all_active_userbot_watchers()
            for w in watchers:
                try: await poll_single_watcher(w)
                except Exception as e: logger.debug(f"poll w {w['id']}: {e}")
        except Exception as e: logger.error(f"poll loop: {e}")
        await asyncio.sleep(POLL_INTERVAL)

# ============================================================
#  WATCHER ENGINE — Bot Sources
# ============================================================
def _media_ok(msg, mf):
    if mf == "any": return True
    if mf == "text": return not (msg.photo or msg.video or msg.document)
    if mf == "photo": return bool(msg.photo)
    if mf == "video": return bool(msg.video)
    return True

def should_process(msg, w):
    text = msg.caption or msg.text or ""
    if not _has_keywords(text, w["keyword_filter"]): return False, "keyword"
    if _has_blockwords(text, w["block_words"]): return False, "blockword"
    if not _media_ok(msg, w["media_filter"]): return False, "media"
    if not _length_ok(text, w["min_length"]): return False, "short"
    return True, ""

async def fetch_image_bytes(b, msg):
    if not msg.photo: return None
    try:
        file = await b.get_file(msg.photo[-1].file_id)
        buf = await b.download_file(file.file_path)
        return buf.read() if hasattr(buf, "read") else bytes(buf)
    except Exception as e: logger.warning(f"img fetch: {e}"); return None

async def _forward_via_bot(source_bot, dest_bot, dest_chat_id,
                           source_chat_id, message_id, mode="forward"):
    try:
        if mode == "forward":
            await source_bot.forward_message(dest_chat_id, source_chat_id, message_id)
        else:
            await source_bot.copy_message(dest_chat_id, source_chat_id, message_id)
        return True, "via source bot"
    except Exception as e1: logger.debug(f"source bot {mode} failed: {e1}")
    if dest_bot is not source_bot:
        try:
            if mode == "forward":
                await dest_bot.forward_message(dest_chat_id, source_chat_id, message_id)
            else:
                await dest_bot.copy_message(dest_chat_id, source_chat_id, message_id)
            return True, "via dest bot"
        except Exception as e2: logger.debug(f"dest bot {mode} failed: {e2}")
    return False, "both failed"

async def process_source_post(source_bot, msg, source_bot_db_id=0):
    source_chat_id = msg.chat.id
    source_username = f"@{msg.chat.username}" if msg.chat.username else ""
    watchers = await db_find_watchers_bot(source_chat_id, source_username, source_bot_db_id)
    if not watchers: return
    src_text = msg.caption or msg.text or ""
    logger.info(f"🎯 bot#{source_bot_db_id} msg {msg.message_id} → {len(watchers)} watchers")
    for w in watchers:
        ok, reason = should_process(msg, w)
        if not ok: continue
        if await db_is_processed(w["id"], str(source_chat_id), msg.message_id): continue
        await db_mark_processed(w["id"], str(source_chat_id), msg.message_id)
        mode = w["mode"]; dests = await db_get_watcher_dests(w["id"])
        if not dests: continue
        delay = int(w["delay_seconds"] or 3); sent_any = False
        if mode in ("forward", "copy"):
            for d in dests:
                try:
                    tb = get_bot_for_token(d["bot_token"] or TOKEN)
                    ok, detail = await _forward_via_bot(source_bot, tb, d["chat_id"],
                        source_chat_id, msg.message_id, mode)
                    if ok:
                        await db_log_watcher(w["id"], msg.message_id, d["account_id"],
                            mode, "ok", detail); sent_any = True
                    else:
                        await db_log_watcher(w["id"], msg.message_id, d["account_id"],
                            mode, "fail", detail)
                except Exception as e:
                    await db_log_watcher(w["id"], msg.message_id, d["account_id"],
                        mode, "fail", str(e))
                await asyncio.sleep(delay)
        elif mode in ("direct_forward", "direct_copy"):
            ub_id = w["userbot_id"] if "userbot_id" in w.keys() else 0
            if not ub_id: continue
            client = _userbot_clients.get(ub_id)
            if not client: continue
            for d in dests:
                dest_chat = d["chat_id"]
                try:
                    dest_id = int(dest_chat) if str(dest_chat).lstrip("-").isdigit() else dest_chat
                except Exception: dest_id = dest_chat
                try:
                    if mode == "direct_forward":
                        await client.forward_messages(dest_id, source_chat_id, msg.message_id)
                    else:
                        await client.copy_message(dest_id, source_chat_id, msg.message_id)
                    await db_log_watcher(w["id"], msg.message_id, d["account_id"], mode, "ok")
                    sent_any = True
                except Exception as e:
                    await db_log_watcher(w["id"], msg.message_id, d["account_id"],
                        mode, "fail", str(e))
                await asyncio.sleep(delay)
        elif mode in ("ai_rewrite", "ai_rewrite_image"):
            has_media = bool(msg.photo or msg.video or msg.document)
            base_text = src_text.strip()
            if not base_text and not has_media: continue
            logger.info(f"Watcher #{w['id']}: AI rewrite START ({mode})")
            rewritten = ""
            if base_text:
                prompt = (f"Rewrite this post in {w['rewrite_language'] or 'English'} "
                          f"with completely fresh wording.\n\nORIGINAL:\n{base_text[:2000]}\n\n"
                          f"RULES: unique wording, keep all facts, no markdown, output ONLY the rewritten content.")
                r = await ai_generate_text(prompt, system="You are a professional journalist.")
                if not r.get("ok"):
                    errs = "; ".join(r.get("errors", []))[:400]
                    for d in dests:
                        await db_log_watcher(w["id"], msg.message_id, d["account_id"],
                            mode, "fail", f"AI: {errs}")
                    continue
                rewritten = strip_md_stars(clean_text(r["text"]))
                if not rewritten.strip(): continue
                logger.info(f"Watcher #{w['id']}: AI OK via {r['provider']}")
            footer = w["footer"] if "footer" in w.keys() else ""
            if footer:
                rewritten = (rewritten + "\n\n" + footer).strip() if rewritten else footer
            photo_bytes = None
            if msg.photo:
                photo_bytes = await fetch_image_bytes(source_bot, msg)
            branded = None
            if mode == "ai_rewrite_image" and photo_bytes:
                try:
                    color_hex = w["brand_color"] if "brand_color" in w.keys() else "#ffce00"
                    template = w["brand_template"] if "brand_template" in w.keys() else "bottom_bar"
                    branded = await compose_image(photo_bytes, headline="",
                        template=template, color_hex=color_hex)
                except Exception as e: logger.error(f"brand #{w['id']}: {e}")
            send_photo = branded or photo_bytes
            for d in dests:
                acc_id = d["account_id"]; acc = await db_get_account(acc_id)
                if not acc:
                    await db_log_watcher(w["id"], msg.message_id, acc_id,
                        mode, "fail", f"account #{acc_id} missing")
                    continue
                try:
                    ok, err = await _send_ai_rewrite(acc, rewritten, image_bytes=send_photo)
                    if ok and not send_photo and (msg.video or msg.document):
                        try:
                            tb = get_bot_for_token(d["bot_token"] or TOKEN)
                            ok2, detail = await _forward_via_bot(source_bot, tb, d["chat_id"],
                                source_chat_id, msg.message_id, "copy")
                            if not ok2:
                                logger.warning(f"media fallback #{w['id']}: {detail}")
                        except Exception as e:
                            logger.warning(f"media fallback #{w['id']}: {e}")
                    await db_log_watcher(w["id"], msg.message_id, acc_id,
                        mode, "ok" if ok else "fail", err)
                    if ok: sent_any = True
                except Exception as e:
                    await db_log_watcher(w["id"], msg.message_id, acc_id,
                        mode, "fail", str(e))
                await asyncio.sleep(delay)
        if sent_any:
            await db_bump_watcher_count(w["id"])

# ============================================================
#  BOT POLLERS
# ============================================================
async def start_bot_poller(bot_row):
    bid = bot_row["id"]
    if bot_row["token"] == TOKEN: return
    if bid in _bot_pollers: return
    task = asyncio.create_task(_poll_added_bot(bid))
    _bot_pollers[bid] = task
    logger.info(f"🔄 Poller started for bot #{bid}")

async def stop_bot_poller(bid):
    if bid in _bot_pollers:
        _bot_pollers[bid].cancel()
        try: await _bot_pollers[bid]
        except Exception: pass
        del _bot_pollers[bid]

async def start_all_bot_pollers():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM bots WHERE status='active' AND token != ?", (TOKEN,))
        rows = await cur.fetchall()
    for r in rows: await start_bot_poller(r)
    logger.info(f"Started {len(_bot_pollers)} extra bot pollers.")

async def _poll_added_bot(bid):
    bot_row = await db_get_bot(bid)
    if not bot_row: return
    b = get_bot_for_token(bot_row["token"])
    try: await b.delete_webhook(drop_pending_updates=False)
    except Exception: pass
    offset = 0
    while True:
        try:
            updates = await b.get_updates(offset=offset, timeout=15,
                allowed_updates=["channel_post", "my_chat_member", "message"])
            for upd in updates:
                offset = upd.update_id + 1
                try: await _handle_added_bot_update(bid, upd, b)
                except Exception as e: logger.debug(f"upd handler: {e}")
        except asyncio.CancelledError: return
        except Exception as e:
            logger.warning(f"poller {bid}: {e}"); await asyncio.sleep(5)

async def _handle_added_bot_update(bid, upd, b):
    if upd.channel_post:
        await process_source_post(b, upd.channel_post, source_bot_db_id=bid)

# ============================================================
#  FSM STATES
# ============================================================
class AddProviderSG(StatesGroup):
    choose_type = State(); enter_key = State(); enter_model = State()
class SettingsSG(StatesGroup):
    imgbb_key = State(); brand_name = State(); brand_handle = State()
    brand_website = State(); brand_color = State()
class ComposeSG(StatesGroup):
    enter_topic = State()
class AccountSG(StatesGroup):
    name = State(); bot_token = State(); chat_id = State()
class BotSG(StatesGroup):
    name = State(); token = State()
class UserbotSG(StatesGroup):
    name = State(); api_id = State(); api_hash = State()
    phone = State(); otp = State(); password = State()
class HashtagSG(StatesGroup):
    name = State(); tags = State()
class AutoSG(StatesGroup):
    name = State(); content_source = State(); topic = State(); language = State()
    post_length = State(); image_size = State(); image_template = State()
    image_source = State(); color_theme = State(); num_images = State()
    headline_on_image = State(); inline_buttons = State(); posts_per_day = State()
    post_window = State(); days = State(); accounts = State(); hashtags = State()
    hashtag_group = State(); link = State(); mode = State(); confirm = State()
class BroadcastSG(StatesGroup):
    choose_targets = State(); enter_content = State()
class WatcherSG(StatesGroup):
    source_type = State(); source_bot = State(); userbot_pick = State()
    source_chat = State(); mode = State(); lang = State()
    keyword = State(); block = State(); min_length = State(); media_filter = State()
    template = State(); color = State(); footer = State(); delay = State()
    dests = State(); confirm = State()
class PaymentSG(StatesGroup):
    enter_trx = State()
class AdminSG(StatesGroup):
    grant_user_id = State(); grant_plan_choose = State(); grant_days = State()
    broadcast_text = State()

# ============================================================
#  KEYBOARDS
# ============================================================
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠  Dashboard", callback_data="m_dash"),
         InlineKeyboardButton(text="⚡  Auto Post", callback_data="m_auto")],
        [InlineKeyboardButton(text="📡  Auto Forward", callback_data="m_watch"),
         InlineKeyboardButton(text="🎨  AI Compose", callback_data="m_compose")],
        [InlineKeyboardButton(text="📣  Broadcast", callback_data="m_bcast"),
         InlineKeyboardButton(text="📊  Statistics", callback_data="m_stats")],
        [InlineKeyboardButton(text="📱  Accounts", callback_data="m_accounts"),
         InlineKeyboardButton(text="🤖  My Bots", callback_data="m_bots")],
        [InlineKeyboardButton(text="👤  Userbots", callback_data="m_userbots"),
         InlineKeyboardButton(text="👁  Seen Chats", callback_data="chats_refresh")],
        [InlineKeyboardButton(text="⚙️  Automations", callback_data="m_autos"),
         InlineKeyboardButton(text="#️⃣  Hashtags", callback_data="m_hashtags")],
        [InlineKeyboardButton(text="🔧  Settings", callback_data="m_set"),
         InlineKeyboardButton(text="📖  Help", callback_data="m_help")],
        [InlineKeyboardButton(text="⭐  Premium Plans", callback_data="pm_main"),
         InlineKeyboardButton(text="💎  My Status", callback_data="pm_status")],
    ])

def settings_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧠  AI Providers", callback_data="s_prov"),
         InlineKeyboardButton(text="☁️  ImgBB", callback_data="s_imgbb")],
        [InlineKeyboardButton(text="🏷  Branding", callback_data="s_brand"),
         InlineKeyboardButton(text="🎨  Templates", callback_data="s_tpl")],
        [InlineKeyboardButton(text="🏠  Back", callback_data="m_home")]])

def back_home():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠  Main Menu", callback_data="m_home")]])

def days_kb(sel):
    rows = []
    for i, d in enumerate(WEEKDAYS):
        mark = "✅" if i in sel else "☐"
        rows.append([InlineKeyboardButton(text=f"{mark}  {d}  ·  {WEEKDAYS_BN[i]}",
                                          callback_data=f"ady_{i}")])
    rows.append([InlineKeyboardButton(text="✓  Confirm Selection", callback_data="ady_DONE")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def templates_kb(active=None):
    rows = []; items = list(TEMPLATE_LABELS.items())
    for i in range(0, len(items), 2):
        row = [InlineKeyboardButton(
            text=("✅ " if items[i][0] == active else "") + items[i][1],
            callback_data=f"atpl_{items[i][0]}")]
        if i + 1 < len(items):
            row.append(InlineKeyboardButton(
                text=("✅ " if items[i+1][0] == active else "") + items[i+1][1],
                callback_data=f"atpl_{items[i+1][0]}"))
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)

def size_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=v, callback_data=f"asize_{k}")]
        for k, v in SIZE_LABELS.items()])

def color_kb():
    rows = []; items = list(COLOR_LABELS.items())
    for i in range(0, len(items), 2):
        row = [InlineKeyboardButton(text=items[i][1], callback_data=f"acolor_{items[i][0]}")]
        if i + 1 < len(items):
            row.append(InlineKeyboardButton(text=items[i+1][1], callback_data=f"acolor_{items[i+1][0]}"))
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)

def source_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=v, callback_data=f"asrc_img_{k}")]
        for k, v in IMAGE_SOURCES.items()])

def plans_kb(current_plan):
    rows = []
    for key in ["free", "premium", "pro", "starter_yearly"]:
        p = PLANS[key]
        price = "Free" if p["price"] == 0 else f"৳{p['price']:,}"
        marker = " ✓" if key == current_plan else ""
        rows.append([InlineKeyboardButton(
            text=f"{p['emoji']} {p['name']} · {price}{marker}",
            callback_data=f"pm_plan_{key}")])
    rows.append([InlineKeyboardButton(text="📊 My Status", callback_data="pm_status")])
    rows.append([InlineKeyboardButton(text="🏠 Main Menu", callback_data="m_home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def plan_detail_kb(plan_key, is_current):
    rows = []
    if not is_current and PLANS[plan_key]["price"] > 0:
        rows.append([InlineKeyboardButton(text="💳 Buy / Upgrade",
                                          callback_data=f"pm_buy_{plan_key}")])
    rows.append([InlineKeyboardButton(text="◀ Back", callback_data="pm_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def methods_kb(plan_key):
    rows = [[InlineKeyboardButton(
        text=f"{cfg['emoji']} {cfg['name']}",
        callback_data=f"pm_m_{m}_{plan_key}")]
        for m, cfg in PAYMENT_METHODS.items()]
    rows.append([InlineKeyboardButton(text="◀ Back", callback_data=f"pm_plan_{plan_key}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Pending", callback_data="adm_pending"),
         InlineKeyboardButton(text="📊 Stats", callback_data="adm_stats")],
        [InlineKeyboardButton(text="🎁 Grant", callback_data="adm_grant"),
         InlineKeyboardButton(text="📢 Broadcast", callback_data="adm_broadcast")],
        [InlineKeyboardButton(text="🏠 Menu", callback_data="m_home")]])

# ============================================================
#  START COMMAND
# ============================================================
@router.message(CommandStart())
async def cmd_start(m: Message):
    await register_user(m.from_user)
    uid = m.from_user.id
    uname = m.from_user.first_name or "there"
    accts = await db_list_accounts(uid)
    autos = await db_list_automations(uid)
    watch = await db_list_watchers(uid)
    bots_db = await db_list_bots(uid)
    ubs = await db_list_userbots(uid)
    provs = await db_list_providers()
    imgbb = await get_setting("imgbb_key", "")
    active = sum(1 for a in autos if a["active"])
    info = await get_user_plan(uid)
    plan = info["plan_obj"]
    ready = sum([bool(accts), bool(provs), bool(imgbb)])
    pct = int(ready / 3 * 100)
    bar = progress_bar(pct, 12, "▰", "▱")
    exp_line = ""
    if info["plan"] != "free" and info["expires"]:
        exp_line = f"  📅 Plan Expiry    `{fmt_date(info['expires'])}`  _(in {fmt_remaining(info['expires'])})_\n"
    txt = (
        f"🎙  *{sc('AlphaPost Studio Pro')}*\n"
        f"`v16  ·  Premium Edition`\n\n"
        f"👋  Welcome, *{uname}*!\n"
        f"  {plan['emoji']} Plan           *{plan['name']}*\n"
        f"{exp_line}\n"
        f"{divider('Setup Progress')}\n"
        f"`{bar}`  *{pct}%*\n"
        f"  {'✅' if accts else '⬜'}  Destination accounts\n"
        f"  {'✅' if provs else '⬜'}  AI providers\n"
        f"  {'✅' if imgbb else '⬜'}  ImgBB\n\n"
        f"{divider('Overview')}\n"
        f"  📱  Accounts        `{len(accts)}`\n"
        f"  🤖  My Bots         `{len(bots_db)}`\n"
        f"  👤  Userbots        `{len(ubs)}`\n"
        f"  ⚡  Automations     `{len(autos)}`  _(active: {active})_\n"
        f"  📡  Watchers        `{len(watch)}`\n"
        f"  🧠  AI Providers    `{len(provs)}`\n\n"
        f"{divider('Quick Start')}\n"
        f"  `1.`  /addaccount\n"
        f"  `2.`  /adduserbot\n"
        f"  `3.`  /watch\n"
        f"  `4.`  /auto\n"
        f"  `5.`  /premium   ← upgrade to unlock more\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━")
    await send_safe(m.chat.id, txt, reply_markup=main_menu())

@router.message(Command("help"))
async def cmd_help(m: Message):
    txt = (
        f"📖  *HELP*\n{divider()}\n\n"
        f"*Basic:* /start /help /cancel /stats /premium /mystatus\n\n"
        f"*Accounts:* /addaccount /accounts /addbot /mybots\n"
        f"/adduserbot /userbots /chats\n\n"
        f"*Automation:* /auto /watch /watchers /compose /broadcast\n\n"
        f"*Settings:* /setimgbb /branding /hashtags /providers\n\n"
        f"*Admin:* /admin /revoke <uid>\n\n"
        f"💡 *Tips:*\n"
        f"  • Userbot needs admin in source\n"
        f"  • Bot needs admin in source\n"
        f"  • Use ai_rewrite to avoid copyright\n"
        f"  • Upgrade with /premium for more limits\n")
    await send_safe(m.chat.id, txt, reply_markup=back_home())

@router.callback_query(F.data == "m_help")
async def cb_help(c: CallbackQuery):
    await c.answer()
    await cmd_help(c.message)

@router.callback_query(F.data == "m_dash")
async def cb_dash(c: CallbackQuery):
    await c.answer("Loading…")
    uid = c.from_user.id
    accts = await db_list_accounts(uid); autos = await db_list_automations(uid)
    watch = await db_list_watchers(uid); bots_db = await db_list_bots(uid)
    ubs = await db_list_userbots(uid)
    active = sum(1 for a in autos if a["active"]); wa = sum(1 for w in watch if w["active"])
    provs = await db_list_providers(); imgbb = await get_setting("imgbb_key", "")
    info = await get_user_plan(uid); plan = info["plan_obj"]
    async with aiosqlite.connect(DB_PATH) as db:
        ok = (await (await db.execute("SELECT COUNT(*) FROM history WHERE status='ok'")).fetchone())[0]
        fl = (await (await db.execute("SELECT COUNT(*) FROM history WHERE status='fail'")).fetchone())[0]
    rate = int(ok / max(1, ok + fl) * 100)
    bar = progress_bar(rate, 12, "▰", "▱")
    txt = (
        f"📊  *DASHBOARD*\n\n"
        f"  {plan['emoji']} Plan          *{plan['name']}*\n"
        f"{divider('Connections')}\n"
        f"  📱  Accounts       `{len(accts)}`\n"
        f"  🤖  Bots           `{len(bots_db)}`\n"
        f"  👤  Userbots       `{len(ubs)}`\n\n"
        f"{divider('Automation')}\n"
        f"  ⚡  Schedulers     `{len(autos)}`  _(active: {active})_\n"
        f"  📡  Watchers       `{len(watch)}`  _(active: {wa})_\n\n"
        f"{divider('Delivery')}\n"
        f"  `{bar}`  *{rate}%*\n"
        f"  ✅  OK   `{ok}`    ❌  Fail  `{fl}`")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Premium", callback_data="pm_main"),
         InlineKeyboardButton(text="📊 My Status", callback_data="pm_status")],
        [InlineKeyboardButton(text="🔄 Refresh", callback_data="m_dash"),
         InlineKeyboardButton(text="🏠 Menu", callback_data="m_home")]])
    await edit_safe(c.message, txt, reply_markup=kb)

@router.callback_query(F.data == "m_home")
async def cb_home(c: CallbackQuery):
    await c.answer()
    await cmd_start_home(c)

async def cmd_start_home(c):
    uid = c.from_user.id
    accts = await db_list_accounts(uid); autos = await db_list_automations(uid)
    watch = await db_list_watchers(uid); bots_db = await db_list_bots(uid)
    ubs = await db_list_userbots(uid)
    info = await get_user_plan(uid); plan = info["plan_obj"]
    txt = (
        f"🎙  *{sc('AlphaPost Studio Pro')}*\n\n"
        f"  {plan['emoji']}  *{plan['name']}*\n"
        f"  📱 `{len(accts)}`  🤖 `{len(bots_db)}`  👤 `{len(ubs)}`  "
        f"⚡ `{len(autos)}`  📡 `{len(watch)}`\n\n"
        f"_Select an option below_ 👇")
    await edit_safe(c.message, txt, reply_markup=main_menu())

@router.message(Command("stats"))
async def cmd_stats(m: Message):
    accts = await db_list_accounts(m.from_user.id)
    autos = await db_list_automations(m.from_user.id)
    watch = await db_list_watchers(m.from_user.id)
    bots_db = await db_list_bots(m.from_user.id)
    ubs = await db_list_userbots(m.from_user.id)
    async with aiosqlite.connect(DB_PATH) as db:
        ok = (await (await db.execute("SELECT COUNT(*) FROM history WHERE status='ok'")).fetchone())[0]
        fl = (await (await db.execute("SELECT COUNT(*) FROM history WHERE status='fail'")).fetchone())[0]
    rate = int(ok / max(1, ok + fl) * 100)
    bar = progress_bar(rate, 12, "▰", "▱")
    await send_safe(m.chat.id,
        f"📊  *STATISTICS*\n\n"
        f"  📱  Accounts   `{len(accts)}`\n"
        f"  🤖  Bots       `{len(bots_db)}`\n"
        f"  👤  Userbots   `{len(ubs)}`\n"
        f"  ⚡  Automations `{len(autos)}`\n"
        f"  📡  Watchers   `{len(watch)}`\n\n"
        f"  ✅  OK   `{ok}`   ❌ Fail `{fl}`\n"
        f"  `{bar}`  *{rate}%*",
        reply_markup=back_home())

@router.callback_query(F.data == "m_stats")
async def cb_mstats(c: CallbackQuery):
    await c.answer()
    await cmd_stats(c.message)

@router.message(Command("cancel"))
async def cmd_cancel(m: Message, state: FSMContext):
    uid = m.from_user.id
    if uid in _login_clients:
        try: await _login_clients[uid].disconnect()
        except Exception: pass
        del _login_clients[uid]
    await state.clear()
    await send_safe(m.chat.id, "✗ Cancelled.", reply_markup=main_menu())

# ============================================================
#  PREMIUM HANDLERS
# ============================================================
@router.message(Command("premium"))
async def cmd_premium(m: Message, state: FSMContext):
    await state.clear(); await register_user(m.from_user)
    info = await get_user_plan(m.from_user.id); plan = info["plan_obj"]
    exp_line = ""
    if info["plan"] != "free" and info["expires"]:
        exp_line = (f"\n  📅 Expires       `{fmt_date(info['expires'])}`  "
                    f"_(in {fmt_remaining(info['expires'])})_")
    txt = (
        f"⭐  *PREMIUM PLANS*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"  👤 Current Plan   {plan['emoji']}  *{plan['name']}*\n"
        f"{exp_line}\n\n"
        f"  🎁 *Free*           ৳0  ·  forever\n"
        f"  ⭐ *Premium*        ৳599  ·  30 days\n"
        f"  💎 *Pro*            ৳1,499  ·  30 days\n"
        f"  🎯 *Starter Yearly* ৳4,999  ·  365 days  _(30% off)_")
    await m.answer(txt, parse_mode="Markdown", reply_markup=plans_kb(info["plan"]))

@router.message(Command("mystatus"))
async def cmd_mystatus(m: Message):
    await register_user(m.from_user)
    info = await get_user_plan(m.from_user.id); plan = info["plan_obj"]; lim = plan["limits"]
    exp = ("Lifetime / no expiry" if not info["expires"]
           else f"{fmt_date(info['expires'])} ({fmt_remaining(info['expires'])})")
    txt = (
        f"📊  *MY STATUS*\n\n"
        f"  👤 User         `{m.from_user.id}`\n"
        f"  {plan['emoji']} Plan         *{plan['name']}*\n"
        f"  📅 Expiry       {exp}\n"
        f"  💰 Total Paid   ৳{info['total_paid']:,}\n\n"
        f"  📱 Accounts     `{fmt_num(lim['accounts'])}`\n"
        f"  ⚡ Automations  `{fmt_num(lim['automations'])}`\n"
        f"  📡 Watchers     `{fmt_num(lim['watchers'])}`\n"
        f"  👤 Userbots     `{fmt_num(lim['userbots'])}`\n"
        f"  📝 Posts/mo     `{fmt_num(lim['posts_per_month'])}`\n"
        f"  🤖 AI Rewrite   `{'✅' if lim['ai_rewrite'] else '❌'}`\n"
        f"  🎨 All Templates `{'✅' if lim['all_templates'] else '❌'}`")
    await m.answer(txt, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐ View Plans", callback_data="pm_main")],
            [InlineKeyboardButton(text="🏠 Menu", callback_data="m_home")]]))

@router.callback_query(F.data == "pm_main")
async def cb_pm_main(c: CallbackQuery):
    await c.answer()
    info = await get_user_plan(c.from_user.id); plan = info["plan_obj"]
    txt = (
        f"⭐  *PREMIUM PLANS*\n\n"
        f"  👤 Current: {plan['emoji']} *{plan['name']}*\n\n"
        f"  🎁 *Free*           ৳0\n"
        f"  ⭐ *Premium*        ৳599/30d\n"
        f"  💎 *Pro*            ৳1,499/30d\n"
        f"  🎯 *Starter Yearly* ৳4,999/365d")
    try:
        await c.message.edit_text(txt, parse_mode="Markdown",
            reply_markup=plans_kb(info["plan"]))
    except Exception:
        await c.message.answer(txt, parse_mode="Markdown",
            reply_markup=plans_kb(info["plan"]))

@router.callback_query(F.data.startswith("pm_plan_"))
async def cb_pm_plan(c: CallbackQuery):
    key = c.data.replace("pm_plan_", "")
    plan = PLANS.get(key)
    if not plan:
        await c.answer("Unknown", show_alert=True); return
    info = await get_user_plan(c.from_user.id); is_current = info["plan"] == key
    price = "Free" if plan["price"] == 0 else f"৳{plan['price']:,} / {plan['duration_days']} days"
    features = "\n".join(f"  ✅ {f}" for f in plan["features"])
    txt = (f"{plan['emoji']}  *{plan['name']}*\n_{plan['tagline']}_\n\n"
           f"💰 Price  *{price}*\n\n📋 *What you get:*\n{features}\n\n"
           + ("✅ *Current plan*" if is_current else "💡 *Tap Buy to start*"))
    await c.message.edit_text(txt, parse_mode="Markdown",
        reply_markup=plan_detail_kb(key, is_current))

@router.callback_query(F.data == "pm_status")
async def cb_pm_status(c: CallbackQuery):
    await c.answer(); await cmd_mystatus(c.message)

@router.callback_query(F.data.startswith("pm_buy_"))
async def cb_pm_buy(c: CallbackQuery):
    key = c.data.replace("pm_buy_", "")
    plan = PLANS.get(key)
    if not plan or plan["price"] == 0:
        await c.answer("Can't purchase", show_alert=True); return
    txt = (f"💳  *Select Payment Method*\n\n"
           f"  {plan['emoji']} Plan       *{plan['name']}*\n"
           f"  💰 Amount     *৳{plan['price']:,}*")
    await c.message.edit_text(txt, parse_mode="Markdown", reply_markup=methods_kb(key))

@router.callback_query(F.data.startswith("pm_m_"))
async def cb_pm_method(c: CallbackQuery, state: FSMContext):
    parts = c.data.split("_")
    method = parts[2]; plan_key = "_".join(parts[3:])
    plan = PLANS.get(plan_key); cfg = PAYMENT_METHODS.get(method)
    if not plan or not cfg:
        await c.answer("Invalid", show_alert=True); return
    await state.update_data(plan_key=plan_key, method=method)
    await state.set_state(PaymentSG.enter_trx)
    txt = (f"{cfg['emoji']}  *{cfg['name']} Payment*\n\n"
           f"  🎯 Plan       *{plan['name']}*\n"
           f"  💰 Amount     *৳{plan['price']:,}*\n\n"
           f"📱 *Instructions:*\n{cfg['instruction']}\n\n"
           f"✅ *Send the TrxID after payment*\n"
           f"_Example:_ `9F2A1B4C5D`")
    await c.message.edit_text(txt, parse_mode="Markdown")

@router.message(PaymentSG.enter_trx)
async def enter_trx(m: Message, state: FSMContext):
    d = await state.get_data()
    plan_key = d.get("plan_key"); method = d.get("method")
    plan = PLANS.get(plan_key)
    if not plan:
        await state.clear(); await m.answer("❌ Session expired. /premium"); return
    trx = (m.text or "").strip().upper()
    if len(trx) < 6 or " " in trx:
        await m.answer("❌ Invalid TrxID (min 6 characters, no spaces)."); return
    pid = await create_payment(m.from_user.id,
        m.from_user.username or m.from_user.first_name or "",
        plan_key, plan["price"], method, trx)
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 My Status", callback_data="pm_status")],
        [InlineKeyboardButton(text="🏠 Menu", callback_data="m_home")]])
    await m.answer(
        f"✅  *Payment Submitted*\n\n"
        f"  🆔 Receipt    `#PAY-{pid}`\n"
        f"  🎯 Plan       *{plan['name']}*\n"
        f"  💰 Amount     *৳{plan['price']:,}*\n"
        f"  🏦 Method     *{PAYMENT_METHODS[method]['name']}*\n"
        f"  📝 TrxID      `{trx}`\n\n"
        f"⏳ *Pending admin verification.*",
        parse_mode="Markdown", reply_markup=kb)
    try:
        admin_kb_msg = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Approve", callback_data=f"adm_ap_{pid}"),
             InlineKeyboardButton(text="❌ Reject", callback_data=f"adm_rj_{pid}")]])
        await bot.send_message(ADMIN_ID,
            f"💳  *NEW PAYMENT*\n\n"
            f"  🆔 Receipt  `#PAY-{pid}`\n"
            f"  👤 User     `{m.from_user.id}` (@{m.from_user.username or '—'})\n"
            f"  🎯 Plan     *{plan['name']}*\n"
            f"  💰 Amount   *৳{plan['price']:,}*\n"
            f"  🏦 Method   *{PAYMENT_METHODS[method]['name']}*\n"
            f"  📝 TrxID    `{trx}`",
            parse_mode="Markdown", reply_markup=admin_kb_msg)
    except Exception as e: logger.warning(f"notify admin: {e}")

# ── ADMIN ──
def _is_admin(uid): return uid == ADMIN_ID

@router.message(Command("admin"))
async def cmd_admin(m: Message, state: FSMContext):
    if not _is_admin(m.from_user.id):
        await m.answer("⛔ Admin only."); return
    await state.clear()
    stats = await get_premium_stats()
    txt = (f"👑  *ADMIN PANEL*\n\n"
           f"  👥 Users    `{stats['total']}`\n"
           f"  ⭐ Premium  `{stats['premium']}`\n"
           f"  💰 Revenue  `৳{stats['revenue']:,}`\n"
           f"  ⏳ Pending  `{stats['pending']}`")
    await m.answer(txt, parse_mode="Markdown", reply_markup=admin_kb())

@router.callback_query(F.data == "adm_stats")
async def cb_adm_stats(c: CallbackQuery):
    if not _is_admin(c.from_user.id):
        await c.answer("Admin only", show_alert=True); return
    await c.answer()
    stats = await get_premium_stats()
    txt = (f"📊  *PREMIUM STATS*\n\n"
           f"  👥 Total Users       `{stats['total']}`\n"
           f"  ⭐ Premium           `{stats['premium']}`\n"
           f"  📈 Conversion        `{stats['premium']*100//max(1,stats['total'])}%`\n"
           f"  💰 Total Revenue     `৳{stats['revenue']:,}`\n"
           f"  ✅ Approved          `{stats['approved']}`\n"
           f"  ⏳ Pending           `{stats['pending']}`")
    await c.message.edit_text(txt, parse_mode="Markdown", reply_markup=admin_kb())

@router.callback_query(F.data == "adm_pending")
async def cb_adm_pending(c: CallbackQuery):
    if not _is_admin(c.from_user.id):
        await c.answer("Admin only", show_alert=True); return
    await c.answer()
    pend = await list_pending_payments()
    if not pend:
        await c.message.edit_text("✅ *No pending payments.*", parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀ Back", callback_data="adm_back")]]))
        return
    lines = ["💳 *PENDING PAYMENTS*\n"]
    for p in pend:
        m_name = PAYMENT_METHODS.get(p["method"], {}).get("name", p["method"])
        lines.append(f"  *#PAY-{p['id']}* — {p['username'] or p['user_id']}\n"
                     f"    {PLANS[p['plan']]['name']} · ৳{p['amount']:,} · {m_name}")
    kb_rows = [[InlineKeyboardButton(text=f"👁 #{p['id']}",
        callback_data=f"adm_view_{p['id']}")] for p in pend[:10]]
    kb_rows.append([InlineKeyboardButton(text="◀ Back", callback_data="adm_back")])
    await c.message.edit_text("\n".join(lines), parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows))

@router.callback_query(F.data.startswith("adm_view_"))
async def cb_adm_view(c: CallbackQuery):
    if not _is_admin(c.from_user.id):
        await c.answer("Admin only", show_alert=True); return
    pid = int(c.data.replace("adm_view_", ""))
    p = await get_payment(pid)
    if not p:
        await c.answer("Not found", show_alert=True); return
    await c.answer()
    m_name = PAYMENT_METHODS.get(p["method"], {}).get("name", p["method"])
    txt = (f"💳  *PAYMENT #{p['id']}*\n\n"
           f"  👤 User ID   `{p['user_id']}`\n"
           f"  🏷 Username  @{p['username'] or '—'}\n"
           f"  🎯 Plan      *{PLANS[p['plan']]['name']}*\n"
           f"  💰 Amount    *৳{p['amount']:,}*\n"
           f"  🏦 Method    *{m_name}*\n"
           f"  📝 TrxID     `{p['trx_id']}`\n"
           f"  🕒 Date      `{fmt_date(p['submitted_at'])}`")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Approve", callback_data=f"adm_ap_{pid}"),
         InlineKeyboardButton(text="❌ Reject", callback_data=f"adm_rj_{pid}")],
        [InlineKeyboardButton(text="◀ Back", callback_data="adm_pending")]])
    await c.message.edit_text(txt, parse_mode="Markdown", reply_markup=kb)

@router.callback_query(F.data.startswith("adm_ap_"))
async def cb_adm_approve(c: CallbackQuery):
    if not _is_admin(c.from_user.id):
        await c.answer("Admin only", show_alert=True); return
    pid = int(c.data.replace("adm_ap_", ""))
    pay = await approve_payment(pid, c.from_user.id)
    if not pay:
        await c.answer("Already processed", show_alert=True); return
    await c.answer("✅ Approved")
    plan = PLANS[pay["plan"]]
    await c.message.edit_text(
        f"✅  *PAYMENT APPROVED*\n\n"
        f"  🆔 #{pid}\n"
        f"  👤 `{pay['user_id']}`\n"
        f"  🎯 {plan['name']} activated\n"
        f"  💰 ৳{pay['amount']:,}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀ Back", callback_data="adm_back")]]))
    try:
        await bot.send_message(pay["user_id"],
            f"🎉  *Payment Approved!*\n\n"
            f"  🎯 Plan *{plan['name']}* activated\n"
            f"  💰 Paid *৳{pay['amount']:,}*\n\n"
            f"_Enjoy all premium features!_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📊 My Status", callback_data="pm_status")]]))
    except Exception: pass

@router.callback_query(F.data.startswith("adm_rj_"))
async def cb_adm_reject(c: CallbackQuery):
    if not _is_admin(c.from_user.id):
        await c.answer("Admin only", show_alert=True); return
    pid = int(c.data.replace("adm_rj_", ""))
    pay = await reject_payment(pid, c.from_user.id, "Rejected")
    if not pay:
        await c.answer("Already processed", show_alert=True); return
    await c.answer("❌ Rejected")
    await c.message.edit_text(f"❌  *PAYMENT #{pid} REJECTED*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀ Back", callback_data="adm_back")]]))
    try:
        await bot.send_message(pay["user_id"],
            f"❌  *Payment Not Verified*\n\n"
            f"  🆔 #{pid}\n  📝 TrxID `{pay['trx_id']}`\n\n"
            f"_Please verify and try again._",
            parse_mode="Markdown")
    except Exception: pass

@router.callback_query(F.data == "adm_back")
async def cb_adm_back(c: CallbackQuery):
    if not _is_admin(c.from_user.id):
        await c.answer("Admin only", show_alert=True); return
    await c.answer()
    stats = await get_premium_stats()
    await c.message.edit_text(
        f"👑  *ADMIN PANEL*\n\n"
        f"  👥 `{stats['total']}`  ⭐ `{stats['premium']}`  "
        f"💰 `৳{stats['revenue']:,}`  ⏳ `{stats['pending']}`",
        parse_mode="Markdown", reply_markup=admin_kb())

@router.callback_query(F.data == "adm_grant")
async def cb_adm_grant(c: CallbackQuery, state: FSMContext):
    if not _is_admin(c.from_user.id):
        await c.answer("Admin only", show_alert=True); return
    await c.answer()
    await state.set_state(AdminSG.grant_user_id)
    await c.message.answer("🎁 Send the *user ID* to grant premium.\n_Example:_ `8530165612`",
        parse_mode="Markdown")

@router.message(AdminSG.grant_user_id)
async def adm_grant_user(m: Message, state: FSMContext):
    if not _is_admin(m.from_user.id):
        await state.clear(); return
    raw = (m.text or "").strip()
    if not raw.isdigit():
        await m.answer("❌ Numeric user ID required."); return
    await state.update_data(target_user=int(raw))
    await state.set_state(AdminSG.grant_plan_choose)
    rows = [[InlineKeyboardButton(text=f"{p['emoji']} {p['name']}", callback_data=f"adm_gp_{k}")]
            for k, p in PLANS.items() if k != "free"]
    await m.answer("🎯 Choose plan:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

@router.callback_query(AdminSG.grant_plan_choose, F.data.startswith("adm_gp_"))
async def adm_grant_plan(c: CallbackQuery, state: FSMContext):
    if not _is_admin(c.from_user.id):
        await state.clear(); return
    key = c.data.replace("adm_gp_", "")
    await state.update_data(grant_plan=key)
    await state.set_state(AdminSG.grant_days)
    plan = PLANS[key]
    await c.message.edit_text(
        f"📅 *{plan['name']}*\n\nSend days (`0` = default {plan['duration_days']}).",
        parse_mode="Markdown")

@router.message(AdminSG.grant_days)
async def adm_grant_days(m: Message, state: FSMContext):
    if not _is_admin(m.from_user.id):
        await state.clear(); return
    raw = (m.text or "").strip()
    if not raw.isdigit():
        await m.answer("❌ Number required."); return
    days = int(raw); d = await state.get_data()
    target = d["target_user"]; plan_key = d["grant_plan"]
    ok = await grant_plan(target, plan_key, days if days else None)
    await state.clear()
    if not ok:
        await m.answer("❌ Failed."); return
    plan = PLANS[plan_key]
    await m.answer(f"✅ *Granted*\n\n  👤 `{target}`\n  {plan['emoji']} *{plan['name']}*\n  📅 `{days or plan['duration_days']}` days",
        parse_mode="Markdown")
    try:
        await bot.send_message(target,
            f"🎁  *Premium Activated!*\n\n  {plan['emoji']} *{plan['name']}*\n\n"
            f"_Use /mystatus to see limits._", parse_mode="Markdown")
    except Exception: pass

@router.message(Command("revoke"))
async def cmd_revoke(m: Message):
    if not _is_admin(m.from_user.id): return
    parts = (m.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await m.answer("Usage: /revoke <user_id>"); return
    uid = int(parts[1]); await revoke_plan(uid)
    await m.answer(f"✅ Revoked `{uid}`.", parse_mode="Markdown")

@router.callback_query(F.data == "adm_broadcast")
async def cb_adm_broadcast(c: CallbackQuery, state: FSMContext):
    if not _is_admin(c.from_user.id):
        await c.answer("Admin only", show_alert=True); return
    await c.answer()
    await state.set_state(AdminSG.broadcast_text)
    await c.message.answer("📢 *Broadcast*\n\nSend text to broadcast to all users.\n/broadcast_cancel to abort.",
        parse_mode="Markdown")

@router.message(Command("broadcast_cancel"))
async def cmd_broadcast_cancel(m: Message, state: FSMContext):
    await state.clear(); await m.answer("✓ Cancelled.")

@router.message(AdminSG.broadcast_text)
async def adm_do_broadcast(m: Message, state: FSMContext):
    if not _is_admin(m.from_user.id):
        await state.clear(); return
    text = m.text or ""
    if not text:
        await m.answer("Send text."); return
    await state.clear()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT user_id FROM app_users")
        uids = [r[0] for r in await cur.fetchall()]
    sent = failed = 0
    status = await m.answer(f"📤 Sending to {len(uids)}…")
    for i, uid in enumerate(uids):
        try: await bot.send_message(uid, text); sent += 1
        except Exception: failed += 1
        if i % 20 == 0:
            try: await status.edit_text(f"📤 {i+1}/{len(uids)} · ✅{sent} ❌{failed}")
            except Exception: pass
    try:
        await status.edit_text(f"✅ *Done*\n\nSent: `{sent}`\nFailed: `{failed}`",
            parse_mode="Markdown")
    except Exception: pass

# ═══════════════════════════════════════════════════════════
#  Note: All remaining handlers (accounts, bots, userbots,
#  providers, settings, hashtags, auto, watch, compose,
#  broadcast) — same as original v15, but with LIMIT CHECKS
#  added to the 4 wizard entry points.
# ═══════════════════════════════════════════════════════════

# ── LIMIT-CHECK HELPER ──
async def _enforce_limit(m_or_c, resource, resource_name):
    """Returns True if allowed; otherwise sends upgrade prompt."""
    uid = (m_or_c.from_user.id if hasattr(m_or_c, "from_user")
           else m_or_c.chat.id)
    ok, cur, mx, plan = await check_limit(uid, resource)
    if ok: return True
    txt = (f"⛔  *{resource_name} Limit Reached*\n\n"
           f"  Plan: *{plan.title()}*  ·  `{cur}/{mx}`\n\n"
           f"_Upgrade to increase your limit._")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ View Plans", callback_data="pm_main")]])
    if hasattr(m_or_c, "message") and hasattr(m_or_c, "answer"):
        await m_or_c.answer("Limit reached", show_alert=True)
        await m_or_c.message.answer(txt, parse_mode="Markdown", reply_markup=kb)
    else:
        await send_safe(m_or_c.chat.id, txt, reply_markup=kb)
    return False

# ═══════════════════════════════════════════════════════════
#  ACCOUNTS
# ═══════════════════════════════════════════════════════════
@router.message(Command("accounts"))
async def cmd_accounts(m: Message):
    await render_accounts(m)

@router.callback_query(F.data == "m_accounts")
async def cb_accounts(c: CallbackQuery):
    await c.answer(); await render_accounts(c)

async def render_accounts(target):
    uid = target.from_user.id; accts = await db_list_accounts(uid)
    if not accts:
        txt = (f"📱 *Destination Accounts*\n\n❌ None configured.\n\n"
               f"_A destination = bot + channel pair._")
    else:
        lines = [f"📱 *Accounts* ({len(accts)})\n"]
        for a in accts:
            posts = a["post_count"] if "post_count" in a.keys() else 0
            last = human_time(a["last_post"] if "last_post" in a.keys() else None)
            lines.append(f"  *#{a['id']}* {a['name']}\n     `{a['chat_id']}`\n     📝 `{posts}` · 🕒 `{last}`")
        txt = "\n".join(lines)
    rows = [[InlineKeyboardButton(text=f"🧪 #{a['id']}", callback_data=f"acct_test_{a['id']}"),
             InlineKeyboardButton(text=f"🗑 #{a['id']}", callback_data=f"acct_del_{a['id']}")]
            for a in accts[:10]]
    rows.append([InlineKeyboardButton(text="➕ Add", callback_data="acct_add")])
    rows.append([InlineKeyboardButton(text="🏠 Menu", callback_data="m_home")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    if isinstance(target, Message): await send_safe(target.chat.id, txt, reply_markup=kb)
    else: await edit_safe(target.message, txt, reply_markup=kb)

@router.message(Command("addaccount"))
async def cmd_addacct(m: Message, state: FSMContext):
    if not await _enforce_limit(m, "accounts", "Accounts"): return
    await start_account_wizard(m, state)

@router.callback_query(F.data == "acct_add")
async def cb_add_acct(c: CallbackQuery, state: FSMContext):
    await c.answer()
    if not await _enforce_limit(c, "accounts", "Accounts"): return
    await start_account_wizard(c.message, state)

async def start_account_wizard(m, state):
    await state.clear(); await state.set_state(AccountSG.name)
    await send_safe(m.chat.id,
        f"📱 *Add Account*\n\n*Step 1/3* · Name\n_Example:_ `Daily News`")

@router.message(AccountSG.name)
async def acct_name(m: Message, state: FSMContext):
    await state.update_data(name=(m.text or "").strip()[:60] or "Account")
    await state.set_state(AccountSG.bot_token)
    await send_safe(m.chat.id,
        f"*Step 2/3* · Bot Token\n\n_Or /samebot to use main bot._")

@router.message(Command("samebot"))
async def acct_samebot(m: Message, state: FSMContext):
    d = await state.get_data()
    if not d.get("name"):
        await m.answer("Set name first."); return
    await state.update_data(bot_token=TOKEN); await state.set_state(AccountSG.chat_id)
    await send_safe(m.chat.id,
        f"✅ Main bot.\n*Step 3/3* · Chat ID or @username")

@router.message(AccountSG.bot_token)
async def acct_token(m: Message, state: FSMContext):
    tok = (m.text or "").strip()
    if not re.match(r"^\d+:[A-Za-z0-9_-]+$", tok):
        await m.answer("✗ Invalid token."); return
    await state.update_data(bot_token=tok); await state.set_state(AccountSG.chat_id)
    await send_safe(m.chat.id, f"*Step 3/3* · Chat ID or @username")

@router.message(AccountSG.chat_id)
async def acct_chat(m: Message, state: FSMContext):
    chat = (m.text or "").strip()
    if not chat: await m.answer("Chat ID required."); return
    d = await state.get_data(); name = d.get("name", "Account"); bt = d.get("bot_token", "")
    tb = get_bot_for_token(bt or TOKEN)
    try:
        await tb.get_me()
        await tb.send_message(chat, f"🔔 Connected to `{name}`", parse_mode="Markdown")
    except Exception as e:
        await send_safe(m.chat.id, f"❌ Failed:\n`{str(e)[:300]}`")
        await state.clear(); return
    aid = await db_add_account({"owner_id": m.from_user.id, "platform": "telegram",
        "name": name, "bot_token": bt or TOKEN, "chat_id": chat})
    await state.clear()
    await send_safe(m.chat.id,
        f"✅ *Account #{aid} Added*\n\n`{name}` → `{chat}`",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📱 Accounts", callback_data="m_accounts")],
            [InlineKeyboardButton(text="🏠 Menu", callback_data="m_home")]]))

@router.callback_query(F.data.startswith("acct_test_"))
async def acct_test(c: CallbackQuery):
    aid = int(c.data.rsplit("_", 1)[1]); acc = await db_get_account(aid)
    if not acc: await c.answer("Not found", show_alert=True); return
    await c.answer("Testing…")
    ok, err = await send_text_to(acc, f"🧪 Test OK for #{aid}")
    await c.message.answer(f"{'✅ Sent' if ok else '❌ ' + err}")

@router.callback_query(F.data.startswith("acct_del_"))
async def acct_del(c: CallbackQuery):
    aid = int(c.data.rsplit("_", 1)[1]); acc = await db_get_account(aid)
    if not acc or acc["owner_id"] != c.from_user.id:
        await c.answer("Not owner", show_alert=True); return
    await db_del_account(aid, c.from_user.id)
    await c.answer("Deleted"); await render_accounts(c)

# ═══════════════════════════════════════════════════════════
#  BOTS
# ═══════════════════════════════════════════════════════════
@router.message(Command("addbot"))
async def cmd_addbot(m: Message, state: FSMContext):
    await start_bot_wizard(m, state)

@router.callback_query(F.data == "bot_add")
async def cb_bot_add(c: CallbackQuery, state: FSMContext):
    await c.answer(); await start_bot_wizard(c.message, state)

async def start_bot_wizard(m, state):
    await state.clear(); await state.set_state(BotSG.name)
    await send_safe(m.chat.id,
        f"🤖 *Add Bot*\n\n*Step 1/2* · Name\n_Example:_ `News Source`")

@router.message(BotSG.name)
async def bot_name(m: Message, state: FSMContext):
    name = (m.text or "").strip()[:60] or "Bot"
    await state.update_data(name=name); await state.set_state(BotSG.token)
    await send_safe(m.chat.id, f"✅ `{name}`\n\n*Step 2/2* · Bot Token")

@router.message(BotSG.token)
async def bot_token(m: Message, state: FSMContext):
    tok = (m.text or "").strip()
    if not re.match(r"^\d+:[A-Za-z0-9_-]+$", tok):
        await m.answer("❌ Invalid token."); return
    existing = await db_get_bot_by_token(tok)
    if existing and existing["owner_id"] == m.from_user.id:
        await m.answer("⚠️ Already added."); await state.clear(); return
    if tok == TOKEN:
        await m.answer("⚠️ That's the main bot."); await state.clear(); return
    msg = await m.answer("⏳ Verifying…")
    try:
        temp = Bot(token=tok); me = await temp.get_me(); await temp.session.close()
    except Exception as e:
        await send_safe(m.chat.id, f"❌ Verify failed:\n`{str(e)[:300]}`")
        try: await msg.delete()
        except Exception: pass
        await state.clear(); return
    d = await state.get_data()
    bid = await db_add_bot({"owner_id": m.from_user.id, "name": d.get("name", "Bot"),
        "token": tok, "bot_id": me.id, "bot_username": me.username or ""})
    try: _bot_cache[tok] = Bot(token=tok)
    except Exception: pass
    row = await db_get_bot(bid)
    if row: await start_bot_poller(row)
    await state.clear()
    try: await msg.delete()
    except Exception: pass
    await send_safe(m.chat.id,
        f"✅ *Bot #{bid} Added*\n\n  @{me.username}\n  Poller: {'🟢' if bid in _bot_pollers else '🔴'}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🤖 My Bots", callback_data="m_bots")],
            [InlineKeyboardButton(text="🏠 Menu", callback_data="m_home")]]))

@router.message(Command("mybots"))
async def cmd_mybots(m: Message): await render_bots(m)

@router.callback_query(F.data == "m_bots")
async def cb_mybots(c: CallbackQuery):
    await c.answer(); await render_bots(c)

async def render_bots(target):
    uid = target.from_user.id; rows = await db_list_bots(uid)
    if not rows:
        txt = f"🤖 *My Bots*\n\n❌ None added.\n\n_Extra bots watch source channels._"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Add Bot", callback_data="bot_add")],
            [InlineKeyboardButton(text="🏠 Menu", callback_data="m_home")]])
    else:
        lines = [f"🤖 *My Bots* ({len(rows)})\n"]
        for b in rows:
            poll = "🟢" if b["id"] in _bot_pollers else "🔴"
            lines.append(f"  {poll} *#{b['id']}* {b['name']} @{b['bot_username'] or '—'}")
        txt = "\n".join(lines)
        kr = [[InlineKeyboardButton(text=f"🗑 #{b['id']} {b['name']}",
                callback_data=f"botdel_{b['id']}")] for b in rows[:10]]
        kr.append([InlineKeyboardButton(text="➕ Add", callback_data="bot_add")])
        kr.append([InlineKeyboardButton(text="🏠 Menu", callback_data="m_home")])
        kb = InlineKeyboardMarkup(inline_keyboard=kr)
    if isinstance(target, Message): await send_safe(target.chat.id, txt, reply_markup=kb)
    else: await edit_safe(target.message, txt, reply_markup=kb)

@router.callback_query(F.data.startswith("botdel_"))
async def cb_bot_del(c: CallbackQuery):
    bid = int(c.data.split("_", 1)[1]); row = await db_get_bot(bid)
    if not row or row["owner_id"] != c.from_user.id:
        await c.answer("Not owner", show_alert=True); return
    await stop_bot_poller(bid)
    tok = row["token"]
    if tok in _bot_cache:
        try: await _bot_cache[tok].session.close()
        except Exception: pass
        del _bot_cache[tok]
    await db_del_bot(bid, c.from_user.id)
    await c.answer("Deleted"); await render_bots(c)

# ═══════════════════════════════════════════════════════════
#  USERBOTS
# ═══════════════════════════════════════════════════════════
@router.message(Command("userbots"))
async def cmd_userbots(m: Message): await render_userbots(m)

@router.callback_query(F.data == "m_userbots")
async def cb_userbots(c: CallbackQuery):
    await c.answer(); await render_userbots(c)

async def render_userbots(target):
    uid = target.from_user.id; ubs = await db_list_userbots(uid)
    if not ubs:
        txt = (f"👤 *My Userbots*\n\n❌ None added.\n\n"
               f"⚠️ Use secondary accounts only.\n"
               f"_Userbots unlock 2GB direct._")
    else:
        lines = [f"👤 *My Userbots* ({len(ubs)})\n"]
        for u in ubs:
            running = "🟢" if u["id"] in _userbot_clients else "🔴"
            lines.append(f"  {running} *#{u['id']}* {u['name']} `{mask_phone(u['phone'])}`")
        txt = "\n".join(lines)
    rows = []
    for u in ubs[:10]:
        rows.append([InlineKeyboardButton(text=f"🔄 #{u['id']}", callback_data=f"ub_restart_{u['id']}"),
                     InlineKeyboardButton(text=f"🗑 #{u['id']}", callback_data=f"ub_del_{u['id']}")])
    rows.append([InlineKeyboardButton(text="➕ Add", callback_data="ub_add")])
    rows.append([InlineKeyboardButton(text="🏠 Menu", callback_data="m_home")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    if isinstance(target, Message): await send_safe(target.chat.id, txt, reply_markup=kb)
    else: await edit_safe(target.message, txt, reply_markup=kb)

@router.message(Command("adduserbot"))
async def cmd_adduserbot(m: Message, state: FSMContext):
    if not await _enforce_limit(m, "userbots", "Userbots"): return
    await start_userbot_wizard(m, state)

@router.callback_query(F.data == "ub_add")
async def cb_ub_add(c: CallbackQuery, state: FSMContext):
    await c.answer()
    if not await _enforce_limit(c, "userbots", "Userbots"): return
    await start_userbot_wizard(c.message, state)

async def start_userbot_wizard(m, state):
    await state.clear(); await state.set_state(UserbotSG.name)
    await send_safe(m.chat.id,
        f"👤 *Add Userbot*\n\n⚠️ Use secondary account.\n\n*Step 1/5* · Name")

@router.message(UserbotSG.name)
async def ub_name(m: Message, state: FSMContext):
    await state.update_data(name=(m.text or "").strip()[:60] or "Userbot")
    await state.set_state(UserbotSG.api_id)
    await send_safe(m.chat.id, f"*Step 2/5* · API ID\nmy.telegram.org/apps")

@router.message(UserbotSG.api_id)
async def ub_api_id(m: Message, state: FSMContext):
    t = (m.text or "").strip()
    if not t.isdigit(): await m.answer("❌ Number required."); return
    await state.update_data(api_id=int(t)); await state.set_state(UserbotSG.api_hash)
    await send_safe(m.chat.id, f"*Step 3/5* · API Hash")

@router.message(UserbotSG.api_hash)
async def ub_api_hash(m: Message, state: FSMContext):
    t = (m.text or "").strip()
    if len(t) < 20: await m.answer("❌ Too short."); return
    await state.update_data(api_hash=t); await state.set_state(UserbotSG.phone)
    await send_safe(m.chat.id, f"*Step 4/5* · Phone\nFormat: `+8801XXXXXXXXX`")

@router.message(UserbotSG.phone)
async def ub_phone(m: Message, state: FSMContext):
    phone = (m.text or "").strip()
    if not phone.startswith("+") or len(phone) < 8:
        await m.answer("❌ Include +countrycode."); return
    d = await state.get_data(); uid = m.from_user.id
    if uid in _login_clients:
        try: await _login_clients[uid].disconnect()
        except Exception: pass
        del _login_clients[uid]
    msg = await m.answer("📞 Sending OTP…")
    session_name = os.path.join(SESSION_DIR, f"login_{uid}")
    try:
        client = PyroClient(name=session_name, api_id=d["api_id"],
            api_hash=d["api_hash"], in_memory=False)
        await client.connect()
        sent = await client.send_code(phone)
        _login_clients[uid] = client
        await state.update_data(phone=phone, phone_code_hash=sent.phone_code_hash,
                                session_name=session_name)
        await state.set_state(UserbotSG.otp)
        try: await msg.delete()
        except Exception: pass
        await send_safe(m.chat.id,
            f"📩 OTP sent\n\n*Step 5/5* · Send code with spaces like: `1 2 3 4 5`")
    except Exception as e:
        try: await msg.delete()
        except Exception: pass
        await send_safe(m.chat.id, f"❌ Send OTP failed:\n`{str(e)[:300]}`")

@router.message(UserbotSG.otp)
async def ub_otp(m: Message, state: FSMContext):
    code = re.sub(r"\s+", "", (m.text or "").strip())
    if not code.isdigit() or len(code) < 4:
        await m.answer("❌ Send like `1 2 3 4 5`"); return
    uid = m.from_user.id; d = await state.get_data()
    client = _login_clients.get(uid)
    if not client:
        await m.answer("❌ Session expired."); await state.clear(); return
    msg = await m.answer("⏳ Verifying…")
    try:
        try:
            await client.sign_in(phone_number=d["phone"],
                phone_code_hash=d["phone_code_hash"], phone_code=code)
        except SessionPasswordNeeded:
            await state.set_state(UserbotSG.password)
            try: await msg.delete()
            except Exception: pass
            await send_safe(m.chat.id, f"🔐 2FA required. Send cloud password.")
            return
        session_string = await client.export_session_string()
        me = await client.get_me(); username = me.username or me.first_name
        ub_id = await db_add_userbot({"owner_id": uid, "name": d.get("name", "Userbot"),
            "phone": d["phone"], "api_id": d["api_id"], "api_hash": d["api_hash"],
            "session_string": session_string})
        try: await client.disconnect()
        except Exception: pass
        del _login_clients[uid]; await state.clear()
        row = await db_get_userbot(ub_id); ok, info = await start_userbot_from_db(row)
        try: await msg.delete()
        except Exception: pass
        await send_safe(m.chat.id,
            f"✅ *Userbot #{ub_id}* {'🟢' if ok else '🔴'}\n\n`{username}`",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👤 Userbots", callback_data="m_userbots")],
                [InlineKeyboardButton(text="🏠 Menu", callback_data="m_home")]]))
    except PhoneCodeInvalid:
        try: await msg.delete()
        except Exception: pass
        await send_safe(m.chat.id, "❌ Wrong OTP.")
    except PhoneCodeExpired:
        try: await msg.delete()
        except Exception: pass
        await send_safe(m.chat.id, "❌ OTP expired.")
        try: await client.disconnect()
        except Exception: pass
        if uid in _login_clients: del _login_clients[uid]
        await state.clear()
    except Exception as e:
        try: await msg.delete()
        except Exception: pass
        await send_safe(m.chat.id, f"❌ `{str(e)[:300]}`")

@router.message(UserbotSG.password)
async def ub_password(m: Message, state: FSMContext):
    pwd = (m.text or "").strip()
    if not pwd: await m.answer("Send password."); return
    uid = m.from_user.id; d = await state.get_data()
    client = _login_clients.get(uid)
    if not client:
        await m.answer("Session expired."); await state.clear(); return
    msg = await m.answer("⏳ Verifying 2FA…")
    try:
        await client.check_password(pwd)
        ss = await client.export_session_string()
        me = await client.get_me(); username = me.username or me.first_name
        ub_id = await db_add_userbot({"owner_id": uid, "name": d.get("name", "Userbot"),
            "phone": d["phone"], "api_id": d["api_id"], "api_hash": d["api_hash"],
            "session_string": ss})
        try: await client.disconnect()
        except Exception: pass
        del _login_clients[uid]; await state.clear()
        row = await db_get_userbot(ub_id); ok, _ = await start_userbot_from_db(row)
        try: await msg.delete()
        except Exception: pass
        await send_safe(m.chat.id,
            f"✅ *Userbot #{ub_id}* (2FA)\n\n`{username}`",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👤 Userbots", callback_data="m_userbots")]]))
    except PasswordHashInvalid:
        try: await msg.delete()
        except Exception: pass
        await send_safe(m.chat.id, "❌ Wrong password.")
    except Exception as e:
        try: await msg.delete()
        except Exception: pass
        await send_safe(m.chat.id, f"❌ `{str(e)[:300]}`")

@router.callback_query(F.data.startswith("ub_restart_"))
async def ub_restart(c: CallbackQuery):
    uid = int(c.data.rsplit("_", 1)[1]); row = await db_get_userbot(uid)
    if not row or row["owner_id"] != c.from_user.id:
        await c.answer("Not owner", show_alert=True); return
    await c.answer("Restarting…")
    await stop_userbot(uid); ok, info = await start_userbot_from_db(row)
    await c.message.answer(f"{'✅' if ok else '❌'} #{uid}: `{info}`", parse_mode="Markdown")

@router.callback_query(F.data.startswith("ub_del_"))
async def ub_del(c: CallbackQuery):
    uid = int(c.data.rsplit("_", 1)[1]); row = await db_get_userbot(uid)
    if not row or row["owner_id"] != c.from_user.id:
        await c.answer("Not owner", show_alert=True); return
    await stop_userbot(uid); await db_del_userbot(uid, c.from_user.id)
    await c.answer("Deleted"); await render_userbots(c)

# ═══════════════════════════════════════════════════════════
#  PROVIDERS
# ═══════════════════════════════════════════════════════════
async def render_providers(target):
    provs = await db_list_providers()
    if not provs:
        txt = f"🧠 *AI Providers*\n\n❌ None configured.\n\n_Free: LLM7, UncloseAI_"
    else:
        lines = [f"🧠 *AI Providers* ({len(provs)})\n"]
        for p in provs:
            st = "🟢" if p["enabled"] else "⏸"
            lines.append(f"  {st} *#{p['id']}* {p['name']}\n     🔑 `{mask_key(p['api_key'])}` · 🎯 `{p['model']}`")
        txt = "\n".join(lines)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add", callback_data="prov_add"),
         InlineKeyboardButton(text="🧪 Test", callback_data="prov_test")],
        [InlineKeyboardButton(text="🗑 Clear", callback_data="prov_clear")],
        [InlineKeyboardButton(text="◀ Settings", callback_data="m_set")]])
    if isinstance(target, Message): await send_safe(target.chat.id, txt, reply_markup=kb)
    else: await edit_safe(target.message, txt, reply_markup=kb)

@router.message(Command("providers"))
async def cmd_providers(m: Message): await render_providers(m)

@router.callback_query(F.data == "s_prov")
async def cb_prov(c: CallbackQuery):
    await c.answer(); await render_providers(c)

@router.callback_query(F.data == "prov_add")
async def cb_prov_add(c: CallbackQuery, state: FSMContext):
    await c.answer()
    rows = []
    for i in range(0, len(PROVIDER_DEFS), 2):
        row = [InlineKeyboardButton(text=PROVIDER_DEFS[i]["name"],
            callback_data=f"pvtype_{PROVIDER_DEFS[i]['type']}")]
        if i + 1 < len(PROVIDER_DEFS):
            row.append(InlineKeyboardButton(text=PROVIDER_DEFS[i+1]["name"],
                callback_data=f"pvtype_{PROVIDER_DEFS[i+1]['type']}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(text="✗ Cancel", callback_data="prov_cancel")])
    await edit_safe(c.message, f"🧠 *Add Provider*",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await state.set_state(AddProviderSG.choose_type)

@router.callback_query(AddProviderSG.choose_type, F.data.startswith("pvtype_"))
async def prov_type(c: CallbackQuery, state: FSMContext):
    pt = c.data.split("_", 1)[1]
    defn = next((d for d in PROVIDER_DEFS if d["type"] == pt), None)
    if not defn: await c.answer("Unknown", show_alert=True); return
    await state.update_data(ptype=pt, pname=defn["name"], base=defn["base"],
                            model=defn["model"], caps=defn["caps"])
    if defn.get("nokey"):
        await state.update_data(api_key="unused")
        await edit_safe(c.message,
            f"✅ {defn['name']}\n🎯 Send model name or `default`.\nDefault: `{defn['model']}`")
        await state.set_state(AddProviderSG.enter_model); return
    await edit_safe(c.message, f"✅ {defn['name']}\n🔑 Send API key.")
    await state.set_state(AddProviderSG.enter_key)

@router.message(AddProviderSG.enter_key)
async def prov_key(m: Message, state: FSMContext):
    k = (m.text or "").strip()
    if not k: await m.answer("Key required."); return
    await state.update_data(api_key=k)
    d = await state.get_data()
    await m.answer(f"🎯 Send model or tap below.\nDefault: `{d.get('model','')}`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✓ Default", callback_data="pvmodel_default")]]))
    await state.set_state(AddProviderSG.enter_model)

@router.message(AddProviderSG.enter_model)
async def prov_model(m: Message, state: FSMContext):
    model = (m.text or "").strip()
    if not model or model.lower() == "default":
        d = await state.get_data(); model = d.get("model") or ""
    await state.update_data(model=model); await finish_provider(m, state)

@router.callback_query(F.data == "pvmodel_default")
async def prov_model_default(c: CallbackQuery, state: FSMContext):
    await c.answer(); await finish_provider(c.message, state)

async def finish_provider(m, state):
    d = await state.get_data()
    pid = await db_add_provider({"type": d["ptype"], "name": d["pname"],
        "api_key": d.get("api_key", ""), "base_url": d.get("base", ""),
        "model": d.get("model", ""), "caps": d.get("caps", ["text"])})
    await state.clear()
    await send_safe(m.chat.id,
        f"✅ *Provider #{pid}*\n\n  {d['pname']} · `{d.get('model','')}`",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🧠 Providers", callback_data="s_prov")]]))

@router.callback_query(F.data == "prov_cancel")
async def prov_cancel(c: CallbackQuery, state: FSMContext):
    await state.clear(); await c.answer("Cancelled")
    await edit_safe(c.message, "✗ Cancelled.", reply_markup=settings_menu())

@router.callback_query(F.data == "prov_test")
async def prov_test(c: CallbackQuery):
    await c.answer("Testing…")
    msg = await c.message.answer("⏳ Sending test…")
    r = await ai_generate_text("Reply: OK", system="Reply only OK.")
    try: await msg.delete()
    except Exception: pass
    if r.get("ok"):
        await send_safe(c.message.chat.id,
            f"✅ *Test OK*\n\n  🧠 `{r['provider']}`\n  🎯 `{r['model']}`")
    else:
        errs = "\n".join(f"  • {e}" for e in r.get("errors", [])[:5])
        await send_safe(c.message.chat.id, f"❌ *All failed*\n\n{errs}")

@router.callback_query(F.data == "prov_clear")
async def prov_clear(c: CallbackQuery):
    await c.answer()
    await edit_safe(c.message, "⚠️ *Delete all providers?*",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚠️ Yes", callback_data="prov_clear_yes")],
            [InlineKeyboardButton(text="✗ Cancel", callback_data="s_prov")]]))

@router.callback_query(F.data == "prov_clear_yes")
async def prov_clear_yes(c: CallbackQuery):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM providers"); await db.commit()
    await c.answer("Cleared"); await render_providers(c)

# ═══════════════════════════════════════════════════════════
#  SETTINGS
# ═══════════════════════════════════════════════════════════
@router.callback_query(F.data == "m_set")
async def cb_set(c: CallbackQuery):
    await c.answer()
    await edit_safe(c.message, f"🔧 *Settings*",
        reply_markup=settings_menu())

@router.message(Command("setimgbb"))
async def cmd_setimgbb(m: Message, state: FSMContext):
    cur = await get_setting("imgbb_key", "")
    txt = f"☁️ *ImgBB*\n" + (f"  🔑 `{mask_key(cur)}`\n\n" if cur else "") + \
          f"Send API key.\nhttps://api.imgbb.com"
    await send_safe(m.chat.id, txt)
    await state.set_state(SettingsSG.imgbb_key)

@router.callback_query(F.data == "s_imgbb")
async def cb_imgbb(c: CallbackQuery, state: FSMContext):
    await c.answer()
    cur = await get_setting("imgbb_key", "")
    txt = (f"☁️ *ImgBB*\n  {'✅ Connected' if cur else '❌ Not configured'}"
           + (f"\n  🔑 `{mask_key(cur)}`" if cur else ""))
    await edit_safe(c.message, txt, reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Edit", callback_data="imgbb_edit")],
            [InlineKeyboardButton(text="◀ Back", callback_data="m_set")]]))

@router.callback_query(F.data == "imgbb_edit")
async def cb_imgbb_edit(c: CallbackQuery, state: FSMContext):
    await c.answer(); await c.message.answer("🔑 Send API key:")
    await state.set_state(SettingsSG.imgbb_key)

@router.message(SettingsSG.imgbb_key)
async def set_imgbb_key(m: Message, state: FSMContext):
    k = (m.text or "").strip()
    if not k: await m.answer("Key required."); return
    await set_setting("imgbb_key", k); await state.clear()
    await send_safe(m.chat.id, f"✅ Saved `{mask_key(k)}`", reply_markup=settings_menu())

async def show_branding(target):
    name = await get_setting("brand_name", ""); handle = await get_setting("brand_handle", "")
    web = await get_setting("brand_website", ""); color = await get_setting("brand_color", "#ffce00")
    txt = (f"🏷 *Branding*\n\n  📛 `{name}`\n  📮 `{handle}`\n"
           f"  🌐 `{web}`\n  🎨 `{color}`")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Name", callback_data="br_name"),
         InlineKeyboardButton(text="✏️ Handle", callback_data="br_handle")],
        [InlineKeyboardButton(text="✏️ Website", callback_data="br_website"),
         InlineKeyboardButton(text="🎨 Color", callback_data="br_color")],
        [InlineKeyboardButton(text="◀ Back", callback_data="m_set")]])
    if isinstance(target, Message): await send_safe(target.chat.id, txt, reply_markup=kb)
    else: await edit_safe(target.message, txt, reply_markup=kb)

@router.message(Command("branding"))
async def cmd_brand(m: Message): await show_branding(m)

@router.callback_query(F.data == "s_brand")
async def cb_brand(c: CallbackQuery):
    await c.answer(); await show_branding(c)

@router.callback_query(F.data == "s_tpl")
async def cb_tpl_preview(c: CallbackQuery):
    await c.answer("Rendering…")
    msg = await c.message.answer("🎨 Generating previews…")
    try:
        raw = await generate_ai_image("abstract aesthetic", 1080, 1080, "cascade")
        if not raw:
            try: await msg.delete()
            except Exception: pass
            await send_safe(c.message.chat.id, "✗ No sample."); return
        c_hex = await get_setting("brand_color", "#ffce00")
        for t in ["glass_card", "neon_glow", "split_screen", "bold_stripe"]:
            comp = await compose_image(raw, headline="Preview", template=t, color_hex=c_hex)
            await bot.send_photo(c.message.chat.id,
                BufferedInputFile(comp, filename=f"{t}.jpg"),
                caption=f"✨ {TEMPLATE_LABELS.get(t, t)}", parse_mode="Markdown")
        try: await msg.delete()
        except Exception: pass
    except Exception as e:
        try: await msg.delete()
        except Exception: pass
        await send_safe(c.message.chat.id, f"✗ {str(e)[:200]}")

@router.callback_query(F.data == "br_name")
async def br_name(c: CallbackQuery, state: FSMContext):
    await c.answer(); await c.message.answer("📛 Send brand name:")
    await state.set_state(SettingsSG.brand_name)

@router.callback_query(F.data == "br_handle")
async def br_handle(c: CallbackQuery, state: FSMContext):
    await c.answer(); await c.message.answer("📮 Send handle:")
    await state.set_state(SettingsSG.brand_handle)

@router.callback_query(F.data == "br_website")
async def br_website(c: CallbackQuery, state: FSMContext):
    await c.answer(); await c.message.answer("🌐 Send website:")
    await state.set_state(SettingsSG.brand_website)

@router.callback_query(F.data == "br_color")
async def br_color(c: CallbackQuery, state: FSMContext):
    await c.answer(); await c.message.answer("🎨 Send hex (`#ffce00`):")
    await state.set_state(SettingsSG.brand_color)

@router.message(SettingsSG.brand_name)
async def set_bn(m: Message, state: FSMContext):
    await set_setting("brand_name", (m.text or "").strip()[:60])
    await state.clear()
    await send_safe(m.chat.id, "✅ Saved", reply_markup=settings_menu())

@router.message(SettingsSG.brand_handle)
async def set_bh(m: Message, state: FSMContext):
    await set_setting("brand_handle", (m.text or "").strip()[:60])
    await state.clear()
    await send_safe(m.chat.id, "✅ Saved", reply_markup=settings_menu())

@router.message(SettingsSG.brand_website)
async def set_bw(m: Message, state: FSMContext):
    await set_setting("brand_website", (m.text or "").strip()[:120])
    await state.clear()
    await send_safe(m.chat.id, "✅ Saved", reply_markup=settings_menu())

@router.message(SettingsSG.brand_color)
async def set_bc(m: Message, state: FSMContext):
    c = (m.text or "").strip()
    if not re.match(r"^#[0-9a-fA-F]{6}$", c):
        await m.answer("✗ Invalid. Example: `#ffce00`"); return
    await set_setting("brand_color", c); await state.clear()
    await send_safe(m.chat.id, "✅ Saved", reply_markup=settings_menu())

# ═══════════════════════════════════════════════════════════
#  HASHTAGS
# ═══════════════════════════════════════════════════════════
@router.message(Command("hashtags"))
async def cmd_hashtags(m: Message): await render_hashtags(m)

@router.callback_query(F.data == "m_hashtags")
async def cb_hashtags(c: CallbackQuery):
    await c.answer(); await render_hashtags(c)

async def render_hashtags(target):
    uid = target.from_user.id; groups = await db_list_hashtags(uid)
    if groups:
        lines = [f"#️⃣ *Hashtags* ({len(groups)})\n"]
        for g in groups: lines.append(f"  *#{g['id']}* {g['name']}\n     {g['tags'][:80]}")
        txt = "\n".join(lines)
    else:
        txt = f"#️⃣ *Hashtag Groups*\n\n❌ None yet."
    rows = [[InlineKeyboardButton(text=f"🗑 #{g['id']} {g['name']}",
            callback_data=f"hdel_{g['id']}")] for g in groups[:10]]
    rows.append([InlineKeyboardButton(text="➕ New", callback_data="hadd")])
    rows.append([InlineKeyboardButton(text="🏠 Menu", callback_data="m_home")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    if isinstance(target, Message): await send_safe(target.chat.id, txt, reply_markup=kb)
    else: await edit_safe(target.message, txt, reply_markup=kb)

@router.callback_query(F.data == "hadd")
async def cb_hadd(c: CallbackQuery, state: FSMContext):
    await c.answer(); await state.set_state(HashtagSG.name)
    await c.message.answer(f"#️⃣ *New Group*\n\n*Step 1/2* · Name")

@router.message(HashtagSG.name)
async def h_name(m: Message, state: FSMContext):
    await state.update_data(name=(m.text or "").strip()[:40] or "Group")
    await state.set_state(HashtagSG.tags)
    await m.answer(f"*Step 2/2* · Send hashtags (space-separated)")

@router.message(HashtagSG.tags)
async def h_tags(m: Message, state: FSMContext):
    raw = (m.text or "").strip()
    tags = " ".join("#" + x.lstrip("#") for x in raw.split() if x)
    if not tags: await m.answer("At least one."); return
    d = await state.get_data()
    hid = await db_add_hashtags(m.from_user.id, d.get("name", "Group"), tags)
    await state.clear()
    await send_safe(m.chat.id, f"✅ *Group #{hid}*\n\n{tags[:200]}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="#️⃣ All", callback_data="m_hashtags")]]))

@router.callback_query(F.data.startswith("hdel_"))
async def h_del(c: CallbackQuery):
    hid = int(c.data.split("_", 1)[1])
    await db_del_hashtags(hid, c.from_user.id)
    await c.answer("Deleted"); await render_hashtags(c)

# ═══════════════════════════════════════════════════════════
#  AUTO POST WIZARD
# ═══════════════════════════════════════════════════════════
@router.message(Command("auto"))
async def cmd_auto(m: Message):
    txt = (f"⚡ *Auto Post*\n\n"
           f"Schedule AI-generated posts.\n\n"
           f"_Create a new automation._")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Create", callback_data="auto_new")],
        [InlineKeyboardButton(text="📋 My", callback_data="m_autos")],
        [InlineKeyboardButton(text="🏠 Menu", callback_data="m_home")]])
    await send_safe(m.chat.id, txt, reply_markup=kb)

@router.callback_query(F.data == "m_auto")
async def cb_m_auto(c: CallbackQuery):
    await c.answer()
    await edit_safe(c.message, f"⚡ *Auto Post Studio*",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Create", callback_data="auto_new")],
            [InlineKeyboardButton(text="📋 My", callback_data="m_autos")],
            [InlineKeyboardButton(text="🏠 Menu", callback_data="m_home")]]))

@router.callback_query(F.data == "auto_new")
async def auto_new(c: CallbackQuery, state: FSMContext):
    await c.answer()
    if not await _enforce_limit(c, "automations", "Automations"): return
    accts = await db_list_accounts(c.from_user.id)
    if not accts:
        await edit_safe(c.message,
            f"❌ *No Accounts*\n\nAdd one first.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📱 Add", callback_data="acct_add")]]))
        return
    await state.clear(); await state.set_state(AutoSG.name)
    await c.message.answer(f"⚡ *New Automation*\n\n*Step 1/18* · Name")

@router.message(AutoSG.name)
async def as_name(m: Message, state: FSMContext):
    await state.update_data(name=(m.text or "").strip()[:60] or "Automation")
    await state.set_state(AutoSG.content_source)
    await m.answer(f"*Step 2/18* · Content Source",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📰 RSS", callback_data="asrc_rss")],
            [InlineKeyboardButton(text="🤖 AI", callback_data="asrc_ai")]]))

@router.callback_query(AutoSG.content_source, F.data.startswith("asrc_"))
async def as_source(c: CallbackQuery, state: FSMContext):
    src = c.data.split("_", 1)[1]
    await state.update_data(content_source=src); await state.set_state(AutoSG.topic)
    hint = ("Enter news keyword (e.g. `crypto`)" if src == "rss"
            else "Enter topic (e.g. `healthy tips`)")
    await edit_safe(c.message, f"*Step 3/18* · Topic\n\n{hint}")

@router.message(AutoSG.topic)
async def as_topic(m: Message, state: FSMContext):
    topic = (m.text or "").strip()
    if not topic: await m.answer("Topic required."); return
    await state.update_data(topic=topic[:300]); await state.set_state(AutoSG.language)
    await m.answer(f"*Step 4/18* · Language",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🇬🇧 EN", callback_data="alang_English"),
             InlineKeyboardButton(text="🇧🇩 BN", callback_data="alang_Bangla")]]))

@router.callback_query(AutoSG.language, F.data.startswith("alang_"))
async def as_lang(c: CallbackQuery, state: FSMContext):
    await state.update_data(language=c.data.split("_", 1)[1])
    await state.set_state(AutoSG.post_length)
    await edit_safe(c.message, f"*Step 5/18* · Length",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Short", callback_data="alen_short"),
             InlineKeyboardButton(text="Medium", callback_data="alen_medium"),
             InlineKeyboardButton(text="Long", callback_data="alen_long")]]))

@router.callback_query(AutoSG.post_length, F.data.startswith("alen_"))
async def as_len(c: CallbackQuery, state: FSMContext):
    await state.update_data(post_length=c.data.split("_", 1)[1])
    await state.set_state(AutoSG.image_size)
    await edit_safe(c.message, f"*Step 6/18* · Size", reply_markup=size_kb())

@router.callback_query(AutoSG.image_size, F.data.startswith("asize_"))
async def as_size(c: CallbackQuery, state: FSMContext):
    await state.update_data(image_size=c.data.split("_", 1)[1])
    await state.set_state(AutoSG.image_template)
    await edit_safe(c.message, f"*Step 7/18* · Template", reply_markup=templates_kb())

@router.callback_query(AutoSG.image_template, F.data.startswith("atpl_"))
async def as_tpl(c: CallbackQuery, state: FSMContext):
    await state.update_data(image_template=c.data.split("_", 1)[1])
    await state.set_state(AutoSG.image_source)
    await edit_safe(c.message, f"*Step 8/18* · Source", reply_markup=source_kb())

@router.callback_query(AutoSG.image_source, F.data.startswith("asrc_img_"))
async def as_imgsrc(c: CallbackQuery, state: FSMContext):
    src = c.data.replace("asrc_img_", "", 1)
    if src not in IMAGE_SOURCES: src = "cascade"
    await state.update_data(image_source=src); await state.set_state(AutoSG.color_theme)
    await edit_safe(c.message, f"*Step 9/18* · Color", reply_markup=color_kb())

@router.callback_query(AutoSG.color_theme, F.data.startswith("acolor_"))
async def as_color(c: CallbackQuery, state: FSMContext):
    await state.update_data(color_theme=c.data.split("_", 1)[1])
    await state.set_state(AutoSG.num_images)
    await edit_safe(c.message, f"*Step 10/18* · Images",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="1", callback_data="anum_1"),
             InlineKeyboardButton(text="2", callback_data="anum_2"),
             InlineKeyboardButton(text="3", callback_data="anum_3")]]))

@router.callback_query(AutoSG.num_images, F.data.startswith("anum_"))
async def as_num(c: CallbackQuery, state: FSMContext):
    await state.update_data(num_images=int(c.data.split("_", 1)[1]))
    await state.set_state(AutoSG.headline_on_image)
    await edit_safe(c.message, f"*Step 11/18* · Headline on image?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Yes", callback_data="ahoi_1")],
            [InlineKeyboardButton(text="✗ No", callback_data="ahoi_0")]]))

@router.callback_query(AutoSG.headline_on_image, F.data.startswith("ahoi_"))
async def as_hoi(c: CallbackQuery, state: FSMContext):
    await state.update_data(headline_on_image=int(c.data.split("_", 1)[1]))
    await state.set_state(AutoSG.inline_buttons)
    await edit_safe(c.message,
        f"*Step 12/18* · Inline Buttons\n\n"
        f"Format: `Label|url;Label2|url2`\nExample: `Read More|https://x.com`",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏭ Skip", callback_data="abtn_skip")]]))

@router.callback_query(F.data == "abtn_skip")
async def as_btn_skip(c: CallbackQuery, state: FSMContext):
    await state.update_data(inline_buttons="")
    await as_ask_ppd(c.message, state)

@router.message(AutoSG.inline_buttons)
async def as_btn(m: Message, state: FSMContext):
    await state.update_data(inline_buttons=(m.text or "").strip()[:500])
    await as_ask_ppd(m, state)

async def as_ask_ppd(m, state):
    await state.set_state(AutoSG.posts_per_day)
    await m.answer(f"*Step 13/18* · Posts/day",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="1", callback_data="appd_1"),
             InlineKeyboardButton(text="2", callback_data="appd_2"),
             InlineKeyboardButton(text="3", callback_data="appd_3")],
            [InlineKeyboardButton(text="4", callback_data="appd_4"),
             InlineKeyboardButton(text="6", callback_data="appd_6"),
             InlineKeyboardButton(text="8", callback_data="appd_8")]]))

@router.callback_query(AutoSG.posts_per_day, F.data.startswith("appd_"))
async def as_ppd(c: CallbackQuery, state: FSMContext):
    await state.update_data(posts_per_day=int(c.data.split("_", 1)[1]))
    await state.set_state(AutoSG.post_window)
    await edit_safe(c.message, f"*Step 14/18* · Time window",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="08:00–22:00", callback_data="awin_08:00-22:00")],
            [InlineKeyboardButton(text="06:00–23:00", callback_data="awin_06:00-23:00")],
            [InlineKeyboardButton(text="00:00–23:59", callback_data="awin_00:00-23:59")]]))

@router.callback_query(AutoSG.post_window, F.data.startswith("awin_"))
async def as_win(c: CallbackQuery, state: FSMContext):
    fr, un = c.data.split("_", 1)[1].split("-")
    await state.update_data(post_from=fr, post_until=un, days=[])
    await state.set_state(AutoSG.days)
    await edit_safe(c.message, f"*Step 15/18* · Active days",
        reply_markup=days_kb([]))

@router.callback_query(AutoSG.days, F.data.startswith("ady_"))
async def as_days(c: CallbackQuery, state: FSMContext):
    val = c.data.split("_", 1)[1]; d = await state.get_data()
    sel = d.get("days", [])
    if val == "DONE":
        if not sel: await c.answer("Select at least 1.", show_alert=True); return
        await state.update_data(days=sel, sel_accounts=[])
        accts = await db_list_accounts(c.from_user.id)
        rows = [[InlineKeyboardButton(text=f"☐ #{a['id']} {a['name']}",
            callback_data=f"aacc_{a['id']}")] for a in accts]
        rows.append([InlineKeyboardButton(text="✅ All", callback_data="aacc_ALL")])
        rows.append([InlineKeyboardButton(text="✓ Done", callback_data="aacc_DONE")])
        await state.set_state(AutoSG.accounts)
        await edit_safe(c.message, f"*Step 16/18* · Accounts",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
        return
    i = int(val)
    if i in sel: sel.remove(i)
    else: sel.append(i)
    await state.update_data(days=sel)
    await c.message.edit_reply_markup(reply_markup=days_kb(sel))
    await c.answer()

@router.callback_query(AutoSG.accounts, F.data.startswith("aacc_"))
async def as_accs(c: CallbackQuery, state: FSMContext):
    val = c.data.split("_", 1)[1]; d = await state.get_data()
    if val == "ALL":
        accts = await db_list_accounts(c.from_user.id)
        await state.update_data(sel_accounts=[a["id"] for a in accts])
        await as_ask_hashtag(c.message, state); return
    if val == "DONE":
        if not d.get("sel_accounts", []):
            await c.answer("Select at least 1.", show_alert=True); return
        await as_ask_hashtag(c.message, state); return
    aid = int(val); sel = d.get("sel_accounts", [])
    if aid in sel: sel.remove(aid)
    else: sel.append(aid)
    await state.update_data(sel_accounts=sel)
    accts = await db_list_accounts(c.from_user.id)
    rows = [[InlineKeyboardButton(
        text=("✅ " if a["id"] in sel else "☐ ") + f"#{a['id']} {a['name']}",
        callback_data=f"aacc_{a['id']}")] for a in accts]
    rows.append([InlineKeyboardButton(text="✅ All", callback_data="aacc_ALL")])
    rows.append([InlineKeyboardButton(text="✓ Done", callback_data="aacc_DONE")])
    await c.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await c.answer()

async def as_ask_hashtag(m, state):
    await state.set_state(AutoSG.hashtags)
    await m.answer(f"*Step 17/18* · Hashtags?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Yes", callback_data="atag_yes")],
            [InlineKeyboardButton(text="✗ No", callback_data="atag_no")]]))

@router.callback_query(AutoSG.hashtags, F.data.startswith("atag_"))
async def as_tags(c: CallbackQuery, state: FSMContext):
    use = c.data.endswith("yes")
    await state.update_data(use_hashtags=1 if use else 0)
    if use:
        groups = await db_list_hashtags(c.from_user.id)
        if groups:
            rows = [[InlineKeyboardButton(text=f"📌 {g['name']}",
                callback_data=f"ahg_{g['id']}")] for g in groups[:8]]
            rows.append([InlineKeyboardButton(text="🤖 AI", callback_data="ahg_ai")])
            await state.set_state(AutoSG.hashtag_group)
            await edit_safe(c.message, f"Hashtag source?",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
            return
    await state.update_data(hashtag_group="")
    await as_ask_link(c.message, state)

@router.callback_query(AutoSG.hashtag_group, F.data.startswith("ahg_"))
async def as_hg(c: CallbackQuery, state: FSMContext):
    val = c.data.split("_", 1)[1]
    await state.update_data(hashtag_group="" if val == "ai" else val)
    await as_ask_link(c.message, state)

async def as_ask_link(m, state):
    await state.set_state(AutoSG.link)
    await m.answer(f"*Step 18/18* · Link? (optional)",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏭ Skip", callback_data="alink_skip")]]))

@router.callback_query(F.data == "alink_skip")
async def as_link_skip(c: CallbackQuery, state: FSMContext):
    await state.update_data(link="", text_before_link="")
    await as_ask_mode(c.message, state)

@router.message(AutoSG.link)
async def as_link(m: Message, state: FSMContext):
    await state.update_data(link=(m.text or "").strip()[:300])
    await as_ask_mode(m, state)

async def as_ask_mode(m, state):
    await state.set_state(AutoSG.mode)
    await m.answer(f"Publish mode",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Auto", callback_data="amode_auto")],
            [InlineKeyboardButton(text="📝 Draft", callback_data="amode_draft")]]))

@router.callback_query(AutoSG.mode, F.data.startswith("amode_"))
async def as_mode(c: CallbackQuery, state: FSMContext):
    await state.update_data(mode=c.data.split("_", 1)[1])
    await as_show_confirm(c.message, state)

async def as_show_confirm(m, state):
    d = await state.get_data()
    slots = auto_slot_times(d["posts_per_day"], d["post_from"], d["post_until"])
    when = " · ".join(f"{h:02d}:{mm:02d}" for h, mm in slots)
    days_txt = ", ".join(WEEKDAYS[i] for i in sorted(d["days"]))
    src = "📰 RSS" if d.get("content_source") == "rss" else "🤖 AI"
    summary = (f"📋 *Confirm*\n\n"
               f"  📛 `{d['name']}`\n"
               f"  📡 {src}\n"
               f"  📝 `{d['topic'][:40]}`\n"
               f"  🌐 `{d['language']}`\n"
               f"  ⏰ `{d['posts_per_day']}×` · {when}\n"
               f"  📅 {days_txt}\n"
               f"  📮 `{len(d.get('sel_accounts', []))}` accounts")
    await state.set_state(AutoSG.confirm)
    await edit_safe(m, summary, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Create", callback_data="asave_Y")],
        [InlineKeyboardButton(text="✗ Cancel", callback_data="asave_N")]]))

@router.callback_query(AutoSG.confirm, F.data.startswith("asave_"))
async def as_save(c: CallbackQuery, state: FSMContext):
    d = await state.get_data()
    if not d.get("name") or not d.get("topic"):
        await state.clear(); await c.answer("Session expired", show_alert=True)
        await send_safe(c.message.chat.id, "⚠️ Session expired. Run /auto again.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔁 Retry", callback_data="auto_new")]]))
        return
    if c.data.endswith("N"):
        await state.clear(); await edit_safe(c.message, "✗ Cancelled."); return
    try:
        aid = await db_add_automation({
            "owner_id": c.from_user.id, "name": d["name"],
            "content_source": d.get("content_source", "ai"),
            "topic": d["topic"], "language": d["language"],
            "post_length": d["post_length"],
            "image_size": d.get("image_size", "square"),
            "image_template": d.get("image_template", "bottom_bar"),
            "image_source": d.get("image_source", "cascade"),
            "color_theme": d.get("color_theme", "gold"),
            "headline_on_image": d.get("headline_on_image", 1),
            "num_images": d.get("num_images", 1),
            "inline_buttons": d.get("inline_buttons", ""),
            "posts_per_day": d["posts_per_day"],
            "post_from": d["post_from"], "post_until": d["post_until"],
            "days": ",".join(map(str, d["days"])),
            "account_ids": ",".join(map(str, d.get("sel_accounts", []))),
            "generate_image": 1, "image_style": "real",
            "use_hashtags": d["use_hashtags"],
            "hashtag_group": d.get("hashtag_group", ""),
            "link": d["link"], "text_before_link": "", "mode": d["mode"]})
    except Exception as e:
        logger.error(f"db_add_automation: {e}")
        await c.answer("Save failed", show_alert=True); return
    row = await db_get_automation(aid); register_automation_jobs(row)
    await state.clear()
    await edit_safe(c.message,
        f"🎉 *Automation #{aid} Created!*\n\n  `{d['name']}`\n  `{d['posts_per_day']}× /day`",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Run Now", callback_data=f"arun_{aid}")],
            [InlineKeyboardButton(text="📋 All", callback_data="m_autos"),
             InlineKeyboardButton(text="🏠 Menu", callback_data="m_home")]]))

@router.callback_query(F.data == "m_autos")
async def cb_autos(c: CallbackQuery):
    await c.answer(); autos = await db_list_automations(c.from_user.id)
    if not autos:
        await edit_safe(c.message, f"📋 *Automations*\n\n❌ None.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Create", callback_data="auto_new")],
                [InlineKeyboardButton(text="🏠 Menu", callback_data="m_home")]]))
        return
    lines = [f"📋 *Automations* ({len(autos)})\n"]
    for a in autos:
        st = "🟢" if a["active"] else "⏸"
        lines.append(f"  {st} *#{a['id']}* {a['name']}\n     `{a['topic'][:30]}` · `{a['posts_per_day']}×/day`\n"
                     f"     ✅`{a['success_count']}` ❌`{a['fail_count']}`")
    rows = [[
        InlineKeyboardButton(text=f"▶️ #{a['id']}", callback_data=f"arun_{a['id']}"),
        InlineKeyboardButton(text=f"⏸ #{a['id']}", callback_data=f"atog_{a['id']}"),
        InlineKeyboardButton(text=f"🗑 #{a['id']}", callback_data=f"adel_{a['id']}")]
        for a in autos[:8]]
    rows.append([InlineKeyboardButton(text="➕ Create", callback_data="auto_new")])
    rows.append([InlineKeyboardButton(text="🏠 Menu", callback_data="m_home")])
    await edit_safe(c.message, "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

@router.callback_query(F.data.startswith("arun_"))
async def cb_arun(c: CallbackQuery):
    aid = int(c.data.split("_", 1)[1])
    await c.answer("Running…")
    await c.message.answer(f"⏳ Running #{aid}…", parse_mode="Markdown")
    asyncio.create_task(run_automation(aid, 999))

@router.callback_query(F.data.startswith("atog_"))
async def cb_atog(c: CallbackQuery):
    aid = int(c.data.split("_", 1)[1]); auto = await db_get_automation(aid)
    if not auto or auto["owner_id"] != c.from_user.id:
        await c.answer("Not owner", show_alert=True); return
    new = not bool(auto["active"])
    await db_toggle_automation(aid, c.from_user.id, new)
    register_automation_jobs(await db_get_automation(aid))
    await c.answer("On" if new else "Off")

@router.callback_query(F.data.startswith("adel_"))
async def cb_adel(c: CallbackQuery):
    aid = int(c.data.split("_", 1)[1])
    await db_del_automation(aid, c.from_user.id)
    for i in range(24):
        try: scheduler.remove_job(f"auto_{aid}_{i}")
        except Exception: pass
    await c.answer("Deleted")

# ═══════════════════════════════════════════════════════════
#  WATCHER WIZARD
# ═══════════════════════════════════════════════════════════
@router.message(Command("watch"))
async def cmd_watch(m: Message, state: FSMContext):
    if not await _enforce_limit(m, "watchers", "Watchers"): return
    await start_watcher_wizard(m, state)

@router.callback_query(F.data == "m_watch")
async def cb_m_watch(c: CallbackQuery):
    await c.answer()
    await edit_safe(c.message, f"📡 *Auto Forward*",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ New", callback_data="watch_new")],
            [InlineKeyboardButton(text="📋 My", callback_data="watch_list")],
            [InlineKeyboardButton(text="🏠 Menu", callback_data="m_home")]]))

@router.callback_query(F.data == "watch_list")
async def cb_watch_list(c: CallbackQuery):
    await c.answer(); await render_watchers(c)

@router.message(Command("watchers"))
async def cmd_watchers(m: Message): await render_watchers(m)

async def render_watchers(target):
    uid = target.from_user.id; rows = await db_list_watchers(uid)
    if not rows:
        txt = f"📡 *Watchers*\n\n❌ None configured."
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ New", callback_data="watch_new")],
            [InlineKeyboardButton(text="🏠 Menu", callback_data="m_home")]])
    else:
        lines = [f"📡 *Watchers* ({len(rows)})\n"]
        for w in rows:
            st = "🟢" if w["active"] else "⏸"
            stype = "🤖" if (w["source_type"] if "source_type" in w.keys() else "bot") == "bot" else "👤"
            dests = await db_get_watcher_dests(w["id"])
            lines.append(f"  {st} *#{w['id']}* {stype} `{w['source_chat']}`\n"
                         f"     `{len(dests)}` dest · `{w['mode']}` · ✓`{w['processed_count']}`")
        txt = "\n".join(lines)
        kr = []
        for w in rows[:8]:
            tg = "⏸" if w["active"] else "▶️"
            kr.append([InlineKeyboardButton(text=f"{tg} #{w['id']}", callback_data=f"wtog_{w['id']}"),
                       InlineKeyboardButton(text=f"🗑 #{w['id']}", callback_data=f"wdel_{w['id']}")])
        kr.append([InlineKeyboardButton(text="➕ New", callback_data="watch_new")])
        kr.append([InlineKeyboardButton(text="🏠 Menu", callback_data="m_home")])
        kb = InlineKeyboardMarkup(inline_keyboard=kr)
    if isinstance(target, Message): await send_safe(target.chat.id, txt, reply_markup=kb)
    else: await edit_safe(target.message, txt, reply_markup=kb)

@router.callback_query(F.data == "watch_new")
async def cb_watch_new(c: CallbackQuery, state: FSMContext):
    await c.answer()
    if not await _enforce_limit(c, "watchers", "Watchers"): return
    await start_watcher_wizard(c.message, state)

async def start_watcher_wizard(m, state):
    await state.clear(); await state.set_state(WatcherSG.source_type)
    await m.answer(f"📡 *New Watcher*\n\n*Step 1/12* · Source type",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🤖 Bot Source", callback_data="wstype_bot")],
            [InlineKeyboardButton(text="👤 Userbot (2GB)", callback_data="wstype_userbot")]]))

@router.callback_query(WatcherSG.source_type, F.data.startswith("wstype_"))
async def w_stype(c: CallbackQuery, state: FSMContext):
    st = c.data.replace("wstype_", "", 1)
    await state.update_data(source_type=st)
    if st == "bot":
        bots_db = await db_list_bots(c.from_user.id)
        rows = [[InlineKeyboardButton(text=f"🤖 {b['name']}",
            callback_data=f"wsb_{b['id']}")] for b in bots_db[:8]]
        rows.append([InlineKeyboardButton(text="⚡ Main Bot", callback_data="wsb_MAIN")])
        rows.append([InlineKeyboardButton(text="✗ Cancel", callback_data="m_home")])
        await state.set_state(WatcherSG.source_bot)
        await edit_safe(c.message, f"*Step 2/12* · Select bot",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)); return
    ubs = await db_list_userbots(c.from_user.id)
    if not ubs:
        await edit_safe(c.message, f"❌ No userbots available.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👤 Add", callback_data="ub_add")]]))
        return
    rows = [[InlineKeyboardButton(text=f"👤 {u['name']}",
        callback_data=f"wub_{u['id']}")] for u in ubs]
    rows.append([InlineKeyboardButton(text="✗ Cancel", callback_data="m_home")])
    await state.set_state(WatcherSG.userbot_pick)
    await edit_safe(c.message, f"*Step 2/12* · Select userbot",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

@router.callback_query(WatcherSG.userbot_pick, F.data.startswith("wub_"))
async def w_pick_ub(c: CallbackQuery, state: FSMContext):
    ub_id = int(c.data.split("_", 1)[1]); row = await db_get_userbot(ub_id)
    if not row or row["owner_id"] != c.from_user.id:
        await c.answer("Not owner", show_alert=True); return
    await c.answer(); await state.update_data(userbot_id=ub_id)
    await state.set_state(WatcherSG.source_chat)
    await edit_safe(c.message,
        f"✅ Userbot #{ub_id}\n\n*Step 3/12* · Source channel\n"
        f"_Send @username or -100..._")

@router.callback_query(WatcherSG.source_bot, F.data.startswith("wsb_"))
async def w_source_bot(c: CallbackQuery, state: FSMContext):
    val = c.data.replace("wsb_", "", 1); await c.answer()
    if val == "MAIN":
        await state.update_data(source_bot_db_id=0, source_bot_token=TOKEN)
    else:
        bid = int(val); row = await db_get_bot(bid)
        if not row or row["owner_id"] != c.from_user.id:
            await c.answer("Not owner", show_alert=True); return
        await state.update_data(source_bot_db_id=bid, source_bot_token=row["token"])
    await state.set_state(WatcherSG.source_chat)
    await edit_safe(c.message,
        f"*Step 3/12* · Source channel\n\n_Send @username or -100..._\n"
        f"_Or forward a message to auto-detect._")

@router.message(WatcherSG.source_chat)
async def w_source(m: Message, state: FSMContext):
    d = await state.get_data()
    src = str(m.forward_from_chat.id) if m.forward_from_chat else (m.text or "").strip()
    if not src: await m.answer("Source required."); return
    await state.update_data(source_chat=src); await state.set_state(WatcherSG.mode)
    if d.get("source_type") == "userbot":
        rows = [
            [InlineKeyboardButton(text="🚀 Direct Fwd (2GB)", callback_data="wmode_direct_forward")],
            [InlineKeyboardButton(text="⚡ Direct Copy (2GB)", callback_data="wmode_direct_copy")],
            [InlineKeyboardButton(text="📨 Bot Fwd (48MB)", callback_data="wmode_forward")],
            [InlineKeyboardButton(text="📋 Bot Copy", callback_data="wmode_copy")],
            [InlineKeyboardButton(text="🤖 AI Rewrite", callback_data="wmode_ai_rewrite")],
            [InlineKeyboardButton(text="🎨 AI + Image", callback_data="wmode_ai_rewrite_image")]]
    else:
        rows = [
            [InlineKeyboardButton(text="📨 Bot Fwd", callback_data="wmode_forward")],
            [InlineKeyboardButton(text="📋 Bot Copy", callback_data="wmode_copy")],
            [InlineKeyboardButton(text="🚀 Direct Fwd (userbot)", callback_data="wmode_direct_forward")],
            [InlineKeyboardButton(text="🤖 AI Rewrite", callback_data="wmode_ai_rewrite")],
            [InlineKeyboardButton(text="🎨 AI + Image", callback_data="wmode_ai_rewrite_image")]]
    await m.answer(f"*Step 4/12* · Mode",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

@router.callback_query(WatcherSG.mode, F.data.startswith("wmode_"))
async def w_mode(c: CallbackQuery, state: FSMContext):
    mode = c.data.replace("wmode_", "", 1); await state.update_data(mode=mode)
    if mode in ("forward", "copy", "direct_forward", "direct_copy"):
        await ask_media_filter(c.message, state); return
    await state.set_state(WatcherSG.lang)
    await edit_safe(c.message, f"*Step 5/12* · Language",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🇬🇧 EN", callback_data="wlang_English"),
             InlineKeyboardButton(text="🇧🇩 BN", callback_data="wlang_Bangla")]]))

@router.callback_query(WatcherSG.lang, F.data.startswith("wlang_"))
async def w_lang(c: CallbackQuery, state: FSMContext):
    await state.update_data(rewrite_language=c.data.replace("wlang_", "", 1))
    await ask_media_filter(c.message, state)

async def ask_media_filter(m, state):
    await state.set_state(WatcherSG.media_filter)
    await m.answer(f"*Step 6/12* · Media filter",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🌐 Any", callback_data="wmed_any")],
            [InlineKeyboardButton(text="📝 Text", callback_data="wmed_text")],
            [InlineKeyboardButton(text="🖼 Photo", callback_data="wmed_photo")],
            [InlineKeyboardButton(text="🎬 Video", callback_data="wmed_video")],
            [InlineKeyboardButton(text="📄 Doc", callback_data="wmed_document")],
            [InlineKeyboardButton(text="🎞 Media", callback_data="wmed_media")]]))

@router.callback_query(WatcherSG.media_filter, F.data.startswith("wmed_"))
async def w_med(c: CallbackQuery, state: FSMContext):
    await state.update_data(media_filter=c.data.replace("wmed_", "", 1))
    await state.set_state(WatcherSG.keyword)
    await edit_safe(c.message, f"*Step 7/12* · Keywords\n(comma-separated or skip)",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏭ Skip", callback_data="wkw_skip")]]))

@router.callback_query(F.data == "wkw_skip")
async def w_kw_skip(c: CallbackQuery, state: FSMContext):
    await state.update_data(keyword_filter="")
    await ask_block(c.message, state)

@router.message(WatcherSG.keyword)
async def w_kw(m: Message, state: FSMContext):
    await state.update_data(keyword_filter=(m.text or "").strip()[:300])
    await ask_block(m, state)

async def ask_block(m, state):
    await state.set_state(WatcherSG.block)
    await m.answer(f"*Step 8/12* · Block words",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏭ Skip", callback_data="wbl_skip")]]))

@router.callback_query(F.data == "wbl_skip")
async def w_bl_skip(c: CallbackQuery, state: FSMContext):
    await state.update_data(block_words="")
    await ask_minlen(c.message, state)

@router.message(WatcherSG.block)
async def w_bl(m: Message, state: FSMContext):
    await state.update_data(block_words=(m.text or "").strip()[:300])
    await ask_minlen(m, state)

async def ask_minlen(m, state):
    await state.set_state(WatcherSG.min_length)
    await m.answer(f"*Step 9/12* · Min length",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="0", callback_data="wml_0"),
             InlineKeyboardButton(text="50", callback_data="wml_50"),
             InlineKeyboardButton(text="100", callback_data="wml_100")]]))

@router.callback_query(WatcherSG.min_length, F.data.startswith("wml_"))
async def w_ml(c: CallbackQuery, state: FSMContext):
    await state.update_data(min_length=int(c.data.split("_", 1)[1]))
    d = await state.get_data(); mode = d.get("mode", "forward")
    if mode == "ai_rewrite_image":
        await state.set_state(WatcherSG.template)
        await edit_safe(c.message, f"*Step 10/12* · Template", reply_markup=templates_kb())
        return
    if mode == "ai_rewrite":
        await state.update_data(brand_template="bottom_bar", brand_color="#ffce00")
    await ask_footer(c.message, state)

@router.callback_query(WatcherSG.template, F.data.startswith("atpl_"))
async def w_tpl(c: CallbackQuery, state: FSMContext):
    await state.update_data(brand_template=c.data.split("_", 1)[1])
    await state.set_state(WatcherSG.color)
    await edit_safe(c.message, f"*Step 11/12* · Color", reply_markup=color_kb())

@router.callback_query(WatcherSG.color, F.data.startswith("acolor_"))
async def w_color(c: CallbackQuery, state: FSMContext):
    theme = c.data.split("_", 1)[1]
    await state.update_data(color_theme=theme,
                            brand_color=COLOR_THEMES.get(theme, "#ffce00"))
    await ask_footer(c.message, state)

async def ask_footer(m, state):
    await state.set_state(WatcherSG.footer)
    await m.answer(f"*Step 12/12* · Footer (optional)",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏭ Skip", callback_data="wft_skip")]]))

@router.callback_query(F.data == "wft_skip")
async def w_ft_skip(c: CallbackQuery, state: FSMContext):
    await state.update_data(footer="")
    await ask_delay(c.message, state)

@router.message(WatcherSG.footer)
async def w_ft(m: Message, state: FSMContext):
    await state.update_data(footer=(m.text or "").strip()[:200])
    await ask_delay(m, state)

async def ask_delay(m, state):
    await state.set_state(WatcherSG.delay)
    await m.answer(f"Delay between destinations",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="3s", callback_data="wdly_3"),
             InlineKeyboardButton(text="10s", callback_data="wdly_10"),
             InlineKeyboardButton(text="30s", callback_data="wdly_30")]]))

@router.callback_query(WatcherSG.delay, F.data.startswith("wdly_"))
async def w_dly(c: CallbackQuery, state: FSMContext):
    await state.update_data(delay_seconds=int(c.data.split("_", 1)[1]))
    accts = await db_list_accounts(c.from_user.id)
    if not accts:
        await edit_safe(c.message, f"❌ No accounts.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📱 Add", callback_data="acct_add")]]))
        await state.clear(); return
    rows = [[InlineKeyboardButton(text=f"☐ #{a['id']} {a['name']}",
        callback_data=f"wdst_{a['id']}")] for a in accts]
    rows.append([InlineKeyboardButton(text="✅ All", callback_data="wdst_ALL")])
    rows.append([InlineKeyboardButton(text="✓ Done", callback_data="wdst_DONE")])
    await state.update_data(sel_dests=[])
    await state.set_state(WatcherSG.dests)
    await edit_safe(c.message, f"*Destinations*",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

@router.callback_query(WatcherSG.dests, F.data.startswith("wdst_"))
async def w_dst(c: CallbackQuery, state: FSMContext):
    val = c.data.split("_", 1)[1]; d = await state.get_data()
    if val == "ALL":
        accts = await db_list_accounts(c.from_user.id)
        await state.update_data(sel_dests=[a["id"] for a in accts])
        await w_confirm(c.message, state, c.from_user.id); return
    if val == "DONE":
        if not d.get("sel_dests", []):
            await c.answer("Select at least 1.", show_alert=True); return
        await w_confirm(c.message, state, c.from_user.id); return
    aid = int(val); sel = d.get("sel_dests", [])
    if aid in sel: sel.remove(aid)
    else: sel.append(aid)
    await state.update_data(sel_dests=sel)
    accts = await db_list_accounts(c.from_user.id)
    rows = [[InlineKeyboardButton(
        text=("✅ " if a["id"] in sel else "☐ ") + f"#{a['id']} {a['name']}",
        callback_data=f"wdst_{a['id']}")] for a in accts]
    rows.append([InlineKeyboardButton(text="✅ All", callback_data="wdst_ALL")])
    rows.append([InlineKeyboardButton(text="✓ Done", callback_data="wdst_DONE")])
    await c.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await c.answer()

async def w_confirm(m, state, owner_id):
    d = await state.get_data()
    if not d.get("source_chat"):
        await state.clear()
        await send_safe(m.chat.id, "⚠️ Session expired. Run /watch again.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔁 Retry", callback_data="watch_new")]]))
        return
    accts = await db_list_accounts(owner_id); sel = d.get("sel_dests", [])
    dest_list = []
    for aid in sel:
        a = next((x for x in accts if x["id"] == aid), None)
        if a: dest_list.append(f"  • #{a['id']} {a['name']}")
    stype = d.get("source_type", "bot")
    txt = (f"📋 *Confirm Watcher*\n\n"
           f"  📥 `{d.get('source_chat')}`\n"
           f"  🔖 {stype}\n"
           f"  ⚙️ `{d.get('mode')}`\n"
           f"  🌐 `{d.get('rewrite_language', 'English')}`\n"
           f"  🎯 `{d.get('media_filter')}`\n"
           f"  ⏱ `{d.get('delay_seconds')}s`\n\n"
           f"  📤 Destinations ({len(sel)}):\n" + "\n".join(dest_list))
    await state.set_state(WatcherSG.confirm)
    await edit_safe(m, txt, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Create", callback_data="wsave_Y")],
        [InlineKeyboardButton(text="✗ Cancel", callback_data="wsave_N")]]))

@router.callback_query(WatcherSG.confirm, F.data.startswith("wsave_"))
async def w_save(c: CallbackQuery, state: FSMContext):
    d = await state.get_data()
    if not d.get("source_chat"):
        await state.clear(); await c.answer("Session expired", show_alert=True)
        await send_safe(c.message.chat.id, "⚠️ Session expired. Run /watch again.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔁 Retry", callback_data="watch_new")]]))
        return
    if c.data.endswith("N"):
        await state.clear(); await edit_safe(c.message, "✗ Cancelled."); return
    src = d["source_chat"]; stype = d.get("source_type", "bot")
    ub_id = d.get("userbot_id", 0); bdb = d.get("source_bot_db_id", 0)
    bt = d.get("source_bot_token", TOKEN)
    suname = ""; scid = ""
    if stype == "userbot" and ub_id:
        client = _userbot_clients.get(ub_id)
        chat = await try_resolve_chat(client, src) if client else None
        if chat:
            scid = str(chat.id); suname = getattr(chat, "username", "") or ""
    elif stype == "bot":
        if bdb:
            row = await db_get_bot(bdb)
            if row:
                try:
                    b = get_bot_for_token(row["token"])
                    ch = await b.get_chat(src)
                    scid = str(ch.id); suname = getattr(ch, "username", "") or ""
                except Exception: pass
        if not scid:
            s = src.strip()
            if s.startswith("@"):
                try:
                    ch = await bot.get_chat(s)
                    scid = str(ch.id); suname = ch.username or ""
                except Exception: pass
            else: scid = s
    try:
        wid = await db_add_watcher({
            "owner_id": c.from_user.id, "source_chat": src, "source_title": src,
            "source_type": stype, "userbot_id": ub_id, "source_bot_db_id": bdb,
            "source_bot_token": bt, "mode": d.get("mode", "forward"),
            "brand_template": d.get("brand_template", "bottom_bar"),
            "brand_color": d.get("brand_color", "#ffce00"),
            "keyword_filter": d.get("keyword_filter", ""),
            "block_words": d.get("block_words", ""),
            "min_length": d.get("min_length", 0),
            "media_filter": d.get("media_filter", "any"),
            "footer": d.get("footer", ""),
            "delay_seconds": d.get("delay_seconds", 3),
            "rewrite_language": d.get("rewrite_language", "English")})
    except Exception as e:
        logger.error(f"db_add_watcher: {e}")
        await c.answer("Save failed", show_alert=True); return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE watchers SET source_username=?, source_chat_id=? WHERE id=?",
                         (suname, scid, wid))
        await db.commit()
    for aid in d.get("sel_dests", []):
        await db_add_watcher_dest(wid, aid)
    await state.clear()
    await edit_safe(c.message,
        f"🎉 *Watcher #{wid} Created!*\n\n  📥 `{scid or src}`\n  📤 `{len(d.get('sel_dests', []))}`",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 All", callback_data="watch_list")],
            [InlineKeyboardButton(text="🏠 Menu", callback_data="m_home")]]))

@router.callback_query(F.data.startswith("wtog_"))
async def w_tog(c: CallbackQuery):
    wid = int(c.data.split("_", 1)[1]); w = await db_get_watcher(wid)
    if not w or w["owner_id"] != c.from_user.id:
        await c.answer("Not owner", show_alert=True); return
    new = not bool(w["active"])
    await db_toggle_watcher(wid, c.from_user.id, new)
    await c.answer("On" if new else "Off"); await render_watchers(c)

@router.callback_query(F.data.startswith("wdel_"))
async def w_del(c: CallbackQuery):
    wid = int(c.data.split("_", 1)[1])
    await db_del_watcher(wid, c.from_user.id)
    await c.answer("Deleted"); await render_watchers(c)

# ═══════════════════════════════════════════════════════════
#  CHANNEL POST HANDLER (main bot)
# ═══════════════════════════════════════════════════════════
@router.channel_post()
async def on_channel_post(msg: Message):
    try: await process_source_post(bot, msg, source_bot_db_id=0)
    except Exception as e: logger.error(f"channel_post: {e}")

# ═══════════════════════════════════════════════════════════
#  AI COMPOSE
# ═══════════════════════════════════════════════════════════
@router.message(Command("compose"))
async def cmd_compose(m: Message, state: FSMContext):
    if not await has_feature(m.from_user.id, "ai_compose"):
        await send_safe(m.chat.id,
            f"⭐ *AI Compose requires Premium*\n\n_Upgrade to unlock._",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⭐ View Plans", callback_data="pm_main")]]))
        return
    await send_safe(m.chat.id, f"🎨 *AI Compose*\n\n_Send the topic._")
    await state.set_state(ComposeSG.enter_topic)

@router.callback_query(F.data == "m_compose")
async def cb_compose(c: CallbackQuery, state: FSMContext):
    await c.answer()
    if not await has_feature(c.from_user.id, "ai_compose"):
        await c.message.answer(
            f"⭐ *AI Compose requires Premium*\n\n_Upgrade to unlock._",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⭐ View Plans", callback_data="pm_main")]]))
        return
    await c.message.answer(f"🎨 *AI Compose*\n\n_Send the topic._", parse_mode="Markdown")
    await state.set_state(ComposeSG.enter_topic)

@router.message(ComposeSG.enter_topic)
async def compose_topic(m: Message, state: FSMContext):
    topic = (m.text or "").strip()
    if not topic: await m.answer("Topic required."); return
    await state.clear()
    wait = await m.answer("⏳ Generating…")
    lang = "Bangla" if re.search(r"[\u0980-\u09FF]", topic) else "English"
    prompt = (f"Write a social post in {lang} about: {topic}\nNo markdown.\n"
              f"Return EXACTLY:\nHeadline: ...\nHook: ...\nBody: ...\nCTA: ...\nHashtags: ...")
    ai = await ai_generate_text(prompt, system="Professional copywriter.")
    if not ai.get("ok"):
        try: await wait.delete()
        except Exception: pass
        await send_safe(m.chat.id, "❌ AI failed."); return
    parsed = parse_labeled(ai["text"])
    if not parsed["headline"]: parsed["headline"] = topic[:80]
    try: await wait.delete()
    except Exception: pass
    wait2 = await m.answer("🎨 Composing image…")
    raw = await generate_ai_image(f"{parsed['headline']}. {parsed['hook'][:80]}", 1080, 1080)
    img_url = None
    if raw:
        raw = await compose_image(raw, headline=parsed["headline"], template="bottom_bar")
        ib = await upload_to_imgbb(raw)
        img_url = ib.get("url") if ib.get("ok") else None
    text = strip_md_stars(clean_text(
        f"{parsed['headline']}\n\n{parsed['hook']}\n\n{parsed['body']}\n\n"
        f"{parsed['cta']}\n\n{parsed['hashtags']}"))
    try: await wait2.delete()
    except Exception: pass
    if raw:
        await bot.send_photo(m.chat.id, BufferedInputFile(raw, filename="post.jpg"),
                             caption=text[:1000])
    else: await send_safe(m.chat.id, text[:4000])
    await state.update_data(ctext=text, cimg_url=img_url,
                            cimg_bytes=raw.hex() if raw else None)
    await send_safe(m.chat.id, f"✅ *Generated via* `{ai['provider']}`",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📣 Broadcast", callback_data="cp_bc")],
            [InlineKeyboardButton(text="🏠 Menu", callback_data="m_home")]]))

@router.callback_query(F.data == "cp_bc")
async def cp_bc(c: CallbackQuery, state: FSMContext):
    await c.answer(); d = await state.get_data(); await state.clear()
    await state.update_data(ctext=d.get("ctext"), cimg_url=d.get("cimg_url"),
                            cimg_bytes=d.get("cimg_bytes"))
    await start_broadcast(c.message, state, c.from_user.id)

# ═══════════════════════════════════════════════════════════
#  BROADCAST
# ═══════════════════════════════════════════════════════════
async def start_broadcast(m, state, owner_id):
    accts = await db_list_accounts(owner_id)
    if not accts:
        await send_safe(m.chat.id, f"❌ No accounts.",
            reply_markup=back_home()); await state.clear(); return
    rows = [[InlineKeyboardButton(text=f"☐ #{a['id']} {a['name']}",
        callback_data=f"bcacc_{a['id']}")] for a in accts]
    rows.append([InlineKeyboardButton(text="📣 All", callback_data="bcacc_ALL")])
    rows.append([InlineKeyboardButton(text="✓ Done", callback_data="bcacc_DONE")])
    rows.append([InlineKeyboardButton(text="✗ Cancel", callback_data="bcacc_CANCEL")])
    await state.update_data(bc_sel=[])
    await state.set_state(BroadcastSG.choose_targets)
    await m.answer(f"📣 *Broadcast*\n\n_Select accounts._",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

@router.message(Command("broadcast"))
async def cmd_bc(m: Message, state: FSMContext):
    await start_broadcast(m, state, m.from_user.id)

@router.callback_query(F.data == "m_bcast")
async def cb_mbc(c: CallbackQuery, state: FSMContext):
    await c.answer(); await start_broadcast(c.message, state, c.from_user.id)

@router.callback_query(BroadcastSG.choose_targets, F.data.startswith("bcacc_"))
async def bc_pick(c: CallbackQuery, state: FSMContext):
    val = c.data.split("_", 1)[1]; d = await state.get_data()
    if val == "CANCEL":
        await state.clear(); await edit_safe(c.message, "✗ Cancelled."); return
    if val == "ALL":
        accts = await db_list_accounts(c.from_user.id)
        await state.update_data(bc_sel=[a["id"] for a in accts])
        await state.set_state(BroadcastSG.enter_content)
        await edit_safe(c.message, f"📝 Send message/photo/video to broadcast."); return
    if val == "DONE":
        if not d.get("bc_sel", []):
            await c.answer("Select at least 1.", show_alert=True); return
        await state.set_state(BroadcastSG.enter_content)
        await edit_safe(c.message, f"📝 Send content."); return
    aid = int(val); sel = d.get("bc_sel", [])
    if aid in sel: sel.remove(aid)
    else: sel.append(aid)
    await state.update_data(bc_sel=sel)
    accts = await db_list_accounts(c.from_user.id)
    rows = [[InlineKeyboardButton(
        text=("✅ " if a["id"] in sel else "☐ ") + f"#{a['id']} {a['name']}",
        callback_data=f"bcacc_{a['id']}")] for a in accts]
    rows.append([InlineKeyboardButton(text="📣 All", callback_data="bcacc_ALL")])
    rows.append([InlineKeyboardButton(text="✓ Done", callback_data="bcacc_DONE")])
    rows.append([InlineKeyboardButton(text="✗ Cancel", callback_data="bcacc_CANCEL")])
    await c.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await c.answer()

@router.message(BroadcastSG.enter_content)
async def bc_content(m: Message, state: FSMContext):
    d = await state.get_data()
    if d.get("ctext"):
        await do_multi_bc(m, state, text=d["ctext"], image_url=d.get("cimg_url"),
                          img_hex=d.get("cimg_bytes")); return
    if m.text: await do_multi_bc(m, state, text=m.text)
    elif m.photo:
        await do_multi_bc(m, state, text=m.caption or "",
                          file_id=m.photo[-1].file_id, ctype="photo")
    elif m.video:
        await do_multi_bc(m, state, text=m.caption or "",
                          file_id=m.video.file_id, ctype="video")

async def do_multi_bc(m, state, text="", image_url=None, img_hex=None,
                      file_id=None, ctype="text"):
    d = await state.get_data(); sel = d.get("bc_sel", [])
    if not sel:
        await m.answer("No accounts."); await state.clear(); return
    img_bytes = bytes.fromhex(img_hex) if img_hex else None
    sent = fail = 0; errors = []
    for aid in sel:
        acc = await db_get_account(aid)
        if not acc: continue
        if file_id: ok, err = await send_file_to(acc, ctype, file_id, text)
        elif image_url or img_bytes:
            ok, err = await send_photo_to(acc, text, image_url=image_url,
                                          image_bytes=img_bytes)
        else: ok, err = await send_text_to(acc, text)
        if ok:
            sent += 1; await db_bump_account_post(aid); await db_log(aid, "ok")
        else:
            fail += 1; errors.append(f"#{aid}: {err}"); await db_log(aid, "fail", err)
    result = f"📣 *Broadcast*\n\n  ✅ `{sent}`\n  ❌ `{fail}`"
    if errors: result += "\n\n" + "\n".join(f"  • {e}" for e in errors[:5])
    await send_safe(m.chat.id, result, reply_markup=main_menu())
    await state.clear()

# ============================================================
#  STARTUP / SHUTDOWN
# ============================================================
async def on_startup():
    await db_init()
    await check_all_expirations()
    scheduler.start()
    await load_all_jobs()
    asyncio.create_task(start_all_userbots())
    asyncio.create_task(poll_userbot_watchers_loop())
    asyncio.create_task(start_all_bot_pollers())
    me = await bot.get_me()
    logger.info(f"✅ v16 Premium Edition started: @{me.username}")

async def on_shutdown():
    try: scheduler.shutdown(wait=False)
    except Exception: pass
    for uid in list(_userbot_clients.keys()):
        try: await stop_userbot(uid)
        except Exception: pass
    for bid in list(_bot_pollers.keys()):
        try: await stop_bot_poller(bid)
        except Exception: pass
    for uid in list(_login_clients.keys()):
        try: await _login_clients[uid].disconnect()
        except Exception: pass
    for b in _bot_cache.values():
        try: await b.session.close()
        except Exception: pass
    await bot.session.close()

async def main():
    await on_startup()
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await on_shutdown()

if __name__ == "__main__":
    asyncio.run(main())