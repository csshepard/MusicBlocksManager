import os
import redis
from subprocess import Popen, PIPE, DEVNULL, call
from time import sleep
from datetime import datetime, timedelta
from app import create_app, db
from app.models import Block, PlayHistory, PlayerState


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
            self._player = Popen(['mpg123', '-R', 'Player'], stdin=PIPE, stdout=DEVNULL)
        except OSError:
            call(['apt-get install mpg123 -y'], shell=True)
            self._player = Popen(['mpg123', '-R', 'Player'], stdin=PIPE, stdout=DEVNULL)
        self._player.stdin.write('SILENCE\nV 100.0\n'.encode())
        self._player.stdin.flush()
        self._volume = 100.0

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
        self._keep_alive()
        self._player.stdin.write('V {}\n'.format(self._volume).encode())
        self._player.stdin.flush()

    def play_song(self, path):
        print('trying to play {}'.format(path))
        if self._quit or not os.path.isfile(path):
            return False
        self._keep_alive()
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
        self._keep_alive()
        self._player.stdin.write('S\n'.encode())
        self._player.stdin.flush()
        self._playing = False
        self.current_file = ''
        return True

    def is_playing(self):
        return self._playing

    def quit(self):
        if not self._quit:
            self._keep_alive()
            self._player.communicate('S\nQ\n'.encode())
            self._quit = True

    def _keep_alive(self):
        if self._player.poll() is not None:
            self._player = Popen(['mpg123', '-R', 'Player'], stdin=PIPE, stdout=DEVNULL)
            self._player.stdin.write('SILENCE\nV {}\n'.format(self._volume).encode())
            self._player.stdin.flush()


def musicblocks():
    def set_volume(player, player_state, value):
        player.volume = float(value)
        player_state.volume = player.volume
        db.session.add(player_state)
        db.session.commit()
        return player_state

    def execute_block(player, player_state, block_num=None, block_uuid=None):
        block = None
        if block_num is not None:
            block = Block.query.filter_by(number=int(block_num)).one_or_none()
        elif block_uuid is not None:
            block = Block.query.filter_by(tag_uuid=block_uuid).one_or_none()
        if block:
            if block.type == 'song':
                if player.stop_song():
                    old_history = PlayHistory.query.order_by(PlayHistory.time_played.desc()).first()
                    old_history.length_played = datetime.utcnow() - old_history.time_played
                    player_state.playing = False
                    player_state.song = None
                    db.session.add(old_history)
                if player.play_song(music_directory + block.song.file):
                    history = PlayHistory(song_title=block.song.title,
                                          block_number=block.number)
                    player_state.playing = True
                    player_state.song = block.song
                    db.session.add(history)
                db.session.add(player_state)
                db.session.commit()
        return player_state

    def stop_block(player, player_state, null=None):
        if player.stop_song():
            old_history = PlayHistory.query.order_by(PlayHistory.time_played.desc()).first()
            old_history.length_played = datetime.utcnow() - old_history.time_played
            player_state.playing = False
            player_state.song = None
            db.session.add(old_history)
            db.session.add(player_state)
            db.session.commit()
        return player_state
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')
    app.app_context().push()
    commands = {b'volume': set_volume, b'stop_block': stop_block, b'execute_block': execute_block}
    music_directory = app.config['MUSICBLOCKS_DIRECTORY']
    r = redis.StrictRedis()
    messages = r.pubsub(ignore_subscribe_messages=True)
    messages.subscribe('musicblocks')
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
        command = messages.get_message()
        if command is not None:
            command = command['data'].split()
            if command[0] in commands.keys():
                player_state = commands[command[0]](player, player_state, command[-1])
        try:
            uid = nfc.select()
            if playing_uid != uid:
                player_state = execute_block(player, player_state, block_uuid=uid)
                playing_uid = uid
        except nxppy.SelectError:
            if playing_uid != '':
                player_state = stop_block(player, player_state)
                playing_uid = ''
        sleep(1)


if __name__ == '__main__':
    musicblocks()
