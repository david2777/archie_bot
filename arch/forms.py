import datetime

import wtforms
from wtforms import validators
from wtforms.fields import html5
from flask_wtf import FlaskForm

from arch import models


class EventForm(FlaskForm):
    try:
        user_list = [(u.id, u.username) for u in models.Users.query.all()]
    except Exception:
        user_list = []

    try:
        dog_list = [(d.id, d.name) for d in models.Dog.query.all()]
    except Exception:
        dog_list = []

    try:
        event_type_list = [(i.id, i.name.capitalize()) for i in models.EventType.query.all()]
    except Exception:
        event_type_list = []

    # TODO: Default get current user
    user = wtforms.SelectField('User', choices=user_list, coerce=int, validators=[validators.data_required()])
    dog = wtforms.SelectMultipleField('Dog', choices=dog_list, coerce=int, validators=[validators.data_required()])
    event = wtforms.SelectField('Event', choices=event_type_list, coerce=int)
    date = html5.DateField('Date', validators=[validators.Optional()], default=datetime.date.today)
    start_time = html5.TimeField('Start Time', validators=[validators.Optional()], default=datetime.datetime.now())
    end_time = html5.TimeField('End Time', validators=[validators.Optional()], default=None)
    note = wtforms.StringField('Note', default=None)
    accident = wtforms.BooleanField('Accident?')
    submit = wtforms.SubmitField('Submit')
