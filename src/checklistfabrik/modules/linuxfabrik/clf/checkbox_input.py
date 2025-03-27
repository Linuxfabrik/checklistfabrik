"""
ChecklistFabrik checkbox_input module

This module renders an HTML checkbox input field.

EXAMPLE:
    - linuxfabrik.clf.checkbox_input:
        label: 'Are backups tested for host {{ host }}?'
        required: true
      fact_name: 'backups_tested'
"""

import jinja2

TEMPLATE_STRING = '''
<div class="form-group">
    <label class="form-checkbox">
        <input name="{{ fact_name }}" type="checkbox"
            {%- if fact_value %} checked="checked" {%- endif %}
            {%- if required %} required="required" {%- endif %}/>
        <i class="form-icon"></i>{{ templated_label }}
    </label>
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
