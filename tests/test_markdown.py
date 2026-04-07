"""Tests for checklistfabrik.core.markdown."""

from checklistfabrik.core.markdown import ClfHtmlRenderer, create_markdown


class TestClfHtmlRenderer:
    def test_block_code_basic(self):
        renderer = ClfHtmlRenderer()
        result = renderer.block_code('print("hi")\n')
        assert '<pre class="code">' in result
        assert "<code>" in result
        assert "clf-code-line" in result
        assert "clf-code-copy-btn" in result

    def test_block_code_with_language(self):
        renderer = ClfHtmlRenderer()
        result = renderer.block_code("x = 1\n", info="python")
        assert 'data-lang="python"' in result

    def test_block_code_escapes_language(self):
        renderer = ClfHtmlRenderer()
        result = renderer.block_code("x\n", info="<script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_block_code_wraps_lines(self):
        renderer = ClfHtmlRenderer()
        result = renderer.block_code("line1\nline2\n")
        assert result.count("clf-code-line") == 2

    def test_link_target_blank(self):
        renderer = ClfHtmlRenderer()
        result = renderer.link("Click", "https://example.com")
        assert 'target="_blank"' in result
        assert 'href="https://example.com"' in result
        assert ">Click</a>" in result

    def test_link_with_title(self):
        renderer = ClfHtmlRenderer()
        result = renderer.link("Click", "https://example.com", title="My Title")
        assert 'title="My Title"' in result


class TestCreateMarkdown:
    def test_returns_callable(self):
        md = create_markdown()
        assert callable(md)

    def test_renders_paragraph(self):
        md = create_markdown()
        result = md("Hello **world**")
        assert "<strong>world</strong>" in result

    def test_renders_code_block(self):
        md = create_markdown()
        result = md("```\ncode\n```")
        assert "clf-code-line" in result

    def test_renders_strikethrough(self):
        md = create_markdown()
        result = md("~~deleted~~")
        assert "<del>deleted</del>" in result

    def test_renders_table(self):
        md = create_markdown()
        result = md("| A | B |\n|---|---|\n| 1 | 2 |")
        assert "<table>" in result
