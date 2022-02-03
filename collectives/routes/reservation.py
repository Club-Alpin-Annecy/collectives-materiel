""" Module for reservation related route

This modules contains the /reservation Blueprint
"""

from flask_login import current_user
from flask import render_template, redirect, url_for, request
from flask import Blueprint, flash

from collectives.forms.equipment import AddEquipmentInReservation
from collectives.models.equipment import Equipment, EquipmentType

from ..models import db
from ..models import Event, RoleIds
from ..models.reservation import Reservation, ReservationLine
from ..forms.reservation import LeaderReservationForm

blueprint = Blueprint("reservation", __name__, url_prefix="/reservation")
""" Reservation blueprint

This blueprint contains all routes for reservations
"""


@blueprint.route("/", methods=["GET"])
def view_reservations():
    """
    Show all the reservations
    """
    return render_template(
        "reservation/reservations.html",
        reservations=Reservation.query.all(),
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
    form = LeaderReservationForm(request.form)

    reservation = Reservation()
    if not form.is_submitted():
        form = LeaderReservationForm(obj=event)
        return render_template(
            "reservation/editreservation.html", event=event, role_id=role_id, form=form
        )

    previous_lines = []
    tentative_lines = []
    has_removed_lines = False

    print("\nPREVIOUS LINES - ", form.lines, form.line_forms.data)
    # Fetch previous lines
    for line_form in form.line_forms:
        # Create new ReservationLine from line
        e_type = EquipmentType.query.get(line_form.data["equipment_type_id"])
        if e_type is None:
            flash("Type inexistant")
            continue
        line = ReservationLine()
        line.quantity = line_form.data["quantity"]
        line.equipment_type_id = e_type.id
        line.equipmentType = e_type

        # Add to previous lines, also to tentative lines if no delete action
        previous_lines.append(line)
        if line_form.data["delete"]:
            has_removed_lines = True
        else:
            tentative_lines.append(line)

    # Update form with previous lines that are undeleted
    form.set_lines(previous_lines)

    # Check if new line has been added
    new_line_id = int(form.add_line.data)
    if new_line_id != 0:
        new_line = ReservationLine()
        new_line.equipment_type_id = new_line_id
        new_line.equipmentType = EquipmentType.query.get(new_line_id)
        new_line.quantity = form.quantity.data
        print(
            "ADDED - Name :",
            new_line.equipmentType.name,
            ", Quantité :",
            new_line.quantity,
        )
        tentative_lines.append(new_line)

    print("TENTATIVE -", tentative_lines)
    # Form won't validate if we just added or deleted lines
    if has_removed_lines or int(form.update_lines.data):
        form.set_lines(tentative_lines)
        form.setup_line_forms()
        print("NEW -", form.lines, "\n\n", form.line_forms.data, "\n")
        return render_template(
            "reservation/editreservation.html",
            event=event,
            role_id=role_id,
            form=form,
        )

    reservation.collect_date = form.collect_date.data
    reservation.event = event
    reservation.user = current_user
    reservation.lines = form.lines
    db.session.add(reservation)

    db.session.commit()

    return redirect(
        url_for("reservation.view_reservation", reservation_id=reservation.id)
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
    return render_template(
        "reservation/reservationLine.html", reservationLine=reservationLine, form=form
    )
