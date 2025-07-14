from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards.kbs import start_keyboard, get_categories_keyboard, date_kb, build_expense_keyboard, build_category_stats_keyboard, back_kb
from states.states import Main_States
from database.database import add_new_cat, add_new_expense, get_user_history, get_monthly_category_stats

router = Router()


# ответ на /start
@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer("Привет! Я бот для учета расходов. Мой создатель @Mjoer1, если будут какие-то идеи по боту, то пиши мне в телеграм.", reply_markup=start_keyboard)


# ответ на нажатие кнопки "Добавить категорию расходов"
@router.message(F.text == "Добавить категории расходов")
async def add_new_category(message: Message, state: FSMContext) -> None:
    await message.answer("Введите название новой категории", reply_markup=back_kb)
    await state.set_state(Main_States.ADD_NEW_CATEGORY)


# принимаем от пользователя название новой категории
@router.message(Main_States.ADD_NEW_CATEGORY)
async def add_new_category_name(message: Message, state: FSMContext) -> None:
    await add_new_cat(message.from_user.id, message.text, message.date.strftime("%d.%m.%Y"))
    await message.answer(f"Категория '{message.text}' была добавлена", reply_markup=start_keyboard)
    await state.clear()


# ответ на нажатие кнопки "Добавить расход"
@router.message(F.text == "Добавить расход")
async def add_new_extense_start(message: Message, state: FSMContext) -> None:
    await message.delete()
    await message.answer("Введите дату, когда была произведена трата (если сегодня, то нажмите на кнопку ниже) в формате: дата.месяц.год (к примеру, 20.06.2025)", reply_markup=date_kb)
    await state.set_state(Main_States.ADD_EXPENSE_DATE)


# принимаем от пользователя дату траты
@router.message(Main_States.ADD_EXPENSE_DATE)
async def get_date_from_user(message: Message, state: FSMContext) -> None:
    date = message.text
    cat_kb = await get_categories_keyboard(message.from_user.id, date)

    if cat_kb:
        await message.answer('Выберите категорию, к которой относится трата', reply_markup=cat_kb)
    else:
        await message.answer('Вы еще не добавили категории трат, сперва добавьте категории трат через главное меню', reply_markup=start_keyboard)

    await message.delete()
    await state.clear()


# принимаем от пользователя сумму траты
@router.message(Main_States.ADD_EXPENSE_AMOUNT)
async def get_amount_from_user(message: Message, state: FSMContext) -> None:
    try:
        info = await state.get_data()
        date = info['date']
        category = info['category']
        amount = float(message.text)

        await message.answer('Введите описание траты')
        await state.set_state(Main_States.ADD_EXPENSE_DESCRIPTION)
        await state.update_data(date=date, category=category, amount=amount)
    except:
        await message.delete()
        await message.answer('Введите сумму траты заново (она должна быть числом)')


# принимаем от пользователя описание траты
@router.message(Main_States.ADD_EXPENSE_DESCRIPTION)
async def get_description_from_user(message: Message, state: FSMContext) -> None:
    info = await state.get_data()
    date = info['date']
    category = info['category']
    amount = info['amount']
    decription = message.text

    await add_new_expense(message.from_user.id, category, amount, date, decription)

    await message.answer('Трата добавлена', reply_markup=start_keyboard)
    await state.clear()


# ответ на нажатие кнопки "Все траты"
@router.message(F.text == "Все траты")
async def return_stats_for_user(message: Message, state: FSMContext) -> None:
    res = await get_user_history(message.from_user.id)
    if res:
        expenses_kb = build_expense_keyboard(res)
        await message.delete()
        await message.answer('Ниже приведена статистика по расходам', reply_markup=expenses_kb)
    else:
        await message.answer('Трат пока не было заявлено')


# ответ на нажатие кнопки "Траты по категориям"
@router.message(F.text == "Траты по категориям")
async def return_stats_for_cats(message: Message, state: FSMContext) -> None:
    res = await get_monthly_category_stats(message.from_user.id, message.date.strftime("%m.%Y"))
    cats_kb = build_category_stats_keyboard(res, message.date.strftime("%m.%Y"))
    await message.delete()
    await message.answer(f'Ниже приведена статистика трат по категориям за {message.date.strftime("%m.%Y")}', reply_markup=cats_kb)


# если сообщение от пользователя не попадает ни под одно условие, то считаем, что пользователь ввел название новой категории
@router.message()
async def fallback_message_handler(message: Message, state: FSMContext) -> None:
    await add_new_cat(message.from_user.id, message.text, message.date.strftime("%d.%m.%Y"))
    await message.answer(f"Категория '{message.text}' была добавлена", reply_markup=start_keyboard)
    await state.clear()
