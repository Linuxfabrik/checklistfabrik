"""
ChecklistFabrik HTML module

This module simply renders Jinja templated HTML.

EXAMPLE::

    - linuxfabrik.clf.html:
        content: 'This is an example text with Jinja expressions, for example {{ host }}.'
"""


def main(**kwargs):
    # The html module is explicitly for raw HTML output. Rendering through the
    # autoescape environment would defeat its purpose by escaping any HTML that
    # comes in through fact substitutions, so the autoescape-free environment is
    # used instead.
    clf_jinja_env_plain = kwargs['clf_jinja_env_plain']

    rendered_content = clf_jinja_env_plain.from_string(kwargs['content']).render(**kwargs)

    return {
        'html': f'<div class="clf-content-block">{rendered_content}</div>',
    }
