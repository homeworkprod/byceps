#!/usr/bin/env python

"""Generate the SQL statements to remove one or more users and their
various (but not all) traces from the database.

Might fail for example if a user posted in a discussion board.

Run script `clean_up_after_deleted_users.py` before this one.

:Copyright: 2006-2021 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from typing import Iterable, Iterator, List

import click

from byceps.services.user import service as user_service
from byceps.typing import UserID
from byceps.util.system import get_config_filename_from_env_or_exit

from _util import app_context
from _validators import validate_user_id_format


def validate_user_ids(ctx, param, user_ids: Iterable[UserID]) -> List[UserID]:
    def _validate():
        for user_id in user_ids:
            yield validate_user_id_format(ctx, param, user_id)

    return list(_validate())


@click.command()
@click.argument('user_ids', callback=validate_user_ids, nargs=-1, required=True)
def execute(user_ids):
    statements = generate_delete_statements_for_users(user_ids)
    for statement in statements:
        print(statement)


def generate_delete_statements_for_users(
    user_ids: Iterable[UserID],
) -> Iterator[str]:
    users = user_service.find_users(user_ids)
    existing_user_ids = {u.id for u in users}

    for user_id in user_ids:
        if user_id not in existing_user_ids:
            click.secho(
                # Mask as SQL comment in case STDERR output, is copied and
                # pasted/piped with the actual SQL statements into a RDBMS.
                f'-- Skipping unknown user ID "{user_id}".\n',
                fg='yellow',
                err=True,
            )
            continue

        yield from generate_delete_statements_for_user(user_id)
        yield ''  # empty line


def generate_delete_statements_for_user(user_id: UserID) -> Iterator[str]:
    for table, user_id_column in [
        ('user_avatars', 'creator_id'),
        ('user_details', 'user_id'),
        ('user_events', 'user_id'),
        ('users', 'id'),
    ]:
        yield f"DELETE FROM {table} WHERE {user_id_column} = '{user_id}';"


if __name__ == '__main__':
    config_filename = get_config_filename_from_env_or_exit()
    with app_context(config_filename):
        execute()
