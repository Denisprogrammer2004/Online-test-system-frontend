from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField, SelectField
from wtforms.validators import DataRequired


class TeacherForm(FlaskForm):
    tests = SelectField("Список тестов", coerce=int, validators=[DataRequired()])
    add_test = SubmitField('Добавить тест')
    edit_test = SubmitField('Редактировать тест')
