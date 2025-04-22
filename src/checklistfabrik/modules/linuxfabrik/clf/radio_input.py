"""
ChecklistFabrik radio_input module

This module renders an HTML radio group.

EXAMPLE::

    - linuxfabrik.clf.radio_input:
        label: 'Backup strategy for host {{ host }}?'
        values:
          - 'hope for the best'
          - '3-2-1'
        required: true
      fact_name: 'backup_strategy'
"""

import jinja2
import mistune

TEMPLATE_STRING = '''
<fieldset>
    <div class="form-label d-flex">
        {% if required %}
        {% include "required_indicator.html.j2" %}
        {% endif %}
    
        <div id="{{ fact_name }}-label">
            {% if not templated_group_label and required %}
            <i>A selection is required</i>
            {% endif %}
            {{ templated_group_label }}
        </div>
    </div>
    
    {% for value in templated_values %}
    <label class="form-radio">
        <input name="{{ fact_name }}" type="radio" value="{{ value }}"
            {%- if fact_value == value %} checked="checked" {%- endif %}
            {%- if required %} required="required" {%- endif %}/>
        <i class="form-icon"></i>{{ value }}
    </label>
    {% endfor %}
</fieldset>
'''


def main(**kwargs):
    clf_template_env = kwargs['clf_template_env']
    fact_name = kwargs['fact_name' if 'fact_name' in kwargs else 'auto_fact_name']

    module_template_env = jinja2.Environment()

    templated_group_label = mistune.html(module_template_env.from_string(kwargs.get('label', '')).render(**kwargs))

    templated_values = [module_template_env.from_string(value).render(**kwargs) for value in kwargs.get('values', [''])]

    return {
        'html': clf_template_env.from_string(
            TEMPLATE_STRING,
        ).render(
            **(kwargs | {
                'fact_name': fact_name,
                'fact_value': kwargs.get(fact_name),
                'templated_group_label': templated_group_label,
                'templated_values': templated_values,
            }),
        ),
        'fact_name': fact_name,
    }
