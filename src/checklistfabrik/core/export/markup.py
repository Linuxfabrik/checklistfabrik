"""Convert Markdown source into the markup dialects used by the static exporters.

Task labels and `linuxfabrik.clf.markdown` content are authored in Markdown. The
interactive HTML interface converts them with Mistune, but the static exporters need
the same content as reStructuredText, AsciiDoc, Markdown or plain text. The Markdown
source is therefore parsed once into Mistune's abstract syntax tree and walked by one
writer per target dialect, so every format is built from the same structure.

Known limitations, because the target dialects have no equivalent construct:

- reStructuredText has no strikethrough, so struck-through text is written as-is.
- reStructuredText has no inline image, so images become links.
- Headings inside task content become bold paragraphs in reStructuredText and AsciiDoc,
  because an arbitrary heading level inside a task would break the section hierarchy of
  the surrounding document.
"""

import html
import re

import mistune

# Same plugin set as the HTML interface, minus `speedup` which only tunes the HTML
# renderer and has no effect on the abstract syntax tree.
_parse_markdown = mistune.create_markdown(renderer=None, plugins=['strikethrough', 'table'])

_HTML_TAG = re.compile(r'<[^>]+>')
_TRAILING_UNDERSCORE = re.compile(r'_(?=\s|$)')


def strip_tags(text):
    """Reduce an HTML snippet to its text content."""

    return html.unescape(_HTML_TAG.sub('', text)).strip()


def indent_lines(text, prefix, first_prefix=None):
    """Indent every line of `text`, optionally with a different prefix on the first line."""

    if first_prefix is None:
        first_prefix = prefix

    lines = text.split('\n')
    indented = [f'{first_prefix}{lines[0]}'.rstrip()]
    indented += [f'{prefix}{line}'.rstrip() for line in lines[1:]]

    return '\n'.join(indented)


def parse(text):
    """Parse Markdown source into Mistune's abstract syntax tree."""

    return _parse_markdown(text or '')


def split_lead_html(html):
    """Split rendered HTML into the content of its first paragraph and the remaining blocks.

    The HTML exporter puts the first sentence of a label next to the checkbox marker and
    the rest below it, mirroring what `split_lead_paragraph` does for the other formats.
    """

    if html.startswith('<p>'):
        end = html.find('</p>')

        if end != -1:
            return html[len('<p>') : end], html[end + len('</p>') :].strip()

    return '', html.strip()


def split_lead_paragraph(text):
    """Split Markdown source into its leading paragraph and the remaining blocks.

    Task labels regularly consist of a sentence followed by a code block or a list. The
    exporters put that first sentence next to the checkbox marker and lay the rest out
    below it. A label that starts with a block right away has no leading paragraph.
    """

    nodes = [node for node in parse(text) if node['type'] != 'blank_line']

    if nodes and nodes[0]['type'] in ('paragraph', 'block_text'):
        return nodes[0], nodes[1:]

    return None, nodes


