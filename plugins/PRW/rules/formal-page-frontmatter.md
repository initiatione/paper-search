# Formal Page Frontmatter

Required frontmatter fields: `title`, `category`, `page_family`, `tags`, `aliases`, `sources`, `summary`, `provenance`, `base_confidence`, `lifecycle`, `lifecycle_changed`, `tier`, `created`, and `updated`.

`sources` must contain only Obsidian wikilinks to original paper PDFs, each displayed as the paper slug: `"[[_epi/raw/papers/<slug>/paper.pdf|<slug>]]"`. Plain path text, Markdown links, aliases such as `原论文 PDF`, and metadata/MinerU/DOI/arXiv entries do not satisfy the contract because the Obsidian properties view must show the source slug and still click through to the PDF.

Initial lifecycle is `draft` or `review-needed`. Do not mark pages `verified` until source reread, formula review, figure/table review, lint, and human review have passed.
