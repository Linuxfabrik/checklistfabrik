import argparse
import logging
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
        self.args = self.arg_parser.parse_args(args)

    def validate_args(self):
        pass

    def run(self):
        raise NotImplementedError('This method must be implemented by a subclass')

    def init_logging(self, console_log_level=logging.INFO, file_log_level=logging.DEBUG):
        root_module_name = __name__.split('.', maxsplit=1)[0]
        self.logger = logging.getLogger(root_module_name)
        self.logger.setLevel(min(console_log_level, file_log_level))

        file_handler = logging.FileHandler(f'{root_module_name}.log')
        file_handler.setLevel(file_log_level)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

        self.logger.addHandler(file_handler)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_log_level)
        console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))

        self.logger.addHandler(console_handler)

    @classmethod
    def main(cls, args=None):
        if args is None:
            args = sys.argv[1:]

        cli = cls()

        cli.init_args()
        cli.parse_args(args)
        cli.validate_args()

        cli.init_logging()

        sys.exit(cli.run())
