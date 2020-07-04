from arch import app, db, models
from arch.models import Users, Dog, Event, EventType, ActiveEvent


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Users': Users, 'Dog': Dog, 'Event': Event, 'EventType': EventType,
            'ActiveEvent': ActiveEvent, 'models': models}
