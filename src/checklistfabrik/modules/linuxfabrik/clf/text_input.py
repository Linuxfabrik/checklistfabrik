"""
ChecklistFabrik text_input module

This module renders an HTML text input field.

EXAMPLE:
    - linuxfabrik.clf.text_input:
        label: 'How many backups to keep?'
        required: true
      fact_name: 'nr_backups'
"""

import jinja2

TEMPLATE_STRING = '''
<div class="form-group">
    <label class="form-label" for="{{ fact_name }}">{{ label }}</label>
    <input class="form-input" id="{{ fact_name }}" name="{{ fact_name }}" type="text"
        {%- if required %} required="required" {% endif -%}
        {%- if value %} value="{{ value }}" {% endif -%}
    />
</div>
'''


def main(**kwargs):
    return {
        'html': jinja2.Template(TEMPLATE_STRING).render(**kwargs, value=kwargs.get(kwargs.get('fact_name'))),
    }
