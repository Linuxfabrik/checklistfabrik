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
  <em>ChecklistFabrik</em>
  <span>&#8226;</span>
  <b>made by <a href="https://linuxfabrik.ch/">Linuxfabrik</a></b>
</p>
<div align="center">

![GitHub](https://img.shields.io/github/license/linuxfabrik/checklistfabrik)
![GitHub last commit](https://img.shields.io/github/last-commit/linuxfabrik/checklistfabrik)
![Version](https://img.shields.io/github/v/release/linuxfabrik/checklistfabrik?sort=semver)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/Linuxfabrik/checklistfabrik/badge)](https://scorecard.dev/viewer/?uri=github.com/Linuxfabrik/checklistfabrik)
[![GitHubSponsors](https://img.shields.io/github/sponsors/Linuxfabrik?label=GitHub%20Sponsors)](https://github.com/sponsors/Linuxfabrik)
[![PayPal](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=7AW3VVX62TR4A&source=url)

</div>

<br />

# ChecklistFabrik

ChecklistFabrik (clf-play) is a Python 3 tool designed to manage your team's recurring checklists,
processes, and procedures.
It leverages simple yet powerful YAML templates to create interactive HTML forms for an enhanced user experience.
Utilize variables and logic through the Jinja templating language to define adaptive procedures,
and enjoy seamless progress tracking with Git—supported by plain YAML files.


## Features

* **Enhanced User Experience with an HTML Interface and Local Web Server:**  
  View and complete checklists via a user-friendly HTML interface powered by a built-in local web server.

* **Simple YAML Checklists:**  
  Define templates and generate reports with plain YAML, making version control with systems such as Git straightforward.

* **Template Includes for Rapid Checklist Generation:**  
  Reuse checklist templates to quickly generate multiple checklists from a single file, eliminating the need to start from scratch each time.

* **Jinja Templating Support:**  
  Create dynamic checklists using variables and Boolean expressions enabled by the Jinja templating language.

* **Dynamic Item Exclusion:**  
  Automatically mark pages or tasks as inapplicable using conditional 'when' expressions.  
  (See our [examples](examples/README.md) for more details—search for "when:")


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
  or non-interactive text blocks (see the Task Module section below).

* **Checklist Template:**  
  A YAML file used to create checklists, intended for reuse rather than direct execution.

* **Task Module:**  
  To support an extensible architecture, ChecklistFabrik delegates task rendering to separate,
  pluggable Python modules.  
  A valid task module is any Python module within the `checklistfabrik.modules` namespace
  that provides a main method—returning a dictionary that includes an `html` key with the rendered HTML as its value.


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


## Creating a Checklist Template

For documentation on the YAML format used by ChecklistFabrik, see the [checklist template syntax documentation](docs/checklist_syntax.md).
Example checklist templates can be found in the `examples` folder of this project.


## Creating a New Checklist From a Template

```shell
clf-play --template path/to/template.yml path/to/checklist_to_create.yml
```

The destination file may be omitted; in that case:

- If the template specifies a `report_path`, then that field is used to generate a new filename.
- Otherwise, a generic, timestamped filename is generated.


## Re-Running an Existing Checklist

```shell
clf-play path/to/existing_checklist.yml
```


## Credits, License

* Authors: [Linuxfabrik GmbH, Zurich](https://www.linuxfabrik.ch)
* License: The Unlicense, see [LICENSE file](https://unlicense.org/)
