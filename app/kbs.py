from aiogram.types import (
    KeyboardButton, ReplyKeyboardMarkup,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import (
    InlineKeyboardBuilder, ReplyKeyboardBuilder
)

async def brand_ikbs(is_admin):
    from .handlers import db
    rows = sorted(await db.fetch_brands(), key=lambda row: row['brand_id'])

    ikbs = []

    j = 0

    page = InlineKeyboardBuilder()
    if is_admin:
        page.row(
            InlineKeyboardButton(text='🔍 Поиск 🔍',
            callback_data='search brand')
        )
        page.row(
            InlineKeyboardButton(text='📎 Добавить 📎',
            callback_data='add brand')
        )
        page.row(
            InlineKeyboardButton(text='🗑 Удалить 🗑',
            callback_data='delete brand')
        )
        page.row(
            InlineKeyboardButton(text='✏️ Изменить ✏️',
            callback_data='update brand')
        )
        page.row(
            InlineKeyboardButton(text='🔒 Изменить пароль 🔒',
            callback_data='update password')
        )
        j += 5
    else:
        page.row(
            InlineKeyboardButton(text='🔎 Поиск 🔍',
            callback_data='search brand')
        )
        j += 1
    btns_count = 0
    for i in range(len(rows)):
        if (btns_count % 10 == 0 and btns_count > 0) or j == 10:
            page.row(
                InlineKeyboardButton(text='<<', callback_data='<<'),
                InlineKeyboardButton(text='<', callback_data='<'),
                InlineKeyboardButton(
                    text=str(len(ikbs) + 1), callback_data='None'
                ),
                InlineKeyboardButton(text='>', callback_data='>'),
                InlineKeyboardButton(text='>>', callback_data='>>'),  
            )
            page.row(
                InlineKeyboardButton(text='Назад',
                callback_data='back stage 1')
            )
            ikbs.append(page)
            page = InlineKeyboardBuilder()
            btns_count = 0

        page.row(
            InlineKeyboardButton(text=rows[i]['brand'],
            callback_data=rows[i]['brand'])
        )
        j += 1
        btns_count += 1
        if i == len(rows) - 1:
            page.row(
                InlineKeyboardButton(text='<<', callback_data='<<'),
                InlineKeyboardButton(text='<', callback_data='<'),
                InlineKeyboardButton(
                    text=str(len(ikbs) + 1), callback_data='None'
                ),
                InlineKeyboardButton(text='>', callback_data='>'),
                InlineKeyboardButton(text='>>', callback_data='>>'),  
            )
            page.row(
                InlineKeyboardButton(text='Назад',
                callback_data='back stage 1')
            )
            ikbs.append(page)

    return ikbs

async def model_ikbs(brand_id, is_admin):
    from .handlers import db
    rows = sorted(await db.fetch_models(), key=lambda row: row['model_id'])
    ikbs = []
    page = InlineKeyboardBuilder()

    j = 0
    if is_admin:
        page.row(
            InlineKeyboardButton(text='🔍 Поиск 🔍',
            callback_data='search model')
        )
        page.row(
            InlineKeyboardButton(text='📎 Добавить 📎',
            callback_data='add model')
        )
        page.row(
            InlineKeyboardButton(text='🗑 Удалить 🗑',
            callback_data='delete model')
        )
        page.row(
            InlineKeyboardButton(text='✏️ Изменить ✏️',
            callback_data='update model')
        )
        j += 4
    else:
        page.row(
            InlineKeyboardButton(text='🔎 Поиск 🔍',
            callback_data='search model')
        )
        j += 1
    btns_count = 0
    for i in range(len(rows)):
        if (btns_count % 10 == 0 and btns_count > 0) or j == 10:
            markup = page.as_markup()
            if markup.inline_keyboard:
                page.row(
                    InlineKeyboardButton(text='<<', callback_data='<<'),
                    InlineKeyboardButton(text='<', callback_data='<'),
                    InlineKeyboardButton(
                        text=str(len(ikbs) + 1), callback_data='None'
                    ),
                    InlineKeyboardButton(text='>', callback_data='>'),
                    InlineKeyboardButton(text='>>', callback_data='>>'),  
                )
                page.row(
                    InlineKeyboardButton(text='Назад',
                    callback_data='back stage 2')
                )
                ikbs.append(page)
                page = InlineKeyboardBuilder()
                btns_count = 0

        if rows[i]['brand_id'] == brand_id:
            page.row(
                InlineKeyboardButton(text=rows[i]['model'],
                callback_data=rows[i]['model'])
            )
            btns_count += 1
            j += 1
        if i == len(rows) - 1:
            page.row(
                InlineKeyboardButton(text='<<', callback_data='<<'),
                InlineKeyboardButton(text='<', callback_data='<'),
                InlineKeyboardButton(
                    text=str(len(ikbs) + 1), callback_data='None'
                ),
                InlineKeyboardButton(text='>', callback_data='>'),
                InlineKeyboardButton(text='>>', callback_data='>>'),  
            )
            page.row(
                InlineKeyboardButton(text='Назад',
                callback_data='back stage 2')
            )
            ikbs.append(page)

    return ikbs

async def year_ikbs(model_id, is_admin):
    from .handlers import db
    rows = sorted(await db.fetch_years(), key=lambda row: row['year_id'])
    ikbs = []
    page = InlineKeyboardBuilder()

    j = 0
    if is_admin:
        page.row(
            InlineKeyboardButton(text='🔍 Поиск 🔍',
            callback_data='search year')
        )
        page.row(
            InlineKeyboardButton(text='📎 Добавить 📎',
            callback_data='add year')
        )
        page.row(
            InlineKeyboardButton(text='🗑 Удалить 🗑',
            callback_data='delete year')
        )
        page.row(
            InlineKeyboardButton(text='✏️ Изменить ✏️',
            callback_data='update year')
        )
        j += 4
    else:
        page.row(
            InlineKeyboardButton(text='🔎 Поиск 🔍',
            callback_data='search year')
        )
    
    btns_count = 0
    for i in range(len(rows)):
        if (btns_count % 10 == 0 and btns_count > 0) or j == 10:
            markup = page.as_markup()
            if markup.inline_keyboard:
                page.row(
                    InlineKeyboardButton(text='<<', callback_data='<<'),
                    InlineKeyboardButton(text='<', callback_data='<'),
                    InlineKeyboardButton(
                        text=str(len(ikbs) + 1), callback_data='None'
                    ),
                    InlineKeyboardButton(text='>', callback_data='>'),
                    InlineKeyboardButton(text='>>', callback_data='>>'),  
                )
                page.row(
                    InlineKeyboardButton(text='Назад',
                    callback_data='back stage 3')
                )
                ikbs.append(page)
                page = InlineKeyboardBuilder()
                btns_count = 0

        if rows[i]['model_id'] == model_id:
            page.row(
                InlineKeyboardButton(text=rows[i]['year'],
                callback_data=rows[i]['year'])
            )
            j += 1
            btns_count += 1
        if i == len(rows) - 1:
            page.row(
                InlineKeyboardButton(text='<<', callback_data='<<'),
                InlineKeyboardButton(text='<', callback_data='<'),
                InlineKeyboardButton(
                    text=str(len(ikbs) + 1), callback_data='None'
                ),
                InlineKeyboardButton(text='>', callback_data='>'),
                InlineKeyboardButton(text='>>', callback_data='>>'),  
            )
            page.row(
                InlineKeyboardButton(text='Назад',
                callback_data='back stage 3')
            )
            ikbs.append(page)

    return ikbs



edit_files_ikbs = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='Добавить фото', callback_data='add photo'
            )],
            [InlineKeyboardButton(
                text='Удалить фото', callback_data='delete photo'
            )],

            [InlineKeyboardButton(
                text='Добавить премиальное фото',
                callback_data='add premium photo'
            )],
            [InlineKeyboardButton(
                text='Удалить премиальное фото',
                callback_data='delete premium photo'
            )],

            [InlineKeyboardButton(
                text='Добавить файл', callback_data='add pdf'
            )],
            [InlineKeyboardButton(
                text='Удалить файл', callback_data='delete pdf'
            )],

            [InlineKeyboardButton(
                text='Добавить премиальный файл',
                callback_data='add premium pdf'
            )],
            [InlineKeyboardButton(
                text='Удалить премиальный файл',
                callback_data='delete premium pdf'
            )],
    ]
)

more_photos = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(
            text='Больше фото', callback_data='more photos'
        )]
    ]
)

back_ikb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Назад', callback_data='back stage 4')]
    ]
)

inactive_back_ikb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Назад', callback_data='None')]
    ]
)
