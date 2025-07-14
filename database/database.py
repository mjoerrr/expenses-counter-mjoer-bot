import sqlite3 as sq
import aiosqlite
import json


async def create_dbs() -> None:
    db_cats = sq.connect('database/expense_cats.db')
    cur_cats = db_cats.cursor()
    cur_cats.execute("CREATE TABLE IF NOT EXISTS expense_cats(user_id INTEGER PRIMARY KEY AUTOINCREMENT, user_cats TEXT)")
    db_cats.commit()

    db_history = sq.connect('database/user_stats.db')
    cur_history = db_history.cursor()
    cur_history.execute("CREATE TABLE IF NOT EXISTS user_stats(user_id INTEGER PRIMARY KEY AUTOINCREMENT, user_history TEXT)")
    db_history.commit()

    db_cats_history = sq.connect('database/user_cats_stats.db')
    cur_cats_history = db_cats_history.cursor()
    cur_cats_history.execute("CREATE TABLE IF NOT EXISTS user_cats_stats(user_id INTEGER PRIMARY KEY AUTOINCREMENT, user_cats_history TEXT)")
    db_cats_history.commit()



async def add_new_cat(user_id: int, category: str, today_date: str) -> None:
    # добавление в БД 1 новой категории
    async with aiosqlite.connect('database/expense_cats.db') as db1:
        async with db1.execute("SELECT user_cats FROM expense_cats WHERE user_id = ?", (user_id,)) as cursor1:
            row = await cursor1.fetchone()
            # если пользователя нет в базе данных, то добавляем его туда
            if row is None:
                user_cats = [category]
                await db1.execute(
                    "INSERT INTO expense_cats (user_id, user_cats) VALUES (?, ?)",
                    (user_id, json.dumps(user_cats))
                )

            # если есть, то просто добавляем в существующий список новую категорию
            else:
                user_cats = json.loads(row[0]) if row[0] else []
                if category not in user_cats:
                    user_cats.append(category)
                    await db1.execute(
                        "UPDATE expense_cats SET user_cats = ? WHERE user_id = ?",
                        (json.dumps(user_cats), user_id)
                    )
            await db1.commit()

    # добавление в БД 3 новой категории
    month_key = '01.' + today_date[3:]
    async with aiosqlite.connect('database/user_cats_stats.db') as db3:
        async with db3.execute("SELECT user_cats_history FROM user_cats_stats WHERE user_id = ?", (user_id,)) as cursor3:
            row = await cursor3.fetchone()

        if row is None:
            history = {
                month_key: [{category: 0}]
            }
            await db3.execute("INSERT INTO user_cats_stats (user_id, user_cats_history) VALUES (?, ?)", (user_id, json.dumps(history)))
        else:
            history = json.loads(row[0]) if row[0] else {}

            if month_key not in history:
                history[month_key] = []

            category_exists = any(category in d for d in history[month_key])
            if not category_exists:
                history[month_key].append({category: 0})

            await db3.execute(
                "UPDATE user_cats_stats SET user_cats_history = ? WHERE user_id = ?",
                (json.dumps(history), user_id)
            )

        await db3.commit()


async def add_new_expense(user_id: int, category: str, amount: int, today_date: str, description: str) -> None:
    # добавление в БД 2 новой траты
    async with aiosqlite.connect('database/user_stats.db') as db2:
        async with db2.execute("SELECT user_history FROM user_stats WHERE user_id = ?", (user_id,)) as cursor2:
            row = await cursor2.fetchone()
        new_entry = [today_date, amount, category, description]
        if row is None:
            # если нет записи — создаём новую
            history = [new_entry]
            await db2.execute(
                "INSERT INTO user_stats (user_id, user_history) VALUES (?, ?)",
                (user_id, json.dumps(history))
            )
        else:
            # есть запись — попросту обновляем ее
            history = json.loads(row[0]) if row[0] else []
            history.append(new_entry)

            await db2.execute(
                "UPDATE user_stats SET user_history = ? WHERE user_id = ?",
                (json.dumps(history), user_id)
            )
        await db2.commit()


    # добавление в БД 3 новой траты
    month_key = '01.' + today_date[3:]  # Преобразуем дату в формат месяца

    async with aiosqlite.connect('database/user_cats_stats.db') as db:
        async with db.execute("SELECT user_cats_history FROM user_cats_stats WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()

        if row is None:
            # если пользователь не найден — ничего не делаем
            return

        history = json.loads(row[0]) if row[0] else {}

        if month_key not in history:
            # если месяц не найден — ничего не делаем
            return

        updated = False
        for cat_dict in history[month_key]:
            if category in cat_dict:
                cat_dict[category] += amount
                updated = True
                break

        if not updated:
            # если категория не найдена — ничего не делаем
            return

        await db.execute(
            "UPDATE user_cats_stats SET user_cats_history = ? WHERE user_id = ?",
            (json.dumps(history), user_id)
        )
        await db.commit()


# функция, возвращающая список всех категории
async def get_categories(user_id: int) -> None:
    async with aiosqlite.connect('database/expense_cats.db') as db:
        async with db.execute("SELECT user_cats FROM expense_cats WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()

        if not row or not row[0]:
            return

        categories = json.loads(row[0])

        return categories


# функция, возвращающая историю трат по пользователю
async def get_user_history(user_id: int) -> None:
    async with aiosqlite.connect('database/user_stats.db') as db:
        async with db.execute("SELECT user_history FROM user_stats WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()

        if not row or not row[0]:
            return

        history = json.loads(row[0])
        return history


# функция, возвращающая историю трат по категориям в указанном месяце
async def get_monthly_category_stats(user_id: int, today_date: str) -> None:
    month_key = '01.' + today_date

    async with aiosqlite.connect('database/user_cats_stats.db') as db:
        async with db.execute(
            "SELECT user_cats_history FROM user_cats_stats WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()

        if not row or not row[0]:
            return {}

        history = json.loads(row[0])

        if month_key not in history:
            return {}

        month_data = history[month_key]
        result = {}
        for item in month_data:
            for cat, val in item.items():
                result[cat] = val

        return result