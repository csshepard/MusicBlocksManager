import random
from datetime import datetime, timedelta

class SelectError(Exception):
    pass

class Mifare(object):
    block_tags = [None]
    def __init__(self):
        self.uuid = None
        self.time = datetime.utcnow()

    def select(self, block_num=None):
        if block_num is None:
            if datetime.utcnow() - self.time > timedelta(seconds=15):
                if random.random() > 0.25:
                    self.uuid = random.choice(Mifare.block_tags)
                else:
                    self.uuid = None
                self.time = datetime.utcnow()
        elif block_num == 0:
            self.uuid = None
        else:
            self.uuid = Mifare.block_tags[block_num-1]
        if self.uuid is None:
            raise SelectError
        return self.uuid
