"""
ChecklistFabrik text_input module

This module renders an HTML text input field.

EXAMPLE:
    - linuxfabrik.clf.text_input:
        label: 'How many backups to keep for host {{ host }}?'
        required: true
      fact_name: 'nr_backups'
"""

import jinja2
import mistune

TEMPLATE_STRING = '''
<div class="form-group">
    
    <div class="form-label" id="{{ fact_name }}-label">
        {{ templated_label }}
    </div>
    
    <div class="has-icon-right">
        <input class="form-input" id="{{ fact_name }}" name="{{ fact_name }}" type="text" aria-labelledby="{{ fact_name }}-label"
            {%- if required %} required="required" {%- endif %}
            {%- if fact_value %} value="{{ fact_value }}" {%- endif %}/>
        
        {% if required %}<i class="form-icon fa-solid clf-fa-required text-error"></i>{% endif %}
    </div>
</div>
'''


def main(**kwargs):
    fact_name = kwargs['fact_name' if 'fact_name' in kwargs else 'auto_fact_name']
    templated_label = mistune.html(jinja2.Template(kwargs.get('label', '')).render(**kwargs))

    return {
        'html': jinja2.Template(
            TEMPLATE_STRING,
        ).render(
            **kwargs,
            fact_value=kwargs.get(fact_name),
            templated_label=templated_label,
        ),
        'fact_name': fact_name,
    }
