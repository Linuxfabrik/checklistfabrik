import io
import logging
import sys

from . import models
from . import utils

logger = logging.getLogger(__name__)


class ChecklistDataMapper:
    """Helper to map checklist data from YAML files to Python classes and vice versa."""

    def __init__(self, yaml):
        self.yaml = yaml

    def load_yaml(self, file):
        with open(file, mode='r', encoding='utf-8') as file_handle:
            return self.yaml.load(file_handle.read())

    def load_checklist(self, file):
        """Load a checklist with all of its pages, tasks and facts from a YAML file and process all imports."""

        logger.info('Loading checklist data from "%s"', file)

        return self.process_checklist(self.load_yaml(file))

    def save_checklist(self, file, checklist):
        """Save a checklist and its pages, tasks and facts to a YAML file."""

        logger.info('Saving checklist data to "%s"', file)

        # Before writing the file, dump to a separate stream instead and check if we have an output.
        # This prevents saving an empty file if for some reason the dump fails.
        stream = io.StringIO()
        self.yaml.dump(checklist.to_dict(), stream)

        if stream.tell() == 0:
            raise Exception(f'Yaml dump failed. File "{file}" is left untouched')

        with open(file, mode='w', encoding='utf-8') as checklist_file:
            stream.seek(0)
            checklist_file.write(stream.read())

    def process_checklist(self, checklist):
        facts = {}

        if checklist is None:
            raise ValueError('Cannot load an empty checklist.')

        valid, message = utils.validate_dict_keys(checklist, {'title', 'pages'}, disallow_extra_keys=True)

        if not valid:
            logger.error(message)
            sys.exit(1)

        return models.Checklist(
            checklist['title'],
            self.process_page_list(checklist['pages'], facts),
            facts,
        )

    def process_page_list(self, page_list, facts):
        pages = []

        for page in page_list:
            page_directive, page_context = list(page.items())[0]

            if page_directive == 'linuxfabrik.clf.import':
                pages.extend(self.process_page_list(self.load_yaml(page_context), facts))
                continue

            pages.append(self.process_page(page, facts))

        return pages

    def process_page(self, page, facts):
        valid, message = utils.validate_dict_keys(page, {'title', 'tasks'}, optional_keys={'when'}, disallow_extra_keys=True)

        if not valid:
            logger.error(message)
            sys.exit(1)

        return models.Page(
            page['title'],
            self.process_task_list(page['tasks'], facts),
            page.get('when'),
        )

    def process_task_list(self, task_list, facts):
        tasks = []

        for task in task_list:
            task_module, task_context = list(task.items())[0]

            if task_module == 'linuxfabrik.clf.import':
                tasks.extend(self.process_task_list(self.load_yaml(task_context), facts))
                continue

            tasks.append(self.process_task(task, facts))

        return tasks

    def process_task(self, task, facts):
        task_module, task_context = list(task.items())[0]

        fact_name = task.get('fact_name')
        value = task.get('value')

        if fact_name is not None and value is not None:
            facts[fact_name] = value

        return models.Task(task_module, task_context, fact_name)
