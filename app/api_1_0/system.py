from flask import jsonify, request
from ..models import PlayerState
from . import api, command


@api.route('/system/shutdown', methods=['POST'])
def shutdown():
    command.publish('musicblocks', 'exit 1')
    player_state = PlayerState.query.one().to_json()
    player_state['active'] = False
    return jsonify(player_state)