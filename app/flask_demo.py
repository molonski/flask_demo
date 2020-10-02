from app import create_app, db
from app.main.models import Instrument, TestLog, SensorResult
from app.auth.models import ArtiWebUser


app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'Instrument': Instrument,
        'Testlog': TestLog,
        'Sensorresult': SensorResult,
        'User': ArtiWebUser
        }
