<h1 align="center">
  <a href="https://linuxfabrik.ch" target="_blank">
    <picture>
      <img width="600" src="https://download.linuxfabrik.ch/assets/linuxfabrik-clf-teaser.png">
    </picture>
  </a>
  <br />
  Linuxfabrik ChecklistFabrik
</h1>
<p align="center">
  Python tool that generates interactive HTML checklists from YAML templates. Jinja conditionals, reusable includes, pluggable modules, built-in web server. Ideal for SOPs, deployments & recurring ops.
  <span>&#8226;</span>
  <b>made by <a href="https://linuxfabrik.ch/">Linuxfabrik</a></b>
</p>
<div align="center">

![GitHub Stars](https://img.shields.io/github/stars/linuxfabrik/checklistfabrik)
![GitHub](https://img.shields.io/github/license/linuxfabrik/checklistfabrik)
![Version](https://img.shields.io/github/v/release/linuxfabrik/checklistfabrik?sort=semver)
[![PyPI](https://img.shields.io/pypi/v/checklistfabrik)](https://pypi.org/project/checklistfabrik/)
![Python](https://img.shields.io/badge/Python-3.9+-3776ab)
![GitHub Issues](https://img.shields.io/github/issues/linuxfabrik/checklistfabrik)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/Linuxfabrik/checklistfabrik/badge)](https://scorecard.dev/viewer/?uri=github.com/Linuxfabrik/checklistfabrik)
[![GitHubSponsors](https://img.shields.io/github/sponsors/Linuxfabrik?label=GitHub%20Sponsors)](https://github.com/sponsors/Linuxfabrik)
[![PayPal](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=7AW3VVX62TR4A&source=url)

</div>

<br />

# ChecklistFabrik - Open Source Checklist Maker Tool

ChecklistFabrik (clf-play) is a Python 3 tool designed to manage your team's recurring checklists,
processes, and procedures. It leverages simple yet powerful YAML templates to create interactive HTML forms for an enhanced user experience. Utilize variables and logic through the Jinja templating language to define adaptive procedures, and enjoy seamless progress tracking.


## Features

* **Dashboard:**
  Run `clf-play` without arguments to open a web dashboard that lists all your templates and reports. Start new checklists or re-open previous ones with a single click.

* **Dynamic Item Exclusion:**
  Automatically mark pages or tasks as inapplicable using conditional `when` expressions.
  (See the [User Guide](docs/user_guide.md#conditional-pages-and-tasks) for details.)

* **HTML Interface with Built-In Web Server:**
  View and complete checklists via a user-friendly HTML interface powered by a built-in local web server.

* **Jinja Templating Support:**
  Create dynamic checklists using variables and Boolean expressions enabled by the Jinja templating language.

* **Simple YAML Checklists:**
  Define templates and generate reports with plain YAML, making version control with systems such as Git straightforward.

* **Template Includes for Rapid Checklist Generation:**
  Reuse checklist templates to quickly generate multiple checklists from a single file, eliminating the need to start from scratch each time.


## Definitions and Terms

* **Checklist:**  
  A series of tasks outlining a procedure, organized into pages.

* **Page:**  
  A collection of tasks displayed simultaneously to the user.

* **Report:**  
  The output of a checklist run—a YAML file generated from a template.

* **Task:**
  A description of work to be performed.
  Tasks can appear in various forms, such as text fields, checkboxes, radio buttons,
  or non-interactive text blocks (see the [User Guide](docs/user_guide.md#task-modules) for details).

* **Checklist Template:**
  A YAML file used to create checklists, intended for reuse rather than direct execution.

* **Task Module:**
  To support an extensible architecture, ChecklistFabrik delegates task rendering to separate,
  pluggable Python modules.
  A valid task module is any Python module within the `checklistfabrik.modules` namespace
  that provides a `main` method returning a dictionary that includes an `html` key with the rendered HTML as its value.


## Installation

### From PyPI (Recommended)

ChecklistFabrik releases are available from [PyPI](https://pypi.org/project/checklistfabrik/).

Using [pipx](https://pipx.pypa.io):

```shell
pipx install checklistfabrik
```

Using standard pip (user install):

```shell
pip install --user checklistfabrik
```

Please note that on certain Linux systems `--break-system-packages`
might need to be added when using the system's Python/Pip.


### From Git (For Development or Power Users)

Clone this repository and run `pip install .` at the root of the repo to install ChecklistFabrik.

For development use `--editable` to install ChecklistFabrik in
[Development/Editable Mode](https://setuptools.pypa.io/en/latest/userguide/development_mode.html).
The usage of a virtual environment is *strongly recommended*.


## Quick Start

A checklist template is a simple YAML file:

```yaml
title: 'Server Maintenance'
description: 'Monthly maintenance procedure for production servers.'
version: '2025031901'

pages:
  - title: 'Preparation'
    tasks:
      - linuxfabrik.clf.text_input:
          label: 'Ticket number'
          required: true
        fact_name: 'ticket'

      - linuxfabrik.clf.checkbox_input:
          values:
            - label: 'Notify users about the maintenance window'
            - label: 'Create a full backup'
          required: true

  - title: 'Maintenance'
    tasks:
      - linuxfabrik.clf.markdown:
          content: 'Working on ticket **{{ ticket }}**.'

      - linuxfabrik.clf.checkbox_input:
          label: 'Apply updates and reboot'
          required: true
```

Run it:

```shell
# Open the dashboard (auto-detects templates/ and reports/ subdirectories):
clf-play

# Or run a template directly:
clf-play --template server-maintenance.yml
```

To explore the bundled examples in a dashboard, run:

```shell
cd examples/
clf-play
```

For the full guide on creating checklists—including conditional pages, imports, and all task modules—see the [User Guide](docs/user_guide.md).


## Usage

### Open the Dashboard

```shell
clf-play
```

The dashboard scans for `*.yml` files and lists them as templates and reports:

1. If `templates/` and/or `reports/` subdirectories exist in the current working directory, they are used automatically.
2. If only one of them exists, the other falls back to the current directory.
3. If both point to the same directory, all files are shown in both sections — use "Run" to start a new checklist or "View" to re-open an existing one.

You can override this with explicit paths:

```shell
clf-play --templates-dir ./my-templates --reports-dir ./my-reports
```

### Create a New Checklist From a Template

```shell
clf-play --template path/to/template.yml path/to/report.yml
```

The destination file may be omitted; in that case:

- If the template specifies a `report_path`, then that field is used to generate a new filename.
- Otherwise, a generic, timestamped filename is generated.

### Re-Open an Existing Checklist

```shell
clf-play path/to/existing_checklist.yml
```


## Credits, License

* Authors: [Linuxfabrik GmbH, Zurich](https://www.linuxfabrik.ch)
* License: The Unlicense, see [LICENSE file](https://unlicense.org/)
