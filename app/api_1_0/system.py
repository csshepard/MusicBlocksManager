from flask import jsonify, request
from . import api, red


@api.route('/system/shutdown', methods=['POST'])
def shutdown():
    red.publish('musicblocks', 'exit')
    return redirect(url_for('.player_state'))
