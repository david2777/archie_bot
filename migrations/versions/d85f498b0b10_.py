"""empty message

Revision ID: d85f498b0b10
Revises: 
Create Date: 2020-07-03 23:07:36.419742

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd85f498b0b10'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('dogs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('birthday', sa.Date(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dogs_name'), 'dogs', ['name'], unique=True)
    op.create_table('event_types',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_table('events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('event_type_id', sa.Integer(), nullable=True),
    sa.Column('note', sa.String(length=128), nullable=True),
    sa.Column('start_time', sa.DateTime(), nullable=True),
    sa.Column('end_time', sa.DateTime(), nullable=True),
    sa.Column('is_accident', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['event_type_id'], ['event_types.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_events_start_time'), 'events', ['start_time'], unique=False)
    op.create_table('active_events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('event_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('dog_to_event_table',
    sa.Column('event_id', sa.Integer(), nullable=True),
    sa.Column('dog_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['dog_id'], ['dogs.id'], ),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('dog_to_event_table')
    op.drop_table('active_events')
    op.drop_index(op.f('ix_events_start_time'), table_name='events')
    op.drop_table('events')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_table('users')
    op.drop_table('event_types')
    op.drop_index(op.f('ix_dogs_name'), table_name='dogs')
    op.drop_table('dogs')
    # ### end Alembic commands ###
