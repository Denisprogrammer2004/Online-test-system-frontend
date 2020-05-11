from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField
from wtforms.validators import DataRequired


class SelectTestForm(FlaskForm):
    tests = SelectField("Выбери тест", coerce=int, validators=[DataRequired()])
    submit = SubmitField('Начать')