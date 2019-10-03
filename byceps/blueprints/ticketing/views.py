"""
byceps.blueprints.ticketing.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2019 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from flask import abort, g, redirect, request, url_for

from ...config import get_ticket_management_enabled
from ...services.party import service as party_service
from ...services.ticketing import (
    barcode_service,
    category_service as ticket_category_service,
    ticket_service,
    ticket_seat_management_service,
    ticket_user_management_service,
)
from ...util.framework.blueprint import create_blueprint
from ...util.framework.flash import flash_error, flash_success
from ...util.iterables import find
from ...util.framework.templating import templated
from ...util.views import respond_no_content

from ..authentication.decorators import login_required

from .forms import SpecifyUserForm
from . import notification_service


blueprint = create_blueprint('ticketing', __name__)


@blueprint.route('/mine')
@login_required
@templated
def index_mine():
    """List tickets related to the current user."""
    if g.party_id is None:
        # No party is configured for the current site.
        abort(404)

    party = party_service.get_party(g.party_id)

    current_user = g.current_user

    tickets = ticket_service.find_tickets_related_to_user_for_party(
        current_user.id, party.id)

    tickets = [ticket for ticket in tickets if not ticket.revoked]

    current_user_uses_any_ticket = find(
        lambda t: t.used_by_id == current_user.id, tickets)

    return {
        'party_title': party.title,
        'tickets': tickets,
        'current_user_uses_any_ticket': current_user_uses_any_ticket,
        'is_user_allowed_to_print_ticket': _is_user_allowed_to_print_ticket,
    }


@blueprint.route('/tickets/<uuid:ticket_id>/printable.html')
@login_required
@templated
def view_printable_html(ticket_id):
    """Show a form to select a user to appoint for the ticket."""
    ticket = _get_ticket_or_404(ticket_id)

    if not _is_user_allowed_to_print_ticket(ticket, g.current_user.id):
        # Hide ticket ID validity rather than openly denying access.
        abort(404)

    ticket_category = ticket_category_service.find_category(ticket.category_id)
    party = party_service.get_party(ticket_category.party_id)

    barcode_svg = barcode_service.render_svg(ticket.code)

    # Encode SVG to be used inline as part of a data URI.
    # Replacements are not complete, but sufficient for this case.
    #
    # See https://codepen.io/tigt/post/optimizing-svgs-in-data-uris
    # for details.
    barcode_svg_inline = barcode_svg \
            .replace('<', '%3C') \
            .replace('>', '%3E') \
            .replace('"', '\'') \
            .replace('\n', '%0A')

    return {
        'ticket': ticket,
        'ticket_category': ticket_category,
        'party': party,
        'barcode_svg_inline': barcode_svg_inline,
    }


# -------------------------------------------------------------------- #
# user


@blueprint.route('/tickets/<uuid:ticket_id>/appoint_user')
@login_required
@templated
def appoint_user_form(ticket_id, erroneous_form=None):
    """Show a form to select a user to appoint for the ticket."""
    _abort_if_ticket_management_disabled()

    ticket = _get_ticket_or_404(ticket_id)

    manager = g.current_user.to_dto()

    if not ticket.is_user_managed_by(manager.id):
        abort(403)

    form = erroneous_form if erroneous_form else SpecifyUserForm()

    return {
        'ticket': ticket,
        'form': form,
    }


@blueprint.route('/tickets/<uuid:ticket_id>/user', methods=['POST'])
def appoint_user(ticket_id):
    """Appoint a user for the ticket."""
    _abort_if_ticket_management_disabled()

    form = SpecifyUserForm(request.form)
    if not form.validate():
        return appoint_user_form(ticket_id, form)

    ticket = _get_ticket_or_404(ticket_id)

    manager = g.current_user.to_dto()

    if not ticket.is_user_managed_by(manager.id):
        abort(403)

    user = form.user.data

    ticket_user_management_service \
        .appoint_user(ticket.id, user.id, manager.id)

    flash_success('{} wurde als Nutzer/in von Ticket {} eingetragen.',
        user.screen_name, ticket.code)

    notification_service.notify_appointed_user(ticket, user, manager)

    return redirect(url_for('.index_mine'))


@blueprint.route('/tickets/<uuid:ticket_id>/user', methods=['DELETE'])
@respond_no_content
def withdraw_user(ticket_id):
    """Withdraw the ticket's user and appoint its owner instead."""
    _abort_if_ticket_management_disabled()

    ticket = _get_ticket_or_404(ticket_id)

    manager = g.current_user.to_dto()

    if not ticket.is_user_managed_by(manager.id):
        abort(403)

    ticket_user_management_service \
        .appoint_user(ticket.id, manager.id, manager.id)

    flash_success('Du wurdest als Nutzer/in von Ticket {} eingetragen.',
        ticket.code)


# -------------------------------------------------------------------- #
# user manager


