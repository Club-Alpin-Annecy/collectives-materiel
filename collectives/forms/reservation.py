from wtforms import DateField, SubmitField
from flask_wtf.form import FlaskForm
from wtforms.fields.core import IntegerField, SelectField
from wtforms.validators import NumberRange

from ..models.equipment import EquipmentType
from ..models.reservation import Reservation, ReservationLine


class LeaderReservationForm(FlaskForm):
    """Form for leaders to reserve equipment
    Contrary to lambda user, they don't need to pay nor specify a return date
    """

    class Meta:
        model = Reservation

    collect_date = DateField("Date d'emprunt", format="%d/%m/%Y")

    submit = SubmitField("Enregistrer")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)