from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from states.states import Main_States
from keyboards.kbs import (start_keyboard, get_categories_keyboard, build_expense_keyboard, back_to_expense_kb,
                           build_category_stats_keyboard, build_category_expenses_keyboard, back_to_category_stats_kb)
from database.database import get_user_history, get_monthly_category_stats

router = Router()

@router.callback_query(F.data == "today")
async def add_new_today_expense(callback: CallbackQuery, state: FSMContext) -> None:
    date = callback.message.date.strftime("%d.%m.%Y")
    cat_kb = await get_categories_keyboard(callback.from_user.id, date)

    if cat_kb:
        await callback.message.answer('Выберите категорию, к которой относится трата', reply_markup=cat_kb)
    else:
        await callback.message.answer('Вы еще не добавили ни одной категории трат, сперва добавьте категории трат через главное меню',
                             reply_markup=start_keyboard)

    await callback.message.delete()
    await state.clear()


# когда пользователь вернулся в главное меню
@router.callback_query(F.data == "main_menu")
async def open_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.delete()
    await callback.message.answer("Открыто главное меню", reply_markup=start_keyboard)
    await state.clear()


# Когда пользователь выбрал категорию, к которой относится трата
@router.callback_query(F.data.startswith("cat_"))
async def add_new_amount_expense(callback: CallbackQuery, state: FSMContext) -> None:
    info = callback.data.split('_')
    date = info[-1]
    cat = info[-2]
    await callback.message.delete()
    await callback.message.answer(f'Введите сумму расхода')
    await state.set_state(Main_States.ADD_EXPENSE_AMOUNT)
    await state.update_data(date=date, category=cat)


# когда пользователь нажал на кнопку с тратой
@router.callback_query(F.data.startswith("r_"))
async def handle_expense_details(callback: CallbackQuery) -> None:
    try:
        _, date, amount_str, category = callback.data.split("_")
        amount = float(amount_str)
        user_id = callback.from_user.id
        history = await get_user_history(user_id)

        for entry in history:
            if entry[0] == date and float(entry[1]) == amount and entry[2] == category:
                description = entry[3]
                await callback.message.answer(
                    f"📅 Дата: {date}\n"
                    f"📂 Категория: {category}\n"
                    f"💰 Сумма: {int(amount)}₽\n"
                    f"📝 Описание: {description}"
                    , reply_markup=back_to_expense_kb)
                await callback.message.delete()
    except Exception as e:
        await callback.message.answer("Произошла ошибка при обработке запроса.")
        print(e)


# если нажимаем на кнопку "назад", смотря конкретную трату
@router.callback_query(F.data == "back_to_expenses")
async def show_all_expenses(callback: CallbackQuery) -> None:
    res = await get_user_history(callback.from_user.id)
    expenses_kb = build_expense_keyboard(res)
    await callback.message.answer('Ниже приведена статистика по расходам', reply_markup=expenses_kb)
    await callback.message.delete()


# если смотрим трату в конкретной категории
@router.callback_query(F.data.startswith("c_"))
async def show_category_expenses(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    try:
        _, category, month = callback.data.split("_")
        month_str = f"{month[3:]}"
        history = await get_user_history(user_id)

        # фильтр по категориям и месяцу
        filtered = [
            entry for entry in history
            if entry[2] == category and entry[0][3:] == month_str
        ]

        if not filtered:
            await callback.message.delete()
            await callback.message.answer("Нет расходов в этой категории за выбранный месяц.")
            return

        keyboard = build_category_expenses_keyboard(filtered, month_str)

        await callback.message.edit_text(
            f"Траты в категории {category} за {month_str}",
            reply_markup=keyboard
        )
    except Exception as e:
        await callback.message.delete()
        await callback.message.answer("Ошибка при обработке запроса.")
        print(f"[ERROR in show_category_expenses] {e}")


# если нажимаем на кнопку назад, смотря конкретнуя трату
@router.callback_query(F.data.startswith("back_to_month_"))
async def return_stats_for_cats(callback: CallbackQuery) -> None:
    date = callback.data.split("_")[-1]
    res = await get_monthly_category_stats(callback.from_user.id, date)
    cats_kb = build_category_stats_keyboard(res, date)
    await callback.message.delete()
    await callback.message.answer(f'Ниже приведена статистика расходов по категориям за {date}', reply_markup=cats_kb)


# если пользователь открывает конкретнуюю трату в категориях
@router.callback_query(F.data.startswith("exp_"))
async def handle_expense_each_detail(callback: CallbackQuery):
    try:
        _, date, amount_str, desc = callback.data.split("_")
        amount = float(amount_str)
        user_id = callback.from_user.id

        history = await get_user_history(user_id)

        kb = back_to_category_stats_kb(date[3:])

        for entry in history:
            if entry[0] == date and float(entry[1]) == amount and desc.strip() in entry[3]:
                category = entry[2]
                await callback.message.answer(
                    f"📅 Дата: {date}\n"
                    f"📂 Категория: {category}\n"
                    f"💰 Сумма: {int(amount)}₽\n"
                    f"📝 Описание: {entry[3]}",
                    reply_markup=kb
                )
                await callback.message.delete()
                return

        await callback.message.answer("Расход не найден.", reply_markup=kb)

    except Exception as e:
        await callback.message.answer("Произошла ошибка при обработке запроса.")
        print(f"[ERROR in handle_expense_each_detail] {e}")