class MarkupWriter:
    """Render a Markdown abstract syntax tree into a target markup dialect.

    Subclasses override the small set of `paragraph`/`strong`/... hooks. The tree walk
    itself is shared, so a new output format only has to describe its own syntax.
    """

    BULLET = '- '

    def render(self, text):
        """Render Markdown source as a sequence of blocks."""

        return self.join_blocks(self.render_blocks(parse(text)))

    def render_label(self, text):
        """Render a short Markdown snippet, such as a task label, without block markup."""

        return self.render(text).strip()

    def render_nodes(self, nodes):
        """Render already parsed blocks, for example the remainder of a split label."""

        return self.join_blocks(self.render_blocks(nodes))

    def join_blocks(self, blocks):
        return '\n\n'.join(block for block in blocks if block)

    def render_blocks(self, tokens):
        return [block for block in (self.render_block(token) for token in tokens or []) if block]

    def render_block(self, token):
        node_type = token['type']
        attrs = token.get('attrs') or {}

        if node_type == 'blank_line':
            return ''

        if node_type == 'paragraph':
            return self.paragraph(self.render_inline(token.get('children')))

        if node_type == 'block_text':
            # Mistune wraps the content of a tight list item in a `block_text` token.
            return self.render_inline(token.get('children'))

        if node_type == 'heading':
            return self.heading(self.render_inline(token.get('children')), attrs.get('level', 1))

        if node_type == 'thematic_break':
            return self.thematic_break()

        if node_type == 'block_code':
            return self.code_block(token.get('raw', ''), attrs.get('info'))

        if node_type == 'block_quote':
            return self.quote(self.join_blocks(self.render_blocks(token.get('children'))))

        if node_type == 'list':
            return self.render_list(token)

        if node_type == 'block_html':
            return self.raw_html(token.get('raw', ''))

        if node_type == 'table':
            return self.render_table(token)

        # Unknown block type: keep whatever content it carries instead of dropping it.
        if token.get('children'):
            return self.join_blocks(self.render_blocks(token['children']))

        return self.escape(token.get('raw', ''))

    def render_list(self, token, depth=0):
        ordered = (token.get('attrs') or {}).get('ordered', False)
        items = []

        for item in token.get('children') or []:
            blocks = []

            for child in item.get('children') or []:
                if child['type'] == 'list':
                    blocks.append(self.render_list(child, depth + 1))
                else:
                    rendered = self.render_block(child)

                    if rendered:
                        blocks.append(rendered)

            items.append(self.join_item_blocks(blocks))

        return self.list_block(items, ordered, depth)

    def render_table(self, token):
        head = []
        rows = []

        for section in token.get('children') or []:
            if section['type'] == 'table_head':
                head = [
                    self.render_inline(cell.get('children'))
                    for cell in section.get('children') or []
                ]
            elif section['type'] == 'table_body':
                rows = [
                    [self.render_inline(cell.get('children')) for cell in row.get('children') or []]
                    for row in section.get('children') or []
                ]

        return self.table(head, rows)

    def render_inline(self, tokens):
        parts = []

        for token in tokens or []:
            node_type = token['type']
            attrs = token.get('attrs') or {}

            if node_type == 'text':
                parts.append(self.escape(token.get('raw', '')))
            elif node_type == 'strong':
                parts.append(self.strong(self.render_inline(token.get('children'))))
            elif node_type == 'emphasis':
                parts.append(self.emphasis(self.render_inline(token.get('children'))))
            elif node_type == 'strikethrough':
                parts.append(self.strikethrough(self.render_inline(token.get('children'))))
            elif node_type == 'codespan':
                parts.append(self.codespan(token.get('raw', '')))
            elif node_type == 'link':
                parts.append(
                    self.link(self.render_inline(token.get('children')), attrs.get('url', ''))
                )
            elif node_type == 'image':
                parts.append(
                    self.image(self.render_inline(token.get('children')), attrs.get('url', ''))
                )
            elif node_type == 'linebreak':
                parts.append(self.linebreak())
            elif node_type == 'softbreak':
                # Soft line breaks are reflowed into running text, so exported documents
                # do not inherit the line wrapping of the YAML source.
                parts.append(' ')
            elif node_type == 'inline_html':
                parts.append(self.inline_html(token.get('raw', '')))
            elif token.get('children'):
                parts.append(self.render_inline(token['children']))
            else:
                parts.append(self.escape(token.get('raw', '')))

        return ''.join(parts)

    # --- dialect hooks, overridden by the subclasses ---

    def escape(self, text):
        return text

    def paragraph(self, text):
        return text

    def heading(self, text, level):
        return self.strong(text)

    def thematic_break(self):
        return '---'

    def code_block(self, code, info=None):
        return code.rstrip('\n')

    def quote(self, text):
        return indent_lines(text, '    ')

    def join_item_blocks(self, blocks):
        """Join the blocks that make up a single list item."""

        return self.join_blocks(blocks)

    def list_block(self, items, ordered, depth):
        lines = []

        for index, item in enumerate(items, start=1):
            marker = f'{index}. ' if ordered else self.BULLET
            lines.append(indent_lines(item, ' ' * len(marker), marker))

        # An item that spans several lines needs a blank line around it, otherwise its
        # continuation would be read as part of the previous item.
        separator = '\n' if all('\n' not in item for item in items) else '\n\n'

        return separator.join(lines)

    def table(self, head, rows):
        lines = []

        if head:
            lines.append(' | '.join(head))

        lines += [' | '.join(row) for row in rows]

        return '\n'.join(lines)

    def raw_html(self, html):
        return ''

    def inline_html(self, html):
        return ''

    def linebreak(self):
        return ' '

    def strong(self, text):
        return text

    def emphasis(self, text):
        return text

    def strikethrough(self, text):
        return text

    def codespan(self, text):
        return text

    def link(self, text, url):
        return f'{text} ({url})' if text else url

    def image(self, alt, url):
        return self.link(alt, url)


