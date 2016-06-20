from datetime import datetime
from sqlalchemy import Column, Integer, Enum, String, Text, ForeignKey, DateTime, Interval
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Model = declarative_base()


class Block(Model):
    __tablename__ = 'blocks'

    id = Column(Integer, primary_key=True)
    number = Column(Integer)
    type = Column(Enum('unset', 'song', 'command', name='block_types'))
    tag_uuid = Column(String(16))
    song_id = Column(Integer, ForeignKey('songs.id'))
    command_id = Column(Integer, ForeignKey('commands.id'))


class Song(Model):
    __tablename__ = 'songs'

    id = Column(Integer, primary_key=True)
    title = Column(String(64))
    file = Column(String(64))
    blocks = relationship('Block', backref='song')


class Command(Model):
    __tablename__ = 'commands'

    id = Column(Integer, primary_key=True)
    function = Column(Text())
    args = Column(Text())

    blocks = relationship('Block', backref='command')


class PlayHistory(Model):
    __tablename__ = 'play_history'

    id = Column(Integer, primary_key=True)
    song_title = Column(String(64))
    block_number = Column(Integer)
    time_played = Column(DateTime(), default=datetime.utcnow)
    length_played = Column(Interval())
