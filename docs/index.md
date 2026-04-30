# Linuxfabrik ChecklistFabrik

Python tool that generates interactive HTML checklists from YAML templates. Jinja conditionals, reusable includes, pluggable modules, built-in web server. Ideal for SOPs, deployments and recurring ops.

Made by [Linuxfabrik](https://www.linuxfabrik.ch).


## Overview

ChecklistFabrik (`clf-play`) helps Linux System Engineers manage recurring checklists, processes and procedures. Templates are plain YAML, so they can live next to the rest of your infrastructure code in Git. At runtime, `clf-play` renders them as interactive HTML forms served by a built-in web server, tracks progress on every page submit, and writes the answers to a YAML report file.

Jinja expressions cover dynamic page titles, `when`-conditional pages and tasks, automatic report filenames, and reusable includes. A dashboard lists templates and reports in the current directory and lets you start or resume a checklist with a single click.


## Quick Start

1. Install with [uv](https://docs.astral.sh/uv/): `uvx checklistfabrik`
2. Read the [User Guide](user_guide.md)
3. Browse runnable examples in the [`examples/`](https://github.com/Linuxfabrik/checklistfabrik/tree/main/examples) directory of the repository

A minimal template:

```yaml
title: 'Server Maintenance'
description: 'Monthly maintenance procedure for production servers.'
pages:
  - title: 'Preparation'
    tasks:
      - linuxfabrik.clf.text_input:
          label: 'Ticket number'
          required: true
        fact_name: 'ticket'

      - linuxfabrik.clf.checkbox_input:
          values:
            - label: 'Notify users about the maintenance window'
            - label: 'Create a full backup'
          required: true
```

Run it:

```shell
clf-play --template server-maintenance.yml
```


## Links

- [Changelog](CHANGELOG.md)
- [Contributing](contributing.md)
- [GitHub Repository](https://github.com/Linuxfabrik/checklistfabrik)
- [Linuxfabrik Website](https://www.linuxfabrik.ch)
- [PyPI](https://pypi.org/project/checklistfabrik/)
- [Report an Issue](https://github.com/Linuxfabrik/checklistfabrik/issues/new/choose)
- [Security Policy](security.md)
