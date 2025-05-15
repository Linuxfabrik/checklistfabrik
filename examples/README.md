# Example Files for ChecklistFabrik

This directory contains examples and showcases on how to use ChecklistFabrik and its YAML files.


## Real-Life Examples

Real-life examples all start with the prefix "demo-". To run them, type:

```shell
clf-play --template demo-deploy-keycloak.yml
```


## Built-In Modules Showcase

This example includes showcases of the built-in (task) modules:

- `linuxfabrik.clf.checkbox_input`
- `linuxfabrik.clf.html`
- `linuxfabrik.clf.markdown`
- `linuxfabrik.clf.radio_input`
- `linuxfabrik.clf.select_input`
- `linuxfabrik.clf.text_input`

Please note that the special module `linuxfabrik.clf.import` has its own example.

Run the "module" showcase:

```shell
clf-play --template builtin-modules-showcase.yml
```


## Feature Showcase

This example showcases ChecklistFabrik's main features:

- Storing User Input  
  Store user input for later use in the checklist.

- Conditional Expressions  
  Use conditional expressions to control if a page is shown based on previous user input.

- Multiple Conditionals  
  Examples of how to use more complex conditional expressions to conditionally show pages and tasks.

- Automatic Report names with `report_path`  
  Examples of how to use `report_path` in templates to automatically generate custom save locations.

Run the "feature" showcase:

```shell
clf-play --template feature-showcase.yml
```


## Import Showcase

This example showcases the special `linuxfabrik.clf.import` module,
which can be used to import pages and tasks from separate pages.

Run the "import" showcase:

```shell
clf-play --template import-showcase.yml
```
