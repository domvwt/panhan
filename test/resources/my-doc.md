---
title: A Test Document
panhan:
- 
  use_preset: default
  output_file: test.html
  variables:
    author: Dominic Thorn <dominic.thorn@gmail.com>
  cli_args:
    toc: false
  
-
  use_preset: journal
  variables:
    author: Dominic Thorn <dthorn@student.london.ac.uk>
-
  output_format: pdf
  output_file: report.pdf
  cli_args:
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
variables: dict[str, Any] = dc.field(default_factory=dict)
cli_args: dict[str, Any] = dc.field(default_factory=dict)
filters: dict[str, bool] = dc.field(default_factory=dict)
```