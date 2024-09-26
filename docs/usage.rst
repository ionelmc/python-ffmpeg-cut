=====
Usage
=====

Bunch of examples.

No cutting, just a filter
-------------------------

You just want to add a blur to a clip::

    ffmpeg-cut "recording 1.mp4" recording-blured.mp4 -f 50:760:455:280:boxblur=5:4

That will actually chain 2 filters:

* A `crop filter <https://ffmpeg.org//ffmpeg-filters.html#boxblur>`_ with options ``50:760:455:280``. There will always be a crop filter injected, so if you want the whole area you'll have to specify it, eg: ``1920:1080:0:0``.
* Your filter (`boxblur <https://ffmpeg.org//ffmpeg-filters.html#boxblur>`_) with radius 5 and power 4.

Few cuts without files
----------------------

::

    ffmpeg-cut "recording 1.mp4" recording-cut.mp4 00:00.000-01:23.456 02:34.567-02:56.789


Simple text files
-----------------

If you have a lot of cuts with more than 1 input files create a file named ``my-compilation.txt`` that contains::

    recording 1.mp4
    00:00.000-01:23.456
    02:34.567-02:56.789
    recording 2.mp4
    00:00.000-01:23.456
    02:34.567-02:56.789

Then run::

    ffmpeg-cut --text my-compilation.txt my-compilation.mp4

Files without common fps
-------------------------

A common issue with nvidia overlay 60fps recordings is that input files do not have identical fps (eg: recording 1.mp4 has 59.55, recording 2.mp4 has 59.66 - ). Add this to your command line::

    --fps=60

Uploading clips to chat software
--------------------------------

If you're not uploading to youtube you might want to use very high compression to fit upload limits. Add something like this::

    --encoder=libx265 --quality=32

Cropping and overlaying
-----------------------

Should you want to create vertical videos from desktop captures you can overlay two sections from the input recording::

    TODO: remove hardcoded overlays
