from datetime import date

from flask import render_template, request
from sqlalchemy import func

from arch import app, models
from arch import utils


@app.route('/')
@app.route('/index.html')
def index():
    user = models.User.query.get(1)

    data = {}
    dogs = models.Dog.query.all()
    for d in dogs:
        events = d.events.filter(func.DATE(models.Event.date == date.today())).all()
        data[d] = events

    kwargs = {'user': user,
              'title': 'Home',
              'time_of_day': utils.get_tod(),
              'data': data}

    return render_template('index.html', **kwargs)


@app.route('/edit_event/<event_id>.html')
def edit_event(event_id):
    event = models.Event.query.get(event_id)
    return render_template('edit_event.html', event=event)


@app.route('/add_event.html')
def add_event():
    return render_template('add_event.html')


@app.route('/webhook.html', methods=['POST'])
def webhook():
    data = request.get_json()
    print(data)
    return '{"success":"true"}'
