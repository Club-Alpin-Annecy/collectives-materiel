""" Module for reservation related route

This modules contains the /reservation Blueprint
"""

from flask_login import current_user
from flask import render_template, redirect, url_for
from flask import Blueprint, flash
from wtforms import IntegerField
from collectives.forms.equipment import AddEquipmentInReservation
from collectives.models.equipment import Equipment, EquipmentStatus
from collectives.utils.access import valid_user, confidentiality_agreement, user_is
from collectives.models.equipment import Equipment, EquipmentType

from ..models import db
from ..models import Event, RoleIds
from ..models.reservation import Reservation, ReservationLine
from ..forms.reservation import LeaderReservationForm

blueprint = Blueprint("reservation", __name__, url_prefix="/reservation")
""" Reservation blueprint

This blueprint contains all routes for reservations
"""


@blueprint.before_request
@valid_user()
@confidentiality_agreement()
@user_is("can_manage_reservation")
def before_request():
    """Protect all of the admin endpoints.

    Protection is done by the decorator:

    - check if user is valid :py:func:`collectives.utils.access.valid_user`
    - check if user has signed the confidentiality agreement :py:func:`collectives.utils.access.confidentiality_agreement`
    - check if user is allowed to manage reservation :py:func:`collectives.utils.access.user_is`
    """
    pass


@blueprint.route("/", methods=["GET"])
def view_reservations():
    """
    Show all the reservations
    """
    return render_template(
        "reservation/reservations.html",
    )


@blueprint.route("/reservation_of_day", methods=["GET"])
def view_reservations_of_week():
    """
    Show the reservations of the week
    """
    return render_template(
        "reservation/reservationsDay.html",
    )


@blueprint.route("/reservations_returns_of_day", methods=["GET"])
def view_reservations_returns_of_week():
    """
    Show the reservations returns of the week
    """
    return render_template(
        "reservation/reservationsReturnDay.html",
    )


@blueprint.route("/<int:reservation_id>", methods=["GET"])
def view_reservation(reservation_id=None):
    """
    Shows a reservation
    """
    reservation = (
        Reservation()
        if reservation_id is None
        else Reservation.query.get(reservation_id)
    )
    return render_template(
        "reservation/reservation.html",
        reservation=reservation,
    )


@blueprint.route("/add", methods=["GET"])
@blueprint.route("/<int:reservation_id>", methods=["GET"])
def manage_reservation(reservation_id=None):
    """Reservation creation and modification page.

    If an ``reservation_id`` is given, it is a modification of an existing reservation.

    :param int reservation_id: Primary key of the reservation to manage.
    """
    reservation = (
        Reservation()
        if reservation_id is None
        else Reservation.query.get(reservation_id)
    )

    form = (
        LeaderReservationForm()
        if reservation_id is None
        else LeaderReservationForm(obj=reservation)
    )
    action = "Ajout" if reservation_id is None else "Édition"

    if not form.validate_on_submit():
        return render_template(
            "basicform.html",
            form=form,
            title=f"{action} de réservation",
        )

    form.populate_obj(reservation)

    db.session.add(reservation)
    db.session.commit()

    return redirect(
        url_for("reservation.view_reservation", reservation_id=reservation_id)
    )


@blueprint.route(
    "event/<int:event_id>/role/<int:role_id>/register", methods=["GET", "POST"]
)
def register(event_id, role_id=None):
    """Page for user to create a new reservation.

    The displayed form depends on the role_id, a leader can create an reservation without paying
    and without a max number of equipment.
    The reservation will related to the event of event_id.

    :param int role_id: Role that the user wishes to register has.
    :param int event_id: Primary key of the related event.
    """
    role = RoleIds.get(role_id)
    if role is None:
        flash("Role inexistant", "error")
        return redirect(url_for("event.view_event", event_id=event_id))

    if not current_user.has_role([role_id]) and not current_user.is_moderator():
        flash("Role insuffisant", "error")
        return redirect(url_for("event.view_event", event_id=event_id))

    if not role.relates_to_activity():
        flash("Role non implémenté")
        return redirect(url_for("event.view_event", event_id=event_id))

    event = Event.query.get(event_id)
    # print("\nREQUEST FORM -", request.form)

    class F(LeaderReservationForm):
        """Empty class to create fields dynamically"""

        pass

    for e in EquipmentType.query.all():
        field = IntegerField(f"{e.name}", default=0)
        setattr(F, f"field{e.id}", field)

    form = F(obj=event)

    if form.is_submitted():
        if not form.validate():
            flash("La réservation est incorrecte")
            return render_template(
                "reservation/editreservation.html",
                event=event,
                role_id=role_id,
                form=form,
            )

        reservation = Reservation()
        for e in EquipmentType.query.all():
            quantity = getattr(form, f"field{e.id}").data
            if quantity <= 0:
                continue
            resa_line = ReservationLine()
            resa_line.reservation_id = reservation.id
            resa_line.quantity = quantity
            resa_line.equipment_type_id = e.id
            reservation.lines.append(resa_line)

        reservation.event = event
        reservation.user = current_user
        reservation.collect_date = form.collect_date.data
        db.session.add(reservation)
        db.session.commit()

        return redirect(
            url_for("reservation.view_reservation", reservation_id=reservation.id)
        )
    return render_template(
        "reservation/editreservation.html",
        event=event,
        role_id=role_id,
        form=form,
    )


@blueprint.route("/line/<int:reservationLine_id>", methods=["GET", "POST"])
def view_reservationLine(reservationLine_id):
    """
    Show a reservation line
    """
    form = AddEquipmentInReservation()
    reservationLine = ReservationLine.query.get(reservationLine_id)
    if form.validate_on_submit():
        equipment = Equipment.query.get(form.add_equipment.data)
        reservationLine.equipments.append(equipment)
        equipment.status = EquipmentStatus.Rented
        return redirect(
            url_for(".view_reservationLine", reservationLine_id=reservationLine_id)
        )
    return render_template(
        "reservation/reservationLine.html", reservationLine=reservationLine, form=form
    )
