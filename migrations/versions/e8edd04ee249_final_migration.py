"""final migration

Revision ID: e8edd04ee249
Revises: 
Create Date: 2023-04-02 15:24:57.264779

"""
from hashlib import sha256

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e8edd04ee249'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    admins = op.create_table('admins',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=100), nullable=False),
    sa.Column('password', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('players',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('vk_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('last_name', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name', 'last_name', name='_name_lastname_uc'),
    sa.UniqueConstraint('vk_id')
    )
    questions = op.create_table('questions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('text', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('text')
    )
    answers = op.create_table('answers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('text', sa.String(), nullable=False),
    sa.Column('question_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('games',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('chat_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('wait_status', sa.String(), nullable=False),
    sa.Column('wait_time', sa.Integer(), nullable=False),
    sa.Column('my_points', sa.Integer(), nullable=False),
    sa.Column('players_points', sa.Integer(), nullable=False),
    sa.Column('round', sa.Integer(), nullable=False),
    sa.Column('current_question_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['current_question_id'], ['questions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('game_captains',
    sa.Column('game_id', sa.Integer(), nullable=False),
    sa.Column('player_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['game_id'], ['games.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['player_id'], ['players.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('game_id')
    )
    op.create_table('game_score',
    sa.Column('player_id', sa.Integer(), nullable=False),
    sa.Column('game_id', sa.Integer(), nullable=False),
    sa.Column('points', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['game_id'], ['games.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['player_id'], ['players.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('player_id', 'game_id')
    )
    op.create_table('game_speakers',
    sa.Column('game_id', sa.Integer(), nullable=False),
    sa.Column('player_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['game_id'], ['games.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['player_id'], ['players.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('game_id')
    )
    op.create_table('used_questions',
    sa.Column('game_id', sa.Integer(), nullable=False),
    sa.Column('question_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['game_id'], ['games.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('game_id', 'question_id')
    )
    # ### end Alembic commands ###
    op.bulk_insert(admins,
                   [
                       {
                           "id": 1,
                           "email": "admin@admin.com",
                           "password": sha256("admin".encode()).hexdigest()
                       }
                   ]
                  )
    op.bulk_insert(questions,
                   [
                       {
                           "id": 1,
                           "text": "Какого числа какого месяца в РФ празднуется день программиста (в невисокосный год)?"
                       },
                       {
                           "id": 2,
                           "text": "Какой термин, относящийся к процессу разработки программного обеспечения, появился благодаря коммодору ВМФ США Грейс Хоппер?"
                       },
                       {
                           "id": 3,
                           "text": "Как называлось то, что 'разгадал' Алан Тьюринг?"
                       },
                       {
                           "id": 4,
                           "text": "Из какого материала раньше изготавливались шестерёнки, используемые в конструкциях подводных лодок, для ограничения шума?"
                       },
                       {
                           "id": 5,
                           "text": "Назовите фамилию российского писателя, который написал три произведения, названия которых начинаются на букву 'О'?"
                       },
                       {
                           "id": 6,
                           "text": "Сколько раз ходил к морю старик из сказки А.С. Пушкина 'О рыбаке и рыбке'?"
                       },
                       {
                           "id": 7,
                           "text": "Назовите одно из главных изобретений Архимеда, без которого автомобилисты не рускнут отправиться в дальнюю поездку?"
                       },
                       {
                           "id": 8,
                           "text": "Какое приблизительно расстояние между Царьградом и Константинополем?"
                       },
                       {
                           "id": 9,
                           "text": "Кто использовал в своей работе термин 'ревущие сороковые'?"
                       },
                       {
                           "id": 10,
                           "text": "Птица, способная летать как головой так и хвостом вперёд"
                       }
                   ]

                   )
    op.bulk_insert(
        answers,
        [
            {
                "question_id": 1,
                "id": 1,
                "text": "13 сентября|13сентября|13.09|13 09"
            },
            {
                "question_id": 2,
                "id": 2,
                "text": "дебаг|debugging"
            },
            {
                "question_id": 3,
                "id": 3,
                "text": "Энигма"
            },
            {
                "question_id": 4,
                "id": 4,
                "text": "Дерево"
            },
            {
                "question_id": 5,
                "id": 5,
                "text": "Гончаров"
            },
            {
                "question_id": 6,
                "id": 6,
                "text": "6|шесть"
            },
            {
                "question_id": 7,
                "id": 7,
                "text": "Домкрат"
            },
            {
                "question_id": 8,
                "id": 8,
                "text": "0|Ноль"
            },
            {
                "question_id": 9,
                "id": 9,
                "text": "Моряки|Моряк|Путешественники|Путешественник"
            },
            {
                "question_id": 10,
                "id": 10,
                "text": "колибри"
            }
        ]
    )


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('used_questions')
    op.drop_table('game_speakers')
    op.drop_table('game_score')
    op.drop_table('game_captains')
    op.drop_table('games')
    op.drop_table('answers')
    op.drop_table('questions')
    op.drop_table('players')
    op.drop_table('admins')
    # ### end Alembic commands ###
