from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired
from wtforms.fields.html5 import DateField


class ByDateForm(FlaskForm):
    instrument = SelectField('Instrument', validators=[DataRequired()])
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[DataRequired()])
    result = SelectMultipleField('Test Result', choices=[('pass', 'pass'), ('fail', 'fail')],
                                 default=['pass', 'fail'], validators=[DataRequired()])
    submitbydate = SubmitField('Submit')


class BySerialNumberForm(FlaskForm):
    instrument = SelectField('Instrument', validators=[DataRequired()])
    serial_number = StringField('Serial Number', validators=[DataRequired()])
    submitbysn = SubmitField('Submit')

