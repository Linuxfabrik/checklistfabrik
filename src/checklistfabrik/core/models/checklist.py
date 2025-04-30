class Checklist:
    """Models a ChecklistFabrik checklist."""

    def __init__(self, title, pages, facts, report_path=None, version=None):
        self.title = title
        self.pages = pages
        self.facts = facts
        self.report_path = report_path
        self.version = version

    def __len__(self):
        return len(self.pages)

    def to_dict(self):
        result = {
            'title': self.title,
            'pages': [page.to_dict(self.facts) for page in self.pages],
        }

        if self.version is not None:
            result['version'] = self.version

        return result