@blueprint.route('/tickets/<uuid:ticket_id>/appoint_user_manager')
@login_required
@templated
def appoint_user_manager_form(ticket_id, erroneous_form=None):
    """Show a form to select a user to appoint as user manager for the ticket."""
    _abort_if_ticket_management_disabled()

    ticket = _get_ticket_or_404(ticket_id)

    manager = g.current_user.to_dto()

    if not ticket.is_owned_by(manager.id):
        abort(403)

    form = erroneous_form if erroneous_form else SpecifyUserForm()

    return {
        'ticket': ticket,
        'form': form,
    }


@blueprint.route('/tickets/<uuid:ticket_id>/user_manager', methods=['POST'])
def appoint_user_manager(ticket_id):
    """Appoint a user manager for the ticket."""
    _abort_if_ticket_management_disabled()

    form = SpecifyUserForm(request.form)
    if not form.validate():
        return appoint_user_manager_form(ticket_id, form)

    ticket = _get_ticket_or_404(ticket_id)

    manager = g.current_user.to_dto()

    if not ticket.is_owned_by(manager.id):
        abort(403)

    user = form.user.data

    ticket_user_management_service \
        .appoint_user_manager(ticket.id, user.id, manager.id)

    flash_success('{} wurde als Nutzer-Verwalter/in von Ticket {} eingetragen.',
        user.screen_name, ticket.code)

    notification_service.notify_appointed_user_manager(ticket, user, manager)

    return redirect(url_for('.index_mine'))


@blueprint.route('/tickets/<uuid:ticket_id>/user_manager', methods=['DELETE'])
@respond_no_content
def withdraw_user_manager(ticket_id):
    """Withdraw the ticket's user manager."""
    _abort_if_ticket_management_disabled()

    ticket = _get_ticket_or_404(ticket_id)

    manager = g.current_user.to_dto()

    if not ticket.is_owned_by(manager.id):
        abort(403)

    user = ticket.user_managed_by

    ticket_user_management_service.withdraw_user_manager(ticket.id, manager.id)

    flash_success('Der Nutzer-Verwalter von Ticket {} wurde entfernt.',
                  ticket.code)

    notification_service.notify_withdrawn_user_manager(ticket, user, manager)


# -------------------------------------------------------------------- #
# seat manager


@blueprint.route('/tickets/<uuid:ticket_id>/appoint_seat_manager')
@login_required
@templated
def appoint_seat_manager_form(ticket_id, erroneous_form=None):
    """Show a form to select a user to appoint as seat manager for the ticket."""
    _abort_if_ticket_management_disabled()

    ticket = _get_ticket_or_404(ticket_id)

    manager = g.current_user.to_dto()

    if not ticket.is_owned_by(manager.id):
        abort(403)

    form = erroneous_form if erroneous_form else SpecifyUserForm()

    return {
        'ticket': ticket,
        'form': form,
    }


@blueprint.route('/tickets/<uuid:ticket_id>/seat_manager', methods=['POST'])
def appoint_seat_manager(ticket_id):
    """Appoint a seat manager for the ticket."""
    _abort_if_ticket_management_disabled()

    form = SpecifyUserForm(request.form)
    if not form.validate():
        return appoint_seat_manager_form(ticket_id, form)

    ticket = _get_ticket_or_404(ticket_id)

    manager = g.current_user.to_dto()

    if not ticket.is_owned_by(manager.id):
        abort(403)

    user = form.user.data

    ticket_seat_management_service \
        .appoint_seat_manager(ticket.id, user.id, manager.id)

    flash_success(
        '{} wurde als Sitzplatz-Verwalter/in von Ticket {} eingetragen.',
        user.screen_name, ticket.code)

    notification_service.notify_appointed_seat_manager(ticket, user, manager)

    return redirect(url_for('.index_mine'))


@blueprint.route('/tickets/<uuid:ticket_id>/seat_manager', methods=['DELETE'])
@respond_no_content
def withdraw_seat_manager(ticket_id):
    """Withdraw the ticket's seat manager."""
    _abort_if_ticket_management_disabled()

    ticket = _get_ticket_or_404(ticket_id)

    manager = g.current_user.to_dto()

    if not ticket.is_owned_by(manager.id):
        abort(403)

    user = ticket.seat_managed_by

    ticket_seat_management_service.withdraw_seat_manager(ticket.id, manager.id)

    flash_success('Der Sitzplatz-Verwalter von Ticket {} wurde entfernt.',
                  ticket.code)

    notification_service.notify_withdrawn_seat_manager(ticket, user, manager)


# -------------------------------------------------------------------- #


def _abort_if_ticket_management_disabled():
    if not get_ticket_management_enabled():
        flash_error('Tickets können derzeit nicht verändert werden.')
        abort(403)


def _get_ticket_or_404(ticket_id):
    ticket = ticket_service.find_ticket(ticket_id)

    if (ticket is None) or ticket.revoked:
        abort(404)

    return ticket


def _is_user_allowed_to_print_ticket(ticket, user_id):
    """Return `True` only if the user is allowed to print the ticket."""
    return ticket.is_owned_by(user_id) \
        or ticket.is_managed_by(user_id) \
        or ticket.used_by_id == user_id
