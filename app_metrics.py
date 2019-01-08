"""
metrics application instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2019 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from byceps.metrics.application import create_app
from byceps.util.system import get_env_value


ENV_VAR_NAME_DATABASE_URI = 'DATABASE_URI'


database_uri = get_env_value(ENV_VAR_NAME_DATABASE_URI,
    "No database URI was specified via the '{}' "
    "environment variable.".format(ENV_VAR_NAME_DATABASE_URI))


app = create_app(database_uri)
