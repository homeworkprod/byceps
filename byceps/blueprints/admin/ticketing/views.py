"""
byceps.blueprints.admin.ticketing.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2021 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from flask import abort, g, request
from flask_babel import gettext

from ....services.party import service as party_service
from ....services.shop.order import service as order_service
from ....services.ticketing import (
    ticket_bundle_service,
    ticket_service,
    ticket_user_management_service,
)
from ....util.authorization import register_permission_enum
from ....util.framework.blueprint import create_blueprint
from ....util.framework.flash import flash_error, flash_success
from ....util.framework.templating import templated
from ....util.views import permission_required, redirect_to

from .authorization import TicketingPermission
from .forms import SpecifyUserForm, UpdateCodeForm
from . import service


blueprint = create_blueprint('ticketing_admin', __name__)


register_permission_enum(TicketingPermission)


# -------------------------------------------------------------------- #
# tickets


@blueprint.route('/tickets/for_party/<party_id>', defaults={'page': 1})
@blueprint.route('/tickets/for_party/<party_id>/pages/<int:page>')
@permission_required(TicketingPermission.view)
@templated
def index_for_party(party_id, page):
    """List tickets for that party."""
    party = _get_party_or_404(party_id)

    per_page = request.args.get('per_page', type=int, default=15)

    search_term = request.args.get('search_term', default='').strip()

    tickets = ticket_service.get_tickets_with_details_for_party_paginated(
        party.id, page, per_page, search_term=search_term
    )

    return {
        'party': party,
        'search_term': search_term,
        'tickets': tickets,
    }


@blueprint.route('/tickets/<uuid:ticket_id>')
@permission_required(TicketingPermission.view)
@templated
def view_ticket(ticket_id):
    """Show a ticket."""
    ticket = ticket_service.get_ticket_with_details(ticket_id)
    if ticket is None:
        abort(404)

    party = party_service.get_party(ticket.category.party_id)

    if ticket.order_number:
        order = order_service.find_order_by_order_number(ticket.order_number)
    else:
        order = None

    events = service.get_events(ticket.id)

    return {
        'party': party,
        'ticket': ticket,
        'order': order,
        'events': events,
    }


# -------------------------------------------------------------------- #
# ticket code


@blueprint.route('/tickets/<uuid:ticket_id>/code')
@permission_required(TicketingPermission.administrate)
@templated
def update_code_form(ticket_id, erroneous_form=None):
    """Show a form to set a custom code for the ticket."""
    ticket = _get_ticket_or_404(ticket_id)

    if ticket.user_checked_in:
        flash_error(
            gettext(
                'Code cannot be changed as somebody has already been checked in with this ticket.'
            )
        )
        return redirect_to('.view_ticket', ticket_id=ticket.id)

    party = party_service.get_party(ticket.party_id)

    form = erroneous_form if erroneous_form else UpdateCodeForm()

    return {
        'party': party,
        'ticket': ticket,
        'form': form,
    }


@blueprint.route('/tickets/<uuid:ticket_id>/code', methods=['POST'])
@permission_required(TicketingPermission.administrate)
def update_code(ticket_id):
    """Set a custom code for the ticket."""
    ticket = _get_ticket_or_404(ticket_id)

    if ticket.user_checked_in:
        flash_error(
            gettext(
                'Code cannot be changed as somebody has already been checked in with this ticket.'
            )
        )
        return redirect_to('.view_ticket', ticket_id=ticket.id)

    form = UpdateCodeForm(request.form)
    if not form.validate():
        return update_code_form(ticket.id, form)

    code = form.code.data
    manager = g.user

    ticket_service.update_ticket_code(ticket.id, code, manager.id)

    flash_success(
        gettext(
            'Code for ticket %(ticket_code)s has been updated.',
            ticket_code=ticket.code,
        )
    )

    return redirect_to('.view_ticket', ticket_id=ticket.id)


# -------------------------------------------------------------------- #
# user appointment


@blueprint.route('/tickets/<uuid:ticket_id>/appoint_user')
@permission_required(TicketingPermission.checkin)
@templated
def appoint_user_form(ticket_id, erroneous_form=None):
    """Show a form to select a user to appoint for the ticket."""
    ticket = _get_ticket_or_404(ticket_id)

    party = party_service.get_party(ticket.party_id)

    form = erroneous_form if erroneous_form else SpecifyUserForm()

    return {
        'party': party,
        'ticket': ticket,
        'form': form,
    }


@blueprint.route('/tickets/<uuid:ticket_id>/user', methods=['POST'])
@permission_required(TicketingPermission.checkin)
def appoint_user(ticket_id):
    """Appoint a user for the ticket."""
    form = SpecifyUserForm(request.form)
    if not form.validate():
        return appoint_user_form(ticket_id, form)

    ticket = _get_ticket_or_404(ticket_id)
    user = form.user.data
    manager = g.user

    ticket_user_management_service.appoint_user(ticket.id, user.id, manager.id)

    flash_success(
        gettext(
            '%(screen_name)s has been assigned as user of ticket %(ticket_code)s.',
            screen_name=user.screen_name,
            ticket_code=ticket.code,
        )
    )

    return redirect_to('.view_ticket', ticket_id=ticket.id)


# -------------------------------------------------------------------- #
# bundles


@blueprint.route('/bundles/for_party/<party_id>', defaults={'page': 1})
@blueprint.route('/bundles/for_party/<party_id>/pages/<int:page>')
@permission_required(TicketingPermission.view)
@templated
def index_bundle_for_party(party_id, page):
    """List ticket bundles for that party."""
    party = _get_party_or_404(party_id)

    per_page = request.args.get('per_page', type=int, default=15)

    bundles = ticket_bundle_service.get_bundles_for_party_paginated(
        party.id, page, per_page
    )

    return {
        'party': party,
        'bundles': bundles,
    }


@blueprint.route('/bundles/<uuid:bundle_id>')
@permission_required(TicketingPermission.view)
@templated
def view_bundle(bundle_id):
    """Show a ticket bundle."""
    bundle = ticket_bundle_service.find_bundle(bundle_id)
    if bundle is None:
        abort(404)

    party = party_service.get_party(bundle.ticket_category.party_id)

    tickets = ticket_bundle_service.find_tickets_for_bundle(bundle.id)

    return {
        'party': party,
        'bundle': bundle,
        'tickets': tickets,
    }


# -------------------------------------------------------------------- #
# helpers


def _get_party_or_404(party_id):
    party = party_service.find_party(party_id)

    if party is None:
        abort(404)

    return party


def _get_ticket_or_404(ticket_id):
    ticket = ticket_service.find_ticket(ticket_id)

    if ticket is None:
        abort(404)

    return ticket
