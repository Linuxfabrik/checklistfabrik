import logging

import jinja2.exceptions

import checklistfabrik.core.utils

TEMPLATE_FORMAT_STRING = '''\
<fieldset>
    <legend>{title}</legend>
    {data}
</fieldset>
'''

logger = logging.getLogger(__name__)


class Page:
    """Models a ChecklistFabrik checklist page."""

    def __init__(self, title, tasks, when):
        self.title = title
        self.tasks = tasks
        self.when = when

    def to_dict(self, facts):
        result = {
            'title': self.title,
            'tasks': [task.to_dict(facts) for task in self.tasks],
        }

        if self.when is not None:
            result['when'] = self.when

        return result

    def eval_when(self, facts):
        """
        Evaluate this pages 'when' condition(s) using provided facts.

        The absence of 'when' conditions is considered to be truthy.
        """

        if self.when is None:
            return True

        single_condition = isinstance(self.when, str) and checklistfabrik.core.utils.eval_conditional(facts, self.when)
        multi_conditions = isinstance(self.when, list) and checklistfabrik.core.utils.eval_all_conditionals(facts, self.when)

        return single_condition or multi_conditions

    def render(self, facts):
        """Render the page with all tasks using Jinja."""

        try:
            if self.eval_when(facts):
                data = ''.join([task.render(facts) for task in self.tasks])
            else:
                data = '<div class="toast toast-warning">This page was marked as not applicable based on previous input.</div>'
        except jinja2.exceptions.TemplateSyntaxError as error:
            logger.error('Syntax error at "%s": %s', self.when, error.message)
            data = f'<div class="toast toast-error">Syntax error at "{self.when}": {error.message}</div>'

        return TEMPLATE_FORMAT_STRING.format(title=self.title, data=data)
