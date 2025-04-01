"""
ChecklistFabrik checkbox_input module

This module renders either a single HTML checkbox input field or a group of them.

EXAMPLE::

    - linuxfabrik.clf.checkbox_input:
        label: 'Use "values" if you want a group of checkboxes {{ check_id }}?'
        values:
            - 'Step 1'
            - 'Step 2'
            - 'Step 3'
        required: true
      fact_name: 'check_result'
"""

import jinja2
import mistune

TEMPLATE_MULTI_CHECK_STRING = '''\
<fieldset>
    {% if label %}
    <label>{{ templated_label }}</label>
    {% endif %}

    {% for value in templated_values %}
    <div class="form-group">
        <label class="form-checkbox">
            <input name="{{ fact_name }}[]" type="checkbox" value="{{ value }}"
                {%- if value in fact_value %} checked="checked" {%- endif %}
                {%- if required %} required="required" {%- endif %}/>
            <i class="form-icon"></i>{{ value }}
        </label>
    </div>
    {% endfor %}
    
    {# Hidden field to allow unchecking all checkboxes, since a HTML form does not send unchecked checkboxes. #}
    <input type="hidden" name="{{ fact_name }}[]" value=""/>
</fieldset>
'''

TEMPLATE_SINGLE_CHECK_STRING = '''\
<div class="form-group">
    <label class="form-checkbox">
        <input name="{{ fact_name }}" type="checkbox"
            {%- if fact_value %} checked="checked" {%- endif %}
            {%- if required %} required="required" {%- endif %}/>
        <i class="form-icon"></i>
        {{ templated_label }}
    </label>
</div>

{# Hidden field to allow unchecking a checkbox, since a HTML form does not send unchecked checkboxes. #}
<input type="hidden" name="{{ fact_name }}" value=""/>
'''


def main(**kwargs):
    fact_name = kwargs['fact_name' if 'fact_name' in kwargs else 'auto_fact_name']
    templated_label = mistune.html(jinja2.Template(kwargs.get('label', '')).render(**kwargs))

    if kwargs.get('values'):
        templated_values = [jinja2.Template(value).render(**kwargs) for value in kwargs.get('values', [''])]

        html = jinja2.Template(
            TEMPLATE_MULTI_CHECK_STRING,
        ).render(
            **kwargs,
            fact_value=kwargs.get(fact_name, []),
            templated_label=templated_label,
            templated_values=templated_values,
        )
    else:
        # If we don't have any values just render a single checkbox.
        html = jinja2.Template(
            TEMPLATE_SINGLE_CHECK_STRING,
        ).render(
            **kwargs,
            fact_value=kwargs.get(fact_name),
            templated_label=templated_label,
        )

    return {
        'html': html,
        'fact_name': fact_name,
    }
