from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectMultipleField, widgets
from wtforms.validators import DataRequired


class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """

    widget = widgets.ListWidget(html_tag='ol', prefix_label=False)
    option_widget = widgets.CheckboxInput()


class DisplayTestForm(FlaskForm):
    options = MultiCheckboxField("Варианты ответа:", coerce=int, validators=[DataRequired()])
    submit = SubmitField('Ответить')


