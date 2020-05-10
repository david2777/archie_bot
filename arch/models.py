from enum import Enum, auto
from datetime import datetime, date

from arch import db


class EventID(Enum):
    TEST = auto()
    OTHER = auto()
    EAT = auto()
    MEDICINE = auto()
    CLOMIPRAMINE = auto()
    TRIFEXIS = auto()
    WALK = auto()
    PLAY = auto()
    TRAINING = auto()
    BATH = auto()
    GROOM = auto()
    PEE = auto()
    POOP = auto()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return '<User {} [{}]>'.format(self.id, self.username)


class Dog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    birthday = db.Column(db.Date)
    events = db.relationship('Event', order_by='asc(Event.id)', lazy='dynamic', back_populates='dog')

    def __repr__(self):
        return '<Dog {} [{}]>'.format(self.id, self.name)


class Event(db.Model):
    # Required
    id = db.Column(db.Integer, index=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User')
    dog_id = db.Column(db.Integer, db.ForeignKey('dog.id'))
    dog = db.relationship('Dog', back_populates='events')
    event_id = db.Column(db.Enum(EventID))
    # Optional
    note = db.Column(db.String(128))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    start_time = db.Column(db.DateTime, index=True, default=datetime.now)
    end_time = db.Column(db.DateTime, index=True)
    is_accident = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<Event {} [{}]>'.format(self.id, self.event_id)

    @property
    def event_type(self):
        return self.event_id.name.lower()

    @property
    def event_string(self):
        duration_string = ""
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            s = duration.total_seconds()
            hours, remainder = divmod(s, 3600)
            minutes, seconds = divmod(remainder, 60)
            duration_string = ' - {:01}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))
        return '{0} - {1}{2}'.format(self.event_id.name.capitalize(), self.dog.name, duration_string)

    @property
    def event_info(self):
        return self.note

    @property
    def event_entry(self):
        note_string = ''
        if self.note:
            note_string = ' - {}'.format(self.note)
        nice_time = self.start_time.strftime("%I:%M %p")
        return '{0} @ {1}{2}'.format(self.user.username, nice_time, note_string)


def add_test_data():
    # Users
    db.session.add(User(username='David'))
    db.session.add(User(username='Judy'))

    # Dogs
    db.session.add(Dog(name='Archie', birthday=date.fromtimestamp(1547467200)))

    e = Event(user_id=1, dog_id=1, event_id=EventID.EAT, start_time=datetime.fromtimestamp(15873966000))
    db.session.add(e)

    e = Event(user_id=1, dog_id=1, event_id=EventID.CLOMIPRAMINE, start_time=datetime.fromtimestamp(15873966001))
    db.session.add(e)

    e = Event(user_id=1, dog_id=1, event_id=EventID.WALK, start_time=datetime.fromtimestamp(1587399300),
              end_time=datetime.fromtimestamp(1587400645))
    db.session.add(e)

    e = Event(user_id=1, dog_id=1, event_id=EventID.PEE, start_time=datetime.fromtimestamp(1587399745))
    db.session.add(e)

    e = Event(user_id=1, dog_id=1, event_id=EventID.POOP, start_time=datetime.fromtimestamp(1587399925))
    db.session.add(e)

    e = Event(user_id=1, dog_id=1, event_id=EventID.PLAY, start_time=datetime.fromtimestamp(1587405205),
              end_time=datetime.fromtimestamp(1587406285), note='Played fetch and rope tug')
    db.session.add(e)

    e = Event(user_id=1, dog_id=1, event_id=EventID.PEE, start_time=datetime.fromtimestamp(1587409345),
              is_accident=True)
    db.session.add(e)

    e = Event(user_id=1, dog_id=1, event_id=EventID.BATH, start_time=datetime.fromtimestamp(1587419425))
    db.session.add(e)

    e = Event(user_id=1, dog_id=1, event_id=EventID.GROOM, start_time=datetime.fromtimestamp(1587419425))
    db.session.add(e)

    e = Event(user_id=1, dog_id=1, event_id=EventID.TRAINING, start_time=datetime.fromtimestamp(1587428545),
              end_time=datetime.fromtimestamp(1587430405))
    db.session.add(e)

    db.session.commit()
