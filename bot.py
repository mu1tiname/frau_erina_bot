import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

# Твой токен бота
TOKEN = "7657539488:AAEa7y-BuaFB6sZTaTwIV2OnTjPSNIORIWQ"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хранилище данных пользователей
users_data = {}

# Клавиатура с кнопкой "Дальше"
def next_button():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Дальше", callback_data="next_word")]
    ])
    return keyboard

# Клавиатура после завершения списка слов
def repeat_buttons():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Повторить список", callback_data="repeat_list")],
        [InlineKeyboardButton(text="➕ Загрузить новые слова", callback_data="new_list")]
    ])
    return keyboard

# Команда /start
@dp.message(Command("start"))
async def start_handler(message: Message):
    user_id = message.chat.id
    users_data[user_id] = {"words": [], "index": 0}
    await message.answer("Привет! Отправь список слов или фраз с помощью команды /add.")

# Команда /add для загрузки слов
@dp.message(Command("add"))
async def add_words_handler(message: Message):
    user_id = message.chat.id
    new_words = message.text.replace("/add", "").strip().split("\n")
    
    if user_id not in users_data:
        users_data[user_id] = {"words": [], "index": 0}

    users_data[user_id]["words"].extend(new_words)
    users_data[user_id]["index"] = 0

    await message.answer(f"Добавлено {len(new_words)} слов/фраз. Начинаем изучение!")
    
    # Отправляем первое слово сразу
    await send_next_word(user_id)

# Команда /list для показа списка слов
@dp.message(Command("list"))
async def list_words_handler(message: Message):
    user_id = message.chat.id
    user_data = users_data.get(user_id, {"words": []})

    if not user_data["words"]:
        await message.answer("Список слов пуст. Добавьте слова командой /add.")
    else:
        words_text = "\n".join([f"{i+1}. {word}" for i, word in enumerate(user_data["words"])])
        await message.answer(f"📜 *Ваши слова/фразы:*\n\n{words_text}", parse_mode="Markdown")

# Функция отправки следующего слова
async def send_next_word(user_id):
    user_data = users_data.get(user_id, {"words": [], "index": 0})

    if user_data["index"] < len(user_data["words"]):
        word = user_data["words"][user_data["index"]]
        users_data[user_id]["index"] += 1  # ОБЯЗАТЕЛЬНО ОБНОВЛЯЕМ INDEX!

        # Отправляем слово + кнопку "Дальше"
        await bot.send_message(chat_id=user_id, text=f"📖 {word}", reply_markup=next_button())
    else:
        # Если слова закончились – показать кнопки повторения или загрузки нового списка
        await bot.send_message(chat_id=user_id, text="✅ Ты изучил все слова! Что делать дальше?", reply_markup=repeat_buttons())

# Обработчик кнопки "Дальше"
@dp.callback_query(lambda call: call.data == "next_word")
async def next_word_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.message.chat.id
    await process_next_word(user_id)

# Обработчик **любого** сообщения как "Дальше"
@dp.message()
async def any_message_handler(message: Message):
    user_id = message.chat.id
    await process_next_word(user_id)

# Функция обработки "Дальше" с таймером 5 минут
async def process_next_word(user_id):
    user_data = users_data.get(user_id, {"words": [], "index": 0})

    if user_data["index"] < len(user_data["words"]):
        await bot.send_message(chat_id=user_id, text="⏳ Ждем 5 минут перед следующим словом...")

        # Ожидаем 5 минут
        await asyncio.sleep(30)

        # Отправляем следующее слово
        await send_next_word(user_id)
    else:
        # Если это было последнее слово, сразу предложить повторить или загрузить новые
        await bot.send_message(chat_id=user_id, text="✅ Ты изучил все слова! Что делать дальше?", reply_markup=repeat_buttons())

# Обработчик кнопки "Повторить список"
@dp.callback_query(lambda call: call.data == "repeat_list")
async def repeat_list(callback_query: types.CallbackQuery):
    user_id = callback_query.message.chat.id
    users_data[user_id]["index"] = 0  # Сбрасываем индекс
    await bot.send_message(chat_id=user_id, text="🔁 Начинаем сначала!")
    await send_next_word(user_id)

# Обработчик кнопки "Загрузить новые слова"
@dp.callback_query(lambda call: call.data == "new_list")
async def new_list(callback_query: types.CallbackQuery):
    user_id = callback_query.message.chat.id
    users_data[user_id] = {"words": [], "index": 0}
    await bot.send_message(chat_id=user_id, text="📝 Отправь новый список слов с помощью команды /add.")

# Запуск бота
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())