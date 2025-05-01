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
  ChecklistFabrik supports 'when' expressions for pages and tasks, so pages and tasks can be automatically marked as inapplicable based on input. See the examples for details (grep for `when:`).


## Definitions and Terms

* **Checklist:**  
  A list of tasks that describe a procedure to be done, grouped by pages.

* **Page:**  
  A group of tasks that is simultaneously displayed to the user.

* **Report:**  
  A checklist file, usually generated from a template.

* **Task:**  
  A description of a piece of work that has to be done.
  May be presented in different forms such as text fields, checkboxes, radio buttons or non-interactive text blocks etc... (see Task Module below)

* **(Checklist) Template:**  
  A checklist YAML file that is used to create other checklists instead of being run itself.

* **(Task) Module:**  
  To support an extensible architecture, ChecklistFabrik moves the task rendering into separate, pluggable Python modules such that new task variants can be added easily.
  A valid task module is any Python module under the `checklistfabrik.modules` namespace package that has a main method that returns a dictionary containing the key `html` and as the value the rendered HTML.


## Installation

Clone this repository and run `pip install --user .` at the root of the repo to build and install the ChecklistFabrik package.


## Creating a Checklist Template

For documentation on the YAML format used by ChecklistFabrik, see the [checklist template syntax documentation](docs/checklist_syntax.md). Example checklist templates can be found in the `examples` folder of this project.


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
