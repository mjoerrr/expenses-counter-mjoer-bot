from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton
from aiogram.types.reply_keyboard_markup import ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from datetime import datetime, timedelta

from typing import List

from database.database import get_categories


start_kb = [
    [
        KeyboardButton(text="Добавить категории расходов"),

    ],
    [
        KeyboardButton(text="Добавить расход")
    ],
    [
        KeyboardButton(text="Все траты"),
        KeyboardButton(text="Траты по категориям")
    ]
]
start_keyboard = ReplyKeyboardMarkup(
    keyboard=start_kb,
    resize_keyboard=True
)



# клавиатура с выбором даты
today_btn = InlineKeyboardButton(text='Сегодня', callback_data='today')
cancellation_btn = InlineKeyboardButton(text='Отмена', callback_data='main_menu')
date_kb = InlineKeyboardMarkup(inline_keyboard=[[today_btn], [cancellation_btn]])


# клавиатура с возвращением в главное меню
cancellation_btn = InlineKeyboardButton(text='Отмена', callback_data='main_menu')
back_kb = InlineKeyboardMarkup(inline_keyboard=[[cancellation_btn]])

# клавиатура для возвращения в меню с тратами
back_to_expense_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="back_to_expenses")]])


# функция, возвращающая клавиатуру из категорий
async def get_categories_keyboard(user_id: int, date: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    categories = await get_categories(user_id)
    if categories is not None:
        buttons = []
        for cat in categories:
            callback_data = f"cat_{cat}_{date}"
            buttons.append(InlineKeyboardButton(text=cat, callback_data=f"cat_{cat}_{date}"))

        builder.add(*buttons)

        return builder.adjust(1).as_markup(resize_keyboard=True)
    else:
        return



# функция, возвращающая клавиатуру из трат
def build_expense_keyboard(expenses: List[List]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if expenses:
        for expense in expenses:
            date, amount, category, _ = expense
            text = f"{date} | {int(amount)}₽ | {category}"
            callback_data = f"r_{date}_{int(amount)}_{category}"

            builder.add(
                InlineKeyboardButton(text=text, callback_data=callback_data)
            )
    return builder.adjust(1).as_markup()


# функция, возвращающая клавиатуру из категорий
def build_category_stats_keyboard(data: dict, date: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    date = '01.' + date

    date_obj = datetime.strptime(date, "%d.%m.%Y")

    for category, amount in data.items():
        text = f"{category} | {int(amount)}₽"
        callback_data = f"c_{category}_{date}"
        builder.add(InlineKeyboardButton(text=text, callback_data=callback_data))

    prev_month = (date_obj - timedelta(days=1)).strftime("%m.%Y")
    next_month = (date_obj + timedelta(days=32)).strftime("%m.%Y")

    builder.row(
        InlineKeyboardButton(text="◀️ Прошлый месяц", callback_data=f"back_to_month_{prev_month}"),
        InlineKeyboardButton(text="Следующий месяц ▶️", callback_data=f"back_to_month_{next_month}")
    )
    return builder.adjust(1).as_markup()


# функция, возвращающая клавиатуру из категорий
def build_category_expenses_keyboard(expenses: list, month: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for entry in expenses:
        date, amount, cat, desc = entry
        button_text = f"{date} | {int(amount)}₽ | {desc}"
        callback_data = f"exp_{date}_{int(amount)}_{desc}"[:40]
        builder.add(InlineKeyboardButton(text=button_text, callback_data=callback_data))

    # добавляем кнопку назад
    builder.add(InlineKeyboardButton(text="Назад", callback_data=f"back_to_month_{month}"))
    return builder.adjust(1).as_markup()


# функция, возвращающая статистику по категориям
def back_to_category_stats_kb(month: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # добавляем кнопку назад
    builder.add(InlineKeyboardButton(text="Назад", callback_data=f"back_to_month_{month}"))
    return builder.adjust(1).as_markup()