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

TEMPLATE_STRING = """
<fieldset>
    <legend>
        {% if required %}{% include "required_indicator.html.j2" %}{% endif %}
        <span>{% if not templated_group_label and required %}<i>A selection is required</i>{% endif %}{{ templated_group_label }}</span>
    </legend>

    {% for radio in templated_radios %}
    <label class="form-radio">
        <input name="{{ fact_name }}" type="radio" value="{{ radio.value }}"
            {%- if radio.value == fact_value %} checked{%- endif %}
            {%- if required %} required{%- endif %} />
        <i class="form-icon"></i>
        <span>{{ radio.templated_label | default(radio.value, true) }}</span>
    </label>
    {% endfor %}
</fieldset>
"""


def main(**kwargs):
    clf_jinja_env = kwargs['clf_jinja_env']
    clf_jinja_env_plain = kwargs['clf_jinja_env_plain']
    clf_markdown = kwargs['clf_markdown']
    fact_name = kwargs['fact_name' if 'fact_name' in kwargs else 'auto_fact_name']

    templated_group_label = clf_markdown(
        clf_jinja_env_plain.from_string(kwargs.get('label', '')).render(**kwargs)
    )

    templated_radios = [
        {
            'label': radio.get('label'),
            'templated_label': clf_markdown(
                clf_jinja_env_plain.from_string(radio['label']).render(**kwargs),
            )
            if radio.get('label')
            else None,
            'value': radio.get('value', uuid.uuid4().hex),
        }
        for radio in kwargs.get('values', [])
    ]

    return {
        'html': clf_jinja_env.from_string(
            TEMPLATE_STRING,
        ).render(
            **(
                kwargs
                | {
                    'fact_name': fact_name,
                    'fact_value': kwargs.get(fact_name),
                    'templated_group_label': templated_group_label,
                    'templated_radios': templated_radios,
                }
            ),
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
