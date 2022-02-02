""" API for reservation.

"""
from datetime import datetime, timedelta
import json

from flask_login import current_user
from flask import url_for, request
from marshmallow import fields
from sqlalchemy.sql import text

from collectives.api.equipment import EquipmentSchema, EquipmentSchema
from collectives.models.equipment import Equipment, EquipmentStatus
from collectives.api.equipment import EquipmentSchema, EquipmentSchema

from collectives.models.reservation import (
    Reservation,
    ReservationLine,
)
from collectives.models.user import User
from collectives.utils.numbers import format_currency

from ..models import db


from .common import blueprint, marshmallow


class ReservationSchema(marshmallow.Schema):
    """Schema to describe a reservation"""

    userLicence = fields.Function(lambda obj: obj.user.license)
    statusName = fields.Function(lambda obj: obj.status.display_name())
    userFullname = fields.Function(lambda obj: obj.user.full_name())
    reservationURL = fields.Function(
        lambda obj: url_for("reservation.view_reservation", reservation_id=obj.id)
    )

    reservationURLUser = fields.Function(
        lambda obj: url_for("reservation.my_reservation", reservation_id=obj.id)
    )

    class Meta:
        """Fields to expose"""

        fields = (
            "collect_date",
            "return_date",
            "statusName",
            "userLicence",
            "reservationURL",
            "reservationURLUser",
            "userFullname",
        )


@blueprint.route("/reservations")
def reservations():
    """API endpoint to list reservation.

    :return: A tuple:

        - JSON containing information describe in ReservationSchema
        - HTTP return code : 200
        - additional header (content as JSON)

    :rtype: (string, int, dict)
    """

    query = Reservation.query.all()

    data = ReservationSchema(many=True).dump(query)

    return json.dumps(data), 200, {"content-type": "application/json"}


@blueprint.route("/reservations_of_day")
def reservations_of_day():
    """API endpoint to list reservation.

    :return: A tuple:

        - JSON containing information describe in ReservationSchema
        - HTTP return code : 200
        - additional header (content as JSON)

    :rtype: (string, int, dict)
    """

    dt = datetime.today()
    start = dt - timedelta(days=dt.weekday())
    end = start + timedelta(days=6)

    query = Reservation.query.filter(
        Reservation.collect_date >= start, Reservation.collect_date <= end
    )
    data = ReservationSchema(many=True).dump(query)

    return json.dumps(data), 200, {"content-type": "application/json"}


@blueprint.route("/reservations_returns_of_day")
def reservations_returns_of_day():
    """API endpoint to list reservation.

    :return: A tuple:

        - JSON containing information describe in ReservationSchema
        - HTTP return code : 200
        - additional header (content as JSON)

    :rtype: (string, int, dict)
    """
    dt = datetime.today()
    start = dt - timedelta(days=dt.weekday())
    end = start + timedelta(days=6)

    query = Reservation.query.filter(
        Reservation.return_date >= start, Reservation.return_date <= end
    )
    data = ReservationSchema(many=True).dump(query)

    return json.dumps(data), 200, {"content-type": "application/json"}


@blueprint.route("/reservation/histo_reservations_for_an_equipment<int:equipment_id>")
def equipment_histo_reservations(equipment_id):
    """API endpoint to list the historique of reservations of an equipment.

    :return: A tuple:

        - JSON containing information describe in ReservationShema
        - HTTP return code : 200
        - additional header (content as JSON)

    :rtype: (string, int, dict)
    """

    query = Equipment.query.get(equipment_id).get_reservations()

    data = ReservationSchema(many=True).dump(query)

    return json.dumps(data), 200, {"content-type": "application/json"}


class ReservationLineSchema(marshmallow.Schema):
    """Schema to describe reservation line"""

    equipmentTypeName = fields.Function(lambda obj: obj.equipmentType.name)

    reservationLineURL = fields.Function(
        lambda obj: url_for(
            "reservation.view_reservationLine", reservationLine_id=obj.id
        )
    )

    ratio_equipments = fields.Function(lambda obj: obj.get_ratio_equipments())

    total_price = fields.Function(lambda obj: format_currency(obj.total_price()))

    class Meta:
        """Fields to expose"""

        fields = (
            "quantity",
            "equipmentTypeName",
            "reservationLineURL",
            "ratio_equipments",
            "total_price",
        )


@blueprint.route("/reservation/<int:reservation_id>")
def reservation(reservation_id):
    """API endpoint to list reservation lines.

    :return: A tuple:

        - JSON containing information describe in ReservationLineSchema
        - HTTP return code : 200
        - additional header (content as JSON)

    :rtype: (string, int, dict)
    """

    query = Reservation.query.get(reservation_id).lines

    data = ReservationLineSchema(many=True).dump(query)

    return json.dumps(data), 200, {"content-type": "application/json"}


@blueprint.route("/reservation/ligne/<int:line_id>")
def reservation_line(line_id):
    """API endpoint to list equipment in a reservation line.

    :return: A tuple:

        - JSON containing information describe in EquipmentSchema
        - HTTP return code : 200
        - additional header (content as JSON)

    :rtype: (string, int, dict)
    """
    query = ReservationLine.query.get(line_id).equipments

    data = EquipmentSchema(many=True).dump(query)

    return json.dumps(data), 200, {"content-type": "application/json"}


