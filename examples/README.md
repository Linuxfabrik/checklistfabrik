# Example Files for ChecklistFabrik

This directory contains examples on how to use ChecklistFabrik and its YAML files.


## Built-In Modules Showcase

```shell
clf-play --template builtin-modules-showcase.yml
```

This example includes showcases of the built-in (task) modules:

- `linuxfabrik.clf.checkbox_input`
- `linuxfabrik.clf.markdown`
- `linuxfabrik.clf.radio_input`
- `linuxfabrik.clf.select_input`
- `linuxfabrik.clf.text_input`
- `linuxfabrik.clf.text_output`

Please note that the special module `linuxfabrik.clf.import` has its own example.


## Feature Showcase

```shell
clf-play --template feature-showcase.yml
```

This example showcases ChecklistFabrik's main features:

- Storing User Input  
  Store user input for later use in the checklist.

- Conditional Expressions  
  Use conditional expressions to control if a page is shown based on previous user input.

- Multiple Conditionals  
  Examples of how to use more complex conditional expressions to conditionally show pages and tasks.


## Import Showcase

```shell
clf-play --template import-showcase.yml
```

This example showcases the special `linuxfabrik.clf.import` module,
which can be used to import pages and tasks from separate pages.
