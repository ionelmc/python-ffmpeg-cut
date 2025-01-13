"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?

  You might be tempted to import things from __main__ later, but that will cause
  problems: the code will get executed twice:

  - When you run `python -mffmpeg_cut` python will execute
    ``__main__.py`` as a script. That means there will not be any
    ``ffmpeg_cut.__main__`` in ``sys.modules``.
  - When you import __main__ it will get executed again (as a module) because
    there"s no ``ffmpeg_cut.__main__`` in ``sys.modules``.

  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""

import argparse
import pathlib
import platform
import re
import shlex
import subprocess
import textwrap

from . import __version__
from .structs import ClipList
from .structs import Cut
from .structs import Instruction

CLIP_COMMENT_RE = re.compile(r'# (?P<path>.+?) (?P<start>(\d\d:)?\d\d:\d\d.\d\d\d)-(?P<end>(\d\d:)?\d\d:\d\d.\d\d\d)')
FILE_INSTRUCTION_RE = re.compile("file '(.+)'")
TIMESTAMP_RE = re.compile(r'(?P<start>(\d\d:)?\d\d:\d\d.\d\d\d)-(?P<end>(\d\d:)?\d\d:\d\d.\d\d\d)')


def parse_crop(value):
    if ':' not in value:
        raise argparse.ArgumentTypeError('must ratio in the form: "W:H"')
    try:
        width_ratio, height_ratio = value.split(':')
    except ValueError:
        raise argparse.ArgumentTypeError('must ratio in the form: "W:H"') from None
    try:
        width_ratio = int(width_ratio)
        height_ratio = int(height_ratio)
    except ValueError:
        raise argparse.ArgumentTypeError('must have integer values') from None

    if 1080.0 * width_ratio / height_ratio > 1920:
        raise argparse.ArgumentTypeError('cannot exceed 16:9 ratio')

    height = 1080
    width = 1080.0 * width_ratio / height_ratio
    side_crop = int((1920 - width) / 2.0)
    return [
        (
            f'scale=-1:{height}:flags=lanczos[tmp1];'
            f'[tmp1]split[a][tmp2];'
            f'[tmp2]split[b][tmp3];'
            f'[tmp3]split[c][d];'
            f'[a]crop={width}:{height}:{side_crop}:0[base];'
            f'[b]crop=225:34:1625:42[kills];'
            f'[c]crop=270:270:36:24[map];'
            f'[d]crop=255:275:35:775[wc];'
            f'[base][map]overlay=0:0[out1];'
            f'[out1][wc]overlay=0:main_h-overlay_h[out2];'
            f'[out2][kills]overlay=main_w-overlay_w:0'
        )
    ]


def parse_filter(value):
    try:
        x, y, w, h, spec = value.split(':', 4)
    except ValueError:
        raise argparse.ArgumentTypeError('must be in the form: "X:Y:W:H:filter-spec"') from None
    try:
        x = int(x)
        y = int(y)
        w = int(w)
        h = int(h)
    except ValueError:
        raise argparse.ArgumentTypeError('must have integer values') from None

    return [f'crop={w}:{h}:{x}:{y},{spec}[filter1];[0:v][filter1]overlay={x}:{y}']


def parse_fps(value):
    fps = int(value)
    return [f'fps={fps}']


def parse_cut(value):
    if match := TIMESTAMP_RE.fullmatch(value):
        groups = match.groupdict()
        return Cut(groups['start'], groups['end'])
    else:
        raise argparse.ArgumentTypeError('must be value of the form: HH:MM:SS.mmm-HH:MM:SS.mmm')


