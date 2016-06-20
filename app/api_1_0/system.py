from flask import redirect, url_for
from . import api, red


@api.route('/system/shutdown', methods=['POST'])
def shutdown():
    red.publish('musicblocks', 'exit')
    return redirect(url_for('.player_state'))
