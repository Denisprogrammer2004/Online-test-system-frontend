from flask_wtf import FlaskForm
from wtforms import SubmitField


class TestResultForm(FlaskForm):
    submit = SubmitField('Вернуться к списку тестов')
