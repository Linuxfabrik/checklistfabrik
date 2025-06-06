# Checklist Syntax for ChecklistFabrik

ChecklistFabrik uses YAML files to describe checklists.


## `report_path`

* Type: string

This field can be used *in templates* to auto-generate file paths for the report files based on Jinja templates.
Only applies if used in templates, otherwise this field is ignored.
Environment variable expansion is supported.

Invalid characters for file names (e.g. non-printables, newlines, ...) will automatically be removed.

This field is optional.


## `title`

* Type: string

Title of the checklist.
The title will be used for the HTML title element.
Additionally, the title will be displayed as a heading at the top of the HTML page.


## `pages`

* Type: sequence of mappings

A checklist is built up from one or more pages.
Each page will be rendered as a separate HTML page with a form containing a fieldset where the tasks will be rendered.

### Fields

- **`linuxfabrik.clf.import`**  
  *Type*: string  
  Special directive that can be used to import a list of pages from a separate file.  
  If used *must be the first and only* field in the mapping.

- **`title`**  
  *Type*: string  
  Title of the checklist page.  
  The title will be used as the label for the page's form primary fieldset.  
  Supports Jinja templating.  
  May not be empty.

- **`tasks`**  
  *Type*: sequence of mappings  
  A checklist page is built up from one or more tasks.  
  The rendering of each task is delegated to separate modules.  
  *Fields*:

    - **`<module>`**  
      *Type*: mapping (or string; see below)  
      The very first key in the mapping.  
      Specifies the module, to which to delegate the task rendering.  
      *The mapping is passed to the respective module for rendering.
      Check the syntax documentation of the respective module for its format.*
      The documentation for built-in modules can be found in this document in their respective sections below.  
      There exists a special module `linuxfabrik.clf.import` that can be used to import a sequence of tasks from a different file.
      For this special module, the value must be a string of the path to the file to load (instead of a mapping).

    - **`fact_name`**  
      *Type*: string  
      The name under which this module should register its output.  
      Task modules should use this as the name for their inputs in the HTML form.
      After filling out the corresponding input, the provided input is available under this name as a Jinja variable.  
      This field is optional (yet you most likely want to set it if you want to use its output as a Jinja variable).  
      ChecklistFabrik will auto-generate names for missing fact names that *input modules* may use. All built-in input modules support auto-generated fact names.

    - **`value`**  
      *Type*: any  
      The saved value for the fact registered by this task from a previous run of this checklist.
      Usually this field is edited by `clf-play` and does not need to be edited manually.  
      Can be set in templates to act as a default when creating a checklist from the template.  
      This field is optional.

    - **`when`**  
      *Type*: string or sequence of strings  
      One or multiple Jinja conditional expressions that control if a task is shown or not.  
      The task is shown if the expression evaluates to `true`, otherwise it is hidden.
      Multiple expressions are combined using a logical "and".  
      This field is optional.

- **`when`**  
  *Type*: string or sequence of strings  
  One or multiple Jinja conditional expressions that control if a page is automatically skipped.  
  The page is shown if the expression evaluates to `true`, otherwise it is skipped.
  Multiple expressions are combined using a logical `and`.  
  This field is optional.

## `version`

* Type: string

A freeform text identifier that gets displayed on the HTML form if present.
Does not have any ChecklistFabrik specific meaning.
Users may freely decide over its content and/or format.

The version field from a template will be copied to a new checklist unchanged.

This field could be used, for example, to track from which iteration of a template the checklist was originally generated.


## Task Module *linuxfabrik.clf.checkbox_input*

A task module that renders either a single HTML checkbox input field or a group of them.

### Fields

- **`label`**  
  *Type*: string  
  The text to be used for the HTML label element of the group fieldset.  
  Supports Jinja templating.  
  Supports Markdown formatting.  
  May be left empty.

