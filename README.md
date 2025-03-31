# ChecklistFabrik

ChecklistFabrik (clf-play) is a Python 3 tool for managing your team's recurring checklists and procedures using HTML forms created from simple yet powerful YAML templates, including variables and logic based on Jinja.


## Features

* **Presents checklists as HTML using a built-in local web server:**  
  The HTML interface provides a user-friendly checklist workflow.

* **Saves checklist results as YAML:**  
  If output is stored in version control systems such as Git, changes can be easily tracked.

* **Supports includes:**  
  Checklist templates can be used to quickly generate multiple checklists from a single file, avoiding the need to create multiple checklists from scratch.

* **Jinja support:**  
  Create dynamic checklists using variables and boolean expressions based on Jinja.

* **Dynamically exclude inapplicable items:**  
  ChecklistFabrik supports 'when' expressions for pages, so pages can be automatically marked as inapplicable based on previous input.


## Definitions and Terms

* Checklist: TODO describe
* Page: TODO describe
* Task: TODO describe
* Template: TODO describe
* Module: TODO describe


## Installation

Clone this repository and run `pip install --user .` at the root of the repo to build and install the ChecklistFabrik package.


## Creating a Checklist Template

For documentation on the YAML format used by ChecklistFabrik, see the [checklist template syntax documentation](docs/checklist_syntax.md). Example checklist templates can be found in the `examples` folder of this project.


## Creating a New Checklist From a Template

```shell
clf-play --template path/to/template.yml path/to/checklist_to_create.yml
```


## Re-Running an Existing Checklist

```shell
clf-play path/to/existing_checklist.yml
```


## Credits, License

* Authors: [Linuxfabrik GmbH, Zurich](https://www.linuxfabrik.ch)
* License: The Unlicense, see [LICENSE file](https://unlicense.org/)
