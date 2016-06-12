import subprocess
from flask import render_template, redirect, url_for, flash, request, current_app
from werkzeug.utils import secure_filename
from sqlalchemy import func
from . import main
from .forms import ChangeSong, AdvancedForm
from .. import db
from ..models import Block, Song, PlayHistory

@main.route('/', methods=['GET', 'POST'])
def index():
    form = ChangeSong()
    block_numbers = db.session.query(Block.number).order_by(Block.number).all()
    form.block_number.choices = [(block.number, block.number) for block in block_numbers]
    if form.validate_on_submit():
        song_filename = secure_filename(form.file.data.filename)
        song = db.session.query(Song).filter_by(file=song_filename).one_or_none()
        if song is None:
            song = Song(title=form.song_title.data, file=song_filename)
            form.file.data.save(current_app.config['PATH'] + '/Music/%s' % song_filename)
            db.session.add(song)
        else:
            song.title = form.song_title.data
        block = db.session.query(Block).filter_by(number=form.block_number.data).one()
        block.song = song
        db.session.commit()
    counts =  db.session.query(PlayHistory.song_title, func.count('*').\
        label('play_count')).\
        group_by(PlayHistory.song_title).subquery()
    blocks = db.session.query(Block.number, Song.title, counts.c.play_count).join(Song).outerjoin(counts, Song.title == counts.c.song_title).order_by(Block.number).all()
    history = db.session.query(PlayHistory).order_by(PlayHistory.time_played.desc()).limit(10)
    return render_template('index.html', cs_form=form, blocks=blocks, history=history)


@main.route('/advanced', methods=['GET', 'POST'])
def advanced():
    form = AdvancedForm()
    block_numbers = db.session.query(Block.number).order_by(Block.number).all()
    form.block_number.choices = [(block.number, block.number) for block in block_numbers]
    if form.validate_on_submit():
        if form.shutdown.data:
            subprocess.call(['shutdown -h now "System Shutdown from Web"'], shell=True)
            db.session.close()
            flash('System will shutdown now', 'success')
        elif form.reboot.data:
            subprocess.call(['shutdown -r now "System Rebooted from Web"'], shell=True)
            db.session.close()
            flash('System will reboot now', 'success')
        elif form.delete.data:
            block = db.session.query(Block).filter_by(number=form.block_number.data).one()
            db.session.delete(block)
            db.session.commit()
            form.block_number.choices.remove((form.block_number.data, form.block_number.data))
            flash('Block %i deleted' % form.block_number.data, 'success')
    return render_template('advanced.html', form=form)


@main.route('/history')
@main.route('/history/<int:page>')
def history(page=1):
    history = PlayHistory.query.order_by(PlayHistory.time_played.desc()).paginate(page, 10, False)
    return render_template('history.html', history=history)
