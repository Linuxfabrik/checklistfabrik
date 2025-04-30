import logging

import jinja2.exceptions

from .. import utils

TEMPLATE_FORMAT_STRING = '''\
<fieldset>
    <legend>{title}</legend>
    {data}
</fieldset>
'''

logger = logging.getLogger(__name__)


def remove_last_divider(html: str) -> str:
    """
    HTML hack: Remove the last horizontal line (if any) in a fieldset for aesthetic reasons.
    """
    divider = '<div class="divider"></div>'
    last_index = html.rfind(divider)
    if last_index != -1:
        return html[:last_index] + html[last_index + len(divider):]
    return html


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
        """ Evaluate this task's "when" condition(s) using provided facts."""

        try:
            result = utils.eval_when(facts, self.when)
        except jinja2.exceptions.TemplateSyntaxError as error:
            logger.error('Syntax error at "%s": %s', self.when, error.message)
            return False, f'<div class="toast toast-error">Syntax error at "{self.when}": {error.message}</div>'

        return result, None

    def render(self, facts, template_env, markdown):
        """Render the page with all tasks using Jinja."""

        show_page, error = self.eval_when(facts)

        if show_page:
            data = ''.join([task.render(facts, template_env, markdown) for task in self.tasks])
            data = remove_last_divider(data)
        elif error:
            data = error
        else:
            data = '<div class="toast toast-primary">This page was marked as not applicable based on previous input.</div>'

        return TEMPLATE_FORMAT_STRING.format(title=self.title, data=data)