@blueprint.route("/reservation/lignerented/<int:line_id>")
def reservation_line_equipments_rented(line_id):
    """API endpoint to list equipment rented in a reservation line.

    :return: A tuple:

        - JSON containing information describe in EquipmentSchema
        - HTTP return code : 200
        - additional header (content as JSON)

    :rtype: (string, int, dict)
    """
    query = ReservationLine.query.get(line_id).get_equipments_rented()

    data = EquipmentSchema(many=True).dump(query)

    return json.dumps(data), 200, {"content-type": "application/json"}


@blueprint.route("/reservation/lignereturned/<int:line_id>")
def reservation_line_equipments_returned(line_id):
    """API endpoint to list equipment rented in a reservation line.

    :return: A tuple:

        - JSON containing information describe in EquipmentSchema
        - HTTP return code : 200
        - additional header (content as JSON)

    :rtype: (string, int, dict)
    """
    query = ReservationLine.query.get(line_id).get_equipments_returned()

    data = EquipmentSchema(many=True).dump(query)

    return json.dumps(data), 200, {"content-type": "application/json"}


@blueprint.route(
    "/set_available_equipment/<int:equipment_id>",
    methods=["POST"],
)
def set_available_equipment(equipment_id):
    """
    API endpoint to remove an equipment from a réservation.

    :return: A tuple:

        - JSON containing information if OK
        - HTTP return code : 200
        - additional header (content as JSON)

    :rtype: (string, int, dict)
    """

    equipment = Equipment.query.get(equipment_id)

    equipment.status = EquipmentStatus.Available
    db.session.commit()

    return (
        "{'response': 'Status changed OK'}",
        200,
        {"content-type": "application/json"},
    )


@blueprint.route(
    "/remove_reservationLine_equipment/<int:equipment_id>/<int:line_id>",
    methods=["POST"],
)
def remove_reservationLine_equipment(equipment_id, line_id):
    """
    API endpoint to remove an equipment from a réservation.

    :return: A tuple:

        - JSON containing information if OK
        - HTTP return code : 200
        - additional header (content as JSON)

    :rtype: (string, int, dict)
    """
    line = ReservationLine.query.get(line_id)
    equipment = Equipment.query.get(equipment_id)
    line.equipments.remove(equipment)
    equipment.status = EquipmentStatus.Available
    db.session.commit()

    return (
        "{'response': 'Status changed OK'}",
        200,
        {"content-type": "application/json"},
    )


# ---------------------------------------------------------------- User ----------------------------------------------------
@blueprint.route("/my_reservations/")
def my_reservations():
    """API endpoint to list reservation lines of current user.

    :return: A tuple:

        - JSON containing information describe in ReservationSchema
        - HTTP return code : 200
        - additional header (content as JSON)

    :rtype: (string, int, dict)
    """

    query = User.query.get(current_user.id).get_reservations_planned_and_ongoing()

    data = ReservationSchema(many=True).dump(query)

    return json.dumps(data), 200, {"content-type": "application/json"}


@blueprint.route("/my_reservations_completed/")
def my_reservations_completed():
    """API endpoint to list reservation lines of current user.

    :return: A tuple:

        - JSON containing information describe in ReservationSchema
        - HTTP return code : 200
        - additional header (content as JSON)

    :rtype: (string, int, dict)
    """

    query = User.query.get(current_user.id).get_reservations_completed()

    data = ReservationSchema(many=True).dump(query)

    return json.dumps(data), 200, {"content-type": "application/json"}


@blueprint.route("/my_reservation/<int:reservation_id>")
def my_reservation(reservation_id):
    """API endpoint to list reservation lines.

    :return: A tuple:

        - JSON containing information describe in ReservationLineSchema
        - HTTP return code : 200
        - additional header (content as JSON)

    :rtype: (string, int, dict)
    """

    query = Reservation.query.get(reservation_id).lines

    data = ReservationLineSchema(many=True).dump(query)

    return json.dumps(data), 200, {"content-type": "application/json"}


# ---------------------------------------------------------------- Autocomplete ----------------------------------------------------
class AutocompleteEquipmentSchema(marshmallow.Schema):
    """Schema to describe autocomplete equipment"""

    class Meta:
        """Fields to expose"""

        fields = (
            "id",
            "reference",
        )


def find_equipments_by_reference(q):
    """Find equipment for autocomplete from a part of their full name.

    Comparison are case insensitive.

    :param string q: Part of the name that will be searched.
    :return: List of equipments corresponding to ``q``
    :rtype: list(:py:class:`collectives.models.equipment.Equipment`)
    """

    sql = "SELECT id, reference from equipments WHERE LOWER(reference) LIKE :pattern"

    pattern = f"%{q.lower()}%"
    found_equipments = (
        db.session.query(Equipment).from_statement(text(sql)).params(pattern=pattern)
    )

    return found_equipments


@blueprint.route("/reservation/autocomplete/<int:line_id>")
def autocomplete_availables_equipments(line_id):
    """API endpoint to list equipment in a reservation line.

    :return: A tuple:

        - JSON containing information describe in EquipmentSchema
        - HTTP return code : 200
        - additional header (content as JSON)

    :rtype: (string, int, dict)
    """
    eType = ReservationLine.query.get(line_id).equipmentType

    equipments_of_type = eType.get_all_equipments_availables()
    q = request.args.get("q")
    equipments_of_autocomplete = []
    if q:
        equipments_of_autocomplete = find_equipments_by_reference(q)

    query = list(set(equipments_of_type).intersection(equipments_of_autocomplete))

    data = EquipmentSchema(many=True).dump(query)

    return json.dumps(data), 200, {"content-type": "application/json"}
