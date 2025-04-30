"""
ChecklistFabrik text_output module

This module simply renders Jinja templated text as an HTML paragraph.

EXAMPLE::

    - linuxfabrik.clf.text_output:
        content: 'This is an example text with Jinja expressions, for example {{ host }}.'
"""

TEMPLATE_FORMAT_STRING = '''\
<p>{content}</p>
'''


def main(**kwargs):
    clf_jinja_env = kwargs['clf_jinja_env']

    return {
        'html': clf_jinja_env.from_string(
            TEMPLATE_FORMAT_STRING.format(content=kwargs['content']),
        ).render(**kwargs)
    }
