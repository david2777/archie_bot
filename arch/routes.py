import datetime

import pytz
import flask
from sqlalchemy import or_

from arch import app, models, db, forms
from arch import utils


def log_and_return_error(error, *args, exception=False):
    result = {"success": "false"}
    if exception:
        app.logger.exception(error, *args)
    else:
        app.logger.error(error, *args)
    result['error'] = error % tuple(*args)
    return str(result)


def get_time_in_utc(form):
    date = form.date.data if form.date.data else datetime.date.today()
    tz = pytz.timezone("America/Los_Angeles")
    start_time_utc = None
    end_time_utc = None

    if form.start_time.data:
        start_time = datetime.datetime.combine(date, form.start_time.data)
    else:
        start_time = datetime.datetime.combine(date, datetime.datetime.now().time())

    if form.end_time.data:
        end_time = datetime.datetime.combine(date, form.end_time.data)
    else:
        end_time = None

    if start_time:
        start_time_utc = tz.localize(start_time).astimezone(pytz.utc)
    if end_time:
        end_time_utc = tz.localize(end_time).astimezone(pytz.utc)

    return start_time_utc, end_time_utc


@app.route('/')
@app.route('/index.html')
def index():
    kwargs = {'user': models.User.query.get(1),
              'title': 'Home',
              'time_of_day': utils.get_tod(),
              'today': datetime.date.today().strftime('%m/%d/%Y'),
              'events': models.Event.query.all()}
    return flask.render_template('index.html', **kwargs)


@app.route('/stats.html')
def stats():
    return flask.render_template('stats.html')


@app.route('/edit_event/<event_id>.html', methods=['GET', 'POST'])
def edit_event(event_id):
    event = models.Event.query.get(event_id)
    if not event:
        flask.flash('Cannot find event {} to edit'.format(event_id))
        return flask.redirect(flask.url_for('index'))

    f = forms.EventForm(flask.request.form)
    # Set defaults from the loaded event
    if flask.request.method == 'GET':
        f.user.data = event.user_id
        f.dog.data = [d.dog_id for d in event.dogs]
        f.event.data = event.event_type_id
        if event.start_time_local:
            f.date.data = event.start_time_local.date()
            f.start_time.data = event.start_time_local.time()
        if event.end_time_local:
            f.end_time.data = event.end_time_local.time()
        f.note.data = event.note
        f.accident.data = event.is_accident

    if f.validate_on_submit():
        app.logger.info('Submission Validated')
        start_time_utc, end_time_utc = get_time_in_utc(f)
        event.user_id = int(f.user.data)
        event.event_type_id = f.event.data
        event.start_time = start_time_utc
        event.end_time = end_time_utc
        event.note = f.note.data if f.note.data else None
        event.is_accident = f.accident.data

        dogs = models.Dog.query.filter(models.Dog.dog_id.in_(tuple(f.dog.data)))
        event.dogs = list(dogs)

        db.session.commit()

        flask.flash('Edited Event: {}'.format(event.event_id))
        return flask.redirect(flask.url_for('index'))

    return flask.render_template('edit_event.html', form=f, event=event)


@app.route('/delete_event/<event_id>.html', methods=['GET', 'POST'])
def delete_event(event_id):
    event = models.Event.query.get(event_id)
    if not event:
        flask.flash('Cannot find event {} to delete'.format(event_id))
        return flask.redirect(flask.url_for('index'))
    if flask.request.method == 'POST':
        db.session.delete(event)
        db.session.commit()
        flask.flash('Deleted event {}'.format(event_id))
        return flask.redirect(flask.url_for('index'))
    return flask.render_template('delete_event.html', event=event)


@app.route('/add_event.html', methods=['GET', 'POST'])
def add_event():
    f = forms.EventForm(flask.request.form)
    if f.validate_on_submit():
        app.logger.info('Submission Validated')
        
        start_time_utc, end_time_utc = get_time_in_utc(f)

        e = models.Event(user_id=int(f.user.data),
                         event_type_id=f.event.data,
                         start_time=start_time_utc,
                         end_time=end_time_utc,
                         note=f.note.data if f.note.data else None,
                         is_accident=f.accident.data)

        dogs = models.Dog.query.filter(models.Dog.dog_id.in_(tuple(f.dog.data)))
        e.dogs = list(dogs)

        db.session.add(e)
        db.session.commit()

        flask.flash('Submitted Event: {}'.format(e.event_id))
        return flask.redirect(flask.url_for('index'))

    return flask.render_template('add_event.html', form=f)


@app.route('/add_event_webhook.html', methods=['POST', 'GET'])
def add_event_webhook():
    if flask.request.method == 'GET':
        return '<h1>This is a simple webhook for adding events</h1>'

    # Get JSON Data
    try:
        data = flask.request.get_json()
    except Exception:
        return log_and_return_error("Bad JSON Data", exception=True)

    # If no JSON data, try args
    if not data:
        data = flask.request.args
        if not data:
            return log_and_return_error('No Data Passed')

    # Check for required user inputs
    try:
        user = data['user']
    except KeyError:
        return log_and_return_error("No 'user' value passed")

    try:
        dog = data['dog']
    except KeyError:
        return log_and_return_error("No 'dog' value passed")

    try:
        event = data['event']
    except KeyError:
        return log_and_return_error("No 'event' value passed")

    # Resolve User
    try:
        or_filter = or_(models.User.username == user or models.User.user_id == user)
        user_search = models.User.query.filter(or_filter).all()
    except Exception:
        return log_and_return_error("Bad query for user with '%s'", user, exception=True)

    if not user_search:
        return log_and_return_error("Could not resolve User from '%s'", user)
    elif len(user_search) > 1:
        return log_and_return_error("Found more than one User for '%s'", user)
    else:
        user_object = user_search[0]

    # Resolve Dog
    try:
        or_filter = or_(models.Dog.name == dog or models.Dog.dog_id == dog)
        dog_search = models.Dog.query.filter(or_filter).all()
    except Exception:
        return log_and_return_error("Bad query for dog with '%s'", dog, exception=True)

    if not dog_search:
        return log_and_return_error("Could not resolve Dog from '%s'", dog)
    elif len(dog_search) > 1:
        return log_and_return_error("Found more than one Dog for '%s'", dog)
    else:
        dog_object = dog_search[0]

    # Resolve Event ID
    event_type = models.EventType.query.get(event)
    if not event_type:
        return log_and_return_error("Unable to resolve EventType from '%s'", event)

    # Get remainder of user data
    event_data = {'user': user_object,
                  'dog': dog_object,
                  'event_type': event_type}

    for check in ['note', 'timestamp', 'start_time', 'end_time', 'is_accident']:
        try:
            event_data[check] = data[check]
        except KeyError:
            pass

    # Create event and add to database
    event = models.Event(**event_data)

    db.session.add(event)
    db.session.commit()

    app.logger.info(event)
    return str({"success": "true", "event_id": event.event_id})
