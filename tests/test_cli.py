import subprocess


def test_main():
    assert (
        subprocess.check_output(['ffmpeg-cut', '--help'], text=True)
        == """usage: ffmpeg-cut [-h] [[-j | -c W:H | -f W:H |] -n] [-q CRF] [-d] [-v] [-r] [-s FILTERS] [-e ENCODER] [-t] [-l] input output [cut] [cut ...]

ffmpeg wrapper

positional arguments:
  input                 input file
  output                output file
  cut                   pair of timestamps to cut
  cut                   pair of timestamps to cut

options:
  -h, --help            show this help message and exit
  -j, --join            input file is ffmpeg concat instruction file
  -c W:H, --crop W:H    crop input to a given ratio
  -f W:H, --filter W:H  arbitrary filter on specific zone
  -n, --no-join         only produce the intermediary clips and ffmpeg concat instruction file
  -q CRF, --quality CRF
                        libx265 crf
  -d, --dry-run
  -v, --version         show program's version number and exit
  -r, --dirty
  -s FILTERS, --fps FILTERS
  -e ENCODER, --encoder ENCODER
                        you can use `libx265` for better compression but possibly worse player support
  -t, --text            input file is text file with cuts
  -l, --clips           input file is clips file with cuts

If you use --text then the input file must contain instructions in the form:

    path/to/video.mkv
    HH:MM:SS.mmm-HH:MM:SS.mmm
    HH:MM:SS.mmm-HH:MM:SS.mmm

    path/to/another/video.mp4
    HH:MM:SS.mmm-HH:MM:SS.mmm
    HH:MM:SS.mmm-HH:MM:SS.mmm
    HH:MM:SS.mmm-HH:MM:SS.mmm
"""
    )
