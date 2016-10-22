# -*- coding: utf-8 -*-

"""
byceps.blueprints.core_admin.authorization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2016 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from byceps.util.authorization import create_permission_enum


AdminPermission = create_permission_enum('admin', [
    'access',
])
