from datetime import datetime, timedelta
from wtforms import (
    SubmitField,
    FieldList,
    FormField,
    HiddenField,
    IntegerField,
    StringField,
)
from flask_wtf.form import FlaskForm
from wtforms_alchemy import ModelForm
from collectives.models.equipment import EquipmentType

from ..models.reservation import Reservation


class ReservationLineForm(FlaskForm):
    """
    Form for user to edit quantity of a reservation line or delete it
    """

    equipment_type_id = HiddenField()
    quantity_line = IntegerField("Quantité")
    delete = SubmitField("Supprimer")
    name = StringField("Nom")


class LeaderReservationForm(ModelForm, FlaskForm):
    """Form for leaders to reserve equipment
    Contrary to lambda user, they don't need to pay nor specify a return date
    """

    class Meta:
        model = Reservation
        include = ["collect_date"]

    line_forms = FieldList(FormField(ReservationLineForm))

    save_all = SubmitField("Enregistrer")

    add_line = HiddenField("Ajouter de l'équipement", default=0)
    quantity = IntegerField("Quantité", render_kw={"placeholder": "Quantité..."})
    update_lines = HiddenField(default=0)

    source_event = None

    lines = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "obj" in kwargs:
            self.source_event = kwargs["obj"]
            self.collect_date.data = (self.source_event.start).replace(
                hour=(datetime.now() + timedelta(hours=1)).hour,
                minute=0,
            )

    def setup_line_forms(self):
        """
        Sets up line_forms (FieldList) using lines (List of :py:class:`collectives.models.reservation.ReservationLine`)
        """
        # Remove all existing entries
        while len(self.line_forms) > 0:
            self.line_forms.pop_entry()

        for line in self.lines:
            e_type = EquipmentType.query.get(line.equipment_type_id)

            form = ReservationLineForm()
            form.delete = False
            form.equipment_type_id = e_type.id
            form.quantity_line = line.quantity
            form.name = e_type.name
            print(
                "ADDED IN SETUP - Quantité :", form.quantity_line, ", Name :", form.name
            )
            self.line_forms.append_entry(form)

    def set_lines(self, lines):
        """
        Stores the list of current lines, used to populate form fields

        :param lines: list of current lines
        :type lines: list[:py:class:`collectives.models.reservation.ReservationLine`]
        """
        self.lines = list(lines)

    def equipment_type_ids(self):
        """
        :return: the list of all equipment types in the reservation.
        :rtype: list[int]
        """
        return [l.equipment_type_id for l in self.lines]
