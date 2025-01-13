========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - |github-actions|
    * - package
      - |version| |wheel| |supported-versions| |supported-implementations| |commits-since|
.. |docs| image:: https://readthedocs.org/projects/python-ffmpeg-cut/badge/?style=flat
    :target: https://readthedocs.org/projects/python-ffmpeg-cut/
    :alt: Documentation Status

.. |github-actions| image:: https://github.com/ionelmc/python-ffmpeg-cut/actions/workflows/github-actions.yml/badge.svg
    :alt: GitHub Actions Build Status
    :target: https://github.com/ionelmc/python-ffmpeg-cut/actions

.. |version| image:: https://img.shields.io/pypi/v/ffmpeg-cut.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/ffmpeg-cut

.. |wheel| image:: https://img.shields.io/pypi/wheel/ffmpeg-cut.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/ffmpeg-cut

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/ffmpeg-cut.svg
    :alt: Supported versions
    :target: https://pypi.org/project/ffmpeg-cut

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/ffmpeg-cut.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/ffmpeg-cut

.. |commits-since| image:: https://img.shields.io/github/commits-since/ionelmc/python-ffmpeg-cut/v1.0.2.svg
    :alt: Commits since latest release
    :target: https://github.com/ionelmc/python-ffmpeg-cut/compare/v1.0.2...main



.. end-badges

Cut and join CLI wrapper for ffmpeg.

* Free software: BSD 2-Clause License

Installation
============

::

    pip install ffmpeg-cut

You can also install the in-development version with::

    pip install https://github.com/ionelmc/python-ffmpeg-cut/archive/main.zip


Documentation
=============

https://python-ffmpeg-cut.readthedocs.io/

Usage: ``ffmpeg-cut [-h] [[-j | -c W:H | -f W:H |] -n] [-q CRF] [-d] [-r] [-s FPS] [-e ENCODER] [-t] [-l] input output [cut] [cut ...]``

positional arguments:
  input
    input file
  output
    output file
  cut
    pair of timestamps to cut

options:
  -h, --help                     show this help message and exit
  -j, --join                     input file is ffmpeg concat instruction file
  -c SIZE, --crop SIZE             crop input to a given ratio
  -f SIZE, --filter SIZE           arbitrary filter on specific zone
  -n, --no-join                  only produce the intermediary clips and ffmpeg concat instruction file
  -q CRF, --quality CRF          libx265 crf
  -d, --dry-run                  only display what would be run
  -r, --dirty                    do not delete intermediary files
  -s FPS, --fps FPS              output framerate
  -e ENCODER, --encoder ENCODER  you can use `libx265` for better compression but possibly worse player support
  -t, --text                     input file is text file with cuts
  -l, --clips                    input file is clips file with cuts

If you use --text then the input file must contain instructions in the form::

    path/to/video.mkv
    HH:MM:SS.mmm-HH:MM:SS.mmm
    HH:MM:SS.mmm-HH:MM:SS.mmm

    path/to/another/video.mp4
    HH:MM:SS.mmm-HH:MM:SS.mmm
    HH:MM:SS.mmm-HH:MM:SS.mmm
    HH:MM:SS.mmm-HH:MM:SS.mmm


Development
===========

To run all the tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
