"""
byceps.services.user.stats_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2018 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from datetime import datetime, timedelta

from .models.user import User as DbUser


def count_users() -> int:
    """Return the number of users."""
    return DbUser.query \
        .count()


def count_users_created_since(delta: timedelta) -> int:
    """Return the number of user accounts created since `delta` ago."""
    filter_starts_at = datetime.now() - delta

    return DbUser.query \
        .filter(DbUser.created_at >= filter_starts_at) \
        .count()


def count_enabled_users() -> int:
    """Return the number of enabled user accounts.

    Suspended or deleted accounts are excluded.
    """
    return DbUser.query \
        .filter_by(enabled=True) \
        .filter_by(suspended=False) \
        .filter_by(deleted=False) \
        .count()


def count_disabled_users() -> int:
    """Return the number of disabled user accounts.

    Suspended or deleted accounts are excluded.
    """
    return DbUser.query \
        .filter_by(enabled=False) \
        .filter_by(suspended=False) \
        .filter_by(deleted=False) \
        .count()


def count_suspended_users() -> int:
    """Return the number of suspended user accounts."""
    return DbUser.query \
        .filter_by(suspended=True) \
        .filter_by(deleted=False) \
        .count()


def count_deleted_users() -> int:
    """Return the number of deleted user accounts."""
    return DbUser.query \
        .filter_by(deleted=True) \
        .count()