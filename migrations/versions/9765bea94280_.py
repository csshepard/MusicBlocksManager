"""empty message

Revision ID: 9765bea94280
Revises: None
Create Date: 2016-06-11 20:32:02.722913

"""

# revision identifiers, used by Alembic.
revision = '9765bea94280'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('commands',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('function', sa.Text(), nullable=True),
    sa.Column('args', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('play_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('song_title', sa.String(length=64), nullable=True),
    sa.Column('block_number', sa.Integer(), nullable=True),
    sa.Column('time_played', sa.DateTime(), nullable=True),
    sa.Column('length_played', sa.Interval(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('songs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=64), nullable=True),
    sa.Column('file', sa.String(length=64), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('blocks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('number', sa.Integer(), nullable=True),
    sa.Column('type', sa.Enum('unset', 'song', 'command', name='block_types'), nullable=True),
    sa.Column('tag_uuid', sa.String(length=16), nullable=True),
    sa.Column('song_id', sa.Integer(), nullable=True),
    sa.Column('command_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['command_id'], ['commands.id'], ),
    sa.ForeignKeyConstraint(['song_id'], ['songs.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('player_state',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('playing', sa.Boolean(), nullable=True),
    sa.Column('volume', sa.Float(), nullable=True),
    sa.Column('song_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['song_id'], ['songs.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('player_state')
    op.drop_table('blocks')
    op.drop_table('songs')
    op.drop_table('play_history')
    op.drop_table('commands')
    ### end Alembic commands ###