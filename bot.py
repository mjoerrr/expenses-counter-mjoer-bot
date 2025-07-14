import asyncio

from aiogram import Bot, Dispatcher

import config
from handlers import main_handlers
from callbacks import main_callbacks

from database.database import create_dbs


async def main():
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()

    dp.include_routers(main_handlers.router, main_callbacks.router)
    await create_dbs()

    await dp.start_polling(bot)



if __name__ == '__main__':
    asyncio.run(main())