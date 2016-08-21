import os
import redis
import logging, logging.handlers
from subprocess import Popen, PIPE, call
try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, 'w')
from time import sleep
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models_noflask import Block, PlayHistory

basedir = os.path.abspath(os.path.dirname(__file__))

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

fh = logging.handlers.RotatingFileHandler(basedir + '/logs/musicblocks.log', maxBytes=10000, backupCount=5)
fh.setLevel(logging.WARNING)

sh = logging.StreamHandler()
sh.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

fh.setFormatter(formatter)
sh.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(sh)

if os.path.exists('.env'):
    logger.info('Importing environment from .env...')
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            logger.info('%s = %s', var[0], var[1])
            os.environ[var[0]] = var[1]

config = os.environ.get('FLASK_CONFIG') or 'production'
if config == 'production':
    logger.info('Starting in Production Mode')
    db_url = os.environ.get('DATABASE_URL') or 'sqlite:///{}/musicblocks.sqlite'.format(basedir)
elif config == 'testing':
    logger.info('Starting in Testing Mode')
    db_url = os.environ.get('TEST_DATABASE_URL') or 'sqlite:///{}/musicblocks-test.sqlite'.format(basedir)
else:
    logger.info('Starting in Development Mode')
    db_url = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///{}/musicblocks-dev.sqlite'.format(basedir)
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
session = Session()

if os.environ.get('HARDWARE') == 'laptop' or config == 'testing':
    import nxppy_test as nxppy
    nxppy.Mifare.block_tags = [uuid for (uuid,block_num) in session.query(Block).with_entities(Block.tag_uuid, Block.number).order_by(Block.number).all()]
else:
    import nxppy

class Player(object):
    def __init__(self):
        self._playing = False
        self._quit = False
        self.current_file = ''
        self.max_real_vol = 20.0
        try:
            self._player = Popen(['mpg123', '-R', 'Player'], stdin=PIPE, stdout=DEVNULL)
            logger.info('Player Started')
        except OSError:
            logger.warning('Player Not Installed, Installing Now')
            call(['apt-get install mpg123 -y'], shell=True)
            self._player = Popen(['mpg123', '-R', 'Player'], stdin=PIPE, stdout=DEVNULL)
            logger.info('Player Started')
        self._player.stdin.write('SILENCE\nV {}\n'.format(self.max_real_vol).encode())
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
        volume = self.max_real_vol * (self._volume / 100.0)
        self._keep_alive()
        self._player.stdin.write('V {}\n'.format(volume).encode())
        self._player.stdin.flush()

    def play_song(self, path):
        if self._quit or not os.path.isfile(path):
            return False
        self._keep_alive()
        if self.is_playing():
            self.stop_song()
        self._player.stdin.write('L {}\n'.format(path).encode())
        self._player.stdin.flush()
        self._playing = True
        self.current_file = path
        logger.info('Playing %s', path)
        return True

    def stop_song(self):
        if self._quit or not self.is_playing():
            return False
        self._keep_alive()
        self._player.stdin.write('S\n'.encode())
        self._player.stdin.flush()
        self._playing = False
        self.current_file = ''
        logger.info('Stopped Playing')
        return True

    def is_playing(self):
        return self._playing

    def quit(self):
        if not self._quit:
            self._keep_alive()
            self._player.communicate('S\nQ\n'.encode())
            self._quit = True
            logger.warning('Player Quit')

    def _keep_alive(self):
        if self._player.poll() is not None:
            logger.warning('Player Crashed. Restarting')
            self._player = Popen(['mpg123', '-R', 'Player'], stdin=PIPE, stdout=DEVNULL)
            self._player.stdin.write('SILENCE\nV {}\n'.format(self._volume).encode())
            self._player.stdin.flush()
            logger.warning('Player Restarted')


class MusicBlocks(object):
    def __init__(self, db_session):
        self.player = Player()
        self.commands = {b'volume': self.set_volume, b'stop_block': self.stop_block,
                         b'execute_block': self.execute_block, b'exit': None}
        self.music_directory = os.environ.get('MUSIC_BLOCKS_DIRECTORY') or os.path.join(basedir, 'Music/')
        self.nfc = nxppy.Mifare()
        self.red = redis.StrictRedis()
        self.messages = self.red.pubsub(ignore_subscribe_messages=True)
        self.messages.subscribe('musicblocks')
        self.red.set('mb_active', 'True')
        self.red.set('mb_volume', '100')
        self.red.publish('player_status', 'active')
        self.db = db_session

    def set_volume(self, value):
        if float(value) != self.player.volume:
            self.player.volume = float(value)
            self.red.set('mb_volume', str(self.player.volume))
            self.red.publish('player_status', 'volume')
            logger.info('Volume Changed to %s', self.player.volume)
            return True
        return False

    def execute_block(self, block_num=None, block_uuid=None):
        block = None
        if block_num is not None:
            block = self.db.query(Block).filter_by(number=int(block_num)).one_or_none()
        elif block_uuid is not None:
            block = self.db.query(Block).filter_by(tag_uuid=block_uuid).one_or_none()
        if block:
            logger.info('Executing Block #%s', block.number)
            if block.type == 'song':
                if self.player.stop_song():
                    old_history = self.db.query(PlayHistory).order_by(PlayHistory.time_played.desc()).first()
                    old_history.length_played = datetime.utcnow() - old_history.time_played
                    self.db.add(old_history)
                    self.red.set('mb_playing', 'Not Playing')
                if self.player.play_song(self.music_directory + block.song.file):
                    history = PlayHistory(song_title=block.song.title,
                                          block_number=block.number)
                    self.db.add(history)
                    self.red.set('mb_playing', block.song.title)
                self.db.commit()
            self.red.publish('player_status', 'playing')
            return True
        return False

    def stop_block(self):
        if self.player.stop_song():
            old_history = self.db.query(PlayHistory).order_by(PlayHistory.time_played.desc()).first()
            old_history.length_played = datetime.utcnow() - old_history.time_played
            self.db.add(old_history)
            self.db.commit()
            self.red.set('mb_playing', 'Not Playing')
            self.red.publish('player_status', 'playing')
            return True
        return False

    def start(self):
        playing_uid = ''
        try:
            while True:
                command = self.messages.get_message()
                if command is not None:
                    command = command['data'].split()
                    if command[0] in self.commands.keys():
                        if command[0] == b'exit':
                            break
                        else:
                            self.commands[command[0]](*command[1:])
                try:
                    uid = self.nfc.select()
                    if playing_uid != uid:
                        if self.execute_block(block_uuid=uid):
                            playing_uid = uid
                except nxppy.SelectError:
                    if playing_uid != '':
                        self.stop_block()
                        playing_uid = ''
                sleep(1)
        except KeyboardInterrupt:
            logger.info('Exiting')
        self.stop_block()
        self.red.set('mb_active', 'False')
        self.red.set('mb_playing', 'Not Playing')
        self.red.publish('player_status', 'active')


if __name__ == '__main__':
    musicblocks = MusicBlocks(session)
    musicblocks.start()
