from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, InputFile, LabeledPrice, PreCheckoutQuery
from asyncio import sleep
from aiogram.enums import ChatAction
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import base64
import aiohttp
from io import BytesIO
from PIL import Image
import tempfile
import requests

from .variables import *
from .kbs import *
from .db import *
from .states import Admin, Auto
from config import PAYMENT_TOKEN


router = Router()
db = Database()
scheduler = AsyncIOScheduler()
scheduler.start()


password = None

stages = {} # Done!
pages = {} # Done!

admins = {} # Done!

ikbs = {} # Done!
previous_kbs = {} # Done!
messages_to_delete = {} # Done!

brands = {} # Done!
brand_ids = {} # Done!

models = {} # Done!
model_ids = {} # Done!

years = {} # Done!
year_ids = {} # Done!


async def on_startup(dp):
    from .handlers import db
    await db.connect()

async def on_shutdown(dp):
    from .handlers import db
    await db.disconnect()

async def create_bytes_file(file_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as res:
            result_bytes = await res.read()

    return result_bytes

@router.message(Command('get_premium'))
async def get_premium(message: Message):
    from main import bot

    if message.chat.type == 'private':
        rows = await db.fetch_premium_users()
        chat_id = str(message.chat.id)
        id_in = False
        for row in rows:
            if row['chat_id'] == chat_id:
                id_in = True

                current_time = datetime.now()
                sub_end = datetime.strptime(
                    row['sub_end'], '%Y-%m-%d %H:%M:%S'
                )

                if current_time > sub_end:
                    await message.answer(
                        await delete_premium_user(str(message.chat.id))
                    )
                    id_in = False
                else:
                    await message.answer('У вас уже активен премиум!')
                await message.delete()
                break

        if not id_in:
            await bot.send_invoice(chat_id=message.chat.id,
                title="Премиум подписка на месяц",
                description="Подписка на премиум-аккаунт на один месяц",
                payload="premium",
                provider_token=PAYMENT_TOKEN,
                currency='rub',
                prices=[LabeledPrice(label="Месячная подписка", amount=30000)],
                start_parameter="subscription_1month",
                is_flexible=False,
            )
    else:
        await message.reply("Пожалуйста, напишите мне в личные сообщения.")
    
@router.pre_checkout_query()
async def pre(pre_checkout_query: PreCheckoutQuery):
    from main import bot
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@router.message(F.successful_payment)
async def get_premium(message: Message):
    await message.answer(await add_premium_user(str(message.chat.id)))
    payment_info = message.successful_payment
    await message.answer(
        f"Спасибо за оплату!\
        \nВаш платеж на сумму {payment_info.total_amount / 100} {payment_info.currency} был успешно завершен."
    )

@router.message(Command('my_premium'))
async def my_premium(message: Message):
    rows = await db.fetch_premium_users()
    chat_id = str(message.chat.id)
    id_in = False
    for row in rows:
        if row['chat_id'] == chat_id:
            id_in = True

            current_time = datetime.now()
            sub_end = datetime.strptime(
                row['sub_end'], '%Y-%m-%d %H:%M:%S'
            )

            if current_time > sub_end:
                await message.answer(
                    await delete_premium_user(str(message.chat.id))
                )
                id_in = False
                premium = False
            else:
                status = 'неактивна'
                if row['status'] == 'active':
                    status = 'активна'
                await message.answer(
                    f'Старт подписки: {row["sub_start"]}\
                    \nКонец подписки: {row["sub_end"]}\
                    \nСтатус: {status}'
                )
            break

    if not id_in:
            await message.answer('У вас отсутствует премиум подписка!')
    await message.delete()

@router.message(Command('start'))
async def cmd_start(message: Message):
    global pages, ikbs, stages
    chat_id = message.chat.id

    if chat_id in admins:
        ikbs[message.chat.id] = await brand_ikbs(admins[chat_id])
    else:
        ikbs[message.chat.id] = await brand_ikbs(False)

    stages[chat_id] = 1
    pages[chat_id] = 0
    previous_kbs[chat_id] = await message.answer(
        'Выберите марку авто:',
        reply_markup=ikbs[message.chat.id][pages[chat_id]].as_markup()
    )
    await message.delete()

@router.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer(HELP)
    await message.delete()

# # # # # # # # #
#   A D M I N   #
# # # # # # # # #
@router.message(Command('admin_reg'))
async def admin_reg(message: Message, state: FSMContext):
    global messages_to_delete
    messages_to_delete[message.chat.id] = await message.answer(
        'Введите админский пароль.'
    )
    await state.set_state(Admin.password)
    await message.delete()

@router.message(Admin.password)
async def admin_reg(message: Message):
    global admins, previous_kbs, ikbs, password
    from main import bot

    chat_id = message.chat.id

    await message.delete()

    await bot.delete_message(
        message.chat.id, messages_to_delete[chat_id].message_id
    )

    pass_row = await db.fetch_password()
    password = pass_row[0]['password']

    if message.text == password:
        admins[chat_id] = True
        delete_after_5_sec = await message.answer('Вы успешно вошли как админ!')

        key = chat_id
        if key in previous_kbs:
            if previous_kbs[key] != 1:
                await bot.delete_message(key, previous_kbs[key].message_id)
                previous_kbs[key] = 1

        ikbs[chat_id] = await brand_ikbs(admins[chat_id])
        previous_kbs[chat_id] = await message.answer(
        'Выберите марку авто:', reply_markup=ikbs[chat_id][pages[chat_id]].as_markup()
        )
        await sleep(5)
        await bot.delete_message(
            delete_after_5_sec.chat.id, delete_after_5_sec.message_id
        )

    else:
        admins[chat_id] = False
        delete_after_5_sec = await message.answer('❌ Неверный пароль ❌')
        await sleep(5)
        await bot.delete_message(
            delete_after_5_sec.chat.id, delete_after_5_sec.message_id
        )

@router.message(Command('exit_admin'))
async def admin_exit(message: Message):
    global admins, previous_kbs, ikbs
    from main import bot

    admins[message.chat.id] = False
    await message.delete()
    delete_after_5_sec = await message.answer('Вы успешно вышли из админки!')
    
    ikbs[message.chat.id] = await brand_ikbs(admins[message.chat.id])

    key = message.chat.id
    if key in previous_kbs:
        if previous_kbs[key] != 1:
            await bot.delete_message(key, previous_kbs[key].message_id)
            previous_kbs[key] = 1
    stages[message.chat.id] = 1
    pages[message.chat.id] = 0
    previous_kbs[message.chat.id] = await message.answer(
        'Выберите марку авто:',
        reply_markup=ikbs[message.chat.id][pages[message.chat.id]].as_markup()
    )

    await sleep(5)
    await bot.delete_message(
        delete_after_5_sec.chat.id, delete_after_5_sec.message_id
    )

@router.callback_query(F.data == 'update password')
async def update_pass_in_db(callback_query: CallbackQuery, state: FSMContext):
    global messages_to_delete
    messages_to_delete[message.chat.id] = await callback_query.message.answer(
        'Введите старый пароль.'
    )
    await state.set_state(Admin.old_pass)

@router.message(Admin.old_pass)
async def update_pass_in_db(message: Message, state: FSMContext):
    from main import bot

    await bot.delete_message(
        message.chat.id, messages_to_delete[message.chat.id].message_id
    )
    await message.delete()
    await state.update_data(old_pass=message.text)
    await state.set_state(Admin.new_pass)

@router.message(Admin.new_pass)
async def update_pass_in_db(message: Message, state: FSMContext):
    global previous_kbs
    from main import bot

    pass_row = await db.fetch_password()
    old_pass = pass_row[0]['password']
    data = await state.get_data()
    if data.get('old_pass') != password:
        await message.answer('Неверный пароль!')
    else:
        messages_to_delete[message.chat.id] = await message.answer(
            'Введите новый пароль.'
        )

    if message.chat.id in admins:
        if admins[message.chat.id] == True:
            await message.answer(
                await update_password(message.text)
            )

    await bot.delete_message(
        message.chat.id, messages_to_delete[message.chat.id].message_id
    )
    await message.delete()

# # # # # # # # # #
#   B R A N D S   #
# # # # # # # # # #
@router.callback_query(F.data == 'add brand')
async def add_brand_to_db(callback_query: CallbackQuery, state: FSMContext):
    global messages_to_delete
    messages_to_delete[message.chat.id] = await callback_query.message.answer(
        'Введите марку автомобиля.\
        \nДля добавления списка марок запишите их столбцом:\
        \nМарка 1\
        \nМарка 2\
        \nМарка 3'
    )
    await state.set_state(Auto.brand_to_add)

@router.message(Auto.brand_to_add)
async def add_brand_to_db(message: Message):
    global ikbs
    from main import bot

    rows = await db.fetch_brands()

    _brands = []
    _brand = ''
    i = 0
    for char in message.text:
        i += 1
        if char == '\n' and _brand != "":
            _brands.append(_brand)
            _brand = ""
        elif i == len(message.text):
            _brand += char
            if _brand != '':
                _brands.append(_brand)
        else:
            _brand += char
        
    for brand_ in _brands:
        in_rows = False
        for row in rows:
            if brand_ == row['brand']:
                await message.answer(
                    'Такая марка уже существует в базе данных'
                )
                in_rows = True
                break
        if not in_rows:
            await message.answer(await add_brand(brand_))

    await bot.delete_message(
        message.chat.id, messages_to_delete[message.chat.id].message_id
    )

    key = message.chat.id
    if key in previous_kbs:
        if previous_kbs[key] != 1:
            await bot.delete_message(key, previous_kbs[key].message_id)
            previous_kbs[key] = 1
    if message.chat.id in admins:
        ikbs[message.chat.id] = await brand_ikbs(admins[message.chat.id])
    previous_kbs[message.chat.id] = await message.answer(
        'Выберите марку авто:',
        reply_markup=ikbs[message.chat.id][pages[message.chat.id]].as_markup()
    )
    await message.delete()

@router.callback_query(F.data == 'delete brand')
async def delete_brand_from_db(callback_query: CallbackQuery, state: FSMContext):
    global messages_to_delete
    messages_to_delete[message.chat.id] = await callback_query.message.answer(
        'Введите марку автомобиля которую хотите удалить.\
        \nДля удаления списка марок запишите их столбцом:\
        \nМарка 1\
        \nМарка 2\
        \nМарка 3'
    )
    await state.set_state(Auto.brand_to_delete)

@router.message(Auto.brand_to_delete)
async def delete_brand_from_db(message: Message):
    global previous_kbs, ikbs
    from main import bot

    rows = await db.fetch_brands()

    _brands = []
    _brand = ''
    i = 0
    for char in message.text:
        i += 1
        if char == '\n' and _brand != "":
            _brands.append(_brand)
            _brand = ""
        elif i == len(message.text):
            _brand += char
            if _brand != '':
                _brands.append(_brand)
        else:
            _brand += char

    for brand_ in _brands:
        for row in rows:
            if brand_ == row['brand']:
                await message.answer(await delete_brand(brand_))
                break
    await bot.delete_message(
        message.chat.id, messages_to_delete[message.chat.id].message_id
    )

    key = message.chat.id
    if key in previous_kbs:
        if previous_kbs[key] != 1:
            await bot.delete_message(key, previous_kbs[key].message_id)
            previous_kbs[key] = 1

    await message.delete()
    if message.chat.id in admins:
        ikbs[message.chat.id] = await brand_ikbs(admins[message.chat.id])
    previous_kbs[message.chat.id] = await message.answer(
        'Выберите марку авто:',
        reply_markup=ikbs[message.chat.id][pages[message.chat.id]].as_markup()
    )

@router.callback_query(F.data == 'update brand')
async def update_brand_in_db(callback_query: CallbackQuery, state: FSMContext):
    global messages_to_delete
    messages_to_delete[message.chat.id] = await callback_query.message.answer(
        'Введите марку автомобиля которую заменить.'
    )
    await state.set_state(Auto.old_brand)

@router.message(Auto.old_brand)
async def update_brand_in_db(message: Message, state: FSMContext):
    global messages_to_delete
    from main import bot

    await bot.delete_message(
        message.chat.id, messages_to_delete[message.chat.id].message_id
    )
    await message.delete()

    await state.update_data(old_brand=message.text)

    messages_to_delete[message.chat.id] = await message.answer(
        'Введите новую марку автомобиля.'
    )
    await state.set_state(Auto.new_brand)

@router.message(Auto.new_brand)
async def update_brand_in_db(message: Message, state: FSMContext):
    global previous_kbs, ikbs
    from main import bot

    rows = await db.fetch_brands()
    in_rows = False
    for row in rows:
        if message.text == row['brand']:
            await message.answer('Такая марка уже существует в базе данных')
            in_rows = True
            break
    if not in_rows:
        data = await state.get_data()
        old_brand = data.get('old_brand')
        await message.answer(await update_brand(old_brand, message.text))

    key = message.chat.id
    if key in previous_kbs:
        if previous_kbs[key] != 1:
            await bot.delete_message(key, previous_kbs[key].message_id)
            previous_kbs[key] = 1

    await bot.delete_message(
        message.chat.id, messages_to_delete[message.chat.id].message_id
    )
    await message.delete()
    if message.chat.id in admins:
        ikbs[message.chat.id] = await brand_ikbs(admins[message.chat.id])
    previous_kbs[message.chat.id] = await message.answer(
        'Выберите марку авто:',
        reply_markup=ikbs[message.chat.id][pages[message.chat.id]].as_markup()
    )

@router.callback_query(F.data == 'search brand')
async def search_brand_in_db(callback_query: CallbackQuery, state: FSMContext):
    global messages_to_delete
    messages_to_delete[callback_query.message.chat.id] = await callback_query.message.answer(
        'Введите марку автомобиля которую хотите найти.'
    )
    await state.set_state(Auto.search_brand)

@router.message(Auto.search_brand)
async def search_brand_in_db(message: Message):
    global previous_kbs, ikbs, stages, brands, brand_ids
    from main import bot

    chat_id = message.chat.id

    rows = await db.fetch_brands()

    await bot.delete_message(chat_id, messages_to_delete[chat_id].message_id)
    await message.delete()

    key = chat_id
    if key in previous_kbs:
        if previous_kbs[key] != 1:
            await bot.delete_message(key, previous_kbs[key].message_id)
            previous_kbs[key] = 1

    for row in rows:
        if message.text.lower() == row['brand'].lower():
            stages[chat_id] += 1
            brands[chat_id] = row['brand']
            brand_ids[chat_id] = row['brand_id']
            if message.chat.id in admins:
                ikbs[message.chat.id] = await model_ikbs(
                    row['brand_id'], admins[chat_id]
                )
            else:
                ikbs[chat_id] = await model_ikbs(
                    brand_ids[chat_id], False
                )
            previous_kbs[chat_id] = await message.answer(
                f'Марка: {brands[chat_id]}\
                \nВыберите модель авто:',
                reply_markup=ikbs[chat_id][pages[chat_id]].as_markup()
            )
            break
    else:
        await message.answer(
            f'Марка "{message.text}" не найдена в базе данных.'
        )
        previous_kbs[chat_id] = await message.answer(
            'Выберите марку авто:',
            reply_markup=ikbs[message.chat.id][pages[message.chat.id]].as_markup()
        )

# # # # # # # # # #
#   M O D E L S   #
# # # # # # # # # #
@router.callback_query(F.data == 'add model')
async def add_model_to_db(callback_query: CallbackQuery, state: FSMContext):
    global messages_to_delete
    messages_to_delete[message.chat.id] = await callback_query.message.answer(
        'Введите модель автомобиля.\
        \nДля добавления списка моделей запишите их столбцом:\
        \nМодель 1\
        \nМодель 2\
        \nМодель 3'
    )
    await state.set_state(Auto.model_to_add)

@router.message(Auto.model_to_add)
async def add_model_to_db(message: Message, state: FSMContext):
    global previous_kbs, ikbs
    from main import bot

    chat_id = message.chat.id

    rows = await db.fetch_models()

    _models = []
    _model = ''
    i = 0
    for char in message.text:
        i += 1
        if char == '\n' and _model != "":
            _models.append(_model)
            _model = ""
        elif i == len(message.text):
            _model += char
            if _model != '':
                _models.append(_model)
        else:
            _model += char
        
    for model_ in _models:
        in_rows = False
        for row in rows:
            if model_ == row['model']:
                await message.answer(
                    'Такая модель уже существует в базе данных'
                )
                in_rows = True
                break
        if not in_rows:
            await message.answer(await add_model(model_))

    await bot.delete_message(
        chat_id, messages_to_delete[chat_id].message_id
    )

    key = chat_id
    if key in previous_kbs:
        if previous_kbs[key] != 1:
            await bot.delete_message(key, previous_kbs[key].message_id)
            previous_kbs[key] = 1

    if message.chat.id in admins:
        ikbs[message.chat.id] = await model_ikbs(brand_ids[chat_id], admins[chat_id])
    previous_kbs[chat_id] = await message.answer(
        'Выберите модель авто:',
        reply_markup=ikbs[message.chat.id][pages[message.chat.id]].as_markup()
    )
    await message.delete()

@router.callback_query(F.data == 'delete model')
async def delete_model_from_db(callback_query: CallbackQuery, state: FSMContext):
    global messages_to_delete
    messages_to_delete[message.chat.id] = await callback_query.message.answer(
        'Введите модель автомобиля которую хотите удалить.\
        \nДля удаления списка моделей запишите их столбцом:\
        \nМодель 1\
        \nМодель 2\
        \nМодель 3'
    )
    await state.set_state(Auto.model_to_delete)

@router.message(Auto.model_to_delete)
async def delete_model_from_db(message: Message):
    global previous_kbs, ikbs
    from main import bot

    rows = await db.fetch_models()

    _models = []
    _model = ''
    i = 0
    for char in message.text:
        i += 1
        if char == '\n' and _model != "":
            _models.append(_model)
            _model = ""
        elif i == len(message.text):
            _model += char
            if _model != '':
                _models.append(_model)
        else:
            _model += char

    for model_ in _models:
        for row in rows:
            if model_ == row['model']:
                await message.answer(await delete_model(model_))
                break

    await bot.delete_message(
        message.chat.id, messages_to_delete[message.chat.id].message_id
    )

    key = message.chat.id
    if key in previous_kbs:
        if previous_kbs[key] != 1:
            await bot.delete_message(key, previous_kbs[key].message_id)
            previous_kbs[key] = 1

    await message.delete()

    if message.chat.id in admins:
        ikbs[message.chat.id] = await model_ikbs(
            brand_ids[message.chat.id], admins[message.chat.id]
        )
    previous_kbs[message.chat.id] = await message.answer(
        'Выберите модель авто:',
        reply_markup=ikbs[message.chat.id][pages[message.chat.id]].as_markup()
    )

@router.callback_query(F.data == 'update model')
async def update_model_in_db(callback_query: CallbackQuery, state: FSMContext):
    global messages_to_delete
    messages_to_delete[message.chat.id] = await callback_query.message.answer(
        'Введите модель автомобиля которую заменить.'
    )
    await state.set_state(Auto.old_model)

@router.message(Auto.old_model)
async def update_model_in_db(message: Message, state: FSMContext):
    global messages_to_delete
    from main import bot
    await bot.delete_message(
        message.chat.id, messages_to_delete[message.chat.id].message_id
    )
    await message.delete()
    await state.update_data(old_model=message.text)
    messages_to_delete[message.chat.id] = await message.answer(
        'Введите новую модель автомобиля.'
    )
    await state.set_state(Auto.new_model)

@router.message(Auto.new_model)
async def update_model_in_db(message: Message, state: FSMContext):
    global previous_kbs, ikbs
    from main import bot

    rows = await db.fetch_models()
    data = await state.get_data()

    in_rows = False
    for row in rows:
        if message.text == row['model']:
            await message.answer('Такая модель уже существует в базе данных')
            in_rows = True
            break
    if not in_rows:
        await message.answer(
            await update_model(data.get('old_model'), message.text)
        )

    key = message.chat.id
    if key in previous_kbs:
        if previous_kbs[key] != 1:
            await bot.delete_message(key, previous_kbs[key].message_id)
            previous_kbs[key] = 1

    await bot.delete_message(
        message.chat.id, messages_to_delete[message.chat.id].message_id
    )
    await message.delete()

    if message.chat.id in admins:
        ikbs[message.chat.id] = await model_ikbs(
            brand_ids[message.chat.id], admins[message.chat.id]
        )
    previous_kbs[message.chat.id] = await message.answer(
        'Выберите модель авто:',
        reply_markup=ikbs[message.chat.id][pages[message.chat.id]].as_markup()
    )

@router.callback_query(F.data == 'search model')
async def search_model_in_db(callback_query: CallbackQuery, state: FSMContext):
    global messages_to_delete
    messages_to_delete[message.chat.id] = await callback_query.message.answer(
        'Введите модель автомобиля которую хотите найти.'
    )
    await state.set_state(Auto.search_model)

@router.message(Auto.search_model)
async def search_model_in_db(message: Message):
    global previous_kbs, ikbs, stages, models, model_ids
    from main import bot

    chat_id = message.chat.id

    await bot.delete_message(chat_id, messages_to_delete[chat_id].message_id)
    await message.delete()

    key = chat_id
    if key in previous_kbs:
        if previous_kbs[key] != 1:
            await bot.delete_message(key, previous_kbs[key].message_id)
            previous_kbs[key] = 1

    rows = await db.fetch_models()

    for row in rows:
        if message.text.lower() == row['model'].lower():
            stages[chat_id] += 1
            models[chat_id] = row['model']
            model_ids[chat_id] = row['model_id']
            if message.chat.id in admins:
                ikbs[message.chat.id] = await year_ikbs(
                    model_ids[chat_id], admins[message.chat.id]
                )
            else:
                ikbs[chat_id] = await year_ikbs(
                    model_ids[chat_id], False
                )
            previous_kbs[chat_id] = await message.answer(
                f'Марка: {brands[chat_id]}\
                \nМодель: {models[chat_id]}\
                \nВыберите год авто:',
                reply_markup=ikbs[message.chat.id][pages[message.chat.id]].as_markup()
            )
            break
    else:
        await message.answer(
            f'Модель "{message.text}" не найдена в базе данных.'
        )
        previous_kbs[chat_id] = await message.answer(
            'Выберите модель авто:',
            reply_markup=ikbs[message.chat.id][pages[message.chat.id]].as_markup()
        )

# # # # # # # # #
#   Y E A R S   #
# # # # # # # # #
@router.callback_query(F.data == 'add year')
async def add_year_to_db(callback_query: CallbackQuery, state: FSMContext):
    global messages_to_delete
    messages_to_delete[message.chat.id] = await callback_query.message.answer(
        'Введите год автомобиля.\
        \nДля добавления списка годов запишите их столбцом:\
        \1971\
        \n2001\
        \n2031'
    )
    await state.set_state(Auto.year_to_add)

@router.message(Auto.year_to_add)
async def add_year_to_db(message: Message, state: FSMContext):
    global previous_kbs, ikbs
    from main import bot

    rows = await db.fetch_years()

    _years = []
    _year = ''
    i = 0
    for char in message.text:
        i += 1
        if char == '\n' and _year != "":
            _years.append(_year)
            _year = ""
        elif i == len(message.text):
            _year += char
            if _year != '':
                _years.append(_year)
        else:
            _year += char
        
    for year_ in _years:
        in_rows = False
        for row in rows:
            if year_ == row['year']:
                await message.answer('Такой год уже существует в базе данных')
                in_rows = True
                break
        if not in_rows:
            await message.answer(await add_year(year_))
    await bot.delete_message(
        message.chat.id, messages_to_delete[message.chat.id].message_id
    )

    key = message.chat.id
    if key in previous_kbs:
        if previous_kbs[key] != 1:
            await bot.delete_message(key, previous_kbs[key].message_id)
            previous_kbs[key] = 1
            
    if message.chat.id in admins:
        ikbs[message.chat.id] = await year_ikbs(
            model_ids[message.chat.id], admins[message.chat.id]
        )
    previous_kbs[message.chat.id] = await message.answer(
        'Выберите год авто:',
        reply_markup=ikbs[message.chat.id][pages[message.chat.id]].as_markup()
    )
    await message.delete()

@router.callback_query(F.data == 'delete year')
async def delete_year_from_db(callback_query: CallbackQuery, state: FSMContext):
    global messages_to_delete
    messages_to_delete[message.chat.id] = await callback_query.message.answer(
        'Введите год автомобиля который хотите удалить.\
        \nДля удаления списка годов запишите их столбцом:\
        \1971\
        \n2001\
        \n2031'
    )
    await state.set_state(Auto.year_to_delete)

@router.message(Auto.year_to_delete)
async def delete_year_from_db(message: Message):
    global previous_kbs, ikbs
    from main import bot

    rows = await db.fetch_years()

    _years = []
    _year = ''
    i = 0
    for char in message.text:
        i += 1
        if char == '\n' and _year != "":
            _years.append(_year)
            _year = ""
        elif i == len(message.text):
            _year += char
            if _year != '':
                _years.append(_year)
        else:
            _year += char

    for year_ in _years:
        for row in rows:
            if year_ == row['year']:
                await message.answer(await delete_year(year_))
                break
    await bot.delete_message(
        message.chat.id, messages_to_delete[message.chat.id].message_id
    )

    key = message.chat.id
    if key in previous_kbs:
        if previous_kbs[key] != 1:
            await bot.delete_message(key, previous_kbs[key].message_id)
            previous_kbs[key] = 1

    await message.delete()

    if message.chat.id in admins:
        ikbs[message.chat.id] = await year_ikbs(
            model_ids[message.chat.id], admins[message.chat.id]
        )
    previous_kbs[message.chat.id] = await message.answer(
        'Выберите год авто:',
        reply_markup=ikbs[message.chat.id][pages[message.chat.id]].as_markup()
    )

@router.callback_query(F.data == 'update year')
async def update_year_in_db(callback_query: CallbackQuery, state: FSMContext):
    global messages_to_delete
    messages_to_delete[message.chat.id] = await callback_query.message.answer(
        'Введите год автомобиля который заменить.'
    )
    await state.set_state(Auto.old_year)

@router.message(Auto.old_year)
async def update_year_in_db(message: Message, state: FSMContext):
    global messages_to_delete
    from main import bot
    await bot.delete_message(
        message.chat.id, messages_to_delete[message.chat.id].message_id
    )
    await message.delete()

    await state.update_data(old_year=message.text)
    messages_to_delete[message.chat.id] = await message.answer(
        'Введите новый год для автомобиля.'
    )
    await state.set_state(Auto.new_year)

@router.message(Auto.new_year)
async def update_year_in_db(message: Message, state: FSMContext):
    global previous_kbs, ikbs
    from main import bot

    rows = await db.fetch_years()
    data = await state.get_data()

    in_rows = False
    for row in rows:
        if message.text == row['year']:
            await message.answer('Такой год уже существует в базе данных')
            in_rows = True
            break
    if not in_rows:
        await message.answer(
            await update_year(data.get('old_year'), message.text)
        )

    key = message.chat.id
    if key in previous_kbs:
        if previous_kbs[key] != 1:
            await bot.delete_message(key, previous_kbs[key].message_id)
            previous_kbs[key] = 1

    await bot.delete_message(
        message.chat.id, messages_to_delete[message.chat.id].message_id
    )
    await message.delete()

    if message.chat.id in admins:
        ikbs[message.chat.id] = await year_ikbs(
            model_ids[message.chat.id], admins[message.chat.id]
        )
    previous_kbs[message.chat.id] = await message.answer(
        'Выберите год авто:',
        reply_markup=ikbs[message.chat.id][pages[message.chat.id]].as_markup()
    )

@router.callback_query(F.data == 'search year')
async def search_year_in_db(callback_query: CallbackQuery, state: FSMContext):
    global messages_to_delete
    messages_to_delete[message.chat.id] = await callback_query.message.answer(
        'Введите год автомобиля который хотите найти.'
    )
    await state.set_state(Auto.search_year)

@router.message(Auto.search_year)
async def search_year_in_db(message: Message):
    global previous_kbs, ikbs, stages, years, year_ids
    from main import bot

    chat_id = message.chat.id
    is_admin = False
    if message.chat.id in admins:
        if admins[message.chat.id] == True:
            is_admin = True

    rows = await db.fetch_years()

    await bot.delete_message(chat_id, messages_to_delete[chat_id].message_id)
    await message.delete()

    users_rows = await db.fetch_premium_users()
    files_to_delete = []
    id_in = False

    premium = False

    for row in users_rows:
        if row['chat_id'] == chat_id:
            id_in = True

            current_time = datetime.now()
            sub_end = datetime.strptime(
                row['sub_end'], '%Y-%m-%d %H:%M:%S'
            )

            if current_time > sub_end:
                await message.answer(
                    await delete_premium_user(str(chat_id))
                )
                id_in = False
                premium = False
            else:
                premium = True
            await message.delete()
            break

    last_file = 1
    year_in = False
    file_rows = await db.fetch_files()

    for row in rows:
        if message.text.lower() == row['year'].lower():
            year_in = True
            years[chat_id] = row['year']
            year_ids[chat_id] = row['year_id']

            for file_row in file_rows:
                if year_id == file_row['year_id']:
                    try:
                        last_file = await bot.send_photo(
                            chat_id, file_row['photo']
                        )
                        files_to_delete.append(last_file)
                    except Exception as e:
                        if file_row['photo'] is not None:
                            await message.answer(
                                f'Упс! Произошла ошибка: {e}'
                            )

    if premium or is_admin:
        for row in rows:
            if message.text.lower() == row['year'].lower():
                year_in = True
                years[chat_id] = row['year']
                year_ids[chat_id] = row['year_id']

                for file_row in file_rows:
                    if year_id == file_row['year_id']:
                        try:
                            last_file = await bot.send_photo(
                                chat_id, file_row['premium_photo'],
                                caption='Премиальное изображение'
                            )
                            files_to_delete.append(last_file)
                        except Exception as e:
                            if file_row['premium_photo'] is not None:
                                await message.answer(
                                    f'Упс! Произошла ошибка: {e}'
                                )

    for row in rows:
        if message.text.lower() == row['year'].lower():
            year_in = True
            years[chat_id] = row['year']
            year_ids[chat_id] = row['year_id']

            for file_row in file_rows:
                if year_id == file_row['year_id']:
                    try:
                        result_bytes = await create_bytes_file(
                            file_row['pdf']
                        )
                        await bot.send_chat_action(
                            chat_id, ChatAction.UPLOAD_DOCUMENT
                        )
                        last_file = await bot.send_document(
                            chat_id,
                            types.BufferedInputFile(
                                file=result_bytes,
                                filename=f'{brands[chat_id]} {models[chat_id]} {years[chat_id]}.pdf'
                            )
                        )
                        files_to_delete.append(last_file)
                    except Exception as e:
                        if file_row['pdf'] != None:
                            await message.answer(
                                f'Упс! Произошла ошибка: {e}'
                            )

    if premium or is_admin:
        for row in rows:
            if message.text.lower() == row['year'].lower():
                year_in = True
                years[chat_id] = row['year']
                year_ids[chat_id] = row['year_id']

                for file_row in file_rows:
                    if year_id == file_row['year_id']:
                        try:
                            result_bytes = await create_bytes_file(
                                file_row['premium_pdf']
                            )
                            await bot.send_chat_action(
                                chat_id, ChatAction.UPLOAD_DOCUMENT
                            )
                            last_file = await bot.send_document(
                                chat_id,
                                types.BufferedInputFile(
                                    file=result_bytes,
                                    filename=f'(PREMIUM) {brands[chat_id]} {models[chat_id]} {years[chat_id]}.pdf'
                                )
                            )
                            files_to_delete.append(last_file)
                        except Exception as e:
                            if file_row['premium_pdf'] is not None:
                                await message.answer(
                                    f'Упс! Произошла ошибка: {e}'
                                )

    if year_in:
        key = chat_id
        if key in previous_kbs:
            if previous_kbs[key] != 1:
                await bot.delete_message(key, previous_kbs[key].message_id)
                previous_kbs[key] = 1

        stages[chat_id] += 1
        if is_admin:
            pages[chat_id] = 0
            previous_kbs[chat_id] = await message.answer(
                'Меню администратора:', reply_markup=edit_files_ikbs
            )
        else:
            if last_file == 1:
                previous_kbs = await message.answer(
                    'Фотографий не найдено.', reply_markup=back_ikb
                )
            else:
                await bot.edit_message_reply_markup(
                    chat_id=last_file.chat.id, message_id=last_file.message_id,
                    reply_markup=back_ikb
                )

    for _file in files_to_delete:
        try:
            await sleep(24 * 60 * 60)
            await bot.delete_message(
                _file.chat.id, _file.message_id
            )
        except Exception as e:
            pass

def convert_to_download_link(google_drive_link):
    # Проверяем, что ссылка правильная и содержит нужный шаблон
    if "drive.google.com/file/d/" in google_drive_link:
        # Извлекаем идентификатор файла из ссылки
        file_id = google_drive_link.split("/d/")[1].split("/")[0]
        # Формируем ссылку для скачивания
        download_link = f"https://drive.google.com/uc?export=download&id={file_id}"
        return download_link
    else:
        return "Неверная ссылка!"

# # # # # # # # #
#   P H O T O   #
# # # # # # # # #
@router.callback_query(F.data == 'add photo')
async def add_photo_to_db(callback_query: CallbackQuery, state: FSMContext):
    global messages_to_delete
    messages_to_delete[message.chat.id] = await callback_query.message.answer(
        'Вставьте url изображения на Google Drive.'
    )
    await state.set_state(Auto.photo_to_add)

@router.message(Auto.photo_to_add)
async def add_photo_to_db(message: Message, state: FSMContext):
    global previous_kbs, ikbs
    from main import bot

    correct_link = convert_to_download_link(message.text)

    photo = None
    await message.answer(await add_photo(correct_link))
    try:
        photo = await bot.send_photo(
            message.chat.id, correct_link
        )
    except Exception as e:
            await message.answer(
                f'Упс! Произошла ошибка: {e}'
            )

    if message.chat.id in admins:
        if admins[message.chat.id] == True:
            key = message.chat.id
            if key in previous_kbs:
                if previous_kbs[key] != 1:
                    await bot.delete_message(key, previous_kbs[key].message_id)
                    previous_kbs[key] = 1
            pages[message.chat.id] = 0
            ikbs[message.chat.id] = edit_files_ikbs
            previous_kbs[message.chat.id] = await message.answer(
                'Меню администратора:', reply_markup=edit_files_ikbs
            )

    await bot.delete_message(
        message.chat.id, messages_to_delete[message.chat.id].message_id
    )
    await message.delete()

    if photo:
        await sleep(24 * 60 * 60)
        await bot.delete_message(photo.chat.id, photo.message_id)

@router.callback_query(F.data == 'delete photo')
async def delete_photo_from_db(callback_query: CallbackQuery, state: FSMContext):
    global messages_to_delete
    from main import bot

    rows = await db.fetch_files()
    files_to_delete = []
    for row in rows:
        if row['year_id'] == year_ids[chat_id]:
            try:
                photo = await bot.send_photo(
                    callback_query.message.chat.id,
                    row['photo'],
                    caption=f'Номер фото: {row["column_id"]}',
                )
                files_to_delete.append(photo)
            except Exception as e:
                if row['photo'] != None:
                    await callback_query.message.answer(
                        f'Упс! Произошла ошибка: {e}\
                        \nНомер фото: {row["column_id"]}'
                    )  

    messages_to_delete[message.chat.id] = await callback_query.message.answer(
        'Введите номер изображения.'
    )
    await state.set_state(Auto.photo_to_delete)
    for _file in files_to_delete:
        try:
            await sleep(24 * 60 * 60)
            await bot.delete_message(
                _file.chat.id, _file.message_id
            )
        except Exception as e:
            print('Ошибка при удалении файла!')


@router.message(Auto.photo_to_delete)
async def delete_photo_from_db(message: Message, state: FSMContext):
    global previous_kbs, ikbs
    from main import bot

    await message.answer(await delete_photo(message.text))
    await bot.delete_message(
        message.chat.id, messages_to_delete[message.chat.id].message_id
    )
    await message.delete()

    key = message.chat.id
    if key in previous_kbs:
        if previous_kbs[key] != 1:
            await bot.delete_message(key, previous_kbs[key].message_id)
            previous_kbs[key] = 1
    pages[message.chat.id] = 0
    ikbs[message.chat.id] = edit_files_ikbs
    previous_kbs[message.chat.id] = await message.answer(
        'Меню администратора:', reply_markup=edit_files_ikbs
    )


# # # # # # # # # # # # # # # # #
#   P R E M I U M   P H O T O   #
# # # # # # # # # # # # # # # # #
@router.callback_query(F.data == 'add premium photo')
async def add_premium_photo_to_db(callback_query: CallbackQuery, state: FSMContext):
    global messages_to_delete
    messages_to_delete[message.chat.id] = await callback_query.message.answer(
        'Вставьте url изображения на Google Drive.'
    )
    await state.set_state(Auto.premium_photo_to_add)

@router.message(Auto.premium_photo_to_add)
async def add_premium_photo_to_db(message: Message, state: FSMContext):
    global previous_kbs, ikbs
    from main import bot

    correct_link = convert_to_download_link(message.text)
    photo = None
    await message.answer(await add_premium_photo(correct_link))
    try:
        photo = await bot.send_photo(
            message.chat.id, correct_link,
            caption='Премиальное изображение',
        )
    except Exception as e:
            await message.answer(
                f'Упс! Произошла ошибка: {e}'
            )

    key = message.chat.id
    if key in previous_kbs:
        if previous_kbs[key] != 1:
            await bot.delete_message(key, previous_kbs[key].message_id)
            previous_kbs[key] = 1
    pages[message.chat.id] = 0
    ikbs[message.chat.id] = edit_files_ikbs
    previous_kbs[message.chat.id] = await message.answer(
        'Меню администратора:', reply_markup=edit_files_ikbs
    )

    await bot.delete_message(
        message.chat.id, messages_to_delete[message.chat.id].message_id
    )
    await message.delete()
    if photo:
        await bot.delete_message(photo.chat.id, photo.message_id)

@router.callback_query(F.data == 'delete premium photo')
async def delete_premium_photo_from_db(callback_query: CallbackQuery, state: FSMContext):
    global messages_to_delete
    from main import bot

    rows = await db.fetch_files()
    files_to_delete = []
    for row in rows:
        if row['year_id'] == year_ids[chat_id]:
            try:
                photo = await bot.send_photo(
                    callback_query.message.chat.id,
                    row['premium_photo'],
                    caption=f'Номер фото: {row["column_id"]}',
                )
                files_to_delete.append(photo)
            except Exception as e:
                if row['premium_photo'] != None:
                    await callback_query.message.answer(
                        f'Упс! Произошла ошибка: {e}\
                        \nНомер фото: {row["column_id"]}'
                    )  
    messages_to_delete[message.chat.id] = await callback_query.message.answer(
        'Введите номер изображения.'
    )
    await state.set_state(Auto.premium_photo_to_delete)
    for _file in files_to_delete:
        try:
            await sleep(24 * 60 * 60)
            await bot.delete_message(
                _file.chat.id, _file.message_id
            )
        except Exception as e:
            print('Ошибка при удалении файла!')

@router.message(Auto.premium_photo_to_delete)
async def delete_photo_from_db(message: Message, state: FSMContext):
    global previous_kbs, ikbs
    from main import bot

    await message.answer(await delete_premium_photo(message.text))
    await bot.delete_message(
        message.chat.id, messages_to_delete[message.chat.id].message_id
    )
    await message.delete()

    key = message.chat.id
    if key in previous_kbs:
        if previous_kbs[key] != 1:
            await bot.delete_message(key, previous_kbs[key].message_id)
            previous_kbs[key] = 1
    pages[message.chat.id] = 0
    ikbs[message.chat.id] = edit_files_ikbs
    previous_kbs[message.chat.id] = await message.answer(
        'Меню администратора:', reply_markup=edit_files_ikbs
    )

# # # # # # #
#   P D F   #
# # # # # # #
@router.callback_query(F.data == 'add pdf')
async def add_pdf_to_db(callback_query: CallbackQuery, state: FSMContext):
    global messages_to_delete
    messages_to_delete[message.chat.id] = await callback_query.message.answer(
        'Вставьте url файла на Google Drive.'
    )
    await state.set_state(Auto.pdf_to_add)

@router.message(Auto.pdf_to_add)
async def add_pdf_to_db(message: Message, state: FSMContext):
    global previous_kbs, ikbs
    from main import bot

    correct_link = convert_to_download_link(message.text)
    pdf = None
    await message.answer(await add_pdf(correct_link))
    try:
        result_bytes = await create_bytes_file(correct_link)
        await bot.send_chat_action(
            message.chat.id,
            ChatAction.UPLOAD_DOCUMENT
        )
        pdf = await bot.send_document(
            message.chat.id,
            types.BufferedInputFile(
                file=result_bytes,
                filename=f'{brands[message.chat.id]} {models[message.chat.id]} {years[chat_id]}.pdf'
            )
        )
    except Exception as e:
            await message.answer(
                f'Упс! Произошла ошибка: {e}'
            )

    key = message.chat.id
    if key in previous_kbs:
        if previous_kbs[key] != 1:
            await bot.delete_message(key, previous_kbs[key].message_id)
            previous_kbs[key] = 1
    pages[message.chat.id] = 0
    ikbs[message.chat.id] = edit_files_ikbs
    previous_kbs[message.chat.id] = await message.answer(
        'Меню администратора:', reply_markup=edit_files_ikbs
    )

    await bot.delete_message(
        message.chat.id, messages_to_delete[message.chat.id].message_id
    )
    await message.delete()
    if pdf:
        await bot.delete_message(pdf.chat.id, pdf.message_id)

@router.callback_query(F.data == 'delete pdf')
async def delete_pdf_from_db(callback_query: CallbackQuery, state: FSMContext):
    global messages_to_delete
    from main import bot

    chat_id = callback_query.message.chat.id

    rows = await db.fetch_files()
    files_to_delete = []
    for row in rows:
        if row['year_id'] == year_ids[chat_id]:
            try:
                result_bytes = await create_bytes_file(
                    file_row['pdf']
                )
                await bot.send_chat_action(
                    chat_id, ChatAction.UPLOAD_DOCUMENT
                )
                pdf = await bot.send_document(
                    chat_id,
                    types.BufferedInputFile(
                        file=result_bytes,
                        filename=f'{brands[chat_id]} {models[chat_id]} {years[chat_id]}.pdf'
                    )
                )
                files_to_delete.append(pdf)
            except Exception as e:
                if row['pdf'] != None:
                    await callback_query.message.answer(
                        f'Упс! Произошла ошибка: {e}\
                        \nНомер файла: {row["column_id"]}'
                    )  
    messages_to_delete[message.chat.id] = await callback_query.message.answer(
        'Введите номер файла.'
    )
    await state.set_state(Auto.pdf_to_delete)
    for _file in files_to_delete:
        try:
            await sleep(24 * 60 * 60)
            await bot.delete_message(
                _file.chat.id, _file.message_id
            )
        except Exception as e:
            print('Ошибка при удалении файла!')

@router.message(Auto.pdf_to_delete)
async def delete_photo_from_db(message: Message, state: FSMContext):
    global previous_kbs, ikbs
    from main import bot

    await message.answer(await delete_pdf(message.text))
    await bot.delete_message(
        message.chat.id, messages_to_delete[message.chat.id].message_id
    )
    await message.delete()

    key = message.chat.id
    if key in previous_kbs:
            if previous_kbs[key] != 1:
                await bot.delete_message(key, previous_kbs[key].message_id)
                previous_kbs[key] = 1
    pages[message.chat.id] = 0
    ikbs[message.chat.id] = edit_files_ikbs
    previous_kbs[message.chat.id] = await message.answer(
        'Меню администратора:', reply_markup=edit_files_ikbs
    )

# # # # # # # # # # # # # # #
#   P R E M I U M   P D F   #
# # # # # # # # # # # # # # #
@router.callback_query(F.data == 'add premium pdf')
async def add_premium_pdf_to_db(callback_query: CallbackQuery, state: FSMContext):
    global messages_to_delete
    messages_to_delete[message.chat.id] = await callback_query.message.answer(
        'Вставьте url файла на Google Drive.'
    )
    await state.set_state(Auto.premium_pdf_to_add)

@router.message(Auto.premium_pdf_to_add)
async def add_pdf_to_db(message: Message, state: FSMContext):
    global previous_kbs, ikbs
    from main import bot

    chat_id = callback_query.message.chat.id

    correct_link = convert_to_download_link(message.text)
    pdf = None
    await message.answer(await add_premium_pdf(correct_link))
    try:
        result_bytes = await create_bytes_file(correct_link)
        await bot.send_chat_action(
            chat_id,
            ChatAction.UPLOAD_DOCUMENT
        )
        pdf = await bot.send_document(
            chat_id,
            types.BufferedInputFile(
                file=result_bytes,
                filename=f'(PREMIUM) {brands[chat_id]} {models[chat_id]} {years[chat_id]}.pdf'
            )
        )
    except Exception as e:
            await message.answer(
                f'Упс! Произошла ошибка: {e}'
            )

    key = message.chat.id
    if key in previous_kbs:
        if previous_kbs[key] != 1:
            await bot.delete_message(key, previous_kbs[key].message_id)
            previous_kbs[key] = 1
    pages[message.chat.id] = 0
    ikbs[message.chat.id] = edit_files_ikbs
    previous_kbs[message.chat.id] = await message.answer(
        'Меню администратора:', reply_markup=edit_files_ikbs
    )

    await bot.delete_message(
        message.chat.id, messages_to_delete[message.chat.id].message_id
    )
    await message.delete()
    if pdf:
        await bot.delete_message(pdf.chat.id, pdf.message_id)

@router.callback_query(F.data == 'delete premium pdf')
async def delete_premium_pdf_from_db(callback_query: CallbackQuery, state: FSMContext):
    global messages_to_delete
    from main import bot

    chat_id = callback_query.message.chat.id

    rows = await db.fetch_files()
    files_to_delete = []
    for row in rows:
        if row['year_id'] == year_ids[chat_id]:
            try:
                result_bytes = await create_bytes_file(
                    file_row['premium_pdf']
                )
                await bot.send_chat_action(
                    chat_id,
                    ChatAction.UPLOAD_DOCUMENT
                )
                pdf = await bot.send_document(
                    chat_id,
                    types.BufferedInputFile(
                        file=result_bytes,
                        filename=f'(PREMIUM) {brands[chat_id]} {models[chat_id]} {years[chat_id]}.pdf'
                    )
                )
                files_to_delete.append(pdf)
            except Exception as e:
                            if row['premium_pdf'] is not None:
                                await callback_query.message.answer(
                                    f'Упс! Произошла ошибка {e}\
                                    \nНомер файла: {row["column_id"]}'
                                )

    messages_to_delete[chat_id] = await callback_query.message.answer(
        'Введите номер файла.'
    )
    await state.set_state(Auto.premium_pdf_to_delete)
    for _file in files_to_delete:
        try:
            await sleep(24 * 60 * 60)
            await bot.delete_message(
                _file.chat.id, _file.message_id
            )
        except Exception as e:
            print('Ошибка при удалении файла!')

@router.message(Auto.premium_pdf_to_delete)
async def delete_photo_from_db(message: Message, state: FSMContext):
    global previous_kbs, ikbs
    from main import bot

    await message.answer(await delete_premium_pdf(message.text))
    await bot.delete_message(
        message.chat.id, messages_to_delete[message.chat.id].message_id
    )
    await message.delete()

    key = message.chat.id
    if key in previous_kbs:
        if previous_kbs[key] != 1:
            await bot.delete_message(key, previous_kbs[key].message_id)
            previous_kbs[key] = 1
    pages[message.chat.id] = 0
    ikbs[message.chat.id] = edit_files_ikbs
    previous_kbs[message.chat.id] = await message.answer(
        'Меню администратора:', reply_markup=edit_files_ikbs
    )

# # # # # # # # # # #
#   B U T T O N S   #
# # # # # # # # # # #
@router.callback_query(F.data == '<<')
async def forward(callback_query: CallbackQuery):
    global pages

    if ikbs[callback_query.message.chat.id]:
        if pages[callback_query.message.chat.id] != 0:
            pages[callback_query.message.chat.id] = 0
            await callback_query.message.edit_reply_markup(
                reply_markup=ikbs[callback_query.message.chat.id][pages[callback_query.message.chat.id]].as_markup()
            )
        else:
            await callback_query.answer('Вы на первой странице')

@router.callback_query(F.data == '<')
async def forward(callback_query: CallbackQuery):
    global pages
    pages[callback_query.message.chat.id] -= 1

    if ikbs[callback_query.message.chat.id]:
        if pages[callback_query.message.chat.id] >= 0:
            await callback_query.message.edit_reply_markup(
                reply_markup=ikbs[callback_query.message.chat.id][pages[callback_query.message.chat.id]].as_markup()
            )
        else:
            pages[callback_query.message.chat.id] += 1
            await callback_query.answer('Вы на первой странице')

@router.callback_query(F.data == '>')
async def forward(callback_query: CallbackQuery):
    global pages
    pages[callback_query.message.chat.id] += 1

    if ikbs[callback_query.message.chat.id]:
        if pages[callback_query.message.chat.id] < len(ikbs[callback_query.message.chat.id]):
                await callback_query.message.edit_reply_markup(
                    reply_markup=ikbs[callback_query.message.chat.id][pages[callback_query.message.chat.id]].as_markup()
                )
        else:
            pages[callback_query.message.chat.id] -= 1
            await callback_query.answer('Вы на последней странице')

@router.callback_query(F.data == '>>')
async def forward(callback_query: CallbackQuery):
    global pages

    if ikbs[callback_query.message.chat.id]:
        if pages[callback_query.message.chat.id] != len(ikbs[callback_query.message.chat.id]) - 1:
            pages[callback_query.message.chat.id] = len(ikbs[callback_query.message.chat.id]) - 1
            await callback_query.message.edit_reply_markup(
                reply_markup=ikbs[callback_query.message.chat.id][pages[callback_query.message.chat.id]].as_markup()
            )
        else:
            await callback_query.answer('Вы на последней странице')

@router.callback_query(F.data == 'back stage 1')
async def back(callback_query: CallbackQuery):
    await callback_query.answer('Вы на первом этапе')

@router.callback_query(F.data == 'back stage 2')
async def back(callback_query: CallbackQuery):
    global stages, pages, ikbs

    chat_id = callback_query.message.chat.id

    stages[chat_id] -= 1
    pages[chat_id] = 0
    if chat_id in admins:
        ikbs[chat_id] = await brand_ikbs(admins[chat_id])
    else:
        ikbs[chat_id] = await brand_ikbs(False)
    
    await callback_query.message.edit_text('Выберите марку авто:')
    await callback_query.message.edit_reply_markup(
        reply_markup=ikbs[chat_id][pages[chat_id]].as_markup()
    )

@router.callback_query(F.data == 'back stage 3')
async def back(callback_query: CallbackQuery):
    global stages, pages, ikbs
    pages[callback_query.message.chat.id] = 0
    chat_id = callback_query.message.chat.id
    stages[chat_id] -= 1

    if chat_id in admins:
        ikbs[callback_query.message.chat.id] = await model_ikbs(
            brand_ids[chat_id], admins[chat_id]
        )
    else:
        ikbs[chat_id] = await model_ikbs(
            brand_ids[chat_id], False
        )

    await callback_query.message.edit_text(
            f'Марка: {brands[chat_id]}\
            \nВыберите модель авто:'
        )
    await callback_query.message.edit_reply_markup(
        reply_markup=ikbs[callback_query.message.chat.id][pages[callback_query.message.chat.id]].as_markup()
    )

@router.callback_query(F.data == 'back stage 4')
async def back(callback_query: CallbackQuery):
    global stages, pages, ikbs, previous_kbs
    from main import bot
    chat_id = callback_query.message.chat.id
    stages[chat_id] -= 1
    pages[callback_query.message.chat.id] = 0

    if chat_id in admins:
        ikbs[chat_id] = await year_ikbs(model_ids[chat_id], admins[chat_id])
    else:
        year_ikbs(model_ids[chat_id], False)

    await callback_query.message.edit_text(
        f'Марка: {brands[chat_id]}\
        \nМодель: {models[chat_id]}\
        \nВыберите год авто:'
        )
    await callback_query.message.edit_reply_markup(
        reply_markup=ikbs[chat_id][pages[chat_id]].as_markup()
    )

@router.callback_query()
async def manipulations(callback_query: CallbackQuery):
    global previous_kbs, ikbs, stages, pages
    global brands, brand_ids, models, model_ids, years, year_ids
    from main import bot

    chat_id = callback_query.message.chat.id

    is_admin = False
    if chat_id in admins:
        if admins[chat_id] == True:
            is_admin = True

    brand_rows = await db.fetch_brands()
    for row in brand_rows:
        if callback_query.data == row['brand']:
            stages[chat_id] += 1
            pages[chat_id] = 0
            brands[chat_id] = row['brand']
            brand_ids[chat_id] = row['brand_id']
            if chat_id in admins:
                ikbs[chat_id] = await model_ikbs(
                    brand_ids[chat_id], admins[chat_id]
                )
            else:
                ikbs[chat_id] = await model_ikbs(
                    brand_ids[chat_id], False
                )
            await bot.edit_message_text(
                f'Марка: {brands[chat_id]}\
                \nВыберите модель авто:',
                chat_id=chat_id, message_id=previous_kbs[chat_id].message_id
            )
            await bot.edit_message_reply_markup(
                reply_markup=ikbs[chat_id][pages[chat_id]].as_markup(),
                chat_id=chat_id, message_id=previous_kbs[chat_id].message_id
            )
            break

    model_rows = await db.fetch_models()
    for row in model_rows:
        if callback_query.data == row['model']:
            stages[chat_id] += 1
            pages[chat_id] = 0
            models[chat_id] = row['model']
            model_ids[chat_id] = row['model_id']
            if chat_id in admins:
                ikbs[chat_id] = await year_ikbs(model_ids[chat_id], admins[chat_id])
            else:
                ikbs[chat_id] = await year_ikbs(model_ids[chat_id], False)
            await bot.edit_message_text(
                f'Марка: {brands[chat_id]}\
                \nМодель: {models[chat_id]}\
                \nВыберите год авто:',
                chat_id=chat_id,
                message_id=previous_kbs[chat_id].message_id
            )
            await bot.edit_message_reply_markup(
                reply_markup=ikbs[chat_id][pages[chat_id]].as_markup(),
                chat_id=chat_id,
                message_id=previous_kbs[chat_id].message_id
            )
            break

    premium = False
    users_rows = await db.fetch_premium_users()
    id_in = False
    for row in users_rows:
        if row['chat_id'] == chat_id:
            id_in = True

            current_time = datetime.now()
            sub_end = datetime.strptime(
                row['sub_end'], '%Y-%m-%d %H:%M:%S'
            )

            if current_time > sub_end:
                await callback_query.message.answer(
                    await delete_premium_user(str(chat_id))
                )
                id_in = False
                premium = False
            else:
                premium = True
            break

    last_file = 1
    year_in = False
    year_rows = await db.fetch_years()
    file_rows = await db.fetch_files()

    files_to_delete = []

    for row in year_rows:
        if callback_query.data == row['year']:
            stages[chat_id] += 1
            year_in = True
            years[chat_id] = row['year']
            year_ids[chat_id] = row['year_id']

            for file_row in file_rows:
                if year_ids[chat_id] == file_row['year_id']:
                    if file_row['photo']:
                        try:
                            last_file = await bot.send_photo(
                                chat_id,
                                file_row['photo']
                            )
                            files_to_delete.append(last_file)
                            
                        except Exception as e:
                            await callback_query.message.answer(
                                f'Упс! Произошла ошибка: {e}'
                            )


    if premium or is_admin:
        for row in year_rows:
            if callback_query.data == row['year']:
                year_in = True
                years[chat_id] = row['year']
                year_ids[chat_id] = row['year_id']

                for file_row in file_rows:
                    if year_ids[chat_id] == file_row['year_id']:
                        if file_row['premium_photo']:
                            try:
                                last_file = await bot.send_photo(
                                    message.chat.id,
                                    file_row['premium_photo'],
                                    caption='Премиальное изображение'
                                )
                                files_to_delete.append(last_file)

                            except Exception as e:
                                await message.answer(
                                    f'Упс! Произошла ошибка: {e}'
                                )

    for row in year_rows:
        if callback_query.data == row['year']:
            year_in = True
            years[chat_id] = row['year']
            year_ids[chat_id] = row['year_id']

            for file_row in file_rows:
                if year_ids[chat_id] == file_row['year_id']:
                    if file_row['pdf']:
                        try:
                            result_bytes = await create_bytes_file(
                                file_row['pdf']
                            )
                            await bot.send_chat_action(
                                chat_id,
                                ChatAction.UPLOAD_DOCUMENT
                            )
                            last_file = await bot.send_document(
                                chat_id,
                                types.BufferedInputFile(
                                    file=result_bytes,
                                    filename=f'{brands[chat_id]} {models[chat_id]} {years[chat_id]}.pdf'
                                )
                            )
                            files_to_delete.append(last_file)

                        except Exception as e:
                            await callback_query.message.answer(
                                f'Упс! Произошла ошибка: {e}'
                        )

    if premium or is_admin:
        for row in year_rows:
            if callback_query.data == row['year']:
                year_in = True
                years[chat_id] = row['year']
                year_ids[chat_id] = row['year_id']

                for file_row in file_rows:
                    if year_ids[chat_id] == file_row['year_id']:
                        if file_row['premium_pdf']:
                                try:
                                    result_bytes = await create_bytes_file(
                                        file_row['premium_pdf']
                                    )
                                    await bot.send_chat_action(
                                        chat_id,
                                        ChatAction.UPLOAD_DOCUMENT
                                    )
                                    last_file = await bot.send_document(
                                        chat_id,
                                        types.BufferedInputFile(
                                            file=result_bytes,
                                            filename=f'(PREMIUM) {brands[chat_id]} {models[chat_id]} {years[chat_id]}.pdf'
                                        )
                                    )
                                    files_to_delete.append(last_file)

                                except Exception as e:
                                    await callback_query.message.answer(
                                        f'Упс! Произошла ошибка: {e}'
                                    )

    if year_in:
        if is_admin:
            key = chat_id
            if key in previous_kbs:
                if previous_kbs[key] != 1:
                    await bot.delete_message(key, previous_kbs[key].message_id)
                    previous_kbs[key] = 1

        stages[chat_id] += 1
        if is_admin:
            pages[chat_id] = 0
            previous_kbs[chat_id] = await callback_query.message.answer(
                'Меню администратора:', reply_markup=edit_files_ikbs
            )
        else:
            if last_file == 1:
                previous_kbs[str(chat_id)] = await callback_query.message.answer(
                    'Фотографий не найдено.', reply_markup=back_ikb
                )
            else:
                await bot.edit_message_reply_markup(
                    chat_id=last_file.chat.id, message_id=last_file.message_id,
                    reply_markup=back_ikb
                )

    for _file in files_to_delete:
        try:
            await sleep(24 * 60 * 60)
            await bot.delete_message(
                _file.chat.id, _file.message_id
            )
        except Exception as e:
            print('Ошибка при удалении файла!')


