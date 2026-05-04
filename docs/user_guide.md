# User Guide

This guide walks you through creating and running checklists with ChecklistFabrik, from your very first template to advanced features like conditional pages and reusable includes.


## Your First Checklist

A checklist is a YAML file with a `title` and one or more `pages`, where each page contains `tasks`. Here is a minimal example:

```yaml
title: 'Server Maintenance'
pages:
  - title: 'Pre-Maintenance'
    tasks:
      - linuxfabrik.clf.checkbox_input:
          label: 'Notify users about the upcoming maintenance window'
          required: true
      - linuxfabrik.clf.checkbox_input:
          label: 'Create a full backup'
          required: true
```

Save this as `server-maintenance.yml` and run it:

```shell
clf-play --template server-maintenance.yml
```

A browser window opens with your checklist. Fill it out and click **Finish** on the last page. ChecklistFabrik saves a report file with your answers and shuts the local server down. Your progress is also written to the report file on every page submit, so closing the tab mid-run does not lose what you already entered — re-open the report file later to continue, or click **Continue Later** to stop the server explicitly.


## Templates vs. Reports

* A **template** is the YAML file you write—it defines the structure and tasks of your checklist.
* A **report** is the YAML file that ChecklistFabrik generates when you run a template. It contains your answers.

You run a template to create a new report:

```shell
clf-play --template my-template.yml my-report.yml
```

You re-open an existing report to continue or review it:

```shell
clf-play my-report.yml
```

