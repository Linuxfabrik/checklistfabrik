"""
ChecklistFabrik radio_input module

This module renders an HTML radio group.

EXAMPLE:
    - linuxfabrik.clf.radio_input:
        label: 'Backup strategy for host {{ host }}?'
        values:
          - 'hope for the best'
          - '3-2-1'
        required: true
      fact_name: 'backup_strategy'
"""

import jinja2

TEMPLATE_STRING = '''
<div class="form-group">
    <label class="form-label">{{ templated_group_label }}</label>
    {% for value in values %}
    <label class="form-radio">
        <input name="{{ fact_name }}" type="radio" value="{{ value }}"
            {%- if fact_value == value %} checked="checked" {%- endif %}
            {%- if required %} required="required" {%- endif %}/>
        <i class="form-icon"></i>{{ value }}
    </label>
    {% endfor %}
</div>
'''


def main(**kwargs):
    templated_group_label = jinja2.Template(kwargs.get('label', '')).render(**kwargs)

    return {
        'html': jinja2.Template(
            TEMPLATE_STRING,
        ).render(
            **kwargs,
            fact_value=kwargs.get(kwargs.get('fact_name')),
            templated_group_label=templated_group_label,
        ),
    }
