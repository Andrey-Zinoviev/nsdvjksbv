from aiogram.fsm.state import State, StatesGroup


class Auto(StatesGroup):
    brand_to_add = State()
    brand_to_delete = State()
    old_brand = State()
    new_brand = State()
    search_brand = State()

    model_to_add = State()
    model_to_delete = State()
    old_model = State()
    new_model = State()
    search_model = State()

    year_to_add = State()
    year_to_delete = State()
    old_year = State()
    new_year = State()
    search_year = State()

    photo_to_add = State()
    photo_to_delete = State()
    old_photo = State()
    new_photo = State()

    premium_photo_to_add = State()
    premium_photo_to_delete = State()
    old_premium_photo = State()
    new_premium_photo = State()

    pdf_to_add = State()
    pdf_to_delete = State()
    old_pdf = State()
    new_pdf = State()

    premium_pdf_to_add = State()
    premium_pdf_to_delete = State()
    old_premium_pdf = State()
    new_premium_pdf = State()

class Admin(StatesGroup):
    password = State()
    new_pass = State()
    old_pass = State()