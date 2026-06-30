# AKOS Documentation 

Live Site: **https://the-ak-foundation.github.io/akos-docs**

## About 

This repository contains the source for the AKOS documentation site. The docs
are written in Markdown, rendered with Doxygen, and published automatically to GitHub Pages via GitHub Actions.

## Repository Layout

```sh
.
├── resources/  # Documentation pages, images, and site styling
├── akos/       # The AKOS source tree referenced by the documentation
├── scripts/    # Helper scripts used by the docs generation pipeline
└── Doxyfile    # The main Doxygen configuration for the site
```

## Content Scope

The documentation covers:

- architecture and system overview
- kernel internals
- porting notes
- examples
- guides and reference material

## Source Reference

The `akos/` directory contains the AKOS source tree that this documentation is built from and refers to.

## Local Build

If you want to preview documentation changes locally before contributing:

```bash
./build_docs.sh
```

This generates the HTML site under `out/html/`. If you also want the PDF
output, run:

```bash
./build_docs.sh --pdf
```

## License

Documentation in this repository is licensed under the Apache License 2.0. See
[`LICENSE`](akos/LICENSE) for the full text.
