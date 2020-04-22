from enum import Enum, auto
from datetime import datetime, date

from arch import db


class EventID(Enum):
    TEST = auto()
    OTHER = auto()
    EAT = auto()
    MEDICINE = auto()
    WALK = auto()
    PLAY = auto()
    TRAINING = auto()
    BATH = auto()
    GROOM = auto()
    PEE = auto()
    POOP = auto()

    @property
    def event_color(self):
        return _color_dict.get(self.name, 'gray')


_color_dict = {EventID.PEE.name: 'blue'}


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return '<User {} [{}]>'.format(self.id, self.username)


class Dog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    events = db.relationship('Event', order_by='asc(Event.timestamp)', lazy='dynamic', back_populates='dog')

    def __repr__(self):
        return '<Dog {} [{}]>'.format(self.id, self.name)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User')
    dog_id = db.Column(db.Integer, db.ForeignKey('dog.id'))
    dog = db.relationship('Dog', back_populates='events')
    event_id = db.Column(db.Enum(EventID))
    note = db.Column(db.String(128))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now)
    date = db.Column(db.DateTime, index=True, default=date.today)
    is_accident = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<Event {} [{} @ {}]>'.format(self.id, self.event_id, self.timestamp)

    @property
    def event_type(self):
        return self.event_id.name.lower()

    @property
    def event_string(self):
        return self.event_id.name.capitalize()

    @property
    def event_info(self):
        return self.note

    @property
    def event_entry(self):
        return 'Entered by {0} at {1}'.format(self.user.username, self.timestamp.strftime("%I:%M %p"))
