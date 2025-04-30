"""General purpose functionalities for ChecklistFabrik."""

import jinja2


def eval_conditional(facts, conditional):
    """Evaluates a single jinja conditional statement."""

    # Uses spaces around True/False to ensure the result is still a string in case of rendering with jinja's NativeEnvironment.
    condition_template = jinja2.Template(f'{{% if {conditional} %}} True {{% else %}} False {{% endif %}}')

    return condition_template.render(**facts).strip() == 'True'


def eval_all_conditionals(facts, conditionals):
    """Conjunctive evaluation of a list of jinja conditional statements."""

    for conditional in conditionals:
        if not eval_conditional(facts, conditional):
            return False

    return True


def eval_when(facts, when):
    """
    Automagically evaluate either a when condition or list of conditions.

    The absence of "when" conditions is considered to be truthy.
    """

    if when is None:
        return True, None

    single_condition = isinstance(when, str) and eval_conditional(facts, when)
    multi_conditions = isinstance(when, list) and eval_all_conditionals(facts, when)

    return single_condition or multi_conditions


def validate_dict_keys(
        dictionary,
        required_keys,
        optional_keys=None,
        disallow_extra_keys=False,
):
    """Validate that a dictionary contains required keys and optional keys; if desired, also checks if any extra keys are present."""

    if required_keys is None:
        required_keys = set()

    if optional_keys is None:
        optional_keys = set()

    missing_keys = required_keys - dictionary.keys()

    if len(missing_keys) > 0:
        return False, f'Missing the following required keys: {", ".join(missing_keys)}'

    if disallow_extra_keys:
        extra_keys = dictionary.keys() - required_keys - optional_keys

        if len(extra_keys) > 0:
            return False, f'Unexpected extra keys: "{", ".join(extra_keys)}"'

    return True, 'Valid'
