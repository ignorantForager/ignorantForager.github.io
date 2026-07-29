# ignorantforager.com

Static site built with Flask + Frozen-Flask, hosted on GitHub Pages from `docs/`.

## Adding a new page

Drop a markdown file into `pages/` (e.g. `pages/projects.md`) with frontmatter like:

```markdown
---
title: Projects
---

Your content here.
```

It will automatically appear in the site nav and be reachable at `/projects/`.
Use `nav: Custom Label` to override the nav text, `nav_order: 2` to control
its position in the nav, or `hidden: true` to keep it out of the nav (still
reachable by direct link).

## Adding a new blog post

Drop a markdown file into `pages/posts/` with frontmatter like:

```markdown
---
title: "Post Title"
date: 2026-07-28
category: homelab
tags: [docker, homelab]
---

Your content here.
```

It will automatically appear on the homepage (newest first) and be reachable
at `/posts/your-filename-slug/`. `category` should be one of `networking`,
`homelab`, or `security` to get a matching color dot — anything else falls
back to a default color (see `static/css/style.css`, `.dot-*` classes, and
`build.py`'s `Content.category` if you want to add more categories/colors).

## Building the site

```bash
pip install -r requirements.txt
python build.py
```

This regenerates the entire `docs/` folder (removing anything no longer
produced by a source file, except `CNAME` and `.nojekyll`, which are
protected). Commit and push `docs/` along with any new source files.

## Previewing locally before building

```bash
pip install -r requirements.txt
python -c "from build import app; app.run(debug=True)"
```

Then visit `http://127.0.0.1:5000/`.

## Structure

```
pages/            markdown source for pages (About, future pages)
pages/posts/      markdown source for blog posts
templates/        Jinja2 templates (base, index, post, page)
static/           CSS, favicon, images — referenced by markdown/templates
build.py          Flask app + Frozen-Flask build script
docs/             generated static output — what GitHub Pages serves
```

## GitHub Pages setup

In the repo's Settings → Pages, set the source to the `main` branch,
`/docs` folder. `docs/CNAME` already points at `ignorantforager.com` —
update it if the domain ever changes. `docs/.nojekyll` tells GitHub Pages
not to run Jekyll processing on the output.
