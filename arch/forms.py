import wtforms
from wtforms import validators
from wtforms.fields import html5
from flask_wtf import FlaskForm

from arch import models


class AddEventForm(FlaskForm):
    user = wtforms.SelectField('User', choices=[('1', 'David'), ('2', 'Judy')])
    dog = wtforms.SelectMultipleField('Dog', choices=[('1', 'Archie'), ('2', 'EvilArchie')])
    all_dog_checkbox = wtforms.BooleanField()
    choices = [(str(i.name), str(i.name).capitalize()) for i in models.EventID]
    event = wtforms.SelectField('Event', choices=choices)
    start_time = html5.TimeField('Start Time', validators=[validators.Optional()])
    end_time = html5.TimeField('End Time', validators=[validators.Optional()])
    accident = wtforms.BooleanField('Accident?')
    note = wtforms.StringField('Note', default=None)
    submit = wtforms.SubmitField('Add Event')
