"""
ChecklistFabrik text_input module

This module renders an HTML text input field.

EXAMPLE:
    - linuxfabrik.clf.text_input:
        label: 'How many backups to keep for host {{ host }}?'
        required: true
      fact_name: 'nr_backups'
"""

TEMPLATE_STRING = '''
<div class="form-group">
    <div class="form-label d-flex">
        {% if required %}
        {% include "required_indicator.html.j2" %}
        {% endif %}
    
        <div id="{{ fact_name }}-label">
            {% if not templated_label and required %}
            <i>An input is required</i>
            {% endif %}
            {{ templated_label }}
        </div>
    </div>
    
    <input class="form-input" id="{{ fact_name }}" name="{{ fact_name }}" type="text" aria-labelledby="{{ fact_name }}-label"
        {%- if required %} required="required" {%- endif %}
        {%- if fact_value %} value="{{ fact_value }}" {%- endif %}/>
</div>
'''


def main(**kwargs):
    clf_jinja_env = kwargs['clf_jinja_env']
    clf_markdown = kwargs['clf_markdown']
    fact_name = kwargs['fact_name' if 'fact_name' in kwargs else 'auto_fact_name']

    templated_label = clf_markdown(clf_jinja_env.from_string(kwargs.get('label', '')).render(**kwargs))

    return {
        'html': clf_jinja_env.from_string(
            TEMPLATE_STRING,
        ).render(
            **(kwargs | {
                'fact_name': fact_name,
                'fact_value': kwargs.get(fact_name),
                'templated_label': templated_label,
            }),
        ),
        'fact_name': fact_name,
    }
