"""
ChecklistFabrik checkbox_input module

This module renders either a single HTML checkbox input field or a group of them.

EXAMPLE::

    - linuxfabrik.clf.checkbox_input:
        label: 'Single checkbox input'
        required: false
      fact_name: 'single_check_result'

    - linuxfabrik.clf.checkbox_input:
        label: 'Use "values" if you want a group of checkboxes'
        values:
            - label: 'Step 1'
            - label: 'Step 2'
              value: 'step2'
            - value: 'Step 3'
        required: true
      fact_name: 'multi_check_result'
"""

import uuid

TEMPLATE_MULTI_CHECK_STRING = '''\
<fieldset {%- if templated_label %} aria-labelledby="{{ fact_name }}-label" {%- endif %}>
    {% if templated_label %}
    <div class="form-label" id="{{ fact_name }}-label">
        {{ templated_label }}
    </div>
    {% endif %}

    {% for check in templated_checks %}
    <div class="form-group d-flex">
        <label class="form-checkbox">
            <input name="{{ fact_name }}[]" type="checkbox" value="{{ check.value }}" aria-labelledby="{{ check.value }}-label"
                {%- if check.value in fact_value %} checked="checked" {%- endif %}
                {%- if check.required or required %} required="required" {%- endif %}/>
            <i class="form-icon"></i>
        </label>
        
        <div class="form-label d-flex">
            {% if check.required %}
            {% include "required_indicator.html.j2" %}
            {% endif %}
            
            <div id="{{ check.value }}-label">
                {{ check.templated_label | default(check.value, true) }}
            </div>
        </div>
    </div>
    {% endfor %}
    
    {# Hidden field to allow unchecking all checkboxes, since a HTML form does not send unchecked checkboxes. #}
    <input type="hidden" name="{{ fact_name }}[]" value=""/>
</fieldset>
'''

TEMPLATE_SINGLE_CHECK_STRING = '''\
<div class="form-group d-flex">
    <label class="form-checkbox">
        <input name="{{ fact_name }}" type="checkbox" aria-labelledby="{{ fact_name }}-label"
            {%- if fact_value %} checked="checked" {%- endif %}
            {%- if required %} required="required" {%- endif %}/>
        <i class="form-icon"></i>
    </label>
    
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
</div>

{# Hidden field to allow unchecking a checkbox, since a HTML form does not send unchecked checkboxes. #}
<input type="hidden" name="{{ fact_name }}" value=""/>
'''


def main(**kwargs):
    clf_jinja_env = kwargs['clf_jinja_env']
    clf_markdown= kwargs['clf_markdown']
    fact_name = kwargs['fact_name' if 'fact_name' in kwargs else 'auto_fact_name']

    templated_label = clf_markdown(clf_jinja_env.from_string(kwargs.get('label', '')).render(**kwargs))

    task_context_update = None

    if kwargs.get('values'):
        templated_checks = [
            {
                'label': check.get('label'),
                'templated_label': clf_markdown(clf_jinja_env.from_string(check['label']).render(**kwargs)) if check.get('label') else None,
                'value': check.get('value', uuid.uuid4().hex),
                'required': check.get('required'),
            }
            for check in kwargs['values']
        ]

        html = clf_jinja_env.from_string(
            TEMPLATE_MULTI_CHECK_STRING,
        ).render(
            **(kwargs | {
                'fact_name': fact_name,
                'fact_value': kwargs.get(fact_name, []),
                'templated_label': templated_label,
                'templated_checks': templated_checks,
            }),
        )

        task_context_update = {
            'values': [
                {
                    key: value
                    for key, value in check.items()
                    if key in ('label', 'value', 'required') and value is not None
                }
                for check in templated_checks
            ]
        }
    else:
        # If we don't have any values, just render a single checkbox.
        html = clf_jinja_env.from_string(
            TEMPLATE_SINGLE_CHECK_STRING,
        ).render(
            **(kwargs | {
                'fact_name': fact_name,
                'fact_value': kwargs.get(fact_name),
                'templated_label': templated_label,
            }),
        )

    return {
        'html': html,
        'fact_name': fact_name,
        'task_context_update': task_context_update,
    }
