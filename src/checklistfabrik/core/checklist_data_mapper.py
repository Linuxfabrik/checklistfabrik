import io
import logging
import pathlib
import sys

from . import models
from . import utils

logger = logging.getLogger(__name__)


class ChecklistLoadError(Exception):
    """Failure while loading checklist data."""
    pass


class ChecklistDataMapper:
    """Helper to map checklist data from YAML files to Python classes and vice versa."""

    def __init__(self, yaml):
        self.yaml = yaml

    def load_yaml(self, file):
        try:
            with open(file, mode='r', encoding='utf-8') as file_handle:
                return self.yaml.load(file_handle.read())
        except FileNotFoundError:
            logger.critical('Cannot open file "%s" as it does not exist', file)
            raise ChecklistLoadError
        except IsADirectoryError:
            logger.critical('Cannot open file "%s" as it is a directory', file)
            raise ChecklistLoadError
        except PermissionError:
            logger.critical('Cannot open file "%s" due to insufficient permissions', file)
            raise ChecklistLoadError

    def load_checklist(self, file):
        """Load a checklist with all of its pages, tasks and facts from a YAML file and process all imports."""

        logger.info('Loading checklist data from "%s"', file)

        try:
            return self.process_checklist(self.load_yaml(file), file.parent)
        except ChecklistLoadError:
            logger.critical('Loading checklist data from file failed')
            sys.exit(1)

    def save_checklist(self, file, checklist, overwrite=True):
        """Save a checklist and its pages, tasks and facts to a YAML file."""

        logger.info('Saving checklist data to "%s"', file)

        # Before writing the file, dump to a separate stream instead and check if we have an output.
        # This prevents saving an empty file if for some reason the dump fails.
        stream = io.StringIO()
        self.yaml.dump(checklist.to_dict(), stream)

        if stream.tell() == 0:
            logger.critical('Yaml dump failed and returned an empty result. File "%s" is left untouched', file)
            sys.exit(1)

        try:
            file.parent.mkdir(parents=True, exist_ok=True)
        except (NotADirectoryError, FileExistsError) as error:
            fallback_file = pathlib.Path.cwd() / file.name
            logger.error(
                'Cannot create parent directory "%s" (%s). Saving to "%s" instead',
                file.parent,
                error,
                fallback_file,
            )
            file = fallback_file

        if not overwrite:
            # Find a free file name
            original_file = file
            counter = 1

            while file.exists():
                file = original_file.with_name(f'{original_file.stem}_{counter}{original_file.suffix}')
                counter += 1

            if file != original_file:
                logger.warning('File "%s" already exists. Saving to "%s" instead', original_file, file)

        with open(file, mode='w' if overwrite else 'x', encoding='utf-8') as checklist_file:
            stream.seek(0)
            checklist_file.write(stream.read())

    def process_checklist(self, checklist, workdir):
        facts = {}

        if checklist is None:
            raise ValueError('Cannot load an empty checklist.')

        valid, message = utils.validate_dict_keys(
            checklist,
            {'title', 'pages'},
            {'report_path', 'version'},
            disallow_extra_keys=True,
        )

        if not valid:
            logger.critical('Failed to load checklist: %s', message)
            raise ChecklistLoadError

        page_list = checklist['pages']
        title = checklist['title']

        if not isinstance(title, str):
            logger.critical('Title field of checklist is not a string')
            raise ChecklistLoadError

        if not title or title.isspace():
            logger.warning('Title field of checklist is empty')

        if not isinstance(page_list, list):
            logger.critical('Checklist "%s" does not contain any pages', title)
            raise ChecklistLoadError

        if 'report_path' in checklist and not isinstance(checklist['report_path'], str):
            logger.critical('Report path field of checklist "%s" is not a string', title)
            raise ChecklistLoadError

        if 'version' in checklist and not isinstance(checklist['version'], str):
            logger.critical('Version field of checklist "%s" is not a string', title)
            raise ChecklistLoadError

        return models.Checklist(
            title,
            self.process_page_list(page_list, workdir, facts),
            facts,
            checklist.get('report_path'),
            checklist.get('version'),
        )

    def process_page_list(self, page_list, workdir, facts):
        pages = []

        for page in page_list:
            if not isinstance(page, dict):
                logger.critical('Page data is not a mapping')
                raise ChecklistLoadError

            # Try to detect special directives before processing the page.
            try:
                page_directive, page_context = list(page.items())[0]
            except IndexError:
                page_directive = None
                page_context = None

            if page_directive == 'linuxfabrik.clf.import':
                if not isinstance(page_context, str):
                    logger.critical('Page import key is specified but its value is not a string')
                    raise ChecklistLoadError

                # Relative import paths should be relative to the checklist file.
                import_path = pathlib.Path(page_context)
                computed_import_path = import_path if import_path.is_absolute() else workdir / page_context

                logger.info('Importing pages from "%s"', computed_import_path)

                imported_page_list = self.load_yaml(computed_import_path)

                if not isinstance(imported_page_list, list):
                    logger.critical('Imported data is not a page list')
                    raise ChecklistLoadError

                pages.extend(self.process_page_list(imported_page_list, computed_import_path.parent, facts))
                continue

            pages.append(self.process_page(page, workdir, facts))

        return pages

    def process_page(self, page, workdir, facts):
        valid, message = utils.validate_dict_keys(page, {'title', 'tasks'}, optional_keys={'when'}, disallow_extra_keys=True)

        if not valid:
            logger.critical('Failed to load page: %s', message)
            raise ChecklistLoadError

        task_list = page['tasks']
        title = page['title']

        if not isinstance(title, str):
            logger.critical('Title field of page is not a string')
            raise ChecklistLoadError

        if not title or title.isspace():
            logger.critical('Title field of page is empty')
            raise ChecklistLoadError

        if not isinstance(task_list, list):
            logger.critical('Tasks field on page "%s" is not a list', title)
            raise ChecklistLoadError

        if task_list:
            tasks = self.process_task_list(page['tasks'], workdir, facts)
        else:
            logger.warning('Task list on page "%s" is empty', title)
            tasks = []

        return models.Page(title, tasks, page.get('when'))

    def process_task_list(self, task_list, workdir, facts):
        tasks = []

        for task in task_list:
            if not isinstance(task, dict):
                logger.critical('Task data is not a mapping')
                raise ChecklistLoadError

            task_items = list(task.items())

            if len(task_items) == 0:
                logger.critical('Task data is missing')
                raise ChecklistLoadError

            task_module, task_context = task_items[0]

            if task_module == 'linuxfabrik.clf.import':
                if not isinstance(task_context, str):
                    logger.critical('Task import key is specified but its value is not a string')
                    raise ChecklistLoadError

                # Relative import paths should be relative to the checklist file.
                import_path = pathlib.Path(task_context)
                computed_import_path = import_path if import_path.is_absolute() else workdir / task_context

                logger.info('Importing tasks from "%s"', computed_import_path)

                imported_task_list = self.load_yaml(computed_import_path)

                if not isinstance(imported_task_list, list):
                    logger.critical('Imported data is not a task list')
                    raise ChecklistLoadError

                tasks.extend(self.process_task_list(imported_task_list, computed_import_path.parent, facts))
                continue

            if not isinstance(task_context, dict):
                logger.critical('Task context is not a mapping')
                raise ChecklistLoadError

            fact_name = task.get('fact_name')
            value = task.get('value')
            when = task.get('when')

            unnamed_fact = None

            if fact_name is not None:
                if not fact_name.isidentifier():
                    logger.warning(
                        'Fact name "%s" is not a valid (Python) identifier. It cannot be referenced as a variable in Jinja templates',
                        fact_name,
                    )

                if fact_name.endswith('[]'):
                    logger.critical('Invalid fact name "%s". Fact names may not end with "[]"', fact_name)
                    # ChecklistFabrik uses `[]` as a suffix on HTML forms to differentiate lists from single values.
                    raise ChecklistLoadError

                if value is not None:
                    facts[fact_name] = value
            else:
                unnamed_fact = value

            tasks.append(models.Task(task_module, task_context, fact_name, when, unnamed_fact))

        return tasks
