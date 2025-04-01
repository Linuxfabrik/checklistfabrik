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
import mistune

TEMPLATE_STRING = '''
<div class="form-group">
    <label class="form-label" for={{ fact_name }}>{{ templated_label }}</label>
    <select class="form-select" id="{{ fact_name }}" name="{{ fact_name }}"
        {%- if required %} required="required" {%- endif %}
        {%- if multiple %} multiple="multiple" {%- endif %}>
        {% if not multiple %}
        <option value="">--- Please select ---</option>
        {% endif %}
        {% for value in templated_values %}
        <option {%- if value == fact_value or (not fact_value is string and value in fact_value) %} selected="selected" {%- endif %}>{{ value }}</option>
        {% endfor %}
    </select>
</div>
'''


def main(**kwargs):
    fact_name = kwargs['fact_name' if 'fact_name' in kwargs else 'auto_fact_name']
    templated_label = mistune.html(jinja2.Template(kwargs.get('label', '')).render(**kwargs))

    templated_values = [jinja2.Template(value).render(**kwargs) for value in kwargs.get('values', [''])]

    return {
        'html': jinja2.Template(
            TEMPLATE_STRING,
        ).render(
            **kwargs,
            fact_value=kwargs.get(fact_name, []),
            templated_label=templated_label,
            templated_values=templated_values,
        ),
        'fact_name': fact_name,
    }
