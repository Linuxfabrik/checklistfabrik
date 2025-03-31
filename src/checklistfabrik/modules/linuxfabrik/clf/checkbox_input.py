"""
ChecklistFabrik checkbox_input module

This module renders a group of HTML checkbox input fields.

EXAMPLE::

    - linuxfabrik.clf.checkbox_input:
        label: 'Steps to reproduce issue {{ issue_id }}?'
        values:
            - 'Step 1'
            - 'Step 2'
            - 'Step 3'
        required: true
      fact_name: 'reproduce_issue'
"""

import jinja2

TEMPLATE_STRING = '''\
<fieldset>
    {% if label %}
    <label>{{ templated_label }}</label>
    {% endif %}

    {% for value in templated_values %}
    <div class="form-group">
        <label class="form-checkbox">
            <input name="{{ fact_name }}" type="checkbox" value="{{ value }}"
                {%- if value == fact_value or (not fact_value is string and value in fact_value) %} checked="checked" {%- endif %}
                {%- if required %} required="required" {%- endif %}/>
            <i class="form-icon"></i>{{ value }}
        </label>
    </div>
    {% endfor %}
</fieldset>
'''


def main(**kwargs):
    templated_label = jinja2.Template(kwargs.get('label', '')).render(**kwargs)

    templated_values = [jinja2.Template(value).render(**kwargs) for value in kwargs.get('values', [])]

    return {
        'html': jinja2.Template(
            TEMPLATE_STRING,
        ).render(
            **kwargs,
            fact_value=kwargs.get(kwargs.get('fact_name')),
            templated_label=templated_label,
            templated_values=templated_values,
        ),
    }
