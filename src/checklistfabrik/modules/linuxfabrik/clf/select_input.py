"""
ChecklistFabrik select_input module

This module renders a simple HTML select (multi-selection as well as optgroup and hr elements are not supported).

EXAMPLE::

    - linuxfabrik.clf.select_input:
        label: 'Backup datacenter location for {{ host }}?'
        values:
          - 'Moon'
          - 'Mars'
          - 'Earth'
        required: true
      fact_name: 'backup_datacenter_location'
"""

import jinja2

TEMPLATE_STRING = '''
<div class="form-group">
    <label class="form-label" for={{ fact_name }}>{{ templated_label }}</label>
    <select class="form-select" id="{{ fact_name }}" name="{{ fact_name }}"
        {%- if required %} required="required" {%- endif %}>
        <option value="">--- Please select ---</option>
        {% for value in values %}
        <option {%- if fact_value == value %} selected="selected" {%- endif %}>{{ value }}</option>
        {% endfor %}
    </select>
</div>
'''


def main(**kwargs):
    templated_label = jinja2.Template(kwargs.get('label', '')).render(**kwargs)

    return {
        'html': jinja2.Template(
            TEMPLATE_STRING,
        ).render(
            **kwargs,
            fact_value=kwargs.get(kwargs.get('fact_name')),
            templated_label=templated_label,
        ),
    }
