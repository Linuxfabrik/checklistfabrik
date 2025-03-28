# ChecklistFabrik

ChecklistFabrik (clf-play) is a Python 3 tool to simplify and automate process management using HTML checklists backed by YAML files.


## Features

* **Stores checklists as YAML:**
  Changes can therefore easily be tracked using version control systems such as Git.

* **Presents checklists rendered as HTML using a built-in local webserver:**
  User-friendly workflow with checklists thanks to the HTML interface.

* **Supports checklist templates:**
  Checklist templates can be used to quickly generate multiple checklists from a single file and avoid creating checklists multiple times from scratch.

* **Jinja support:**
  Create checklists with dynamic text using Jinja.

* **Dynamically exclude non-applicable parts:**
  ChecklistFabrik supports 'when' expressions for pages such that pages can automatically be marked as non-applicable based on previous input.


## Installation


### From the Git Repository

Clone this repository and run `pip install .` at the root of the repo to build and install the ChecklistFabrik package.


## Usage

For the documentation of the YAML format used by ChecklistFabrik please refer to the [Checklist Syntax](docs/checklist_syntax.md).


### Creating a New Checklist From a Template

```shell
clf-play --template path/to/template.yml path/to/checklist_to_create.yml
```


### Editing an Existing Checklist

```shell
clf-play path/to/existing_checklist.yml
```


## Credits, License

* Authors: [Linuxfabrik GmbH, Zurich](https://www.linuxfabrik.ch)
* License: The Unlicense, see [LICENSE file](https://unlicense.org/)
