import mistune


class ClfHtmlRenderer(mistune.HTMLRenderer):
    def block_code(self, code, info=None):
        """Renders spectre.css compatible code blocks."""

        attributes = ''

        if info:
            attributes += f' data-lang="{info.split(None, 1)[0]}"'

        return f'<pre class="code"{attributes}><code>{mistune.util.escape(code)}</code></pre>'

    def link(self, text, url, title=None):
        """Renders links as an HTML anchor with the `target="_blank"` attribute."""

        attributes = ''

        if title:
            attributes += f' title="{mistune.util.safe_entity(title)}"'

        return f'<a href="{self.safe_url(url)}" target="_blank"{attributes}>{text}</a>'


def create_markdown():
    return mistune.create_markdown(
        escape=False,
        renderer=ClfHtmlRenderer(),
        plugins=['strikethrough', 'table', 'speedup'],
    )
