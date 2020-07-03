import datetime

import pytz

from arch import db

dog_to_event = db.Table('dog_to_event_table',  #: Association Table to connect Dog with Event objects
                        db.Column('event_id', db.Integer, db.ForeignKey('events.event_id')),
                        db.Column('dog_id', db.Integer, db.ForeignKey('dogs.dog_id')))


class ActiveEvents(db.Model):
    """Active Events Table

    Attributes:
        id (int): Primary Key (Unique)
        event_id (int): Active Event Item ID
        event (Event): Active Event Item

    """
    __tablename__ = 'active_events'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.event_id'))
    event = db.relationship('Event', lazy='joined', join_depth=3)

    @classmethod
    def get_walk(cls):
        return cls.query.\
            join(cls.event, aliased=True).\
            join(Event.event_type, aliased=True).\
            filter_by(name='WALK').\
            first()

    @classmethod
    def add_walk(cls, event):
        if event.event_type.name == 'WALK' and not ActiveEvents.get_active_walk():
            record = cls(event=event)
            db.session.add(record)
            db.session.commit()
            return record

    @classmethod
    def clear_walk(cls):
        event = ActiveEvents.get_active_walk()
        if event:
            db.session.delete(event)
            db.session.commit()


class EventType(db.Model):
    """Event Type Table

    Attributes:
        id (int): Primary Key (Unique)
        name (str): Value (Unique)

    """
    __tablename__ = 'event_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)

    def __repr__(self):
        return '<EventType {} [{}]>'.format(self.id, self.name)


class User(db.Model):
    """User Table

    Attributes:
        user_id (int): Primary Key (Unique)
        username (str): User Name (Unique) (Max 64)
        password_hash (str): User Password Hash (max 128)

    """
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return '<User {} [{}]>'.format(self.user_id, self.username)


class Dog(db.Model):
    """Dog Table

    Attributes:
        dog_id (int): Primary Key (Unique)
        name (str): Dog's Name (Unique) (Max 64)
        birthday (date): Dog's Birthday

    """
    __tablename__ = 'dogs'
    dog_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    birthday = db.Column(db.Date)

    def __repr__(self):
        return '<Dog {} [{}]>'.format(self.dog_id, self.name)


class Event(db.Model):
    """Event Table

    Attributes:
        event_id (int): Primary Key (Unique)
        user_id (int): User ID of the user associated with the event
        user (User): User object of the user associated with the event
        dogs (list of Dog): List of Dog objects associated with the event
        event_type_id (int): ID for the Event Type for this event
        event_type (EventType): Event Type Object for this event
        note (str): Note for the event
        start_time (DateTime): Start time of the event in UTC
        end_time (DateTime): End time for the event in UTC
        is_accident (bool): Boolean if the event is an accident or not

    """
    __tablename__ = 'events'
    # Required
    event_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    user = db.relationship('User')
    dogs = db.relationship('Dog', secondary=dog_to_event)
    event_type_id = db.Column(db.Integer, db.ForeignKey('event_types.id'))
    event_type = db.relationship('EventType')
    # Optional
    note = db.Column(db.String(128))
    start_time = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    end_time = db.Column(db.DateTime)
    is_accident = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<Event {} [{}]>'.format(self.event_id, self.event_type.name)

    @property
    def start_time_local(self):
        """Returns the start_time in local time (default Los Angeles).

        Returns:
            datetime.datetime: start_time attribute converted to local time

        """
        if self.start_time:
            tz = pytz.timezone("America/Los_Angeles")
            utc = pytz.timezone('UTC')
            value = utc.localize(self.start_time, is_dst=None).astimezone(pytz.utc)
            return value.astimezone(tz)

    @property
    def end_time_local(self):
        """Returns the end_time in local time (default Los Angeles).

        Returns:
            datetime.datetime: end_time attribute converted to local time

        """
        if self.end_time:
            tz = pytz.timezone("America/Los_Angeles")
            utc = pytz.timezone('UTC')
            value = utc.localize(self.end_time, is_dst=None).astimezone(pytz.utc)
            return value.astimezone(tz)

    @property
    def event_string(self):
        """Returns a formatted string where '$Event - $Dogs $Duration' where $Duration is if the event has a start_time
        and an end_time. Eg 'Walk - Archie, Evil Archie - 0:30:00' or 'Pee - Archie'. Used for event_time partial
        template.

        Returns:
            str: Event header info string

        """
        duration_string = ""
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            s = duration.total_seconds()
            hours, remainder = divmod(s, 3600)
            minutes, seconds = divmod(remainder, 60)
            duration_string = ' - {:01}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))
        dogs = ', '.join([d.name for d in self.dogs])
        return '{0} - {1}{2}'.format(self.event_type.name.capitalize(), dogs, duration_string)

    @property
    def event_entry(self):
        """Returns a formatted string where '$User @ $LocalTime - $Note'. Eg 'David @ 09:00 AM' or
        'Judy @ 11:50 AM - Played fetch and rope tug'. Used in event_item partial template.

        Returns:
            str: Event entry info string

        """
        note_string = ''
        if self.note:
            note_string = ' - {}'.format(self.note)
        nice_time = self.start_time_local.strftime("%I:%M %p")
        return '{0} @ {1}{2}'.format(self.user.username, nice_time, note_string)


