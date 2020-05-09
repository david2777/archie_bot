from datetime import date

from flask import render_template, request, jsonify
from sqlalchemy import or_

from arch import app, models, db
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
    user = models.User.query.get(1)

    data = {}
    dogs = models.Dog.query.all()
    for d in dogs:
        events = d.events.all()
        data[d] = events

    kwargs = {'user': user,
              'title': 'Home',
              'time_of_day': utils.get_tod(),
              'today': date.today().strftime('%m/%d/%Y'),
              'data': data}

    return render_template('index.html', **kwargs)


@app.route('/edit_event/<event_id>.html')
def edit_event(event_id):
    event = models.Event.query.get(event_id)
    return render_template('edit_event.html', event=event)


@app.route('/add_event.html')
def add_event():
    return render_template('add_event.html')


@app.route('/add_event_webhook.html', methods=['POST', 'GET'])
def add_event_webhook():
    if request.method == 'GET':
        return '<h1>This is a simple webhook for adding events</h1>'

    # Get JSON Data
    try:
        data = request.get_json()
    except Exception:
        return log_and_return_error("Bad JSON Data", exception=True)

    # If no JSON data, try args
    if not data:
        data = request.args
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
        or_filter = or_(models.User.username == user or models.User.id == user)
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
        or_filter = or_(models.Dog.name == dog or models.Dog.id == dog)
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
        event_id = models.EventID(int(event))
    except ValueError:
        try:
            event_id = models.EventID[event]
        except KeyError:
            return log_and_return_error("Unable to resolve EventID from '%s'", event)

    # Get remainder of user data
    event_data = {'user': user_object,
                  'dog': dog_object,
                  'event_id': event_id}

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
    return str({"success": "true", "event_id": event.id})
