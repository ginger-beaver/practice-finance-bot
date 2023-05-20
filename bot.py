from datetime import datetime, date

from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup
from dotenv import load_dotenv

import db
import logging
import os

load_dotenv()
API_KEY = os.getenv("API_KEY")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_KEY)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# Класс для хранения состояний формы добавления расходов
class ExpenseForm(StatesGroup):
    Amount = State()
    Category = State()


# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Привет! Я бот для учета личных расходов. "
                         "Отправь /add_expense, чтобы добавить новый расход.")


# Обработчик команды /add_expense
@dp.message_handler(Command('add_expense'))
async def add_expense(message: types.Message):
    await ExpenseForm.Amount.set()
    await message.reply("Введите сумму расхода:")


# Обработчик ввода суммы расхода
@dp.message_handler(state=ExpenseForm.Amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        await state.update_data(amount=amount)
        await ExpenseForm.Category.set()
        await message.reply("Введите категорию расхода:")

    except ValueError:
        await message.reply("Неправильный формат суммы. Пожалуйста, введите число.")


# Обработчик ввода категории расхода
@dp.message_handler(state=ExpenseForm.Category)
async def process_category(message: types.Message, state: FSMContext):
    category = message.text
    try:
        cursor = db.get_cursor()
        query = "SELECT EXISTS(SELECT 1 FROM category WHERE name = ?)"
        cursor.execute(query, (category,))
        if not cursor.fetchone()[0]:
            raise ValueError
        await state.update_data(category=category)
        data = await state.get_data()
        amount = data.get('amount')

        db.insert("expense", {
            "amount": amount,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "category": category
        })

        await state.finish()
        await message.reply(f"Расходы на сумму {amount} в категории {category} сохранены.")
    except ValueError:
        await message.reply("Неправильный формат категории. Пожалуйста, введите существующую категорию.")

@dp.message_handler(lambda message: message.text.startswith('/del_expense'))
async def del_expense(message: types.Message):
    try:
        id = int(message.text.split()[1])
        db.delete('expense', f"id = {id}")
        await message.answer("Запись о расходе удалена!")
    except ValueError:
        await message.answer("Неправильный формат id. Пожалуйста, введите число")

@dp.message_handler(lambda message: message.text.startswith('/add_category'))
async def add_category(message: types.Message):
    category = message.text.split()[1]
    cursor = db.get_cursor()
    query = "SELECT EXISTS(SELECT 1 FROM category WHERE name = ?)"
    cursor.execute(query, (category,))
    if not cursor.fetchone()[0]:
        db.insert('category', {'name': message.text.split()[1]})
        await message.answer(f"Категория {category} добавлена!")
    else:
        await message.answer("Такая категория уже существует!")

@dp.message_handler(lambda message: message.text.startswith('/del_category'))
async def del_category(message: types.Message):
    category = message.text.split()[1]
    db.delete('category', f"name = '{category}'")
    await message.answer(f"Категория {category} удалена!")

@dp.message_handler(Command('today'))
async def get_today_stats(message: types.Message):
    cursor = db.get_cursor()
    query = "SELECT category, SUM(amount) FROM expense WHERE date(created) = date('now', 'localtime') GROUP BY category"
    cursor.execute(query)
    result = cursor.fetchall()

    query = "SELECT SUM(amount) FROM expense WHERE date(created) = date('now', 'localtime')"
    cursor.execute(query)
    sum = cursor.fetchone()[0]

    await message.answer('Расходы за сегодня:\n' +
                         '\n'.join(f"{c}: {a}" for c, a in result) +
                         f'\nОбщая сумма: {sum}')

@dp.message_handler(Command('month'))
async def get_today_stats(message: types.Message):
    cursor = db.get_cursor()
    today = date.today()
    start_of_month = date(today.year, today.month, 1)
    end_of_month = date(today.year, today.month, today.day)

    query = "SELECT category, SUM(amount) FROM expense WHERE date(created) BETWEEN date(?) AND date(?) GROUP BY category"
    cursor.execute(query, (start_of_month, end_of_month))
    result = cursor.fetchall()

    query = "SELECT SUM(amount) FROM expense WHERE date(created) BETWEEN date(?) AND date(?)"
    cursor.execute(query, (start_of_month, end_of_month))
    sum = cursor.fetchone()[0]

    await message.answer('Расходы за месяц:\n' +
                         '\n'.join(f"{c}: {a}" for c, a in result) +
                         f'\nОбщая сумма: {sum}')


@dp.message_handler(Command('categories'))
async def get_categories(message: types.Message):
    cursor = db.get_cursor()
    cursor.execute("SELECT name FROM category")
    await message.answer("Категории:\n" +
                         '\n'.join(f"{c[0]}" for c in cursor.fetchall()))

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