If you omit the report filename, ChecklistFabrik auto-generates one (see [Automatic Report Names](#automatic-report-names) below).


## Adding Descriptions

Use the optional `description` field to describe what your checklist is about. This is especially useful when using the [dashboard](#the-dashboard):

```yaml
title: 'Server Maintenance'
description: 'Monthly maintenance procedure for production servers.'
pages:
  ...
```


## Task Modules

Each task delegates its rendering to a **module**. ChecklistFabrik ships with these built-in modules:

| Module | Purpose |
|--------|---------|
| `linuxfabrik.clf.checkbox_input` | Single checkbox or checkbox group |
| `linuxfabrik.clf.html` | Static HTML content |
| `linuxfabrik.clf.markdown` | Markdown-formatted content |
| `linuxfabrik.clf.radio_input` | Radio button group (single selection) |
| `linuxfabrik.clf.run_template` | Embedded card with a "Run" button that launches another checklist template in a new tab |
| `linuxfabrik.clf.select_input` | Dropdown (single or multi-select) |
| `linuxfabrik.clf.text_input` | Single-line text input |
| `linuxfabrik.clf.textarea_input` | Multi-line text input (textarea) |


### Text Inputs

Use `linuxfabrik.clf.text_input` to collect freeform text. Add `required: true` to enforce non-empty input:

```yaml
- linuxfabrik.clf.text_input:
    label: 'Ticket number'
    required: true
  fact_name: 'ticket_number'
```

The `fact_name` stores the user's input so it can be referenced later (for example in Jinja expressions or on other pages).

For multi-line input (e.g. command output), use `linuxfabrik.clf.textarea_input`:

```yaml
- linuxfabrik.clf.textarea_input:
    label: 'Paste the output of `dnf check-update`'
    monospace: true
    rows: 10
    required: true
  fact_name: 'dnf_output'
```

`rows` sets the visible height (default `5`). `monospace: true` renders the textarea in a fixed-width font, which is useful when alignment matters (logs, command output, configuration snippets).


### Checkboxes

A single checkbox:

```yaml
- linuxfabrik.clf.checkbox_input:
    label: 'I have read the runbook'
    required: true
```

A group of checkboxes:

```yaml
- linuxfabrik.clf.checkbox_input:
    label: 'Services to restart'
    values:
      - label: 'Apache'
        value: 'apache'
      - label: 'PostgreSQL'
        value: 'postgres'
      - label: 'Redis'
        value: 'redis'
  fact_name: 'services'
```


### Radio Buttons

A group where exactly one option can be selected:

```yaml
- linuxfabrik.clf.radio_input:
    label: 'Environment'
    values:
      - label: 'Staging'
        value: 'staging'
      - label: 'Production'
        value: 'production'
    required: true
  fact_name: 'environment'
```


### Dropdowns

A single-select dropdown:

```yaml
- linuxfabrik.clf.select_input:
    label: 'Datacenter'
    values:
      - 'Zurich'
      - 'Frankfurt'
      - 'Vienna'
    required: true
  fact_name: 'datacenter'
```

A multi-select dropdown (hold Ctrl to select multiple):

```yaml
- linuxfabrik.clf.select_input:
    label: 'Affected components'
    values:
      - 'Database'
      - 'Load Balancer'
      - 'Web Server'
    multiple: true
  fact_name: 'components'
```


### Displaying Text

Use `linuxfabrik.clf.markdown` to show formatted instructions:

```yaml
- linuxfabrik.clf.markdown:
    content: |
      ## Important

      Before proceeding, make sure you have:

      - SSH access to the target server
      - The latest backup available
      - The runbook open in another tab
```

### Linking to Other Checklists

Use `linuxfabrik.clf.run_template` to embed a card that launches another checklist template in a new browser tab. Useful for breaking large procedures into independent, reusable sub-checklists that each produce their own report:

```yaml
- linuxfabrik.clf.run_template:
    path: 'shared/db-maintenance.yml'
```

The card shows the target template's `title` and `description` fields plus a **Run** button. The path is resolved relative to the checklist file that defines the task (same as `linuxfabrik.clf.import`).

Both labels are optional overrides and support Jinja and Markdown:

```yaml
- linuxfabrik.clf.run_template:
    path: 'shared/db-maintenance.yml'
    label: 'Run database maintenance for **{{ host }}**'
    description: 'Restarts services after the maintenance window.'
```

Clicking **Run** starts a new server in the background and opens it in a new tab. The launched checklist is fully independent — its facts and report file are separate from the calling checklist.

For raw HTML, use `linuxfabrik.clf.html`:

```yaml
- linuxfabrik.clf.html:
    content: |
      This is <b>raw HTML</b>.
```


## Multiple Pages

Split your checklist into pages for better structure. Each page gets its own screen with navigation buttons:

```yaml
title: 'Deployment Checklist'
pages:
  - title: 'Preparation'
    tasks:
      - linuxfabrik.clf.text_input:
          label: 'Version to deploy'
          required: true
        fact_name: 'deploy_version'

  - title: 'Deployment'
    tasks:
      - linuxfabrik.clf.checkbox_input:
          label: 'Run database migrations'
          required: true

  - title: 'Verification'
    tasks:
      - linuxfabrik.clf.checkbox_input:
          label: 'Smoke tests passed'
          required: true
```


## Jinja Templating

All labels and Markdown content support [Jinja](https://jinja.palletsprojects.com/) expressions. Once a user fills in a `fact_name`, that value becomes available as a Jinja variable on subsequent pages:

```yaml
pages:
  - title: 'Setup'
    tasks:
      - linuxfabrik.clf.text_input:
          label: 'Server hostname'
          required: true
        fact_name: 'hostname'

  - title: 'Deployment'
    tasks:
      - linuxfabrik.clf.markdown:
          content: |
            Connect to **{{ hostname }}** via SSH and run the deployment script.
```


## Conditional Pages and Tasks

Use `when` to show or hide pages and tasks based on user input:

```yaml
pages:
  - title: 'Setup'
    tasks:
      - linuxfabrik.clf.radio_input:
          label: 'Installation type'
          values:
            - label: 'Fresh install'
              value: 'fresh'
            - label: 'Upgrade'
              value: 'upgrade'
          required: true
        fact_name: 'install_type'

  - title: 'Fresh Install Steps'
    when: 'install_type == "fresh"'
    tasks:
      - linuxfabrik.clf.checkbox_input:
          label: 'Partition disks'
          required: true

  - title: 'Upgrade Steps'
    when: 'install_type == "upgrade"'
    tasks:
      - linuxfabrik.clf.checkbox_input:
          label: 'Create pre-upgrade snapshot'
          required: true
```

Pages where `when` evaluates to `false` are automatically skipped. The same `when` field works on individual tasks, too.

You can combine multiple conditions (logical AND):

```yaml
  - title: 'Production Fresh Install'
    when:
      - 'install_type == "fresh"'
      - 'environment == "production"'
```


## Automatic Report Names

Templates can define a `report_path` to auto-generate meaningful filenames when creating reports:

```yaml
title: 'Server Maintenance'
report_path: 'reports/maintenance-{{ hostname }}-{{ now().strftime("%Y%m%d") }}.yml'
pages:
  ...
```

When running `clf-play --template server-maintenance.yml` (without specifying a report file), ChecklistFabrik generates the filename from this pattern. Environment variables are also supported:

```yaml
report_path: '$HOME/reports/maintenance-{{ now().strftime("%Y%m%d") }}.yml'
```


## Importing Pages and Tasks

Large checklists can be split into separate files using the `linuxfabrik.clf.import` directive.

Import pages from another file:

```yaml
title: 'Full Deployment'
pages:
  - title: 'Preparation'
    tasks:
      - linuxfabrik.clf.markdown:
          content: 'This page is defined inline.'

  - linuxfabrik.clf.import: 'shared/database-pages.yml'
```

Import tasks into a page:

```yaml
pages:
  - title: 'Security Checks'
    tasks:
      - linuxfabrik.clf.import: 'shared/security-tasks.yml'

      - linuxfabrik.clf.checkbox_input:
          label: 'Additional check specific to this checklist'
```

Paths are relative to the importing file.


## Versioning

Use the optional `version` field to track which iteration of a template created a report:

```yaml
title: 'Server Maintenance'
version: '2025031901'
pages:
  ...
```

The version is displayed on the checklist page and carried over to reports.


## The Dashboard

Run `clf-play` without any arguments to open the dashboard:

```shell
clf-play
```

The dashboard opens in your browser and shows two sections:

* **Templates** — click "Run" to start a new checklist from a template (opens in a new tab).
* **Reports** — click "View" to re-open a previous checklist.

The dashboard scans for `*.yml` files and displays their `title` and `description` fields:

1. If `templates/` and/or `reports/` subdirectories exist in the current working directory, they are used automatically.
2. If only one of them exists, the other falls back to the current directory.
3. If both point to the same directory, all files are shown in both sections — use "Run" to start a new checklist or "View" to re-open an existing one.

You can override this with explicit paths:

```shell
clf-play --templates-dir ./my-templates --reports-dir ./my-reports
```

To explore the bundled examples in a dashboard:

```shell
cd examples/
clf-play
```


## Putting It All Together

Here is a complete, real-world-style template that uses most features:

```yaml
title: 'Application Deployment'
description: 'Standard deployment procedure for the web application.'
version: '2025031901'
report_path: 'reports/deploy-{{ app_version }}-{{ now().strftime("%Y%m%d-%H%M") }}.yml'

pages:
  - title: 'General Information'
    tasks:
      - linuxfabrik.clf.text_input:
          label: 'Application version to deploy'
          required: true
        fact_name: 'app_version'

      - linuxfabrik.clf.radio_input:
          label: 'Target environment'
          values:
            - label: 'Staging'
              value: 'staging'
            - label: 'Production'
              value: 'production'
          required: true
        fact_name: 'target_env'

  - title: 'Pre-Deployment Checks for v{{ app_version }} ({{ target_env }})'
    tasks:
      - linuxfabrik.clf.checkbox_input:
          values:
            - label: 'All tests passing on CI'
            - label: 'Release notes prepared'
          required: true

      - linuxfabrik.clf.checkbox_input:
          label: 'Stakeholders notified'
          required: true
        when: 'target_env == "production"'

  - title: 'Production Approval for v{{ app_version }}'
    when: 'target_env == "production"'
    tasks:
      - linuxfabrik.clf.markdown:
          content: |
            A production deployment requires explicit approval before proceeding.

      - linuxfabrik.clf.text_input:
          label: 'Approved by (name)'
          required: true
        fact_name: 'approved_by'

  - title: 'Deploy v{{ app_version }} to {{ target_env }}'
    tasks:
      - linuxfabrik.clf.checkbox_input:
          values:
            - label: 'Database migrations executed'
            - label: 'Application deployed'
            - label: 'Health checks passing'
          required: true

      - linuxfabrik.clf.checkbox_input:
          label: 'Notify stakeholders about the deployment'
          required: true
        when: 'target_env == "production"'

  - title: 'Post-Deployment'
    tasks:
      - linuxfabrik.clf.checkbox_input:
          values:
            - label: 'Smoke tests completed'
            - label: 'Monitoring dashboards checked'
            - label: 'Deployment logged in change management system'
          required: true
```

Save it as `deploy-template.yml`, then:

```shell
# Start from the dashboard:
clf-play

# Or run it directly:
clf-play --template deploy-template.yml
```


---

# Reference


## Checklist Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | no | Freeform text shown in the dashboard. |
| `pages` | sequence | yes | One or more pages. See [Page Fields](#page-fields). |
| `report_path` | string (Jinja) | no | Auto-generate report file paths. Supports env vars (`$HOME`). Invalid filename characters are removed automatically. |
| `title` | string | yes | Checklist title, used for browser tab and page heading. |
| `version` | string | no | Freeform identifier displayed on the checklist page. Carried over from template to report. |


## Page Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `linuxfabrik.clf.import` | string | — | Import pages from a separate file. Must be the only field in the mapping. Paths are relative to the importing file. |
| `tasks` | sequence | yes | Tasks to render on this page. See [Task Fields](#task-fields). |
| `title` | string (Jinja) | yes | Page heading. May not be empty. |
| `when` | string or sequence | no | Jinja condition(s). Page is skipped if `false`. Multiple values are combined with AND. |


## Task Fields

Each task mapping starts with a module key, followed by optional metadata:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `<module>` | mapping | yes | First key in the mapping. Specifies the rendering module. See [Task Modules](#task-modules). |
| `fact_name` | string | no | Name under which user input is stored. Available as a Jinja variable on subsequent pages. Auto-generated if omitted. |
| `value` | any (Jinja) | no | Saved value from a previous run (managed by `clf-play`). Can be set in templates as a default. When set in a template, string values are rendered through Jinja once at load time, so expressions like `{{ now().strftime("%Y%m%d") }}` or references to earlier facts are resolved before the default is shown to the user. |
| `when` | string or sequence | no | Jinja condition(s). Task is hidden if `false`. Multiple values are combined with AND. |

The special module `linuxfabrik.clf.import` takes a file path string instead of a mapping and imports tasks from that file.


## Task Modules


### `linuxfabrik.clf.checkbox_input`

Single checkbox or checkbox group.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `label` | string | no | Label for the checkbox or group. Supports Jinja and Markdown. |
| `required` | boolean | no | If `true`, all checkboxes must be checked to proceed. |
| `values` | sequence | no | Checkbox group items (see below). Omit for a single checkbox. |

Each item in `values`:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `label` | string | no | Checkbox label. Falls back to `value`. Supports Jinja and Markdown. |
| `required` | boolean | no | Require this specific checkbox. Overridden by task-level `required`. |
| `value` | string | no | Value stored when checked. Auto-generated if omitted. |


### `linuxfabrik.clf.html`

Renders Jinja-templated HTML directly. For most cases, prefer `linuxfabrik.clf.markdown`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | string | yes | HTML to render. Supports Jinja. |


### `linuxfabrik.clf.markdown`

Renders Markdown content as HTML.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | string | yes | Markdown text to render. Supports Jinja. |


### `linuxfabrik.clf.radio_input`

Radio button group (single selection).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `label` | string | no | Group label. Supports Jinja and Markdown. |
| `required` | boolean | no | If `true`, one option must be selected to proceed. |
| `values` | sequence | yes | Radio button options (see below). |

Each item in `values`:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `label` | string | no | Radio button label. Falls back to `value`. Supports Jinja and Markdown. |
| `value` | string | no | Value stored when selected. Auto-generated if omitted. |


### `linuxfabrik.clf.run_template`

Embeds a card that displays the target checklist template's metadata and a **Run** button. Clicking the button starts the referenced template in a new browser tab.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | no | Override the description shown on the card. Supports Jinja and Markdown. Falls back to the target template's `description` field. |
| `label` | string | no | Override the title shown on the card. Supports Jinja and Markdown. Falls back to the target template's `title` field. |
| `path` | string (Jinja) | yes | Path to a YAML template file. Relative paths are resolved against the checklist file that defines the task. |

The launched checklist runs as an independent server and produces its own report file. Closing the tab does not affect the calling checklist.


### `linuxfabrik.clf.select_input`

Dropdown (single or multi-select). Single-selects always include a `--- Please Select ---` placeholder.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `label` | string | no | Label. Supports Jinja and Markdown. |
| `multiple` | boolean | no | Allow selecting multiple options. |
| `required` | boolean | no | Single: must pick a real option. Multi: at least one must be selected. |
| `values` | sequence | yes | Options to display. Each item is a plain string. |


### `linuxfabrik.clf.text_input`

Single-line text input.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `label` | string | no | Label. Supports Jinja and Markdown. |
| `required` | boolean | no | If `true`, the input must be non-empty to proceed. |


### `linuxfabrik.clf.textarea_input`

Multi-line text input (textarea). Useful for capturing command output, log excerpts, or other multi-line content.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `label` | string | no | Label. Supports Jinja and Markdown. |
| `monospace` | boolean | no | If `true`, render the textarea in a fixed-width font. Default `false`. |
| `placeholder` | string | no | Hint text shown while the textarea is empty. |
| `required` | boolean | no | If `true`, the input must be non-empty to proceed. |
| `rows` | integer | no | Visible number of rows. Default `5`. |


### `linuxfabrik.clf.import`

Import tasks from a separate file.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| (value) | string | yes | Path to a YAML file containing a task list. Relative to the importing file. |


## Jinja Globals

In addition to [Jinja's built-in features](https://jinja.palletsprojects.com/en/stable/templates/), these globals are available in all Jinja-enabled fields:

| Variable | Description |
|----------|-------------|
| `now()` | Current date and time (`datetime.datetime.now()`). Example: `{{ now().strftime("%Y%m%d") }}` |


## Examples

The [examples/](../examples/) directory contains runnable showcases, organized into `templates/` and `reports/` subdirectories. Open them in a dashboard:

```shell
cd examples/
clf-play
```

| Template | Description |
|----------|-------------|
| `builtin-modules-showcase.yml` | Demonstrates all built-in task modules and their options. |
| `demo-deploy-keycloak.yml` | Real-world deployment checklist based on Red Hat documentation. |
| `demo-takeoff-checklist.yml` | Before-takeoff checklist for pilots, based on AOPA guidelines. |
| `feature-showcase.yml` | Conditional pages, Jinja templating, `report_path`. |
| `import-showcase.yml` | Importing pages and tasks from external files. |
