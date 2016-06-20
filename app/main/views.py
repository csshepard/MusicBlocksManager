import subprocess
from flask import url_for, render_template, redirect, flash, current_app
from werkzeug.utils import secure_filename
from sqlalchemy import func
from . import main
from .forms import ChangeSong, AdvancedForm, ReorderForm
from .. import db
from ..models import Block, Song, PlayHistory


@main.route('/', methods=['GET', 'POST'])
def index():
    counts = db.session.query(PlayHistory.song_title, func.count('*').
                              label('play_count')).\
        group_by(PlayHistory.song_title).subquery()
    blocks = db.session.query(Block.number, Song.title, counts.c.play_count).\
        join(Song).outerjoin(counts, Song.title == counts.c.song_title).order_by(Block.number).all()
    history_10 = PlayHistory.query.order_by(PlayHistory.time_played.desc()).limit(10)
    return render_template('index.html', blocks=blocks, history=history_10)


@main.route('/advanced', methods=['GET', 'POST'])
def advanced():
    form = AdvancedForm()
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
            flash('Block %i deleted' % form.block_number.data, 'success')
        return redirect(url_for('.advanced'))
    return render_template('advanced.html', form=form)


@main.route('/history')
@main.route('/history/<int:page>')
def history(page=1):
    history_pagination = PlayHistory.query.order_by(PlayHistory.time_played.desc()).paginate(page, 10, False)
    return render_template('history.html', history=history_pagination)


@main.route('/manage', methods=['GET', 'POST'])
def manage():
    cs_form = ChangeSong()
    if cs_form.validate_on_submit():
        song_filename = secure_filename(cs_form.file.data.filename)
        song = Song.query.filter_by(file=song_filename).one_or_none()
        if song is None:
            song = Song(title=cs_form.song_title.data, file=song_filename)
            cs_form.file.data.save(current_app.config['MUSICBLOCKS_DIRECTORY'] + song_filename)
            db.session.add(song)
        else:
            song.title = cs_form.song_title.data
        block = Block.query.filter_by(number=cs_form.block_number.data).one()
        block.song = song
        db.session.add(block)
        db.session.commit()
        return redirect(url_for('.manage'))
    ro_form = ReorderForm()
    if ro_form.validate_on_submit():
        while len(ro_form.blocks):
            block = Block.query.filter_by(number=ro_form.blocks.pop_entry().data).one()
            song = Song.query.filter_by(title=ro_form.songs.pop_entry().data).one()
            if block.song != song:
                block.song = song
                db.session.add(block)
        db.session.commit()
        return redirect(url_for('.manage'))
    blocks = Block.query.order_by(Block.number).all()
    for block in blocks:
        ro_form.blocks.append_entry(data=block.number)
        ro_form.songs.append_entry(data=block.song.title)
    return render_template('manage.html', blocks=blocks, ro_form=ro_form, cs_form=cs_form)
