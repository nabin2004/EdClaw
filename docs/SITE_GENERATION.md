# Site Generation

EduClaw can scaffold a complete **Jekyll course website** from an autocourse series directory. The system uses [Copier](https://copier.readthedocs.io/) to render a parameterized template, converts autocourse lecture markdown into Jekyll `_lectures/` format, and maintains a central course registry with a browsable catalog page.

## Quick start

```bash
# Generate a site from an existing autocourse series
educlaw site generate content/ir/series/2026-04-23-intro-linear-algebra-8

# Or include site generation in the full pipeline
python scripts/run_full_course_pipeline.py "Linear Algebra" --lectures 4 --generate-site
```

The generated site lands under `sites/<course-slug>/` and the course is registered in `sites/courses.yml`. A catalog landing page is rendered at `sites/index.html`.

Important: `educlaw site generate` only scaffolds and registers the site. It does not install Ruby gems or start Jekyll for you.

## How it works

```
autocourse series dir                    generated site
─────────────────────                    ──────────────
course-plan.json  ─────┐
lecture-01-*.md   ─────┤  educlaw site   sites/<slug>/
lecture-02-*.md   ─────┤  generate       ├── _config.yml     (from template)
...               ─────┘  ───────────>   ├── index.md        (from template)
                                         ├── _lectures/
                                         │   ├── 01_*.md     (converted)
                                         │   └── 02_*.md
                                         ├── _data/
                                         ├── _layouts/
                                         └── ...
```

1. **Read plan** — Parses `course-plan.json` for `title`, `audience`, and `lecture_count`.
2. **Copier scaffold** — Renders `templates/course_site/` with course-specific values into `sites/<slug>/`.
3. **Lecture conversion** — Transforms IR lecture markdown (frontmatter: `id`, `title`, `objective`, etc.) into Jekyll lecture format (`type: lecture`, `date`, `title`, `tldr`).
4. **Registry** — Adds the course to `sites/courses.yml`.
5. **Catalog** — Re-renders `sites/index.html` from the registry.

## CLI commands

| Command | Purpose |
|---------|---------|
| `educlaw site generate <series-dir>` | Generate a Jekyll site from autocourse output |
| `educlaw site generate <series-dir> -o /path/to/sites` | Specify output parent directory |
| `educlaw site catalog` | Re-render the catalog page from the registry |
| `educlaw site list` | List all registered courses |

The generated course directory includes a `Gemfile`, so the normal local preview flow is to run Bundler inside `sites/<slug>/` and then start Jekyll with that bundle.

## Template variables

The Copier template at `templates/course_site/` uses custom Jinja2 delimiters (`[[ ]]` and `[% %]`) to avoid conflicts with Jekyll's Liquid syntax.

| Variable | Type | Default | Maps to |
|----------|------|---------|---------|
| `course_name` | str | *(required)* | `_config.yml` `course_name` |
| `course_slug` | str | *(derived from title)* | `_config.yml` `baseurl` |
| `course_description` | str | `""` | `_config.yml` `course_description` |
| `course_semester` | str | `"Spring 2026"` | `_config.yml` `course_semester` |
| `audience` | str | `"General learners"` | `index.md` body |
| `schoolname` | str | `""` | `_config.yml` `schoolname` |
| `schoolurl` | str | `""` | `_config.yml` `schoolurl` |
| `instructor_name` | str | `"Instructor"` | `_data/people.yml` |
| `theme_color` | str | `"#A51C30"` | Brand/header accent (Harvard Crimson; see `_sass/_user_vars.scss` for full theme) |

When called programmatically (via `generate_site()`), answers are derived from `course-plan.json` automatically.

## Lecture conversion

IR lectures use this frontmatter:

```yaml
id: lecture-1-foundations-of-vector-spaces.1
title: "Lecture 1: Foundations of Vector Spaces"
objective: "Understand vectors and vector spaces"
prerequisites: []
difficulty: 3
modality: [text, quiz]
tags: [generated, autolecture]
```

The converter produces Jekyll-compatible frontmatter:

```yaml
type: lecture
date: "2026-04-23"
title: "Lecture 1: Foundations of Vector Spaces"
tldr: "Understand vectors and vector spaces"
thumbnail: /static_files/presentations/lec.jpg
```

Dates are derived from the series directory name (e.g. `2026-04-23-intro-*`) with weekly spacing between lectures.

## Local preview

From the generated site directory:

```bash
cd sites/introduction-to-linear-algebra
bundle config set --local path vendor/bundle
bundle install
bundle exec jekyll serve
```

This assumes a writable, non-root Ruby environment. If `bundle install` tries to write to a system gem cache or replaces the locked Bundler version, use a project-local Ruby/Bundler setup instead of `sudo`. The error you pasted is consistent with Bundler trying to install into `/var/lib/gems/...` and then failing when it cannot write there, which prevents `jekyll` from being installed into the bundle.

You also need Ruby development headers for native gems such as `commonmarker` and `nokogiri` (`ruby-dev` on Debian/Ubuntu, `ruby-devel` on Fedora/RHEL).

If an older generated site still has a committed `Gemfile.lock`, delete it and rerun `bundle install` so Bundler can resolve a bundle that matches your Ruby version.

If the site was generated on another machine or the lockfile is stale, delete the generated site directory and rerun `educlaw site generate <series-dir>` to recreate a fresh Jekyll bundle.

With the generated `baseurl`, the site is usually available at `http://localhost:4000/<course-slug>/`.

## Course registry

The registry at `sites/courses.yml` tracks all generated courses:

```yaml
courses:
  - slug: introduction-to-linear-algebra
    title: "Introduction to Linear Algebra: Vectors, Eigenvalues, and Concepts"
    audience: "University-level learners"
    semester: Spring 2026
    lecture_count: 8
    site_dir: /absolute/path/to/sites/introduction-to-linear-algebra
    series_dir: /absolute/path/to/content/ir/series/2026-04-23-intro-linear-algebra-8
    created: "2026-04-23"
```

Use `educlaw site list` to see registered courses, or edit `courses.yml` directly and re-run `educlaw site catalog` to update the landing page.

## Customizing the template

The template lives at `templates/course_site/`. Files without a `.jinja` suffix are copied verbatim. To customize:

- **Styles** — Edit `_sass/_user_vars.scss` or `_css/main.scss`.
- **Layouts** — Modify `_layouts/*.html` (these use Liquid, not Copier Jinja2).
- **Navigation** — Edit `_data/nav.yml`.
- **New pages** — Add `.md` files with Jekyll frontmatter.
- **New template variables** — Add entries to `copier.yml` and reference them with `[[ var_name ]]` in `.jinja` files.

## Deploying to GitHub Pages

Push the generated site directory to a GitHub repository and enable Pages in the repo settings. Alternatively, use a GitHub Action to build from the Jekyll source.

## Pipeline integration

The full pipeline script supports site generation with `--generate-site`:

```bash
python scripts/run_full_course_pipeline.py "Your Topic" \
  --lectures 4 \
  --generate-site \
  --site-output-dir sites/
```

## See also

- [AUTOCOURSE.md](AUTOCOURSE.md) — Multi-lecture course generation
- [DEVELOPERS.md](DEVELOPERS.md) — Developer setup and CLI reference
