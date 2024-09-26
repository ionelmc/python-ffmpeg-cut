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

.. |commits-since| image:: https://img.shields.io/github/commits-since/ionelmc/python-ffmpeg-cut/v1.0.0.svg
    :alt: Commits since latest release
    :target: https://github.com/ionelmc/python-ffmpeg-cut/compare/v1.0.0...main



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
