from datetime import datetime, timedelta
from wtforms import SubmitField, DateTimeField
from flask_wtf.form import FlaskForm

from ..models.reservation import Reservation


class LeaderReservationForm(FlaskForm):
    """Form for leaders to reserve equipment
    Contrary to lambda user, they don't need to pay nor specify a return date
    """

    class Meta:
        model = Reservation
        include = ["collect_date"]

    submit = SubmitField("Enregistrer")
    collect_date = DateTimeField("Date")
    event = None
    # lines = FieldList(FormList(ReservationLineForm))
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = kwargs["obj"]
        self.collect_date.data = (self.event.start).replace(
            hour=(datetime.now() + timedelta(hours=1)).hour,
            minute=0,
        )