parser = argparse.ArgumentParser(
    description='ffmpeg wrapper',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
If you use --text then the input file must contain instructions in the form:

    path/to/video.mkv
    HH:MM:SS.mmm-HH:MM:SS.mmm
    HH:MM:SS.mmm-HH:MM:SS.mmm

    path/to/another/video.mp4
    HH:MM:SS.mmm-HH:MM:SS.mmm
    HH:MM:SS.mmm-HH:MM:SS.mmm
    HH:MM:SS.mmm-HH:MM:SS.mmm
""",
)
parser_join_group = parser.add_mutually_exclusive_group()
parser_crop_group = parser_join_group.add_mutually_exclusive_group()
parser_cut_group = parser.add_mutually_exclusive_group()
parser_crop_group.add_argument('-j', '--join', help='input file is ffmpeg concat instruction file', action='store_true')
parser_crop_group.add_argument(
    '-c', '--crop', help='crop input to a given ratio', type=parse_crop, action='extend', dest='filters', metavar='W:H', default=[]
)
parser_crop_group.add_argument(
    '-f',
    '--filter',
    help='arbitrary filter on specific zone',
    type=parse_filter,
    action='extend',
    dest='filters',
    metavar='W:H',
    default=[],
)
parser_join_group.add_argument(
    '-n', '--no-join', help='only produce the intermediary clips and ffmpeg concat instruction file', action='store_true'
)
parser.add_argument('-q', '--quality', help='libx265 crf', type=int, default=15, metavar='CRF')
parser.add_argument('-d', '--dry-run', action='store_true')
parser.add_argument(
    '-v',
    '--version',
    action='version',
    version=f'ffmpeg-cut {__version__} ({platform.python_implementation()} {platform.python_version()})',
)
parser.add_argument('-r', '--dirty', action='store_true')
parser.add_argument('-s', '--fps', dest='filters', action='extend', type=parse_fps, default=[])
parser.add_argument(
    '-e', '--encoder', default='libx264', help='you can use `libx265` for better compression but possibly worse player support'
)
parser.add_argument('input', help='input file', type=pathlib.Path)
parser.add_argument('output', help='output file', type=pathlib.Path)
parser_cut_group.add_argument('-t', '--text', help='input file is text file with cuts', action='store_true')
parser_cut_group.add_argument('-l', '--clips', help='input file is clips file with cuts', action='store_true')
parser_cut_group.add_argument('cut', help='pair of timestamps to cut', type=parse_cut, nargs='?', action='append')
parser.add_argument('cut', help='pair of timestamps to cut', type=parse_cut, nargs='*', action='extend')


def clips_cut(args):
    instructions = []

    for line in args.input.read_text().splitlines():
        line = line.strip()
        if match := CLIP_COMMENT_RE.fullmatch(line):
            groups = match.groupdict()
            instructions.append(
                current_instruction := Instruction(
                    input=pathlib.Path(groups['path']),
                    cut=[Cut(groups['start'], groups['end'])],
                    args=args,
                )
            )
            if not current_instruction.input.exists() and not args.dry_run:
                raise parser.error(f'{line!r} does not exist')

    print('parsed input:')
    for instruction in instructions:
        print(f'    {instruction}')

    clips = ClipList()
    for instruction in instructions:
        multi_cut(clips, instruction)

    join_clips(clips, args)


def text_cut(args):
    instructions = []
    current_instruction = None

    for line in args.input.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        if match := TIMESTAMP_RE.fullmatch(line):
            if current_instruction is None:
                parser.error(f'did not find a path before {line!r}')
            else:
                groups = match.groupdict()
                current_instruction.cut.append(Cut(groups['start'], groups['end']))
        else:
            instructions.append(
                current_instruction := Instruction(
                    input=pathlib.Path(line),
                    cut=[],
                    args=args,
                )
            )
            if not current_instruction.input.exists() and not args.dry_run:
                parser.error(f'{line!r} does not exist')

    print('parsed input:')
    for instruction in instructions:
        print(f'    {instruction}')

    if args.dry_run:
        print('would run:')

    clips = ClipList()
    for instruction in instructions:
        multi_cut(clips, instruction)

    join_clips(clips, args)


def check_call(*args, dry_run):
    pretty = ' '.join(shlex.quote(str(i)) for i in args)
    width = len(pretty) + 8
    if dry_run:
        print(f'    {pretty}')
    else:
        print('=' * width)
        print(f'    {pretty}')
        print('=' * width)
        subprocess.check_call(args)


def multi_cut(clips: ClipList, args):
    cuts = args.cut
    output = args.output

    for cut in cuts:
        clips.append(args.input, cut, clip := output.with_stem(f'{output.stem}-{len(clips):03}').with_suffix(output.suffix))
        if args.dry_run:
            check_call(
                'ffmpeg',
                '-ss',
                cut.start,
                '-to',
                cut.end,
                '-i',
                args.input,
                *join_filters(args.filters),
                '-c:v',
                args.encoder,
                '-crf',
                str(args.quality),
                clip,
                dry_run=True,
            )
        else:
            if clip.exists():
                if clip.stat().st_size:
                    continue
                else:
                    clip.unlink()
            check_call(
                'ffmpeg',
                '-n',
                '-ss',
                cut.start,
                '-to',
                cut.end,
                '-i',
                args.input,
                *join_filters(args.filters),
                '-c:v',
                args.encoder,
                '-crf',
                str(args.quality),
                clip,
                dry_run=args.dry_run,
            )


def join_clips(clips: ClipList, args, dirty=False):
    clips_file = args.output.with_suffix('.clips')

    if args.dry_run:
        print(f'would write to {clips_file}:')
        print(textwrap.indent(clips.as_concat_input(), '    '))
        print('would run:')
    else:
        clips_file.write_text(clips.as_concat_input())

    if not args.no_join:
        check_call('ffmpeg', '-f', 'concat', '-i', clips_file, '-c', 'copy', args.output, dry_run=args.dry_run)
        if not args.dry_run and not args.dirty and not dirty:
            for clip in clips.outputs:
                clip.unlink()


def join_filters(filters):
    if filters:
        filter_chain = []
        last_step = len(filters) - 1
        for step, filter in enumerate(filters):
            if step == last_step:
                output = ''
            else:
                output = f'[step_{step}]'
            if step:
                filter_chain.append(f'[step_{step - 1}]{filter}{output}')
            else:
                filter_chain.append(f'[0:v]{filter}{output}')

        return ['-filter_complex', ';'.join(filter_chain)]
    else:
        return []


def process(args):
    if args.join:
        clips = ClipList()
        with args.input.open('r') as fh:
            while True:
                line = fh.readline()
                if not line:
                    break
                line = line.strip()
                if line.startswith('#'):
                    original_file, cut = line[1:].strip().split()
                    cut = parse_cut(cut)
                elif line:
                    match shlex.split(line):
                        case ['file', clip_path]:
                            clip_file = pathlib.Path(clip_path)
                            if clip_file.exists():
                                clips.append(original_file, cut, clip_file)
                            else:
                                print(f'WARNING: {clip_file!r} does not exist!')
                        case junk:
                            print(f'WARNING: found junk in clips file: {junk!r}')

        join_clips(clips, args, dirty=True)
    else:
        if args.no_join:
            args.dirty = True

        match args.cut:
            case [None] | []:
                if args.text:
                    text_cut(args)
                elif args.clips:
                    clips_cut(args)
                elif args.filters:
                    if args.dry_run:
                        print('would run:')

                    check_call(
                        'ffmpeg',
                        '-i',
                        args.input,
                        *join_filters(args.filters),
                        '-c:v',
                        args.encoder,
                        '-crf',
                        str(args.quality),
                        args.output,
                        dry_run=args.dry_run,
                    )
                else:
                    parser.error('no crop and no timestamps')
            case [(start, end)]:
                if args.dry_run:
                    print('would run:')

                check_call(
                    'ffmpeg',
                    '-ss',
                    start,
                    '-to',
                    end,
                    '-i',
                    args.input,
                    *join_filters(args.filters),
                    '-c:v',
                    args.encoder,
                    '-crf',
                    str(args.quality),
                    args.output,
                    dry_run=args.dry_run,
                )
            case _:
                clips = ClipList()
                multi_cut(clips, args)
                join_clips(clips, args)


def run(args=None):
    args = parser.parse_args(args=args)
    process(args)
    parser.exit(0)
