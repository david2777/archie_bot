from datetime import date

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


@app.route('/')
@app.route('/index.html')
def index():
    events = [e for e in models.Event.query.all() if e.display]
    kwargs = {'user': models.User.query.get(1),
              'title': 'Home',
              'time_of_day': utils.get_tod(),
              'today': date.today().strftime('%m/%d/%Y'),
              'events': events}
    return flask.render_template('index.html', **kwargs)


@app.route('/stats.html')
def stats():
    return flask.render_template('stats.html')


@app.route('/edit_event/<event_id>.html')
def edit_event(event_id):
    event = models.Event.query.get(event_id)
    return flask.render_template('edit_event.html', event=event)


@app.route('/add_event.html', methods=['GET', 'POST'])
def add_event():
    f = forms.AddEventForm(flask.request.form)
    if f.validate_on_submit():
        app.logger.info('Submission Validated')

        e = models.Event(user_id=int(f.user.data),
                         event_enum=models.EventEnum[f.event.data],
                         start_time=f.start_time.data if f.start_time.data else None,
                         end_time=f.end_time.data if f.end_time.data else None,
                         note=f.note.data if f.note.data else None,
                         is_accident=f.accident.data)

        dogs = models.Dog.query.filter(models.Dog.dog_id.in_(tuple(f.dog.data)))
        e.dogs += dogs

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
    try:
        event_enum = models.EventEnum(int(event))
    except ValueError:
        try:
            event_enum = models.EventEnum[event]
        except KeyError:
            return log_and_return_error("Unable to resolve EventEnum from '%s'", event)

    # Get remainder of user data
    event_data = {'user': user_object,
                  'dog': dog_object,
                  'event_enum': event_enum}

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
