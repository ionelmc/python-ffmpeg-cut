#!python3
"""
Example usage:

To create a clip with cuts from 00:28:30.550 to 00:28:35.718 and 00:28:57.711 to 00:29:03.068:
    ffmpeg-wz v:\2022-02-07_22-12-09.mkv clip.mp4 00:28:30.550 00:28:35.718 00:28:57.711 00:29:03.068
To create the same clip but with a warzone-style crop (minimap and stats moved inside the crop) to 1080x1080:
    ffmpeg-wz v:\2022-02-07_22-12-09.mkv -c 1:1 crop.mp4 00:28:30.550 00:28:35.718 00:28:57.711 00:29:03.068

"""
import argparse
import pathlib
import re
import shlex
import subprocess
import textwrap
from dataclasses import dataclass, field


def parse_crop(value):
    if ':' not in value:
        raise argparse.ArgumentTypeError('must ratio in the form: "W:H"')
    try:
        width_ratio, height_ratio = value.split(':')
    except ValueError:
        raise argparse.ArgumentTypeError('must ratio in the form: "W:H"')
    try:
        width_ratio = int(width_ratio)
        height_ratio = int(height_ratio)
    except ValueError:
        raise argparse.ArgumentTypeError('must have integer values')

    if 1080.0 * width_ratio / height_ratio > 1920:
        raise argparse.ArgumentTypeError('cannot exceed 16:9 ratio')

    height = 1080
    width = 1080.0 * width_ratio / height_ratio
    side_crop = int((1920 - width) / 2.0)
    return [
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


timestamp_re = re.compile(r'(?P<start>(\d\d:)?\d\d:\d\d.\d\d\d)-(?P<end>(\d\d:)?\d\d:\d\d.\d\d\d)')
file_instruction_re = re.compile("file '(.+)'")
clip_comment_re = re.compile(r'# (?P<path>.+?) (?P<start>(\d\d:)?\d\d:\d\d.\d\d\d)-(?P<end>(\d\d:)?\d\d:\d\d.\d\d\d)')


@dataclass
class Cut:
    start: str
    end: str


def parse_cut(value):
    if match := timestamp_re.fullmatch(value):
        groups = match.groupdict()
        return Cut(groups['start'], groups['end'])
    else:
        raise argparse.ArgumentTypeError('must be value of the form: HH:MM:SS.mmm-HH:MM:SS.mmm')


@dataclass
class Instruction:
    input: pathlib.Path
    cut: list[Cut]
    args: object

    def __getattr__(self, item):
        return getattr(self.args, item)

    def __str__(self):
        cuts = ' '.join(f'{cut.start}-{cut.end}' for cut in self.cut)
        return f'{self.input} {cuts}'


@dataclass
class Clip:
    input: pathlib.Path
    cut: Cut
    output: pathlib.Path


@dataclass
class ClipList:
    clips: list[Clip] = field(default_factory=list)

    @property
    def outputs(self):
        return [clip.output for clip in self.clips]

    def append(self, input, cut, output):
        self.clips.append(Clip(input=input, cut=cut, output=output))

    def as_concat_input(self):
        return '\n'.join(
            f'# {clip.input} {clip.cut.start}-{clip.cut.end}\n'
            f'file {str(clip.output)!r}\n'
            for clip in self.clips
        )

    def __len__(self):
        return len(self.clips)


def clips_cut(args):
    instructions = []

    for line in args.input.read_text().splitlines():
        line = line.strip()
        if match := clip_comment_re.fullmatch(line):
            groups = match.groupdict()
            instructions.append(current_instruction := Instruction(
                input=pathlib.Path(groups['path']),
                cut=[Cut(groups['start'], groups['end'])],
                args=args,
            ))
            if not current_instruction.input.exists() and not args.dry_run:
                parser.error(f'{line!r} does not exist')

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
        if match := timestamp_re.fullmatch(line):
            if current_instruction is None:
                parser.error(f'did not find a path before {line!r}')
            else:
                groups = match.groupdict()
                current_instruction.cut.append(Cut(groups['start'], groups['end']))
        else:
            instructions.append(current_instruction := Instruction(
                input=pathlib.Path(line),
                cut=[],
                args=args,
            ))
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

    for pos, cut in enumerate(cuts):
        clips.append(args.input, cut,
                     clip := output.with_stem(f'{output.stem}-{len(clips):03}').with_suffix(output.suffix))
        if args.dry_run:
            check_call(
                'ffmpeg', '-ss', cut.start, '-to', cut.end, '-i', args.input, *args.filters, '-c:v', args.encoder, '-crf',
                str(args.quality), clip,
                dry_run=True
            )
        else:
            if clip.exists():
                if clip.stat().st_size:
                    continue
                else:
                    clip.unlink()
            check_call(
                'ffmpeg', '-n', '-ss', cut.start, '-to', cut.end, '-i', args.input, *args.filters, '-c:v', args.encoder, '-crf',
                str(args.quality), clip,
                dry_run=args.dry_run
            )


def join_clips(clips: ClipList, args, dirty=False):
    clips_file = args.output.with_suffix('.clips')

    if args.dry_run:
        print(f'would write to {clips_file}:')
        print(textwrap.indent(clips.as_concat_input(), f'    '))
        print('would run:')
    else:
        clips_file.write_text(clips.as_concat_input())

    if not args.no_join:
        check_call(
            'ffmpeg', '-f', 'concat', '-i', clips_file, '-c', 'copy', args.output,
            dry_run=args.dry_run
        )
        if not args.dry_run and not args.dirty and not dirty:
            for clip in clips.outputs:
                clip.unlink()


parser = argparse.ArgumentParser(
    description='ffmpeg wrapper',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog='''
If you use --text then the input file must contain instructions in the form:

    path/to/video.mkv
    HH:MM:SS.mmm-HH:MM:SS.mmm
    HH:MM:SS.mmm-HH:MM:SS.mmm
    
    path/to/another/video.mp4
    HH:MM:SS.mmm-HH:MM:SS.mmm
    HH:MM:SS.mmm-HH:MM:SS.mmm
    HH:MM:SS.mmm-HH:MM:SS.mmm
''')
parser_join_group = parser.add_mutually_exclusive_group()
parser_crop_group = parser_join_group.add_mutually_exclusive_group()
parser_crop_group.add_argument('-j', '--join', help='input file is ffmpeg concat instruction file', action='store_true')
parser_crop_group.add_argument('-c', '--crop', help='crop input to a given ratio', type=parse_crop, action='extend',
                               dest='filters', metavar='W:H', default=[])
parser_join_group.add_argument('-n', '--no-join',
                               help='only produce the intermediary clips and ffmpeg concat instruction file',
                               action='store_true')
parser.add_argument('-q', '--quality', help='libx265 crf', type=int, default=15, metavar='CRF')
parser.add_argument('-d', '--dry-run', action='store_true')
parser.add_argument('-r', '--dirty', action='store_true')
parser.add_argument('-e', '--encoder', default='libx264', help='you can use `libx265` for better compression but possibly worse player support')
parser.add_argument('input', help='input file', type=pathlib.Path)
parser.add_argument('output', help='output file', type=pathlib.Path)
parser_cut_group = parser.add_mutually_exclusive_group()
parser_cut_group.add_argument('-t', '--text', help='input file is text file with cuts', action='store_true')
parser_cut_group.add_argument('-l', '--clips', help='input file is clips file with cuts', action='store_true')
parser_cut_group.add_argument('cut', help='pair of timestamps to cut', type=parse_cut, nargs='?', action='append')
parser.add_argument('cut', help='pair of timestamps to cut', type=parse_cut, nargs='*', action='extend')


def main():
    args = parser.parse_args()
    print(f'parsed:\n    {args}')

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
                        'ffmpeg', '-i', args.input, *args.filters, '-c:v', args.encoder, '-crf', str(args.quality),
                        args.output,
                        dry_run=args.dry_run
                    )
                else:
                    parser.error('no crop and no timestamps')
            case [(start, end)]:
                if args.dry_run:
                    print('would run:')

                check_call(
                    'ffmpeg', '-ss', start, '-to', end, '-i', args.input, *args.filters, '-c:v', args.encoder, '-crf',
                    str(args.quality), args.output,
                    dry_run=args.dry_run
                )
            case _:
                clips = ClipList()
                multi_cut(clips, args)
                join_clips(clips, args)


if __name__ == '__main__':
    main()
