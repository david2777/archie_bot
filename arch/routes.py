import datetime

import flask
from sqlalchemy import or_

from arch import app, models, db, forms
from arch import utils


@app.route('/')
@app.route('/index.html')
def index():
    kwargs = {'user': models.Users.query.get(1),
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
        f.dog.data = [d.id for d in event.dogs]
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
        start_time_utc, end_time_utc = utils.get_time_in_utc(f)
        event.user_id = int(f.user.data)
        event.event_type_id = f.event.data
        event.start_time = start_time_utc
        event.end_time = end_time_utc
        event.note = f.note.data if f.note.data else None
        event.is_accident = f.accident.data

        dogs = models.Dog.query.filter(models.Dog.id.in_(tuple(f.dog.data)))
        event.dogs = list(dogs)

        db.session.commit()

        flask.flash('Edited Event: {}'.format(event.id))
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
    f.dog.data = [d[0] for d in f.dog_list]
    if f.validate_on_submit():
        app.logger.info('Submission Validated')
        
        start_time_utc, end_time_utc = utils.get_time_in_utc(f)

        e = models.Event(user_id=f.user.data,
                          event_type_id=f.event.data,
                          start_time=start_time_utc,
                          end_time=end_time_utc,
                          note=f.note.data if f.note.data else None,
                          is_accident=f.accident.data)

        dogs = models.Dog.query.filter(models.Dog.id.in_(tuple(f.dog.data)))
        e.dogs = list(dogs)

        db.session.add(e)
        db.session.commit()

        flask.flash('Submitted Event: {}'.format(e.id))
        return flask.redirect(flask.url_for('index'))

    return flask.render_template('add_event.html', form=f)


@app.route('/start_walk.html')
def start_walk():
    walk = models.ActiveEvent.get_walk()
    if walk:
        flask.flash('There is already an active walk in progress...')
    else:
        flask.flash('Stared active walk')
    return flask.redirect(flask.url_for('index'))


@app.route('/add_event_webhook.html', methods=['POST', 'GET'])
def add_event_webhook():
    if flask.request.method == 'GET':
        return '<h1>This is a simple webhook for adding events</h1>'

    # Get JSON Data
    try:
        data = flask.request.get_json()
    except Exception:
        return utils.log_and_return_error("Bad JSON Data", exception=True)

    # If no JSON data, try args
    if not data:
        data = flask.request.args
        if not data:
            return utils.log_and_return_error('No Data Passed')

    # Create event and add to database
    event = models.Event(**data)

    if isinstance(event, int):
        db.session.rollback()
        return utils.log_and_return_error('Error generating event')

    db.session.add(event)
    db.session.commit()

    app.logger.info(event)
    return str({"success": "true", "event_id": event.id})
