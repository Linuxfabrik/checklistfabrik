"""
ChecklistFabrik HTML module

This module simply renders Jinja templated HTML.

EXAMPLE::

    - linuxfabrik.clf.html:
        content: 'This is an example text with Jinja expressions, for example {{ host }}.'
"""


def main(**kwargs):
    clf_jinja_env = kwargs["clf_jinja_env"]

    rendered_content = clf_jinja_env.from_string(kwargs["content"]).render(**kwargs)

    return {
        "html": f'<div class="clf-content-block">{rendered_content}</div>',
    }
