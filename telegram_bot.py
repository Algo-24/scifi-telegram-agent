import os
import re
import asyncio
import threading
from flask import Flask
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from google import genai

# --- 1. RENDER UXLAB QOLMASLIGI UCHUN VEB-SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "🤖 Sci-Fi Rejissyor Bot faol ishlayapti!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# --- 2. BOT VA GEMINI SOZLAMALARI ---
# Kalitlar to'g'ridan-to'g'ri yozilmaydi, Render environment'dan olinadi
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY:
    raise ValueError("TELEGRAM_BOT_TOKEN yoki GEMINI_API_KEY topilmadi!")

client = genai.Client(api_key=GEMINI_API_KEY)
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

SYSTEM_INSTRUCTION = """
Siz dunyo miqyosidagi Hollywood Ilmiy-Fantastik (Sci-Fi) film rejissyori, bosh ssenarist va Lead AI Prompt Engineersiz.
Sizning vazifangiz: Berilgan mavzu asosida chuqur ilmiy asoslangan, falsafiy tagma'noli va YouTube tomoshabinlarini birinchi sekunddanoq o'ziga rom etadigan professional ssenariy yaratish.

### NIMA QILISH KERAK (STRICT RULES):
1. **Chuqur Konsepsiya:** Fizik qonuniyatlar, psixologik bosim va futuristik muhitni ochib bering.
2. **Hook (Ilgak):** Birinchi kadrdayoq tomoshabinning ongini larzaga keltiradigan savol yoki vizual lahza bilan boshlang.
3. **Consistency:** Yagona vizual va ranglar palitrasi standartini belgilang.
4. **Professional Promptlar:** AI Visual Prompt qismlari faqat INGLIZ TILIDA, Midjourney v6 va Flux.1 Ultra standartlariga mos holda yozilsin.
5. **Dublyaj Matni:** O'zbek tilidagi ovoz berish matni ta'sirli va professional bo'lsin.

### NIMA QILISH KERAKMAS (NEGATIVE CONSTRAINTS):
1. **Mavhum so'zlar taqiqlanadi:** 'beautiful', 'cool', 'nice' kabi so'zlarni ishlatmang. Aniq vizual detallar yozing.
2. **Zerikarli kirishlar taqiqlanadi:** 'Qadim zamonlardan beri...', 'Hammaga salom...' demang.
"""

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🤖 **Sci-Fi Rejissyor Agentiga xush kelibsiz!**\n\n"
        "Guruhda ssenariy yozish uchun quyidagi buyruqdan foydalaning:\n"
        "👉 `/ssenariy [film mavzusi]`\n\n"
        "Masalan: `/ssenariy 2150-yilda Marsdagi tashlab ketilgan baza`"
    )

@dp.message(Command("ssenariy"))
async def cmd_ssenariy(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ Iltimos, film mavzusini yozing!\nMasalan: `/ssenariy Koinot chegarasi`")
        return

    movie_topic = args[1]
    processing_msg = await message.answer(f"🚀 **'{movie_topic}'** mavzusi bo'yicha 3.8 Flash rejissyor agent ish boshladi... Kuting ⏳")

    try:
        prompt = f"""
        Mavzu: '{movie_topic}'
        Yuqori darajadagi tahlil bilan professional ssenariy va shotlist tuzing:
        ---
        # FILM KONSEPSIYASI VA ANALIZ
        * **Loglayn/Mavzu:** ...
        * **Psychological & Sci-Fi Hook:** ...
        * **Visual Style & Color Palette:** ...
        ---
        # KADRLAR VA SSENARIY (SHOTLIST)
        ### Kadr [Raqam] ([Vaqt]) - [Kadr nomi]
        * **Ovoz beruvchi matni (UZB):** ...
        * **AI Visual Prompt (ENG):** ...
        * **Audio FX / Sound Design:** ...
        """

        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt,
            config={
                "system_instruction": SYSTEM_INSTRUCTION,
                "temperature": 0.7
            }
        )

        output_dir = "/tmp/SENARIY" if os.name != 'nt' else r"E:\AI AGENTS\SENARIY"
        os.makedirs(output_dir, exist_ok=True)

        safe_topic = re.sub(r'[\\/*?:"<>|]', "", movie_topic).strip()
        if not safe_topic:
            safe_topic = "Ssenariy"

        file_path = os.path.join(output_dir, f"{safe_topic}.txt")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(response.text)

        document = FSInputFile(file_path)
        await message.answer_document(
            document=document,
            caption=f"✅ **'{movie_topic}'** bo'yicha ssenariy tayyor!\n📂 Fayl guruhga yuklandi 🎬"
        )
        
        await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)

    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

async def main():
    print("🤖 Telegram bot va veb-server ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())