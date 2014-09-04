# -*- coding: utf-8 -*-

"""
byceps.blueprints.snippet.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2014 Jochen Kupperschmidt
"""

from ...util.framework import create_blueprint

from .models import Snippet
from .templating import load_template, render_snippet


blueprint = create_blueprint('snippet', __name__)


@blueprint.app_template_global('render_snippet')
def render_snippet_as_partial(name):
    """Render the latest version of the snippet with the given name and
    return the result.
    """
    snippet = Snippet.query.for_current_party.filter_by(name=name).one()
    version = snippet.get_latest_version()
    template = load_template(version)
    return template.render()


def view_latest_by_name(name):
    """Show the latest version of the snippet with the given name."""
    # TODO: Fetch snippet via mountpoint
    # endpoint suffix != snippet name
    snippet = Snippet.query \
        .for_current_party() \
        .filter_by(name=name) \
        .one()
    return render_snippet(snippet.get_latest_version())
