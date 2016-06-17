from flask import jsonify, request, Response, stream_with_context

from .. import db
from ..models import Block
from . import api, red, status


def state_stream():
    status.subscribe('player_status')
    msg = ('data:{{\n'
           'data: "active": {active},\n'
           'data: "playing": "{playing}",\n'
           'data: "volume": {volume}\n'
           'data:}}\n\n')
    player = {}
    player['active'] = 'true' if red.get('mb_active')==b'True' else 'false'
    player['playing'] = red.get('mb_playing').decode()
    player['volume'] = float(red.get('mb_volume'))
    yield msg.format(**player)
    for message in status.listen():
        data = message['data'].decode()
        player['active'] = 'true' if red.get('mb_active')==b'True' else 'false'
        player['playing'] = red.get('mb_playing').decode()
        player['volume'] = float(red.get('mb_volume'))
        yield msg.format(**player)


@api.route('/player/volume', methods=['POST'])
def set_volume():
    value = request.form['volume']
    red.publish('musicblocks', 'volume {}'.format(value).encode())
    return redirect(url_for('.player_state'))


@api.route('/player/execute_block', methods=['POST'])
def execute_block():
    num = request.form['block_number']
    Block.query.filter_by(number=num).one()
    if Block is not None:
        red.publish('musicblocks', 'execute_block {}'.format(num).encode())
    return redirect(url_for('.player_state'))


@api.route('/player/stop_block', methods=['POST'])
def stop_block():
    red.publish('musicblocks', 'stop_block'.encode())
    return redirect(url_for('.player_state'))


@api.route('/player/get_state')
def player_state():
    player = {}
    player['active'] = True if red.get('mb_active') == b'True' else False
    player['playing'] = red.get('mb_playing').decode()
    player['volume'] = float(red.get('mb_volume'))
    return jsonify(player)


@api.route('/player/get_state/stream')
def player_state_stream():
    return Response(state_stream(), mimetype="text/event-stream")
