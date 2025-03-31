"""
ChecklistFabrik text_input module

This module renders an HTML text input field.

EXAMPLE:
    - linuxfabrik.clf.text_input:
        label: 'How many backups to keep for host {{ host }}?'
        required: true
      fact_name: 'nr_backups'
"""

import jinja2
import mistune

TEMPLATE_STRING = '''
<div class="form-group">
    <label class="form-label" for="{{ fact_name }}">{{ templated_label }}</label>
    <input class="form-input" id="{{ fact_name }}" name="{{ fact_name }}" type="text"
        {%- if required %} required="required" {%- endif %}
        {%- if fact_value %} value="{{ fact_value }}" {%- endif %}/>
</div>
'''


def main(**kwargs):
    templated_label = mistune.html(jinja2.Template(kwargs.get('label', '')).render(**kwargs))

    return {
        'html': jinja2.Template(
            TEMPLATE_STRING,
        ).render(
            **kwargs,
            fact_value=kwargs.get(kwargs.get('fact_name')),
            templated_label=templated_label,
        ),
    }
