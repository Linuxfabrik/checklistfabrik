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
        <div class="d-flex" style="height: 1.2rem;">
            <i class="fa-solid clf-fa-required text-error" title="Required" role="img"></i>
        </div>
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
    fact_name = kwargs['fact_name' if 'fact_name' in kwargs else 'auto_fact_name']
    templated_group_label = mistune.html(jinja2.Template(kwargs.get('label', '')).render(**kwargs))

    templated_values = [jinja2.Template(value).render(**kwargs) for value in kwargs.get('values', [''])]

    return {
        'html': jinja2.Template(
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
