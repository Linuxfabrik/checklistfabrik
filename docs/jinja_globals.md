# Jinja Globals

In addition to Jinja's [template features](https://jinja.palletsprojects.com/en/stable/templates/)
ChecklistFabrik exposes the following global variables in all Jinja-enabled fields of its builtin modules
(as well as in all third-party modules that use the `clf_jinja_env` Jinja Environment):

- `now`, references Python's `datetime.datetime.now`
