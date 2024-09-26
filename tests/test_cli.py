import subprocess


def test_main():
    assert subprocess.check_output(['ffmpeg-cut', 'foo', 'foobar'], text=True) == 'foobar\n'