class RstWriter(MarkupWriter):
    """Render Markdown as reStructuredText."""

    def escape(self, text):
        escaped = text.replace('\\', '\\\\')

        for character in ('*', '`', '|'):
            escaped = escaped.replace(character, f'\\{character}')

        # A trailing underscore would turn the word into a reference.
        return _TRAILING_UNDERSCORE.sub('\\_', escaped)

    def code_block(self, code, info=None):
        language = info.split(None, 1)[0] if info else None
        body = indent_lines(code.rstrip('\n'), '   ')

        if language:
            # `code` is the docutils directive and is understood by Sphinx as well, unlike
            # the Sphinx-only `code-block`.
            return f'.. code:: {language}\n\n{body}'

        return f'::\n\n{body}'

    def quote(self, text):
        # A plain indented block quote would be swallowed by a directive that happens to
        # precede it (for example a list-table), so the self-delimiting directive is used.
        return f'.. pull-quote::\n\n{indent_lines(text, "   ")}'

    def table(self, head, rows):
        lines = ['.. list-table::']

        if head:
            lines.append('   :header-rows: 1')

        lines.append('')

        for row in ([head] if head else []) + rows:
            for index, cell in enumerate(row):
                lines.append(f'   {"*" if index == 0 else " "} - {cell}'.rstrip())

        return '\n'.join(lines)

    def raw_html(self, html):
        return f'.. raw:: html\n\n{indent_lines(html.strip(), "   ")}'

    def linebreak(self):
        return ' '

    def strong(self, text):
        return f'**{text}**' if text else ''

    def emphasis(self, text):
        return f'*{text}*' if text else ''

    def codespan(self, text):
        # Inline literals are not parsed further, so the raw text goes in unescaped.
        return f'``{text}``'

    def link(self, text, url):
        if not text:
            return f'`{url} <{url}>`_'

        return f'`{text} <{url}>`_'


class AsciiDocWriter(MarkupWriter):
    """Render Markdown as AsciiDoc."""

    def escape(self, text):
        escaped = text.replace('\\', '\\\\')

        for character in ('*', '_', '`', '#', '+'):
            escaped = escaped.replace(character, f'\\{character}')

        return escaped

    def thematic_break(self):
        return "'''"

    def code_block(self, code, info=None):
        language = info.split(None, 1)[0] if info else None
        header = f'[source,{language}]\n' if language else ''

        return f'{header}----\n{code.rstrip(chr(10))}\n----'

    def quote(self, text):
        return f'____\n{text}\n____'

    def join_item_blocks(self, blocks):
        # AsciiDoc reads an indented line as a literal block, so list items are never
        # indented and a nested list follows on the very next line.
        return '\n'.join(block for block in blocks if block)

    def list_block(self, items, ordered, depth):
        # AsciiDoc expresses nesting by repeating the marker instead of indenting.
        marker = ('.' if ordered else '*') * (depth + 1)

        return '\n'.join(f'{marker} {item}' for item in items)

    def table(self, head, rows):
        lines = []

        if head:
            lines.append('[options="header"]')

        lines.append('|===')

        for row in ([head] if head else []) + rows:
            lines.append(''.join(f'| {cell} ' for cell in row).rstrip())

        lines.append('|===')

        return '\n'.join(lines)

    def raw_html(self, html):
        return f'++++\n{html.strip()}\n++++'

    def inline_html(self, html):
        return f'pass:[{html}]'

    def linebreak(self):
        return ' +\n'

    def strong(self, text):
        return f'*{text}*' if text else ''

    def emphasis(self, text):
        return f'_{text}_' if text else ''

    def strikethrough(self, text):
        return f'[.line-through]#{text}#' if text else ''

    def codespan(self, text):
        return f'`+{text}+`'

    def link(self, text, url):
        return f'{url}[{text}]' if text else url

    def image(self, alt, url):
        return f'image:{url}[{alt}]'


