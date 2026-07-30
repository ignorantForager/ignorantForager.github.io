"""
build.py — ignorantforager.com

Workflow:
    1. Drop a new page's markdown file into pages/ (top-level = a page,
       pages/posts/ = a blog post).
    2. Run:  python build.py
    3. Commit and push the regenerated docs/ folder.

New pages auto-appear in site nav (using their frontmatter `title`,
or `nav` if you want a different nav label). New posts auto-appear
on the homepage, newest first. No code changes needed for new content.
"""

import datetime
import re
from pathlib import Path

import frontmatter
import markdown
from flask import Flask, render_template, abort
from flask_frozen import Freezer

BASE_DIR = Path(__file__).parent
PAGES_DIR = BASE_DIR / "pages"
POSTS_DIR = PAGES_DIR / "posts"

app = Flask(__name__)
app.config["FREEZER_DESTINATION"] = str(BASE_DIR / "docs")
app.config["FREEZER_RELATIVE_URLS"] = False
app.config["FREEZER_REMOVE_EXTRA_FILES"] = True
# CNAME and .nojekyll are GitHub Pages config files, not build output -
# don't let Frozen-Flask delete them on rebuild.
app.config["FREEZER_DESTINATION_IGNORE"] = ["CNAME", ".nojekyll", ".git*"]

MD = markdown.Markdown(
    extensions=["pymdownx.superfences", "pymdownx.highlight", "tables", "sane_lists"],
    extension_configs={
        "pymdownx.highlight": {"css_class": "codehilite", "guess_lang": False},
    },
)


def render_inline(text):
    """Run a single line through the shared markdown pipeline (for link/emphasis
    syntax inside a book-list line) and strip the wrapping <p> it produces."""
    MD.reset()
    html = MD.convert(text)
    return re.sub(r"^<p>(.*)</p>$", r"\1", html, flags=re.S).strip()


RATING_RE = re.compile(r"\(\s*(\d+(?:\.\d+)?)\s*stars?\)\s*$", re.IGNORECASE)
YEAR_RE = re.compile(r"^\d{4}$")
DASHES_RE = re.compile(r"^-+$")


def parse_book_list(text):
    """Parse the 'YEAR / dashes / one book per line' format into
    [{"year": "2026", "books": [{"html": ..., "rating": 3.5 or None}, ...]}, ...]
    Books support optional trailing "(N stars)" (any decimal - quarter/half/etc.)
    and optional [title](url) markdown link syntax."""
    lines = text.splitlines()
    years = []
    current = None
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if (
            YEAR_RE.match(line)
            and i + 1 < len(lines)
            and DASHES_RE.match(lines[i + 1].strip())
        ):
            current = {"year": line, "books": []}
            years.append(current)
            i += 2
            continue
        if current is not None:
            m = RATING_RE.search(line)
            rating = float(m.group(1)) if m else None
            book_text = line[: m.start()].rstrip() if m else line
            current["books"].append({"html": render_inline(book_text), "rating": rating})
        i += 1
    return years


class Content:
    """Wraps a parsed markdown file (page or post)."""

    def __init__(self, path: Path):
        post = frontmatter.load(path)
        self.slug = path.stem
        self.meta = post.metadata
        self.title = self.meta.get("title", self.slug.replace("-", " ").title())
        self.layout = self.meta.get("layout", "default")
        if self.layout == "books":
            self.html = ""
            self.years = parse_book_list(post.content)
        else:
            MD.reset()
            self.html = MD.convert(post.content)

    @property
    def date(self):
        d = self.meta.get("date")
        if isinstance(d, datetime.datetime):
            return d.date()
        if isinstance(d, datetime.date):
            return d
        return datetime.date.min

    @property
    def category(self):
        return self.meta.get("category", "default")

    @property
    def tags(self):
        return self.meta.get("tags", [])

    @property
    def nav_label(self):
        return self.meta.get("nav", self.title)

    @property
    def nav_order(self):
        return self.meta.get("nav_order", 999)

    @property
    def hidden(self):
        return bool(self.meta.get("hidden", False))

    @property
    def excerpt(self):
        """First <p>...</p> block from the rendered HTML, for homepage previews."""
        match = re.search(r"<p>.*?</p>", self.html, re.S)
        return match.group(0) if match else ""


def load_pages():
    """Top-level pages/*.md (not posts/) become generic site pages."""
    pages = {}
    for path in sorted(PAGES_DIR.glob("*.md")):
        c = Content(path)
        pages[c.slug] = c
    return pages


def load_posts():
    """pages/posts/*.md become blog posts, newest first."""
    posts = {}
    for path in sorted(POSTS_DIR.glob("*.md")):
        c = Content(path)
        posts[c.slug] = c
    return posts


PAGES = load_pages()
POSTS = load_posts()


def nav_pages():
    visible = [p for p in PAGES.values() if not p.hidden]
    return sorted(visible, key=lambda p: (p.nav_order, p.nav_label.lower()))


@app.context_processor
def inject_nav():
    return {"nav_pages": nav_pages()}


@app.route("/")
def index():
    ordered = sorted(POSTS.values(), key=lambda p: p.date, reverse=True)
    latest = ordered[0] if ordered else None
    rest = ordered[1:]
    return render_template("index.html", latest=latest, rest=rest, title=None)


@app.route("/posts/<slug>/")
def post(slug):
    p = POSTS.get(slug)
    if p is None:
        abort(404)
    return render_template("post.html", post=p, title=p.title)


@app.route("/<slug>/")
def page(slug):
    p = PAGES.get(slug)
    if p is None:
        abort(404)
    template_name = f"page-{p.layout}.html" if p.layout != "default" else "page.html"
    return render_template(template_name, page=p, title=p.title)


freezer = Freezer(app)


@freezer.register_generator
def post_url_generator():
    for slug in POSTS:
        yield "post", {"slug": slug}


@freezer.register_generator
def page_url_generator():
    for slug in PAGES:
        yield "page", {"slug": slug}


if __name__ == "__main__":
    freezer.freeze()
    print(f"Built {len(PAGES)} page(s) and {len(POSTS)} post(s) -> {app.config['FREEZER_DESTINATION']}")