def add_test_data():
    """Basic function for seeding the database.

    TODO:
        Clean this up

    Returns:
        None

    """
    t = datetime.datetime.utcfromtimestamp

    # Users
    david = User(username='David')
    db.session.add(david)

    judy = User(username='Judy')
    db.session.add(judy)

    # Dogs
    archie = Dog(name='Archie', birthday=t(1547467200))
    db.session.add(archie)

    evil_archie = Dog(name='Evil Archie', birthday=t(1547467200))
    db.session.add(evil_archie)

    # Event Types
    event_types = [0]
    for et in ['TEST',  # 1
               'OTHER',  # 2
               'EAT',  # 3
               'MEDICINE',  # 4
               'CLOMIPRAMINE',  # 5
               'TRIFEXIS',  # 6
               'WALK',  # 7
               'PLAY',  # 8
               'TRAINING',  # 9
               'BATH',  # 10
               'GROOM',  # 11
               'PEE',  # 12
               'POOP']:  # 13
        e = EventType(name=et)
        db.session.add(e)
        event_types.append(e)

    # Events
    e = Event(user=david, event_type=event_types[3], start_time=t(1587398400))
    e.dogs.append(archie)
    e.dogs.append(evil_archie)
    db.session.add(e)

    e = Event(user=david, event_type=event_types[5], start_time=t(1587398400))
    e.dogs.append(archie)
    e.dogs.append(evil_archie)
    db.session.add(e)

    e = Event(user=david, event_type=event_types[7], start_time=t(1587400200), end_time=t(1587402000))
    e.dogs.append(archie)
    e.dogs.append(evil_archie)
    db.session.add(e)

    e = Event(user=david, event_type=event_types[12], start_time=t(1587401100))
    e.dogs.append(archie)
    db.session.add(e)

    e = Event(user=david, event_type=event_types[13], start_time=t(1587401400))
    e.dogs.append(evil_archie)
    db.session.add(e)

    e = Event(user=judy, event_type=event_types[8], start_time=t(1587408600), end_time=t(1587409920),
              note='Played fetch and rope tug')
    e.dogs.append(archie)
    db.session.add(e)

    e = Event(user=judy, event_type=event_types[12], start_time=t(1587409980), is_accident=True)
    e.dogs.append(evil_archie)
    db.session.add(e)

    e = Event(user=judy, event_type=event_types[10], start_time=t(1587415980))
    e.dogs.append(evil_archie)
    db.session.add(e)

    e = Event(user=judy, event_type=event_types[11], start_time=t(1587419580))
    e.dogs.append(evil_archie)
    db.session.add(e)

    e = Event(user=judy, event_type=event_types[9], start_time=t(1587421980), end_time=t(1587423720), note='Stay')
    e.dogs.append(archie)
    db.session.add(e)

    db.session.commit()
