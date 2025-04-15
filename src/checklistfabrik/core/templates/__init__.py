"""Package that contains the ChecklistFabrik Jinja templates and assets."""

import pathlib

import jinja2


def get_assets_path():
    return pathlib.Path(__file__).parent / 'assets'


def get_template_loader():
    return jinja2.PackageLoader(__name__, '.')


def get_template_path():
    return pathlib.Path(__file__).parent
