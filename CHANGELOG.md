# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

### Security

* **ci**: Scope `GITHUB_TOKEN` permissions in the dependabot-auto-merge workflow to the job level, with top-level now `read-all`. Matches the pattern used by the other Linuxfabrik workflows and addresses the OpenSSF Scorecard `Token-Permissions` finding.

### Added

* docs: project website at https://linuxfabrik.github.io/checklistfabrik/, generated from the existing User Guide and the standard repository docs (README, Changelog, Contributing, Security). The site is rebuilt automatically on every push to `main`


## [v1.7.0] - 2026-04-28

### Added

* modules: new `linuxfabrik.clf.run_template` module that embeds another checklist template as a card with a "Run" button. Clicking the button launches the referenced template in a new browser tab as an independent checklist with its own report file. Useful for splitting long procedures into reusable, self-contained sub-checklists. The card shows the target template's title and description by default; both can be overridden per call and support Jinja and Markdown

### Changed

* core: progress is now saved to the report file on every page submit (Next, Previous, Page-Jump, Save & Continue Later) instead of only when the server shuts down cleanly. Closing the browser tab or losing the terminal session no longer drops already-submitted answers
* core: the destination filename is now fixed on the first save (the template's `report_path` and the free-name search are evaluated once). Earlier versions could end up writing to a different file name on every save when `report_path` contained dynamic expressions
* core: a `SIGTERM` or other unclean shutdown now flushes any in-memory state to disk as a last-resort safety net, complementing the new save-on-submit behaviour
* core: the separate "Checklist completed" page is gone. After the last page the server saves and shuts down directly, ending on the existing shutdown screen which now confirms that the report has been saved
* core: button labels in the navigation bar have been clarified. The mid-run "Save and Exit" is now "Continue Later" (with a pause icon and a tooltip explaining what it actually does — stop the local web server; the answers are already on disk thanks to save-on-submit). The last-page "Next" becomes "Finish". "Previous" and "Next" carry direction arrows. Submit values stay the same, so existing report files remain compatible
* core: redesigned the checklist page layout. The container is wider, the redundant top navigation bar is gone (only the bottom one remains so users read tasks before navigating), the page title is shown clearly between the stepper and the form, the template version is rendered small and gray with a tooltip explaining the `YYYYMMDDNN` format, and the "Required fields are marked …" hint only appears on pages that actually contain required tasks
* core: redesigned the page stepper. It now shows real, Jinja-rendered page titles instead of "Page 1, Page 2, …", the active step marker is more prominent, the connector line is coloured to distinguish completed steps from upcoming ones, and tooltips communicate that clicking a step jumps without validating the current page's required fields
* core: each task is now visually framed by a coloured left-border accent — red for required, gray for optional. The previous orange asterisk + orange `:invalid` input border + horizontal divider lines between tasks have been removed
* core: items within checkbox / radio groups are now separated by a thin hairline and aligned with their indicator via a flex layout, so groups with long items (code blocks, bullet lists, multi-line descriptions) stay scannable
* core: pressing Enter anywhere on a checklist page (in or outside an input field) now reliably submits the form as Next. Previously this only worked while a text input was focused
* modules: `linuxfabrik.clf.run_template` cards now use a compact single-row layout (title on the left, Run button on the right). The full target file path is shown in the Run-button tooltip rather than as a separate line, which cuts the per-card height roughly in half and keeps long lists of sub-checklists scannable


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


[Unreleased]: https://github.com/Linuxfabrik/checklistfabrik/compare/v1.7.0...HEAD
[v1.7.0]: https://github.com/Linuxfabrik/checklistfabrik/compare/v1.6.3...v1.7.0
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
