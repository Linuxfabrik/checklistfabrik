import importlib
import logging

MODULE_NAMESPACE = 'checklistfabrik.modules'

logger = logging.getLogger(__name__)


class Task:
    """Models a ChecklistFabrik checklist task."""

    def __init__(self, module, context, fact_name):
        self.module = module
        self.context = context
        self.fact_name = fact_name

    def to_dict(self, facts):
        result = {
            self.module: self.context,
        }

        if self.fact_name is not None:
            result['fact_name'] = self.fact_name

            if facts is not None and self.fact_name in facts:
                result['value'] = facts[self.fact_name]

        return result

    def render(self, facts):
        """Render the task using its module."""

        try:
            loaded_module = importlib.import_module(f'{MODULE_NAMESPACE}.{self.module}')
        except ModuleNotFoundError:
            logger.error('Task rendering error: Cannot find module "%s"', self.module)
            return f'<div class="toast toast-error">Task rendering error: Cannot find module <em>{self.module}</em>. Is it installed?</div>'

        render_context = facts.copy()
        render_context['fact_name'] = self.fact_name
        render_context.update(self.context)

        result = loaded_module.main(**render_context)

        if 'facts' in result:
            facts.update(result['facts'])

        return result.get('html', '')
