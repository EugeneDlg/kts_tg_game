"""final migration

Revision ID: 15e3ba519523
Revises:
Create Date: 2023-04-10 17:13:22.440766

"""
from hashlib import sha256

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "15e3ba519523"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    admins = op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("password", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "players",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vk_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "last_name", name="_name_lastname_uc"),
        sa.UniqueConstraint("vk_id"),
    )
    questions = op.create_table(
        "questions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("blitz", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("text"),
    )
    answers = op.create_table(
        "answers",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("question_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(
            ["question_id"], ["questions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "games",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("wait_status", sa.String(), nullable=False),
        sa.Column("wait_time", sa.Integer(), nullable=False),
        sa.Column("my_points", sa.Integer(), nullable=False),
        sa.Column("players_points", sa.Integer(), nullable=False),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("blitz_round", sa.Integer(), nullable=False),
        sa.Column("current_question_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["current_question_id"],
            ["questions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "game_captains",
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["player_id"], ["players.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("game_id"),
    )
    op.create_table(
        "game_score",
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["player_id"], ["players.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("player_id", "game_id"),
    )
    op.create_table(
        "game_speakers",
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["player_id"], ["players.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("game_id"),
    )
    op.create_table(
        "used_questions",
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["question_id"], ["questions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("game_id", "question_id"),
    )
    # ### end Alembic commands ###
    op.bulk_insert(
        admins,
        [
            {
                "id": 1,
                "email": "admin@admin.com",
                "password": sha256(b"admin").hexdigest(),
            }
        ],
    )
    op.bulk_insert(
        questions,
        [
            {
                "blitz": False,
                "id": "ae4ca5ab-f5e0-48fc-9a1b-6b1ae8856af1",
                "text": "Какого числа какого месяца в РФ празднуется день программиста (в невисокосный год)?"
            },
            {
                "blitz": False,
                "id": "9bd4f933-5a58-4daf-a1d5-feb236e0ec20",
                "text": "Какой термин, относящийся к процессу разработки программного обеспечения, появился благодаря коммодору ВМФ США Грейс Хоппер?"
            },
            {
                "blitz": False,
                "id": "3f563f31-1a6b-4db6-b907-6333fed238b3",
                "text": "Как называлось то, что 'разгадал' Алан Тьюринг?"
            },
            {
                "blitz": False,
                "id": "f8936956-1459-4ba0-a6c1-9d4b94250f96",
                "text": "Из какого материала раньше изготавливались шестерёнки, используемые в конструкциях подводных лодок, для ограничения шума?"
            },
            {
                "blitz": False,
                "id": "66a5c9fc-7a62-4129-9022-d57c2f6e73c5",
                "text": "Назовите фамилию российского писателя, который написал три произведения, названия которых начинаются на букву 'О'?"
            },
            {
                "blitz": False,
                "id": "eb1c295d-2349-409f-a82d-ea7df842922c",
                "text": "Сколько раз ходил к морю старик из сказки А.С. Пушкина 'О рыбаке и рыбке'?"
            },
            {
                "blitz": False,
                "id": "dc9fec6f-359f-4079-8b8b-47aada6b71cc",
                "text": "Назовите одно из главных изобретений Архимеда, без которого автомобилисты не рускнут отправиться в дальнюю поездку?"
            },
            {
                "blitz": False,
                "id": "84140392-164f-4cfd-a5c2-297ecab3aa90",
                "text": "Какое приблизительно расстояние между Царьградом и Константинополем?"
            },
            {
                "blitz": False,
                "id": "f4889ab3-6ec8-49f1-ba92-58359d66fa5e",
                "text": "Кто использовал в своей работе термин 'ревущие сороковые'?"
            },
            {
                "blitz": False,
                "id": "b6097ec6-b7e6-4cf1-b87e-dd61153258cb",
                "text": "Какая птица способна летать как головой так и хвостом вперёд?"
            },
            {
                "blitz": False,
                "id": "5343f8df-28eb-4fb7-9575-aa071f8314ff",
                "text": "Какое самое известное прозвище Нью-Йорка?"
            },
            {
                "blitz": True,
                "id": "60156044-6f30-48c4-9058-4c48c7e2d0c7",
                "text": "Назовите столицу Австралии"
            },
            {
                "blitz": True,
                "id": "2fe360bb-8c38-448d-a2f3-7cceb7ecfa85",
                "text": "Назовите столицу Турции"
            },
            {
                "blitz": False,
                "id": "166780b2-6711-47f3-b6da-d2b14ee6d609",
                "text": "Кому посвящён памятник, на пьедестале которого высечено: 'Он остановил Солнце и сдвинул Землю'?"
            },
            {
                "blitz": True,
                "id": "7c54faf0-5806-4a6f-b08f-bccc32e8be75",
                "text": "Назовите имя доктора Ватсона из серии рассказов о Шерлоке Холмсе А.К. Дойла"
            },
            {
                "blitz": True,
                "id": "fa5cfaf5-ae06-4327-afca-c0bf28b20d43",
                "text": "Какого химического элемента из перечисленных не существует? Германий, рутений, франций, австрий, нихоний?"
            },
            {
                "blitz": True,
                "id": "a68aec1c-03fe-4394-a5bc-0a516f773e67",
                "text": "В средние века каждый рецепт начинался со слова 'возьмите'. А как будет на латыне 'возьмите'?"
            },
            {
                "blitz": True,
                "id": "84a7444b-7ffc-4d9a-9158-b46e31533099",
                "text": "Назовите фамилию американского политика, изображённого на купюре в 100 долларов."
            },
            {
                "blitz": True,
                "id": "8ea0c7e7-2e4e-4963-95af-430503a463da",
                "text": "Назовите то, во что по мнению А. Эйнштейна не играет бог."
            },
            {
                "blitz": False,
                "id": "000ef6fa-4c45-458b-ae7b-d403cf552e30",
                "text": "Микеланджело как-то спросили: 'Что лучше - добро, приносящее зло, или зло, приносящее добро?' Что он ответил?"
            },
            {
                "blitz": True,
                "id": "b3a0dae5-426a-420c-a87d-ddcf9e90ed9a",
                "text": "Как звали одноимённую 'старуху' из советсткого мультфильма, которая носила 'складывающуюся шляпу'?"
            },
            {
                "blitz": True,
                "id": "15d92605-04a8-4c73-a025-8a6ee8db2818",
                "text": "Как сказать на немецком 'место для лечения'?"
            },
            {
                "blitz": False,
                "id": "597de705-197f-419f-952f-72b123773c6b",
                "text": "Как в Древнем Рим называли человека, бегущего возле колесницы Цезаря, возвращающегося из похода с победой и выкрикивающего ему порицания и осуждения, чтобы тот не возгордился?"
            },
            {
                "blitz": False,
                "id": "9450234d-abaa-4c33-9504-6416edcb4ade",
                "text": "В начале 17 века это русское слово было зарегистрировано англичанином Джеймсом, который пояснил его так 'длинные башмаки для снега'"
            },
            {
                "blitz": False,
                "id": "84f5f1ac-4099-433f-a1a4-6422d0cbfd7f",
                "text": "Какое всем известное слово произошло от итальянского слова 'хлОпок'?"
            },
            {
                "blitz": True,
                "id": "5dc37444-bb8f-4248-bb39-37548c269524",
                "text": "Какая страна является родиной гамбургера?"
            },
            {
                "blitz": False,
                "id": "920a9d5f-8c5a-4bd4-81b5-0e9f39abb75f",
                "text": "Какого языка программирования не существует? Варианта: A, B, C, D, E, F"
            },
            {
                "blitz": True,
                "id": "0cb2c31c-61a3-4e59-8458-8826fcc50f14",
                "text": "Какого химического элемента не существует? Эйнштейний, нильсборий, резерфордий или максборний?"
            },
            {
                "blitz": True,
                "id": "c8e7eb88-80e7-4570-8279-996347a2f337",
                "text": "Сколько цветов в радуге по мнению Исаака Ньютона?"
            },
            {
                "blitz": True,
                "id": "1cd0969d-0efc-4962-9958-818bfaae65e6",
                "text": "От какого сорта яблок произошло название персональных компьютеров компании Apple?"
            },
            {
                "blitz": True,
                "id": "5a2ddc95-bca2-4a77-878f-aad5f84e5f44",
                "text": "Как иначе назвать топологическую поверхность 1-го рода?"
            },
            {
                "blitz": True,
                "id": "fcc8d97d-6aec-429c-8844-594c43f969d5",
                "text": "Как иначе назвать гексаэдр?"
            }
        ],
    )
    op.bulk_insert(
        answers,
        [
            {
                "question_id": "ae4ca5ab-f5e0-48fc-9a1b-6b1ae8856af1",
                "id": "32b576d0-661f-4935-a30e-2b7f61cd1a8e",
                "text": "13 сентября|13сентября|13.09|13 09"
            },
            {
                "question_id": "9bd4f933-5a58-4daf-a1d5-feb236e0ec20",
                "id": "a75afccd-485c-4d3d-a10c-356ab3089bcc",
                "text": "дебаг|debugging"
            },
            {
                "question_id": "3f563f31-1a6b-4db6-b907-6333fed238b3",
                "id": "9c4dba94-dd84-4a77-91cd-b02e567d175a",
                "text": "энигма"
            },
            {
                "question_id": "f8936956-1459-4ba0-a6c1-9d4b94250f96",
                "id": "563e8f3d-dff3-495e-a599-79b415d344ad",
                "text": "дерево"
            },
            {
                "question_id": "66a5c9fc-7a62-4129-9022-d57c2f6e73c5",
                "id": "f615207f-a647-4bc0-ab18-cfa07f76edb5",
                "text": "гончаров"
            },
            {
                "question_id": "eb1c295d-2349-409f-a82d-ea7df842922c",
                "id": "de85a367-2666-4800-8dc6-487925b058ef",
                "text": "6"
            },
            {
                "question_id": "dc9fec6f-359f-4079-8b8b-47aada6b71cc",
                "id": "7224e7b9-5e68-457a-b817-1645b400f371",
                "text": "домкрат"
            },
            {
                "question_id": "84140392-164f-4cfd-a5c2-297ecab3aa90",
                "id": "cfc2f7ac-4a5d-4c24-b7a1-25f33e1c9096",
                "text": "0|ноль"
            },
            {
                "question_id": "f4889ab3-6ec8-49f1-ba92-58359d66fa5e",
                "id": "4fd21e41-4559-4821-9210-fa0c777eea9a",
                "text": "моряки|моряк|путешественники|путешественник"
            },
            {
                "question_id": "b6097ec6-b7e6-4cf1-b87e-dd61153258cb",
                "id": "76bea052-0f2c-4653-a1d4-5215b84f5b50",
                "text": "колибри"
            },
            {
                "question_id": "5343f8df-28eb-4fb7-9575-aa071f8314ff",
                "id": "094c59de-b706-4880-aeb4-d001c91e686e",
                "text": "большое яблоко"
            },
            {
                "question_id": "60156044-6f30-48c4-9058-4c48c7e2d0c7",
                "id": "4ce64a3b-efc6-4f87-b085-b4ffa75d6374",
                "text": "канберра"
            },
            {
                "question_id": "2fe360bb-8c38-448d-a2f3-7cceb7ecfa85",
                "id": "6d28f667-e2a2-49d4-ad6d-18a7c4da8d5f",
                "text": "анкара"
            },
            {
                "question_id": "166780b2-6711-47f3-b6da-d2b14ee6d609",
                "id": "7f35604e-e19a-4162-84a1-21bd5cd38dda",
                "text": "коперник"
            },
            {
                "question_id": "7c54faf0-5806-4a6f-b08f-bccc32e8be75",
                "id": "42fa7601-57e0-4f69-b5ed-39d281514857",
                "text": "джон"
            },
            {
                "question_id": "fa5cfaf5-ae06-4327-afca-c0bf28b20d43",
                "id": "bd48f589-b972-4d55-8ba6-a73ab1b785ef",
                "text": "австрий"
            },
            {
                "question_id": "a68aec1c-03fe-4394-a5bc-0a516f773e67",
                "id": "dbaaa675-04d2-4e2f-9aad-8ea80571d874",
                "text": "рецепт"
            },
            {
                "question_id": "84a7444b-7ffc-4d9a-9158-b46e31533099",
                "id": "be49985d-4a8e-4cd6-b918-6b071cfdbc76",
                "text": "франклин"
            },
            {
                "question_id": "8ea0c7e7-2e4e-4963-95af-430503a463da",
                "id": "96fd7d2a-89d8-4461-b78c-1bcff7468dc9",
                "text": "кости"
            },
            {
                "question_id": "000ef6fa-4c45-458b-ae7b-d403cf552e30",
                "id": "99a71132-fd5d-488c-8669-61da64144b72",
                "text": "я не знаю"
            },
            {
                "question_id": "b3a0dae5-426a-420c-a87d-ddcf9e90ed9a",
                "id": "ce1b3cd8-f3ce-4bdf-9a84-cb1b57a2abf1",
                "text": "шапокляк|старуха шапокляк"
            },
            {
                "question_id": "15d92605-04a8-4c73-a025-8a6ee8db2818",
                "id": "d4dab609-79dd-4518-b16b-c56f89ba9026",
                "text": "курорт"
            },
            {
                "question_id": "597de705-197f-419f-952f-72b123773c6b",
                "id": "678e068c-b977-4a42-9be3-0a5a032b9a3c",
                "text": "оппонент"
            },
            {
                "question_id": "9450234d-abaa-4c33-9504-6416edcb4ade",
                "id": "3620566b-b4ae-4c0a-80af-a4ba43843dbf",
                "text": "лыжи"
            },
            {
                "question_id": "84f5f1ac-4099-433f-a1a4-6422d0cbfd7f",
                "id": "e9ce7cfa-d998-434e-9ab0-1463854f75af",
                "text": "бумага"
            },
            {
                "question_id": "5dc37444-bb8f-4248-bb39-37548c269524",
                "id": "39f26fbf-6fb4-4085-8612-1f17565c707b",
                "text": "германия"
            },
            {
                "question_id": "920a9d5f-8c5a-4bd4-81b5-0e9f39abb75f",
                "id": "9eb3c750-da40-4ce6-8c6c-b71bf87975aa",
                "text": "a"
            },
            {
                "question_id": "0cb2c31c-61a3-4e59-8458-8826fcc50f14",
                "id": "3acdf614-47fb-4e82-8220-be633a9e984e",
                "text": "максборний"
            },
            {
                "question_id": "c8e7eb88-80e7-4570-8279-996347a2f337",
                "id": "012a94ad-d1b2-43d7-9eeb-7599e4ce6340",
                "text": "7|семь"
            },
            {
                "question_id": "1cd0969d-0efc-4962-9958-818bfaae65e6",
                "id": "c5f56c0f-5090-4288-9073-be6c696e727a",
                "text": "макинтош"
            },
            {
                "question_id": "5a2ddc95-bca2-4a77-878f-aad5f84e5f44",
                "id": "c4c43f5b-e3c4-4aff-87ca-6027ff712f24",
                "text": "тор|бублик"
            },
            {
                "question_id": "fcc8d97d-6aec-429c-8844-594c43f969d5",
                "id": "0b52cb38-5f38-416a-a690-d2894ec905a9",
                "text": "куб"
            }
        ],
    )


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("used_questions")
    op.drop_table("game_speakers")
    op.drop_table("game_score")
    op.drop_table("game_captains")
    op.drop_table("games")
    op.drop_table("answers")
    op.drop_table("questions")
    op.drop_table("players")
    op.drop_table("admins")
    # ### end Alembic commands ###
