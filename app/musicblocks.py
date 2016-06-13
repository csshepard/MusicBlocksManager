import os
import sys
from subprocess import Popen, PIPE
from time import sleep
from datetime import datetime, timedelta
from flask import current_app
from . import db, celery
from .models import Block, Song, PlayHistory, PlayerState


try:
    import nxppy
except ImportError:
    import random

    class nxppy(object):
        class SelectError(Exception):
            pass

        class Mifare(object):
            def __init__(self):
                self.block_tags = [uuid for (uuid,) in Block.query.with_entities(Block.tag_uuid).all()]
                self.uuid = None
                self.time = datetime.utcnow()

            def select(self):
                if datetime.utcnow() - self.time > timedelta(seconds=15):
                    if random.random() > 0.25:
                        self.uuid = random.choice(self.block_tags)
                    else:
                        self.uuid = None
                    self.time = datetime.utcnow()
                if self.uuid is None:
                    raise nxppy.SelectError
                return self.uuid


class Player(object):
    def __init__(self):
        self._playing = False
        self._quit = False
        self.current_file = ''
        try:
            self._player = Popen(['mpg123', '-R', 'Player'], stdin=PIPE, stdout=PIPE)
            self._player.stdin.write('SILENCE\n'.encode())
            self._player.stdin.flush()
        except OSError:
            sys.exit("Error Running mpg123.\n Run 'apt-get install mpg123'")
        self.volume = 100.0

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        if self._quit:
            return
        if value < 0.0:
            self._volume = 0.0
        elif value > 100.0:
            self._volume = 100.0
        else:
            self._volume = float(value)
        self._player.stdin.write('V {}\n'.format(self._volume).encode())
        self._player.stdin.flush()

    def play_song(self, path):
        print('trying to play {}'.format(path))
        if self._quit or not os.path.isfile(path):
            return False
        if self.is_playing():
            self.stop_song()
        self._player.stdin.write('L {}\n'.format(path).encode())
        self._player.stdin.flush()
        self._playing = True
        self.current_file = path
        return True

    def stop_song(self):
        if self._quit or not self.is_playing():
            return False
        self._player.stdin.write('S\n'.encode())
        self._player.stdin.flush()
        self._player.stdout.flush()
        self._playing = False
        self.current_file = ''
        return True

    def is_playing(self):
        return self._playing

    def quit(self):
        if not self._quit:
            self._player.communicate('S\nQ\n'.encode())
            self._quit = True


@celery.task
def musicblocks():
    music_directory = current_app.config['MUSICBLOCKS_DIRECTORY']
    nfc = nxppy.Mifare()
    player = Player()
    playing_uid = ''
    player_state = PlayerState.query.one()
    player_state.active = True
    player_state.volume = player.volume
    player_state.playing = False
    player_state.song = None
    db.session.add(player_state)
    db.session.commit()
    while True:
        try:
            uid = nfc.select()
            if playing_uid != uid:
                if player.stop_song():
                    print('Stopped Song')
                    history.length_played = datetime.utcnow() - history.time_played
                    player_state.playing = False
                    player_state.song = None
                    db.session.add(history)
                    db.session.add(player_state)
                    db.session.commit()
                block = Block.query.filter_by(tag_uuid=uid).one_or_none()
                if block:
                    if block.type == 'song':
                        player.play_song(music_directory + block.song.file)
                        history = PlayHistory(song_title=block.song.title,
                                              block_number=block.number,
                                              time_played=datetime.utcnow())
                        playing_uid = uid
                        player_state.playing = True
                        player_state.song = block.song
                        db.session.add(player_state)
                        db.session.commit()
        except nxppy.SelectError:
            if player.stop_song():
                print('Stopped Song')
                history.length_played = datetime.utcnow() - history.time_played
                player_state.playing = False
                player_state.song = None
                db.session.add(history)
                db.session.add(player_state)
                db.session.commit()
                playing_uid = ''
        sleep(1)
