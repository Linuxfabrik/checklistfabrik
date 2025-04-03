class Checklist:
    """Models a ChecklistFabrik checklist."""

    def __init__(self, title, pages, facts, version=None):
        self.title = title
        self.pages = {page.title: page for page in pages}
        self.facts = facts
        self.version = version

    def to_dict(self):
        result = {
            'title': self.title,
            'pages': [page.to_dict(self.facts) for page in self.pages.values()],
        }

        if self.version is not None:
            result['version'] = self.version

        return result

    def first_page_name(self):
        key_list = list(self.pages.keys())

        if len(key_list) < 1:
            return None

        return key_list[0]

    def next_page_name(self, page_name):
        key_list = list(self.pages.keys())

        if not page_name in key_list:
            return None

        key_index = key_list.index(page_name)

        if key_index < len(key_list) - 1:
            return key_list[key_index + 1]

        return None

    def prev_page_name(self, page_name):
        key_list = list(self.pages.keys())

        if not page_name in key_list:
            return None

        key_index = key_list.index(page_name)

        if key_index > 0:
            return key_list[key_index - 1]

        return None
