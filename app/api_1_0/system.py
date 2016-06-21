from flask import redirect, url_for, request, flash
from . import api, red
from ..models import Block, Song
from .. import db


@api.route('/system/shutdown', methods=['POST'])
def shutdown():
    red.publish('musicblocks', 'exit')
    return redirect(url_for('.player_state'))


@api.route('/system/reorder', methods=['POST'])
def reorder_blocks():
    form = request.json['songs']
    for song in form:
        block = Block.query.filter_by(number=song['number']).first()
        if block:
            block.song = Song.query.get(song['song'])
            db.session.add(block)
    flash('Blocks Reordered')
    return redirect(url_for('.player_state'))
