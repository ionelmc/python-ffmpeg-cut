import pathlib
from dataclasses import dataclass
from dataclasses import field


@dataclass
class Cut:
    start: str
    end: str


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
        return '\n'.join(f'# {clip.input} {clip.cut.start}-{clip.cut.end}\nfile {str(clip.output)!r}\n' for clip in self.clips)

    def __len__(self):
        return len(self.clips)