class MarkdownWriter(MarkupWriter):
    """Render Markdown as normalised Markdown.

    The Markdown export is not a copy of the source: task labels and content blocks are
    reassembled into a single document, so they go through the same writer pipeline as
    every other format.
    """

    #: Content headings are pushed below the document title and the page headings.
    TOP_HEADING_LEVEL = 3

    def __init__(self):
        self._heading_offset = 0

    def render(self, text):
        tokens = parse(text)

        # Task content is authored on its own, so its top-most heading may sit at any
        # level. The whole block is shifted so it starts right below the page heading.
        levels = [
            (token.get('attrs') or {}).get('level', 1)
            for token in tokens
            if token['type'] == 'heading'
        ]
        self._heading_offset = self.TOP_HEADING_LEVEL - min(levels) if levels else 0

        return self.join_blocks(self.render_blocks(tokens))

    def escape(self, text):
        escaped = text.replace('\\', '\\\\')

        for character in ('*', '_', '`', '[', ']'):
            escaped = escaped.replace(character, f'\\{character}')

        return escaped

    def heading(self, text, level):
        return f'{"#" * min(max(level + self._heading_offset, 1), 6)} {text}'

    def code_block(self, code, info=None):
        language = info.split(None, 1)[0] if info else ''

        return f'```{language}\n{code.rstrip(chr(10))}\n```'

    def quote(self, text):
        return '\n'.join(f'> {line}'.rstrip() for line in text.split('\n'))

    def table(self, head, rows):
        if not head:
            head = [''] * (len(rows[0]) if rows else 0)

        lines = [
            '| ' + ' | '.join(head) + ' |',
            '| ' + ' | '.join(['---'] * len(head)) + ' |',
        ]
        lines += ['| ' + ' | '.join(row) + ' |' for row in rows]

        return '\n'.join(lines)

    def raw_html(self, html):
        return html.strip()

    def inline_html(self, html):
        return html

    def linebreak(self):
        return '  \n'

    def strong(self, text):
        return f'**{text}**' if text else ''

    def emphasis(self, text):
        return f'*{text}*' if text else ''

    def strikethrough(self, text):
        return f'~~{text}~~' if text else ''

    def codespan(self, text):
        return f'`{text}`'

    def link(self, text, url):
        return f'[{text}]({url})' if text else f'<{url}>'

    def image(self, alt, url):
        return f'![{alt}]({url})'


class HtmlWriter(MarkupWriter):
    """Render Markdown as HTML.

    This writer hands the whole tree to Mistune instead of walking it, so the per-node
    hooks of the base class do not apply. Callers that need the leading paragraph of a
    label separately split the rendered HTML with `split_lead_html`.
    """

    def render_inline(self, tokens):
        raise NotImplementedError('HtmlWriter renders whole blocks; use split_lead_html')

    def render_nodes(self, nodes):
        raise NotImplementedError('HtmlWriter renders whole blocks; use split_lead_html')

    def __init__(self):
        # Not the renderer of the interactive interface: that one adds a JavaScript-driven
        # copy button to every code block, which has no meaning in a static document.
        self._render_html = mistune.create_markdown(
            escape=False,
            plugins=['strikethrough', 'table'],
        )

    def render(self, text):
        return str(self._render_html(text or ''))

    def render_label(self, text):
        html = self.render(text).strip()

        # A label is inline content, so the single wrapping paragraph is dropped.
        if html.startswith('<p>') and html.endswith('</p>') and '<p>' not in html[3:]:
            return html[3:-4]

        return html


class TextWriter(MarkupWriter):
    """Render Markdown as plain text, keeping only the structure that survives without markup."""

    def heading(self, text, level):
        return text

    def code_block(self, code, info=None):
        return indent_lines(code.rstrip('\n'), '    ')

    def table(self, head, rows):
        return '\n'.join('  '.join(row) for row in (([head] if head else []) + rows))

    def link(self, text, url):
        return f'{text} ({url})' if text else url

    def raw_html(self, html):
        # A plain-text target cannot show markup, but the text inside it is still content.
        return strip_tags(html)

    def inline_html(self, html):
        return strip_tags(html)
