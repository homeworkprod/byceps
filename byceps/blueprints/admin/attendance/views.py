"""
byceps.blueprints.admin.attendance.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from flask import abort

from ....services.brand import service as brand_service
from ....services.party import service as party_service
from ....services.ticketing import attendance_service
from ....services.user import service as user_service
from ....util.framework.blueprint import create_blueprint
from ....util.framework.templating import templated


blueprint = create_blueprint('attendance_admin', __name__)


@blueprint.route('/brands/<brand_id>')
@templated
def view_for_brand(brand_id):
    """Show most frequent attendees for parties of this brand."""
    brand = brand_service.find_brand(brand_id)
    if brand is None:
        abort(404)

    parties = party_service.get_parties_for_brand(brand.id)
    if parties:
        parties.sort(key=lambda party: party.starts_at, reverse=True)
        most_recent_party = parties[0]
    else:
        most_recent_party = None
    party_total = len(parties)

    top_attendees = attendance_service.get_top_attendees_for_brand(brand.id)

    user_ids = {user_id for user_id, attendance_count in top_attendees}
    users = user_service.find_users(user_ids, include_avatars=False)
    users_by_id = user_service.index_users_by_id(users)

    top_attendees = [
        (users_by_id[user_id], attendance_count)
        for user_id, attendance_count in top_attendees
    ]

    # Sort by highest attendance count first, alphabetical screen name second.
    top_attendees.sort(key=lambda att: (-att[1], att[0].screen_name))

    return {
        'brand': brand,
        'party_total': party_total,
        'most_recent_party': most_recent_party,
        'top_attendees': top_attendees,
    }
