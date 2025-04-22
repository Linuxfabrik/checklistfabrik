import importlib
import inspect
import logging
import uuid

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

    def render(self, facts, template_env):
        """Render the task using its module."""

        try:
            loaded_module = importlib.import_module(f'{MODULE_NAMESPACE}.{self.module}')
        except ModuleNotFoundError:
            logger.error('Task rendering error: Cannot find module "%s"', self.module)
            return f'<div class="toast toast-error">Task rendering error: Cannot find module <em>{self.module}</em>. Is it installed?</div>'

        render_context = facts.copy()
        render_context['clf_template_env'] = template_env
        if self.fact_name:
            render_context['fact_name'] = self.fact_name
        else:
            # Provide an automatic fact name that the module can use.
            # The module needs to report this back as fact_name if it uses the suggested name.
            render_context['auto_fact_name'] = f'auto_{uuid.uuid4().hex}'  # Prefix the hex uuid so that it is a valid Python identifier.
        render_context.update(self.context)

        if not hasattr(loaded_module, 'main') or not callable(loaded_module.main):
            logger.error(
                'Task rendering error: Module "%s" is not a valid ChecklistFabrik module as it has no callable "main"',
                self.module,
            )
            return f'<div class="toast toast-error">Task rendering error: Module <em>{self.module}</em> is not a valid ChecklistFabrik module.</div>'

        main_signature = inspect.signature(loaded_module.main)

        if not inspect.Parameter.VAR_KEYWORD in [param.kind for param in main_signature.parameters.values()]:
            logger.error(
                'Task rendering error: Module "%s" looks like a ChecklistFabrik module but is malformed as its signature does not allow variadic keyword arguments',
                self.module,
            )
            return f'<div class="toast toast-error">Task rendering error: Module <em>{self.module}</em> looks like a ChecklistFabrik module but is malformed.</div>'

        result = loaded_module.main(**render_context)

        if not isinstance(result, dict):
            logger.error(
                'Task rendering error: Module "%s" returned a value of type "%s" but expected "%s"',
                self.module,
                type(result),
                type({}),
            )
            return f'<div class="toast toast-error">Task rendering error: Module <em>{self.module}</em> returned an invalid output.</div>'

        if 'fact_name' in result:
            if not self.fact_name:
                self.fact_name = result['fact_name']
            elif self.fact_name != result['fact_name']:
                logger.warning('Task module reports a different fact name than originally specified. This is most likely a bug in the task module')

        return f'{result.get("html", "")}\n<hr/>'
