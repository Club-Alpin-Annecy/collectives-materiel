from datetime import datetime
from flask_login import current_user
from wtforms import SubmitField, HiddenField

from flask_wtf.form import FlaskForm
from wtforms_alchemy import ModelForm
from ..models.reservation import Reservation
from ..models.user import User


class ReservationForm(FlaskForm, ModelForm):
    class Meta:
        model = Reservation
        include = ["collect_date"]

    save = SubmitField("Enregistrer")
    event = None
    user = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "event" in kwargs and kwargs["event"] is not None:
            self.event = kwargs["event"]
            self.collect_date.data = self.event.start
        else:
            self.collect_date.data = datetime.now()
        self.user = current_user


class LeaderReservationForm(ReservationForm):
    """Form for leaders to reserve equipment
    Contrary to lambda user, they don't need to pay nor specify a return date
    """


class VolunteerReservationForm(ReservationForm):
    """Form for volunteer to reserve equipment
    User related to the reservation must by specified (current user by default)"""

    user_id = HiddenField("Adhérent")
    has_changed_user = HiddenField(default=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.user_id.data:
            self.user = User.query.get(self.user_id.data)


class ReservationToLocationForm(FlaskForm):
    """Form for deleting an equipment"""

    validate = SubmitField("Valider la réservation")


class EndLocationForm(FlaskForm):
    """Form for deleting an equipment"""

    validate = SubmitField("Valider le retour de la location")


class AddEquipmentInReservationForm(FlaskForm):
    """Form to add an equipment in a reservation"""

    add_equipment = HiddenField("Ajouter un équipement")


class NewRentalUserForm(FlaskForm):
    """Form to create a new rental from no reservation"""

    user = HiddenField("Nom d'adhérent")


class NewRentalEquipmentForm(FlaskForm):
    """Form to create a new rental from no reservation"""

    add_equipment = HiddenField("Référence équipement")


class CancelRentalForm(FlaskForm):
    """Form to cancel a new rental from no reservation"""

    cancel = SubmitField("Annuler")
