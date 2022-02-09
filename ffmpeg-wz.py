#!python3
import argparse
import re
import shlex
import subprocess
from itertools import pairwise
from pathlib import Path
from textwrap import dedent


def parse_crop(value):
    if ':' not in value:
        raise argparse.ArgumentTypeError('must ratio in the form: "W:H"')
    try:
        w, h = value.split(':')
    except ValueError:
        raise argparse.ArgumentTypeError('must ratio in the form: "W:H"')
    try:
        w = int(w)
        h = int(h)
    except ValueError:
        raise argparse.ArgumentTypeError('must have integer values')

    if 1080.0 * w / h > 1920:
        raise argparse.ArgumentTypeError('cannot exceed 16:9 ratio')

    return w, h


timestamp_re = re.compile('\d\d:\d\d:\d\d.\d\d\d')


def parse_timestamp(value):
    if not timestamp_re.fullmatch(value):
        raise argparse.ArgumentTypeError('must be value of the form: HH:MM:SS.mmm')
    return value


parser = argparse.ArgumentParser(description='ffmpeg wrapper')
parser.add_argument('input', help='input file', type=argparse.FileType('r'))
parser.add_argument('output', help='output file')
parser.add_argument('timestamp', help='pairs of timestamps to cut', type=parse_timestamp, nargs='*')
parser.add_argument('-c', '--crop', help='crop input to a given ratio', type=parse_crop)
parser.add_argument('-q', '--quality', help='libx265 crf', type=int, default=15)
parser.add_argument('-d', '--dry-run', action='store_true')
parser.add_argument('-r', '--dirty', action='store_true')


def check_call(*args, dry_run):
    pretty = ' '.join(shlex.quote(i) for i in args)
    width = len(pretty) + 8
    if dry_run:
        print(f'    {pretty}')
    else:
        print('=' * width)
        print(f'    {pretty}')
        print('=' * width)
        subprocess.check_call(args)


if __name__ == '__main__':
    args = parser.parse_args()
    if len(args.timestamp) % 2:
        parser.error('must have an even number of timestamps')

    print(f'parsed:\n    {args}')
    if args.dry_run:
        print('would run:')

    if args.crop:
        width_ratio, height_ratio = args.crop
        height = 1080
        width = 1080.0 * width_ratio / height_ratio
        side_crop = int((1920 - width) / 2.0)
        filters = [
            '-filter_complex',
            (f'[0:v]scale=-1:{height}:flags=lanczos[tmp1];'
             f'[tmp1]split[a][tmp2];'
             f'[tmp2]split[b][c];'
             f'[a]crop={height}:{height}:{side_crop}:0[base];'
             f'[b]crop=225:34:1625:42[kills];'
             f'[c]crop=270:270:36:24[map];'
             f'[base][map]overlay=0:0[out];'
             f'[out][kills]overlay=main_w-overlay_w:0')
        ]
    else:
        filters = []
    output = Path(args.output)
    match args.timestamp:
        case None:
            if filters:
                check_call(
                    'ffmpeg', '-i', args.input.name, *filters, '-c:v', 'libx265', '-crf', str(args.quality), args.output,
                    dry_run=args.dry_run
                )
            else:
                parser.error('no crop and no timestamps')
        case [start, end]:
            check_call(
                'ffmpeg', '-ss', start, '-to', end, '-i', args.input.name, *filters, '-c:v', 'libx265', '-crf', str(args.quality), args.output,
                dry_run=args.dry_run
            )
        case [*many]:
            many = iter(many)
            clips = []
            for pos, pair in enumerate(zip(many, many)):
                clips.append(clip := output.with_stem(f'{output.stem}-{pos:03}').with_suffix(output.suffix))
                start, end = pair
                if args.dry_run:
                    check_call(
                        'ffmpeg', '-ss', start, '-to', end, '-i', args.input.name, *filters, '-c:v', 'libx265', '-crf', str(args.quality), str(clip),
                        dry_run=True
                    )
                else:
                    if clip.exists():
                        if clip.stat().st_size:
                            continue
                        else:
                            clip.unlink()
                    check_call(
                        'ffmpeg', '-n', '-ss', start, '-to', end, '-i', args.input.name, *filters, '-c:v', 'libx265', '-crf', str(args.quality), str(clip),
                        dry_run=args.dry_run
                    )
            output_concat = output.with_suffix('.clips')
            if not args.dry_run:
                output_concat.write_text('\n'.join(f'file {str(clip)!r}' for clip in clips))
            check_call(
                'ffmpeg', '-f', 'concat', '-i', str(output_concat), '-c', 'copy', str(args.output),
                dry_run=args.dry_run
            )

            if args.dry_run:
                print(f'would write to {output_concat}:\n    ', end='')
                print('\n    '.join(f'file {str(clip)!r}' for clip in clips))
            elif not args.dirty:
                for clip in clips:
                    clip.unlink()

