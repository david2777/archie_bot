from arch import app, db
from arch.models import User, Dog, Event, EventType, ActiveEvents, add_test_data


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Dog': Dog, 'Event': Event, 'EventType': EventType, 'ActiveEvents': ActiveEvents,
            't': add_test_data}
