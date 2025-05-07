import argparse
import logging
import os
import pathlib
import platform
import sys


class BaseCli:
    """A base CLI implementation of common code for building complete CLIs."""

    def __init__(self, description=None):
        self.arg_parser = argparse.ArgumentParser(description=description)
        self.args = None
        self.logger = None

    def init_args(self):
        raise NotImplementedError('This method must be implemented by a subclass')

    def parse_args(self, args):
        self.arg_parser.prog = os.path.basename(args[0])
        self.args = self.arg_parser.parse_args(args[1:])

    def validate_args(self):
        pass

    def run(self):
        raise NotImplementedError('This method must be implemented by a subclass')

    def init_logging(self, console_log_level=logging.INFO, file_log_level=logging.DEBUG):
        root_module_name = __name__.split('.', maxsplit=1)[0]
        self.logger = logging.getLogger(root_module_name)
        self.logger.setLevel(min(console_log_level, file_log_level))

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_log_level)
        console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))

        self.logger.addHandler(console_handler)

        instance_module_name = type(self).__module__.rsplit(".", maxsplit=1)[-1]
        log_file_name = f'{root_module_name}-{instance_module_name}.log'
        os_name = platform.system()

        if os_name == 'Darwin':
            log_path = pathlib.Path.home() / 'Library' / 'Logs' / root_module_name / log_file_name
        elif os_name == 'Linux':
            log_path = pathlib.Path(os.getenv('XDG_DATA_HOME', pathlib.Path.home() / '.local' / 'share')) / log_file_name
        elif os_name == 'Windows' and 'APPDATA' in os.environ:
            log_path = pathlib.Path(os.environ['APPDATA']) / root_module_name / log_file_name
        else:
            log_path = pathlib.Path.cwd() / log_file_name

        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.touch(mode=0o644, exist_ok=True)
        except FileExistsError:
            self.logger.error('Cannot create/open log file in "%s" as it is not a directory', log_path.parent)
        except PermissionError:
            self.logger.error('Cannot write to log file "%s"', log_path)
        else:
            self.logger.info('Writing log to file "%s"', log_path)

            file_handler = logging.FileHandler(log_path, mode='w')
            file_handler.setLevel(file_log_level)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

            self.logger.addHandler(file_handler)

    @classmethod
    def main(cls, args=None):
        if args is None:
            args = sys.argv

        cli = cls()

        cli.init_args()
        cli.parse_args(args)
        cli.validate_args()

        cli.init_logging(
            console_log_level=logging.DEBUG if getattr(cli.args, 'verbose', False) else logging.INFO,
        )

        sys.exit(cli.run())


class IntRange:
    """
    "Type" for argparse to check if an integer is in a given range.

    Use this instead of `choices=range(min, max + 1)` to avoid printing each
    possible value on the help text (especially helpful for large ranges).
    """

    def __init__(self, min, max):
        self.min = min
        self.max = max

    def __call__(self, string):
        value = None

        try:
            value = int(string)

            if not (self.min <= value <= self.max):
                raise ValueError

            return value
        except ValueError:
            msg = f'must be an integer in range [{self.min}, {self.max}]'

            if type(value) == int:
                msg += f', got {value}'

            raise argparse.ArgumentTypeError(msg)
