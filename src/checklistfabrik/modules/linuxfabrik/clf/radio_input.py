"""
ChecklistFabrik radio_input module

This module renders an HTML radio group.

EXAMPLE::

    - linuxfabrik.clf.radio_input:
        label: 'Choose your favourite food'
        values:
          - label: 'Pizza'
            value: 'pizza'
          - value: 'burger'
          - label: 'Other'
        required: true
      fact_name: 'fav_food'
"""

import uuid

TEMPLATE_STRING = '''
<fieldset {%- if templated_label %} aria-labelledby="{{ fact_name }}-label" {%- endif %}>
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
    
    {% for radio in templated_radios %}
    <div class="form-group d-flex">
        <label class="form-radio">
            <input name="{{ fact_name }}" type="radio" value="{{ radio.value }}" aria-labelledby="{{ radio.value }}-label"
                {%- if radio.value == fact_value %} checked="checked" {%- endif %}
                {%- if required %} required="required" {%- endif %}/>
            <i class="form-icon"></i>
        </label>
        
        <div class="form-label" id="{{ radio.value }}-label">
            {{ radio.templated_label | default(radio.value, true) }}
        </div>
    </div>
    {% endfor %}
</fieldset>
'''


def main(**kwargs):
    clf_jinja_env = kwargs['clf_jinja_env']
    clf_markdown = kwargs['clf_markdown']
    fact_name = kwargs['fact_name' if 'fact_name' in kwargs else 'auto_fact_name']

    templated_group_label = clf_markdown(clf_jinja_env.from_string(kwargs.get('label', '')).render(**kwargs))

    templated_radios = [
        {
            'label': radio.get('label'),
            'templated_label': clf_markdown(
                clf_jinja_env.from_string(radio['label']).render(**kwargs),
            ) if radio.get('label') else None,
            'value': radio.get('value', uuid.uuid4().hex),
        }
        for radio in kwargs['values']
    ]

    return {
        'html': clf_jinja_env.from_string(
            TEMPLATE_STRING,
        ).render(
            **(kwargs | {
                'fact_name': fact_name,
                'fact_value': kwargs.get(fact_name),
                'templated_group_label': templated_group_label,
                'templated_radios': templated_radios,
            }),
        ),
        'fact_name': fact_name,
        'task_context_update': {
            'values': [
                {
                    key: value
                    for key, value in radio.items()
                    if key in ('label', 'value') and value is not None
                }
                for radio in templated_radios
            ]
        },
    }
