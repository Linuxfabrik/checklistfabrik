"""
ChecklistFabrik textarea_input module

This module renders an HTML textarea for multi-line input. Useful for capturing
command output or other multi-line content.

EXAMPLE:
    - linuxfabrik.clf.textarea_input:
        label: 'Paste the output of `dnf check-update`'
        monospace: true
        rows: 10
        required: true
      fact_name: 'dnf_output'
"""

TEMPLATE_STRING = """
<div class="form-group">
    <div class="form-label" id="{{ fact_name }}-label">
        {% if required %}{% include "required_indicator.html.j2" %}{% endif %}
        <div>{% if not templated_label and required %}<i>An input is required</i>{% endif %}{{ templated_label }}</div>
    </div>
    <textarea class="form-input{% if monospace %} clf-textarea-monospace{% endif %}"
        id="{{ fact_name }}" name="{{ fact_name }}"
        aria-labelledby="{{ fact_name }}-label"
        rows="{{ rows | default(5) }}"
        {%- if placeholder %} placeholder="{{ placeholder }}"{%- endif %}
        {%- if required %} required{%- endif %}>{{- fact_value | default('', true) -}}</textarea>
</div>
"""


def main(**kwargs):
    clf_jinja_env = kwargs['clf_jinja_env']
    clf_jinja_env_plain = kwargs['clf_jinja_env_plain']
    clf_markdown = kwargs['clf_markdown']
    fact_name = kwargs['fact_name' if 'fact_name' in kwargs else 'auto_fact_name']

    templated_label = clf_markdown(
        clf_jinja_env_plain.from_string(kwargs.get('label', '')).render(**kwargs)
    )

    return {
        'html': clf_jinja_env.from_string(
            TEMPLATE_STRING,
        ).render(
            **(
                kwargs
                | {
                    'fact_name': fact_name,
                    'fact_value': kwargs.get(fact_name),
                    'templated_label': templated_label,
                }
            ),
        ),
        'fact_name': fact_name,
    }
