import logging

import jinja2.exceptions
import markupsafe

from .. import utils

TEMPLATE_FORMAT_STRING = '{data}'

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
        """Evaluate this task's "when" condition(s) using provided facts."""

        try:
            result = utils.eval_when(facts, self.when)
        except jinja2.exceptions.TemplateSyntaxError as error:
            logger.error('Syntax error at "%s": %s', self.when, error.message)
            safe_when = markupsafe.escape(self.when)
            safe_message = markupsafe.escape(error.message)
            return (
                False,
                f'<div class="toast toast-error">Syntax error at "{safe_when}": {safe_message}</div>',
            )

        return result, None

    def render(self, facts, template_env, markdown, template_env_plain=None):
        """Render the page with all tasks using Jinja."""

        show_page, error = self.eval_when(facts)

        if show_page:
            data = ''.join(
                [
                    task.render(facts, template_env, markdown, template_env_plain)
                    for task in self.tasks
                ]
            )
        elif error:
            data = error
        else:
            data = '<div class="toast toast-primary">This page was marked as not applicable based on previous input.</div>'

        return TEMPLATE_FORMAT_STRING.format(
            title=markupsafe.escape(template_env.from_string(self.title).render(**facts)),
            data=data,
        )
