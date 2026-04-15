# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

tbd


## [v1.6.3] - 2026-04-15

### Added

* core: `clf-play` now prints the product name and version as the first line on the console (e.g. `INFO - ChecklistFabrik v1.6.3`) so the running version is immediately visible in logs and bug reports

### Changed

* core: checkbox and radio group labels now blend in with the surrounding text input labels instead of inheriting the larger, bolder Spectre default style for `<legend>`
* core: standalone Markdown task blocks (`linuxfabrik.clf.markdown`) now keep the normal paragraph spacing. Previously a CSS rule intended for compact input labels also squashed the paragraphs inside standalone Markdown blocks

### Fixed

* core: Jinja expressions in template `value:` defaults (e.g. `value: '{{ now().strftime("%Y%m%d") }}01'`) are now resolved once at template load time. Before, the raw expression ended up in the facts and therefore also in any later Markdown/HTML content that referenced that fact. Applies to all input modules (checkbox, radio, select, text), not only `text_input`
* core: the line-wrap indicator (`↳`) inside code blocks no longer also appears on the first, non-wrapped visual line (caused by `background-repeat: repeat-y` wrapping the sprite above its starting position)
* modules: fact values containing special characters such as `"` no longer get double-escaped when interpolated into Markdown content or input labels (appeared as `&amp;#34;` in the browser instead of `"`). Regression introduced in v1.6.1 by enabling Jinja2 HTML autoescape on top of Mistune's own HTML escaping

### Security

* Harden the CI supply chain: the `pre-commit` install in the pre-commit-autoupdate workflow is now hash-pinned via `.github/pre-commit/requirements.txt` (generated with `pip-compile --generate-hashes --strip-extras`), and `dependabot/fetch-metadata` is pinned to a commit SHA so all GitHub Actions used in `.github/workflows/` are now pinned by hash. The policy is documented in CONTRIBUTING.md under "CI Supply Chain"


## [v1.6.2] - 2026-04-13

### Fixed

* modules: render Markdown in input labels as HTML again instead of showing the raw tags (e.g. `<strong>`) in the browser. Regression introduced in v1.6.1 by enabling Jinja2 HTML autoescape ([#99](https://github.com/Linuxfabrik/checklistfabrik/issues/99))


## [v1.6.1] - 2026-04-12

### Added

* Add bandit (security scanning) and vulture (dead code detection) to pre-commit hooks

### Changed

* Enforce a consistent Python code style (single-quoted strings, ruff lint rules) across the whole codebase ([#96](https://github.com/Linuxfabrik/checklistfabrik/issues/96))
* Silence false-positive bandit findings in test files so routine commits are no longer blocked ([#100](https://github.com/Linuxfabrik/checklistfabrik/issues/100))

### Fixed

* ci: fix `--require-hashes` pip installs in CI workflows by using pinned versions instead
* core: preserve the original error cause in tracebacks when re-raising exceptions

### Security

* core: prevent cross-site scripting in the checklist and dashboard web interfaces by enabling Jinja2 HTML autoescaping and escaping interpolated values in server-generated error messages. Users running untrusted checklist YAML files are strongly encouraged to upgrade ([#99](https://github.com/Linuxfabrik/checklistfabrik/issues/99))


## [v1.6.0] - 2026-04-07


### Added

* Add automated test suite (pytest) covering core utilities, data models, data mapper, all task modules, and the WSGI application
* Add GitHub Actions workflow for running tests and linting on every push and pull request
* Add linting and testing sections to CONTRIBUTING
* Add ruff linter and formatter to pre-commit hooks

### Fixed

* core: fix copying code blocks losing empty lines
* core: fix `not ... in` style to idiomatic `... not in`
* core: fix f-string without placeholders
* core: fix type comparison using `==` instead of `isinstance()`


## [v1.5.0] - 2026-04-01

### Added

* Add CONTRIBUTING
* Add pre-commit hooks
* core: wrap long lines in code blocks with hanging indent and a visual wrap indicator


## [v1.4.0] - 2026-03-19

### Added

* core: `clf-play` without arguments opens a dashboard listing available templates and reports
* core: new optional `description` field for checklist templates, displayed in the dashboard

### Changed

* core: log the full path when auto-generating report filenames
* modules: HTML improvements (accessible labels, semantic markup, HTML5 boolean attributes)

### Fixed

* core: also check page 0 for `when` conditions when navigating backwards
* core: escape code block language attribute to prevent XSS
* core: fix port validation allowing invalid port 65536
* core: remove unused import


## [v1.3.0] - 2025-10-31

### Added

* core: implicitly save when jumping through pages

### Changed

* core: split on_page URL route into separate functions for GET/POST

### Fixed

* core: also skip n/a pages with the previous button


## [v1.2.1] - 2025-07-16

### Fixed

* templates: only show the "Pages" progress indicator if there is more than one page available


## [v1.2.0] - 2025-05-15

### Added

* core: also save form with the "previous" button
* core: support Jinja in page titles

### Changed

* modules: rename text_output module to html

### Fixed

* core: allow loading from data URLs
* core: fix incorrect detection of HTML form checkbox/radio changed state
* core: add missing copy buttons to Markdown generated code blocks
* core: fix optical alignment of multiline HTML lists
* core: minor visual clarity improvements to inline code style
* templates: make HTML/CSS layout and design consistent


## [v1.1.0.0] - 2025-05-07

### Added

* core: auto-select free port for the HTTP server

### Fixed

* core: generate Windows-compatible fallback filenames
* core: don't validate HTML form on "Save and Exit" (so that one does not need to complete a page before saving)


## [v1.0.0.1] - 2025-05-02

Initial public release.


[Unreleased]: https://github.com/Linuxfabrik/checklistfabrik/compare/v1.6.3...HEAD
[v1.6.3]: https://github.com/Linuxfabrik/checklistfabrik/compare/v1.6.2...v1.6.3
[v1.6.2]: https://github.com/Linuxfabrik/checklistfabrik/compare/v1.6.1...v1.6.2
[v1.6.1]: https://github.com/Linuxfabrik/checklistfabrik/compare/v1.6.0...v1.6.1
[v1.6.0]: https://github.com/Linuxfabrik/checklistfabrik/compare/v1.5.0...v1.6.0
[v1.5.0]: https://github.com/Linuxfabrik/checklistfabrik/compare/v1.4.0...v1.5.0
[v1.4.0]: https://github.com/Linuxfabrik/checklistfabrik/compare/v1.3.0...v1.4.0
[v1.3.0]: https://github.com/Linuxfabrik/checklistfabrik/compare/v1.2.1...v1.3.0
[v1.2.1]: https://github.com/Linuxfabrik/checklistfabrik/compare/v1.2.0...v1.2.1
[v1.2.0]: https://github.com/Linuxfabrik/checklistfabrik/compare/v1.1.0.0...v1.2.0
[v1.1.0.0]: https://github.com/Linuxfabrik/checklistfabrik/compare/v1.0.0.1...v1.1.0.0
[v1.0.0.1]: https://github.com/Linuxfabrik/checklistfabrik/releases/tag/v1.0.0.1
