# Checklist Syntax for ChecklistFabrik

ChecklistFabrik uses YAML files to describe checklists.


## `title`

* Type: string

Title of the checklist.
The title will be used for the HTML title element.
Additionally, the title will be displayed as a heading at the top of the HTML page.


## `pages`

* Type: sequence of mappings

A checklist is built up from one or more pages.
Each page will be rendered as a separate HTML page with a form containing a fieldset where the tasks will be rendered.


## `pages[*].'linuxfabrik.clf.import'`

* Type: string

Special directive that can be used to import a list of pages from a separate file.
If used *must be the first and only* entry in the mapping.


## `pages[*].title`

* Type: string

Title of the checklist page.
The title will be used as the label for the page's form primary fieldset.


## `pages[*].tasks`

* Type: sequence of mappings

A checklist page is built up from one or more tasks.
The rendering of each task is delegated to separate modules.


## `pages[*].tasks[*].<module>`

* Type: mapping (or string; see below)

The very first key in the mapping.
Specifies the module, to which to delegate the task rendering.

The mapping is passed to the respective module for rendering.
Check the syntax documentation of the respective module for its format.

There exists a special module `linuxfabrik.clf.import` that can be used to import a sequence of tasks from a different file.
The type string must be used for this special module, and the value should be the path to the file to load.


## `pages[*].tasks[*].fact_name`

* Type: string

The name under which this module should register its output.
Task modules should use this as the name for their inputs in the HTML form.
After filling out the corresponding input the provided input is available under this name as a Jinja variable.

This field is optional (yet it would be nonsensical to not use it for input modules).


## `pages[*].tasks[*].value`

* Type: any

The saved value for the fact registered by this task of a previous run of this checklist.
Usually this field is edited by `clf-play` and does not need to be edited manually.

This field is optional.


# Task Module *linuxfabrik.clf.checkbox_input*

A task module that renders an HTML checkbox input.


## `label`

* Type: string

The text to be used for the HTML label element of the rendered checkbox input element.
Supports Jinja templating.


## `required`

* Type: boolean

Controls the `required` attribute of the HTML input element.
Setting this key to `true` has the effect that the checkbox *must be checked* to pass validation.


# Task Module *linuxfabrik.clf.radio_input*

A task module that renders a group of HTML radio inputs (also named radio buttons).


## `label`

* Type: string

The text to be used for the HTML label element of the radio button group.
Supports Jinja templating.


## `values`

* Type: sequence

Each list element will be rendered as a radio button of the same radio button group.
As by the nature of radio buttons, only one of them may be checked at all times.


## `required`

* Type: boolean

Controls the `required` attribute of the HTML input element.
Setting this key to `true` has the effect that *one* of the radio buttons must be checked to pass validation.


# Task Module *linuxfabrik.clf.select_input*

A task module that renders an HTML select.


## `label`

* Type: string

The text to be used for the HTML label element of the rendered select element.
Supports Jinja templating.


## `values`

* Type: sequence

Each list item will be rendered as a select option.
The special option `--- Please Select ---` will always be present to denote an "empty" state.


## `required`

* Type: boolean

Controls the `required` attribute of the HTML input element.
Setting this key to `true` has the effect that an option other than `--- Please Select ---` must be selected to pass validation.


# Task Module *linuxfabrik.clf.text*

A task module that renders an HTML paragraph.


## `content`

* Type: string

The text to render as an HTML paragraph.
May include HTML tags.
Supports Jinja templating.


# Task Module *linuxfabrik.clf.text_input*

A task module that renders an HTML text input.


## `label`

* Type: string

The text to be used for the HTML label element of the rendered text input.
Supports Jinja templating.


## `required`

* Type: boolean

Controls the `required` attribute of the HTML input element.
Setting this key to `true` has the effect that the text input *must be non-empty* to pass validation.
