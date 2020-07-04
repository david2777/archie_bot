import os
import datetime

import pytz
from sqlalchemy import or_

import arch
from arch import app, db

dog_to_event = db.Table('dog_to_event_table',  #: Association Table to connect Dog with Event objects
                        db.Column('event_id', db.Integer, db.ForeignKey('events.id')),
                        db.Column('dog_id', db.Integer, db.ForeignKey('dogs.id')))


class ActiveEvent(db.Model):
    """Active Event Table

    Attributes:
        id (int): Primary Key (Unique)
        event_id (int): Active Event Item ID
        event (Event): Active Event Item

    """
    __tablename__ = 'active_events'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    event = db.relationship('Event')

    @classmethod
    def get_walk(cls):
        return cls.query.\
            join(cls.event, aliased=True).\
            join(Event.event_type, aliased=True).\
            filter_by(name='WALK').\
            first()

    @classmethod
    def add_walk(cls, event):
        if event.event_type.name == 'WALK' and not ActiveEvent.get_active_walk():
            record = cls(event=event)
            db.session.add(record)
            db.session.commit()
            return record

    @classmethod
    def clear_walk(cls):
        event = ActiveEvent.get_active_walk()
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


class Users(db.Model):
    """User Table

    Attributes:
        id (int): Primary Key (Unique)
        username (str): User Name (Unique) (Max 64)
        password_hash (str): User Password Hash (max 128)

    """
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return '<User {} [{}]>'.format(self.id, self.username)


class Dog(db.Model):
    """Dog Table

    Attributes:
        id (int): Primary Key (Unique)
        name (str): Dog's Name (Unique) (Max 64)
        birthday (date): Dog's Birthday

    """
    __tablename__ = 'dogs'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    birthday = db.Column(db.Date)

    def __repr__(self):
        return '<Dog {} [{}]>'.format(self.id, self.name)


class Event(db.Model):
    """Event Table

    Attributes:
        id (int): Primary Key (Unique)
        user_id (int): User ID of the user associated with the event
        user (Users): User object of the user associated with the event
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
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('Users')
    dogs = db.relationship('Dog', secondary=dog_to_event)
    event_type_id = db.Column(db.Integer, db.ForeignKey('event_types.id'))
    event_type = db.relationship('EventType')
    # Optional
    note = db.Column(db.String(128))
    start_time = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    end_time = db.Column(db.DateTime)
    is_accident = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<Event {} [{}]>'.format(self.id, self.event_type.name)

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

    @staticmethod
    def event_factory(**kwargs):
        data = {}
        # Check inputs for required fields
        try:
            user = kwargs['user']
        except KeyError:
            app.logger.error("No 'user' value passed")
            return -2

        try:
            dogs = kwargs['dogs']
        except KeyError:
            dogs = None

        try:
            event_type = kwargs['event_type']
        except KeyError:
            app.logger.error("No 'event' value passed")
            return -4

        # Resolve User
        try:
            _user = Users.query.filter(or_(Users.username == user, Users.id == user)).first()
        except Exception:
            app.logger.exception("Bad query for user with '%s'", user)
            return -5

        if not _user:
            app.logger.error("Could not resolve User from '%s'", user)
            return -5
        else:
            data['user'] = _user

        # Resolve Dog
        if dogs is None:
            data['dogs'] = Dog.query.all()
        else:
            for d in dogs:
                try:
                    _dog = Dog.query.filter(or_(Dog.name == d, Dog.id == d)).first()
                except Exception:
                    app.logger.exception("Bad query for dog with '%s'", d)
                    return -6

                if not _dog:
                    app.logger.error("Could not resolve Dog from '%s'", d)
                    return -6
                else:
                    try:
                        data['dogs'].append(_dog)
                    except KeyError:
                        data['dogs'] = [_dog]

        # Resolve Event Type
        _event_type = EventType.query.filter(or_(EventType.name == event_type, EventType.id == event_type)).first()
        if not _event_type:
            app.logger.error("Unable to resolve EventType from '%s'", event_type)
            return -7
        data['event_type'] = _event_type

        # Resolve other possible flags
        for arg in ['note', 'is_accident']:
            try:
                data[arg] = kwargs[arg]
            except KeyError:
                pass

        for t_arg in ['start_time', 'end_time']:
            try:
                t_data = kwargs[t_arg]
                if isinstance(t_data, int):
                    t_data = datetime.datetime.utcfromtimestamp(t_data)
                data[t_arg] = t_data
            except KeyError:
                pass

        # Instantiate and return
        try:
            ins = Event(**data)
        except Exception:
            app.logger.exception("Instantiation Error")
            return -1
        return ins


def _convert_times(data):
    """Check and convert datetime attrs from seed_data.yml

    Args:
        data (dict): Dict with datetime attrs (eg Dog, Event)

    Returns:
        dict: Data with datetime attrs converted from ints to datetime objects.

    """
    checks = ['birthday', 'start_time', 'end_time']
    for k, v in data.items():
        if k in checks:
            data[k] = datetime.datetime.utcfromtimestamp(v)
    return data


def clear_db():
    """Convenience function to drop all tables.

    Returns:
        None

    """
    for model in [Event, EventType, Dog, Users, ActiveEvent]:
        db.session.query(model).delete()
    db.session.commit()


def seed_db():
    """Basic function for seeding the database.

    Returns:
        None

    """
    import yaml

    app.logger.info('Seeding DB')
    if Users.query.first() or Dog.query.first() or EventType.query.first() or Event.query.first():
        app.logger.info('One or more DBs is not empty, un able to seed.')
        return

    test_data_path = os.path.join(os.path.split(os.path.split(arch.__file__)[0])[0], 'seed_data.yml')
    app.logger.info('Loading data from %s', test_data_path)
    with open(test_data_path) as f:
        data = yaml.safe_load(f)

    app.logger.info('Adding Users')
    for user in data['Users']:
        _data = data['Users'][user]
        u = Users(**_data)
        db.session.add(u)

    app.logger.info('Adding Dog')
    for dog in data['Dog']:
        _data = data['Dog'][dog]
        _data = _convert_times(_data)
        d = Dog(**_data)
        db.session.add(d)

    app.logger.info('Adding Event Types')
    for event_type in data['EventType']:
        et = EventType(name=event_type)
        db.session.add(et)

    app.logger.info('Adding Event')
    for event in data['Event']:
        _data = data['Event'][event]
        e = Event.event_factory(**_data)
        if not isinstance(e, int):
            app.logger.info('%s', e)
            db.session.add(e)

    app.logger.info('Committing DB')
    db.session.commit()
    app.logger.info('Done!')
