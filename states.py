from aiogram.fsm.state import State, StatesGroup


class AddPortfolio(StatesGroup):
    waiting_photo = State()
    waiting_category = State()
    waiting_title = State()
    waiting_description = State()
    waiting_tags = State()


class AddMaterialBulk(StatesGroup):
    waiting_category = State()
    waiting_lines = State()


class DeletePortfolio(StatesGroup):
    waiting_id = State()


class AddChannel(StatesGroup):
    waiting_forward_or_id = State()


class Broadcast(StatesGroup):
    waiting_content = State()
    waiting_confirm = State()


class SetBasePrice(StatesGroup):
    waiting_price = State()


class SetAgreedPrice(StatesGroup):
    waiting_price = State()


class AddPayment(StatesGroup):
    waiting_amount = State()


class SetDeliveryDate(StatesGroup):
    waiting_date = State()


class EditPortfolio(StatesGroup):
    waiting_id = State()
    waiting_field = State()
    waiting_new_value = State()


class SetAboutUs(StatesGroup):
    waiting_text = State()


class ManualOrder(StatesGroup):
    waiting_customer = State()
    waiting_description = State()
    waiting_price = State()
    waiting_paid = State()
    waiting_delivery_date = State()


class CustomerOrderRequest(StatesGroup):
    waiting_description = State()
    waiting_phone = State()


class RegisterPhone(StatesGroup):
    waiting_contact = State()
