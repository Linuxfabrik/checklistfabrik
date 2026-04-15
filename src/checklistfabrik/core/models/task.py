import importlib
import inspect
import logging
import uuid

import jinja2
import markupsafe

from .. import utils

MODULE_NAMESPACE = 'checklistfabrik.modules'

TEMPLATE_FORMAT_STRING = '{html}\n<div class="divider"></div>'

logger = logging.getLogger(__name__)


class Task:
    """Models a ChecklistFabrik checklist task."""

    def __init__(self, module, context, fact_name, when, unnamed_fact=None):
        self.module = module
        self.context = context
        self.fact_name = fact_name
        self.when = when
        self.unnamed_fact = unnamed_fact

    def to_dict(self, facts):
        result = {
            self.module: self.context,
        }

        if self.fact_name is not None:
            result['fact_name'] = self.fact_name

            if facts is not None and self.fact_name in facts:
                result['value'] = facts[self.fact_name]

        if self.when is not None:
            result['when'] = self.when

        return result

    def eval_when(self, facts):
        """Evaluate this page's 'when' condition(s) using provided facts."""

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
        """Render the task using its module."""

        show_task, error = self.eval_when(facts)

        if not show_task:
            return ''
        elif error:
            return TEMPLATE_FORMAT_STRING.format(html=error)

        try:
            loaded_module = importlib.import_module(f'{MODULE_NAMESPACE}.{self.module}')
        except ModuleNotFoundError:
            logger.error('Task rendering error: Cannot find module "%s"', self.module)
            safe_module = markupsafe.escape(self.module)
            return f'<div class="toast toast-error">Task rendering error: Cannot find module <em>{safe_module}</em>. Is it installed?</div>'

        render_context = facts.copy()
        render_context['clf_jinja_env'] = template_env
        render_context['clf_jinja_env_plain'] = template_env_plain or template_env
        render_context['clf_markdown'] = markdown
        if self.fact_name:
            render_context['fact_name'] = self.fact_name
        else:
            # Provide an automatic fact name that the module can use.
            # The module needs to report this back as fact_name if it uses the suggested name.
            auto_fact_name = f'auto_{uuid.uuid4().hex}'
            render_context['auto_fact_name'] = (
                auto_fact_name  # Prefix the hex uuid so that it is a valid Python identifier.
            )

            # Inject value that was provided without fact name.
            if self.unnamed_fact:
                render_context[auto_fact_name] = self.unnamed_fact
        render_context.update(self.context)

        if not hasattr(loaded_module, 'main') or not callable(loaded_module.main):
            logger.error(
                'Task rendering error: Module "%s" is not a valid ChecklistFabrik module as it has no callable "main"',
                self.module,
            )
            safe_module = markupsafe.escape(self.module)
            return f'<div class="toast toast-error">Task rendering error: Module <em>{safe_module}</em> is not a valid ChecklistFabrik module.</div>'

        main_signature = inspect.signature(loaded_module.main)

        if inspect.Parameter.VAR_KEYWORD not in [
            param.kind for param in main_signature.parameters.values()
        ]:
            logger.error(
                'Task rendering error: Module "%s" looks like a ChecklistFabrik module but is malformed as its signature does not allow variadic keyword arguments',
                self.module,
            )
            safe_module = markupsafe.escape(self.module)
            return TEMPLATE_FORMAT_STRING.format(
                html=f'<div class="toast toast-error">Task rendering error: Module <em>{safe_module}</em> looks like a ChecklistFabrik module but is malformed.</div>',
            )

        try:
            result = loaded_module.main(**render_context)
        except Exception as exception:
            logger.error(
                'Task rendering error: Rendering module "%s" failed: %s',
                self.module,
                exception,
            )
            safe_module = markupsafe.escape(self.module)
            safe_exception = markupsafe.escape(str(exception))
            return TEMPLATE_FORMAT_STRING.format(
                html=f'<div class="toast toast-error">Task rendering error: Rendering module <em>{safe_module}</em> failed: <pre>{safe_exception}</pre></div>',
            )

        if not isinstance(result, dict):
            logger.error(
                'Task rendering error: Module "%s" returned a value of type "%s" but expected "%s"',
                self.module,
                type(result),
                type({}),
            )
            safe_module = markupsafe.escape(self.module)
            return TEMPLATE_FORMAT_STRING.format(
                html=f'<div class="toast toast-error">Task rendering error: Module <em>{safe_module}</em> returned an invalid output.</div>',
            )

        if 'fact_name' in result:
            # Set fact name to the reported one from the module if we do not already have one.
            # Note that pure output modules (i.e. they do not render inputs) might not report a fact name (as they don't need it).
            if not self.fact_name:
                self.fact_name = result['fact_name']
            elif self.fact_name != result['fact_name']:
                logger.warning(
                    'Task module reports a different fact name than originally specified. This is most likely a bug in the task module'
                )

        task_context_update = result.get('task_context_update')

        if task_context_update:
            self.context.update(task_context_update)

        return TEMPLATE_FORMAT_STRING.format(html=result.get('html', ''))
