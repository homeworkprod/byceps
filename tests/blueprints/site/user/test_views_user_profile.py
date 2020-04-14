"""
:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

import pytest

from tests.conftest import database_recreated
from tests.helpers import create_site, create_user, http_client


@pytest.fixture(scope='module')
def app(party_app, db, make_email_config):
    with party_app.app_context():
        with database_recreated(db):
            make_email_config()
            create_site()
            yield party_app


def test_view_profile_of_existing_user(app):
    user = create_user('ExistingUser')

    response = request_profile(app, user.id)

    assert response.status_code == 200
    assert response.mimetype == 'text/html'


def test_view_profile_of_uninitialized_user(app):
    user = create_user('UninitializedUser', initialized=False)

    response = request_profile(app, user.id)

    assert response.status_code == 404


def test_view_profile_of_suspended_user(app):
    user = create_user('SuspendedUser', suspended=True)

    response = request_profile(app, user.id)

    assert response.status_code == 404


def test_view_profile_of_deleted_user(app):
    user = create_user('DeletedUser', deleted=True)

    response = request_profile(app, user.id)

    assert response.status_code == 404


def test_view_profile_of_unknown_user(app):
    unknown_user_id = '00000000-0000-0000-0000-000000000000'

    response = request_profile(app, unknown_user_id)

    assert response.status_code == 404


# helpers


def request_profile(app, user_id):
    url = f'/users/{user_id}'

    with http_client(app) as client:
        return client.get(url)