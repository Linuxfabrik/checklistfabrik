"""
ChecklistFabrik HTML module

This module simply renders Jinja templated HTML.

EXAMPLE::

    - linuxfabrik.clf.html:
        content: 'This is an example text with Jinja expressions, for example {{ host }}.'
"""

TEMPLATE_FORMAT_STRING = '''\
<div style="margin-block: 0.8rem;">{content}</div>
'''


def main(**kwargs):
    clf_jinja_env = kwargs['clf_jinja_env']

    return {
        'html': clf_jinja_env.from_string(
            TEMPLATE_FORMAT_STRING.format(content=kwargs['content']),
        ).render(**kwargs)
    }
