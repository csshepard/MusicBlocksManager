from flask_wtf import Form
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired


class ChangeSong(Form):
    file = FileField('File', validators=[FileRequired(), FileAllowed(['mp3'], 'Mp3s only')])
    block_number = SelectField('Block #', validators=[DataRequired()], coerce=int)
    song_title = StringField('Song Title', validators=[DataRequired()])
    submit = SubmitField('Submit')


class AdvancedForm(Form):
    shutdown = SubmitField('Shutdown')
    reboot = SubmitField('Reboot')
    block_number = SelectField('Block #', coerce=int)
    delete = SubmitField('Delete Block')
