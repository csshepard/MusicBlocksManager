from flask import jsonify
from ..models import PlayerState, Block
from . import api, command


@api.route('/player/volume/<float:value>')
def set_volume(value):
    command.publish('musicblocks', 'volume {}'.format(value).encode())
    player_state = PlayerState.query.one().to_json()
    player_state['volume'] = value
    return jsonify(player_state)


@api.route('/player/execute_block/<int:num>')
def execute_block(num):
    Block.query.filter_by(number=num).one()
    if Block is not None:
        command.publish('musicblocks', 'execute_block {}'.format(num).encode())
    player_state = PlayerState.query.one().to_json()
    return jsonify(player_state)


@api.route('/player/stop_block')
def stop_block():
    player_state = PlayerState.query.one()
    if player_state.playing:
        command.publish('musicblocks', 'stop_block'.encode())
    player_state.playing = False
    player_state.song_id = None
    return jsonify(player_state.to_json())