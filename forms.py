from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DateField, SelectField, SubmitField, FloatField
from wtforms.validators import DataRequired, NumberRange

class ModuleForm(FlaskForm):
    """Form for adding/editing modules"""
    name = StringField('Module Name', validators=[DataRequired()])
    hours_required = FloatField('Hours Required per Assignment', validators=[DataRequired(), NumberRange(min=0.5)])
    days_before = IntegerField('Days Before Due Date to Submit', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Save Module')

class AssignmentForm(FlaskForm):
    """Form for adding assignments to a module"""
    module_id = IntegerField('Module ID', validators=[DataRequired()])
    name = StringField('Assignment Name', validators=[DataRequired()])
    due_date = DateField('Due Date', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Add Assignment')

class StudyForm(FlaskForm):
    """Form for study settings"""
    # Days of the week settings will be handled via JavaScript
    leave_days = IntegerField('Number of Leave Days', validators=[NumberRange(min=0)], default=0)
    submit = SubmitField('Save Settings')
