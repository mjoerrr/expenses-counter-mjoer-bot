from aiogram.fsm.state import StatesGroup, State

class Main_States(StatesGroup):
    ADD_NEW_CATEGORY = State()
    ADD_EXPENSE_DATE = State()
    ADD_EXPENSE_CATEGORY = State()
    ADD_EXPENSE_AMOUNT = State()
    ADD_EXPENSE_DESCRIPTION = State()
