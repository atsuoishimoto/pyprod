import mistune
from pygments import highlight
from pygments.formatters import html
from pygments.lexers import get_lexer_by_name


class HighlightRenderer(mistune.HTMLRenderer):
    def block_code(self, code, info=None):
        if info:
            if info == "mermaid":
                return "<pre class='mermaid'>\n" + mistune.escape(code) + "\n</pre>"
            else:
                lexer = get_lexer_by_name(info, stripall=True)
                formatter = html.HtmlFormatter(noclasses=True)
                return highlight(code, lexer, formatter)
        return "<pre><code>" + mistune.escape(code) + "</code></pre>"


renderer = HighlightRenderer()
markdown = mistune.create_markdown(renderer=renderer, plugins=["math"])


def md_to_html(md):
    return markdown(md)
