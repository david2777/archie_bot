from arch import app, db
from arch.models import User, Dog, Event, EventEnum, add_test_data


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Dog': Dog, 'Event': Event, 'EventEnum': EventEnum, 't': add_test_data}
