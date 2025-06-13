# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)


## [Unreleased]

### Fixed ("fix")

- templates: only show the 'Pages' progress indicator if there is more than one page available



## [v1.2.0] - 2025-05-15

### Added ("feat")

- core: also save form with the 'previous' button
- core: support Jinja in page titles


### Fixed ("fix")

- make html/css layout and design consistent
- core: allow loading from data urls
- core: fix incorrect detection of HTML form checkbox/radio changed state
- core: add missing copy buttons to Markdown generated code blocks
- core: fix optical alignment of multiline HTML lists
- core: minor visual clarity improvements to inline code style



## [v1.1.0.0] - 2025-05-07

### Added ("feat")

- core: auto-select free port for the HTTP server


### Fixed ("fix")

- core: generate Windows compatible fallback filenames
- core: don't validate HTML form on "Save and Exit" (so that one does not need to complete a page before saving)



## [v1.0.0.1] - 2025-05-02

Initial public release


[Unreleased]: https://github.com/Linuxfabrik/checklistfabrik/compare/v1.2.0...HEAD
[v1.2.0]: https://github.com/Linuxfabrik/checklistfabrik/compare/v1.1.0.0...v1.2.0
[v1.1.0.0]: https://github.com/Linuxfabrik/checklistfabrik/compare/v1.0.0.1...v1.1.0.0
[v1.0.0.1]: https://github.com/Linuxfabrik/checklistfabrik/releases/tag/v1.0.0.1
