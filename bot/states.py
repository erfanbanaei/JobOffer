from aiogram.fsm.state import State, StatesGroup


class AddSearchStates(StatesGroup):
    choosing_provider = State()
    waiting_for_keyword = State()
    choosing_city = State()
    choosing_job_types = State()
