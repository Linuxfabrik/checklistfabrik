"""
ChecklistFabrik select_input module

This module renders a simple HTML select (multi-selection as well as optgroup and hr elements are not supported).

EXAMPLE::

    - linuxfabrik.clf.select_input:
        label: 'Backup datacenter location for {{ host }}?'
        values:
          - 'Moon'
          - 'Mars'
          - 'Earth'
        required: true
        multiple: false
      fact_name: 'backup_datacenter_location'
"""

TEMPLATE_MULTI_SELECT_STRING = '''\
<div class="form-group">
    <div class="form-label d-flex">
        {% if required %}
        {% include "required_indicator.html.j2" %}
        {% endif %}
        
        <div id="{{ fact_name }}-label">
            {% if not templated_label and required %}
            <i>A selection is required</i>
            {% endif %}
            {{ templated_label }}
        </div>
    </div>
    
    <select class="form-select" id="{{ fact_name }}" name="{{ fact_name }}[]" multiple="multiple" aria-labelledby="{{ fact_name }}-label"
        {%- if required %} required="required" {%- endif %}/>
        {% for value in templated_values %}
        <option {%- if value in fact_value %} selected="selected" {%- endif %}>{{ value }}</option>
        {% endfor %}
    </select>
    
    {# Hidden input to allow selecting no option, since a HTML form does not send empty selections. #}
    <input type="hidden" name="{{ fact_name }}[]" value=""/>
</div>
'''

TEMPLATE_SINGLE_SELECT_STRING = '''\
<div class="form-group">
    <div class="form-label d-flex">
        {% if required %}
        {% include "required_indicator.html.j2" %}
        {% endif %}
        
        <div id="{{ fact_name }}-label">
            {% if not templated_label and required %}
            <i>A selection is required</i>
            {% endif %}
            {{ templated_label }}
        </div>
    </div>
    
    <select class="form-select" id="{{ fact_name }}" name="{{ fact_name }}" aria-labelledby="{{ fact_name }}-label"
        {%- if required %} required="required" {%- endif %}/>
        <option value="">--- Please select ---</option>
        {% for value in templated_values %}
        <option {%- if value == fact_value %} selected="selected" {%- endif %}>{{ value }}</option>
        {% endfor %}
    </select>
</div>
'''


def main(**kwargs):
    clf_jinja_env = kwargs['clf_jinja_env']
    clf_markdown = kwargs['clf_markdown']
    fact_name = kwargs['fact_name' if 'fact_name' in kwargs else 'auto_fact_name']

    templated_label = clf_markdown(clf_jinja_env.from_string(kwargs.get('label', '')).render(**kwargs))

    templated_values = [clf_jinja_env.from_string(value).render(**kwargs) for value in kwargs.get('values', [''])]

    if kwargs.get('multiple'):
        html = clf_jinja_env.from_string(
            TEMPLATE_MULTI_SELECT_STRING,
        ).render(
            **(kwargs | {
                'fact_name': fact_name,
                'fact_value': kwargs.get(fact_name, []),
                'templated_label': templated_label,
                'templated_values': templated_values,
            }),
        )
    else:
        html = clf_jinja_env.from_string(
            TEMPLATE_SINGLE_SELECT_STRING,
        ).render(
            **(kwargs | {
                'fact_name': fact_name,
                'fact_value': kwargs.get(fact_name),
                'templated_label': templated_label,
                'templated_values': templated_values,
            }),
        )

    return {
        'html': html,
        'fact_name': fact_name,
    }
