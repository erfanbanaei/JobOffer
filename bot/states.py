from aiogram.fsm.state import State, StatesGroup


class AddSearchStates(StatesGroup):
    waiting_for_keyword = State()
    choosing_providers = State()
    choosing_city = State()
    choosing_job_types = State()
