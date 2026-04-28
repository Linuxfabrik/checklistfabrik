"""
ChecklistFabrik run_template module

This module renders a card with the title and description of another
checklist template plus a "Run" button. Clicking the button starts the
referenced checklist in a new browser tab.

The path is resolved relative to the file that defines this task (mirroring
how `linuxfabrik.clf.import` resolves nested paths). Absolute paths are
used as-is.

EXAMPLE::

    - linuxfabrik.clf.run_template:
        path: 'shared/db-maintenance.yml'

    # Override the title and description shown for the embedded card:
    - linuxfabrik.clf.run_template:
        path: 'shared/db-maintenance.yml'
        label: 'Run database maintenance for {{ host }}'
        description: 'Restarts services after the maintenance window.'
"""

import pathlib

import markupsafe
import ruamel.yaml

TEMPLATE_STRING = """\
<div class="clf-run-template">
    <div class="clf-run-template-row">
        <div class="clf-run-template-title">{{ templated_title | safe }}</div>
        <button class="btn btn-sm btn-primary tooltip tooltip-left"
                type="button"
                data-tooltip="Launches {{ display_path }} in a new tab."
                data-action="run-template"
                data-path="{{ resolved_path }}">
            <i class="fa-solid fa-play"></i> Run
        </button>
    </div>
    {% if templated_description %}
    <div class="clf-run-template-description text-gray">{{ templated_description | safe }}</div>
    {% endif %}
</div>
"""

ERROR_TEMPLATE = (
    '<div class="toast toast-error"><em>linuxfabrik.clf.run_template</em>: {message}</div>'
)


def _error(message):
    return {
        'html': ERROR_TEMPLATE.format(message=markupsafe.escape(message)),
    }


def main(**kwargs):
    clf_jinja_env = kwargs['clf_jinja_env']
    clf_jinja_env_plain = kwargs['clf_jinja_env_plain']
    clf_markdown = kwargs['clf_markdown']
    workdir = kwargs.get('clf_task_workdir')

    raw_path = kwargs.get('path')

    if not raw_path or not isinstance(raw_path, str):
        return _error('A "path" field pointing to a YAML template file is required.')

    # Render the path through Jinja so users can build it from facts.
    rendered_path = clf_jinja_env_plain.from_string(raw_path).render(**kwargs)

    target = pathlib.Path(rendered_path)

    if not target.is_absolute():
        if workdir is None:
            return _error(
                f'Cannot resolve relative path "{rendered_path}" because the calling '
                'template directory is unknown.'
            )

        target = pathlib.Path(workdir) / target

    target = target.resolve()

    if not target.is_file():
        return _error(f'Template file "{target}" does not exist.')

    try:
        with open(target, mode='r', encoding='utf-8') as file_handle:
            data = ruamel.yaml.YAML().load(file_handle.read())
    except (OSError, ruamel.yaml.YAMLError) as error:
        return _error(f'Could not read template "{target}": {error}')

    if not isinstance(data, dict):
        return _error(f'Template "{target}" does not contain a YAML mapping.')

    # Field overrides win, otherwise fall back to the target template's metadata.
    raw_title = kwargs.get('label')
    if raw_title is None:
        raw_title = data.get('title', '')

    raw_description = kwargs.get('description')
    if raw_description is None:
        raw_description = data.get('description', '')

    templated_title = clf_markdown(clf_jinja_env_plain.from_string(str(raw_title)).render(**kwargs))
    templated_description = (
        clf_markdown(clf_jinja_env_plain.from_string(str(raw_description)).render(**kwargs))
        if raw_description
        else ''
    )

    return {
        'html': clf_jinja_env.from_string(TEMPLATE_STRING).render(
            **(
                kwargs
                | {
                    'display_path': str(rendered_path),
                    'resolved_path': str(target),
                    'templated_description': templated_description,
                    'templated_title': templated_title,
                }
            ),
        ),
    }
