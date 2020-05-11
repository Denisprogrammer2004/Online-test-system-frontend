from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class AddTestForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    subject = StringField('Предмет', validators=[DataRequired()])
    group = StringField('Класс', validators=[DataRequired()])
    add_test = SubmitField('Добавить')