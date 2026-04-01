# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

tbd


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


[Unreleased]: https://github.com/Linuxfabrik/checklistfabrik/compare/v1.5.0...HEAD
[v1.5.0]: https://github.com/Linuxfabrik/checklistfabrik/compare/v1.4.0...v1.5.0
[v1.4.0]: https://github.com/Linuxfabrik/checklistfabrik/compare/v1.3.0...v1.4.0
[v1.3.0]: https://github.com/Linuxfabrik/checklistfabrik/compare/v1.2.1...v1.3.0
[v1.2.1]: https://github.com/Linuxfabrik/checklistfabrik/compare/v1.2.0...v1.2.1
[v1.2.0]: https://github.com/Linuxfabrik/checklistfabrik/compare/v1.1.0.0...v1.2.0
[v1.1.0.0]: https://github.com/Linuxfabrik/checklistfabrik/compare/v1.0.0.1...v1.1.0.0
[v1.0.0.1]: https://github.com/Linuxfabrik/checklistfabrik/releases/tag/v1.0.0.1
