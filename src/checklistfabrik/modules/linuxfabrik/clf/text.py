"""
ChecklistFabrik text module

This module simply renders Jinja templated text as an HTML paragraph.

EXAMPLE::

    - linuxfabrik.clf.text:
        content: 'This is an example text with Jinja expressions, for example {{ host }}.'
"""

import jinja2

TEMPLATE_FORMAT_STRING = '''\
<p>{content}</p>
'''


def main(**kwargs):
    return {
        'html': jinja2.Template(TEMPLATE_FORMAT_STRING.format(content=kwargs['content'])).render(**kwargs)
    }
