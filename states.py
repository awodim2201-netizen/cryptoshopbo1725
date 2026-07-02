from aiogram.fsm.state import State, StatesGroup

class OrderStates(StatesGroup):
    selecting_city = State()
    viewing_product = State()
    ordering = State()
    waiting_for_payment = State()
    waiting_for_photo = State()
    waiting_for_location = State()