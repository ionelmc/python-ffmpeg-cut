
Changelog
=========
1.0.2 (2025-01-13)
------------------

* Switch to Matroska clips for the intermediate files to avoid "Non-monotonic DTS" warnings.
* Added some timestamp fixup (avoid_negative_ts) in the cut phase to avoid some warnings (and maybe wrong output).

1.0.1 (2025-01-13)
------------------

* Added `--version` option.
* Fixed broken `run` function.

1.0.0 (2024-09-26)
------------------

* First release on PyPI.
