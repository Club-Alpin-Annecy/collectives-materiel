from wtforms import SubmitField
from flask_wtf.form import FlaskForm
from wtforms_alchemy import ModelForm

from ..models.reservation import Reservation


class LeaderReservationForm(ModelForm, FlaskForm):
    """Form for leaders to reserve equipment
    Contrary to lambda user, they don't need to pay nor specify a return date
    """

    class Meta:
        model = Reservation
        include = ["collect_date"]

    submit = SubmitField("Enregistrer")
