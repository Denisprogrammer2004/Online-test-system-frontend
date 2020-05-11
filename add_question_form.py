from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField, IntegerField
from wtforms.validators import DataRequired


class AddQuestionForm(FlaskForm):
    question = StringField('Вопрос', validators=[DataRequired()])
    score = IntegerField('Баллы', validators=[DataRequired()])
    option1 = StringField('Вариант ответа 1', validators=[DataRequired()])
    option1_chb = BooleanField('Верный ответ')
    option2 = StringField('Вариант ответа 2')
    option2_chb = BooleanField('Верный ответ')
    option3 = StringField('Вариант ответа 3')
    option3_chb = BooleanField('Верный ответ')
    option4 = StringField('Вариант ответа 4')
    option4_chb = BooleanField('Верный ответ')
    option5 = StringField('Вариант ответа 5')
    option5_chb = BooleanField('Верный ответ')
    add_quest = SubmitField('Добавить и перейти к следующему')
    complete_quest = SubmitField('Добавить и закончить')