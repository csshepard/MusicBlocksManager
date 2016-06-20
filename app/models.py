from datetime import datetime
from . import db


class Block(db.Model):
    __tablename__ = 'blocks'

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer)
    type = db.Column(db.Enum('unset', 'song', 'command', name='block_types'))
    tag_uuid = db.Column(db.String(16))
    song_id = db.Column(db.Integer, db.ForeignKey('songs.id'))
    command_id = db.Column(db.Integer, db.ForeignKey('commands.id'))


class Song(db.Model):
    __tablename__ = 'songs'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    file = db.Column(db.String(64))
    blocks = db.relationship('Block', backref='song')


class Command(db.Model):
    __tablename__ = 'commands'

    id = db.Column(db.Integer, primary_key=True)
    function = db.Column(db.Text())
    args = db.Column(db.Text())

    blocks = db.relationship('Block', backref='command')


class PlayHistory(db.Model):
    __tablename__ = 'play_history'

    id = db.Column(db.Integer, primary_key=True)
    song_title = db.Column(db.String(64))
    block_number = db.Column(db.Integer)
    time_played = db.Column(db.DateTime(), default=datetime.utcnow)
    length_played = db.Column(db.Interval())
