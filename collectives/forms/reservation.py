from datetime import datetime, timedelta
from wtforms import SubmitField
from flask_wtf.form import FlaskForm
from wtforms_alchemy import ModelForm
from ..models.reservation import Reservation


class LeaderReservationForm(FlaskForm, ModelForm):
    """Form for leaders to reserve equipment
    Contrary to lambda user, they don't need to pay nor specify a return date
    """

    class Meta:
        model = Reservation
        include = ["collect_date"]

    submit = SubmitField("Enregistrer")
    event = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = kwargs["obj"]
        self.collect_date.data = (self.event.start).replace(
            hour=(datetime.now() + timedelta(hours=1)).hour,
            minute=0,
        )
