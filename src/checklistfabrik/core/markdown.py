import mistune


class ClfHtmlRenderer(mistune.HTMLRenderer):
    def block_code(self, code, info=None):
        """Renders spectre.css compatible code blocks."""

        attributes = ''

        if info:
            attributes += f' data-lang="{mistune.util.escape(info.split(None, 1)[0])}"'

        lines = code.split('\n')
        if lines and lines[-1] == '':
            lines = lines[:-1]
        wrapped = ''.join(
            f'<span class="clf-code-line">{mistune.util.escape(line)}</span>'
            for line in lines
        )

        return (
            # DO NOT include line breaks / other whitespace in the `pre`-element as whitespace is displayed for `pre`-elements.
            f'<pre class="code"{attributes}>'
            '<button class="btn btn-link btn-sm clf-code-copy-btn" type="button">Copy</button>'
            f'<code>{wrapped}</code>'
            '</pre>'
        )

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
