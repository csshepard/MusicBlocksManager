from flask_wtf import Form
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SelectField, SubmitField, FieldList, IntegerField, ValidationError
from wtforms.validators import DataRequired
from wtforms.widgets import TableWidget

from ..models import Block


class ChangeSong(Form):
    file = FileField('File', validators=[FileRequired(), FileAllowed(['mp3'], 'Mp3s only')])
    block_number = SelectField('Block #', validators=[DataRequired()], coerce=int)
    song_title = StringField('Song Title', validators=[DataRequired()])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(ChangeSong, self).__init__(*args, **kwargs)
        self.block_number.choices = [(block.number, block.number)
                                     for block in Block.query.order_by(Block.number).all()]


class AdvancedForm(Form):
    shutdown = SubmitField('Shutdown')
    reboot = SubmitField('Reboot')
    block_number = SelectField('Block #', coerce=int)
    delete = SubmitField('Delete Block')

    def __init__(self, *args, **kwargs):
        super(AdvancedForm, self).__init__(*args, **kwargs)
        self.block_number.choices = [(block.number, block.number)
                                     for block in Block.query.order_by(Block.number).all()]


class ReorderForm(Form):
    blocks = FieldList(IntegerField(), validators=[DataRequired()])
    songs = FieldList(StringField(), validators=[DataRequired()])
    submit = SubmitField('Reorder Blocks')

    def validate_blocks(self, fields):
            entries = set([field.data for field in fields])
            if len(entries) != len(fields):
                raise ValidationError("Missing Numbers")
            block_nums = [block.number for block in Block.query.all()]
            for entry in entries:
                if entry not in block_nums:
                    raise ValidationError("{} not a valid block number".format(entry))
