from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired


class InstrumentForm(FlaskForm):
    instrument = SelectField('Instrument', validators=[DataRequired()])
    submitinst = SubmitField('Submit')