- **`values`**  
  *Type*: sequence  
  Each list element will be rendered as a separate checkbox *of the same group*.
  Multiple checkboxes may be checked at any time.  
  Use multiple checkbox tasks with a single value each if you want independent checkboxes.  
  May be omitted if one only wants a single checkbox.
  In that case, the (group) label would be the label of the checkbox.  
  *Fields*:

    - **`label`**  
      *Type*: string  
      Text to render as a label for a checkbox.
      If omitted will fall back to `value`.  
      Supports Jinja templating.  
      Supports Markdown formatting.

    - **`value`**  
      *Type*: string  
      Value for the checkbox.
      Use this for human-friendly names when referencing the checkbox.  
      Will be auto-generated by ChecklistFabrik if omitted (albeit not in human-friendly form).

  - **`required`**  
    *Type*: boolean  
    Controls the `required` attribute of the HTML input element of the checkbox.  
    Use this to mark single checkboxes in a group as required.
    If `required: true` is set on the task level all checkboxes of the group will be marked as required regardless of their individual `required` key.

- **`required`**  
  *Type*: boolean  
  Controls the `required` attribute of the HTML input element.  
  Setting this key to `true` has the effect that *all checkboxes of the same group must be checked* to pass validation.


## Task Module *linuxfabrik.clf.html*

A task module that renders Jinja templated HTML.

### Fields

- **`content`**  
  *Type*: string  
  The text to render as an HTML paragraph.  
  May include HTML tags.  
  Supports Jinja templating.


## Task Module *linuxfabrik.clf.markdown*

A task module that renders markdown content as HTML.

### Fields

- **`content`**  
  *Type*: string  
  The Markdown formatted text to render as an HTML paragraph.  
  Supports Jinja templating.


## Task Module *linuxfabrik.clf.radio_input*

A task module that renders a group of HTML radio inputs (also named radio buttons).

### Fields

- **`label`**  
  *Type*: string  
  The text to be used for the HTML label element of the radio button group.  
  Supports Jinja templating.  
  Supports Markdown formatting.

- **`values`**  
  *Type*: sequence  
  Each list element will be rendered as a radio button of the same radio button group.
  As by the nature of radio buttons, only one of them may be checked at all times.  
  *Fields*:

    - **`label`**  
      *Type*: string  
      Text to render as a label for a radio button.
      If omitted will fall back to `value`.  
      Supports Jinja templating.  
      Supports Markdown formatting.
      
    - **`value`**  
      *Type*: string  
      Value for the radio button.
      Use this for human-friendly names when referencing the radio button.  
      Will be auto-generated by ChecklistFabrik if omitted (albeit not in human-friendly form).

- **`required`**  
  *Type*: boolean  
  Controls the `required` attribute of the HTML input element.  
  Setting this key to `true` has the effect that *one* of the radio buttons must be checked to pass validation.


## Task Module *linuxfabrik.clf.select_input*

A task module that renders an HTML select.

### Fields

- **`label`**  
  *Type*: string  
  The text to be used for the HTML label element of the rendered select element.  
  Supports Jinja templating.  
  Supports Markdown formatting.

- **`values`**  
  *Type*: sequence  
  Each list item will be rendered as a select option.  
  The special option `--- Please Select ---` will always be present to denote an "empty" state.

- **`multiple`**  
  *Type:* boolean  
  If set to true renders the HTML select with the multiple attribute so that multiple options may be selected.

- **`required`**  
  *Type*: boolean  
  Controls the `required` attribute of the HTML select element.  
  Setting this key to `true` has the following effects:
    - for single-select: any option other than `--- Please Select ---` must be selected to pass validation.
    - for multi-select: at least one option must be selected to pass validation.


## Task Module *linuxfabrik.clf.text_input*

A task module that renders an HTML text input.

### Fields

- **`label`**  
  *Type*: string  
  The text to be used for the HTML label element of the rendered text input.  
  Supports Jinja templating.  
  Supports Markdown formatting.

- **`required`**  
  *Type*: boolean  
  Controls the `required` attribute of the HTML input element.  
  Setting this key to `true` has the effect that the text input *must be non-empty* to pass validation.
