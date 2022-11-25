---
title: A Test Document
panhan:
- 
  use_preset: default
  output_file: test.html
  metadata:
    author: Dominic Thorn <dominic.thorn@gmail.com>
  pandoc_args:
    toc: false
-
  use_preset: journal
  metadata:
    author: Dominic Thorn <dthorn@student.london.ac.uk>
-
  output_format: pdf
  output_file: report.pdf
  pandoc_args:
    pdf_engine: weasyprint
---

# Heading One

Lorem ipsum.

Panhan expects a list of mappings - is there a better way to do this?

Use sequence of mappings example from [reference page](https://yaml.org/spec/1.2.2/#chapter-1-introduction-to-yaml).

## Possible keys

```plaintext
use_preset: str | None = None
output_format: str | None = None
output_file: Path | None = None
metadata: dict[str, Any] = dc.field(default_factory=dict)
pandoc_args: dict[str, Any] = dc.field(default_factory=dict)
filters: dict[str, bool] = dc.field(default_factory=dict)
```
