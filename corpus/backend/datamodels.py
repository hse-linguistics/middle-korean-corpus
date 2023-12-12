from dataclasses import dataclass, field
from typing import Iterable, List


@dataclass
class Stem:
    translit: str
    en: str
    ru: str


@dataclass
class Morph:
    translit: str
    gloss: str


@dataclass
class Token:
    sent_address: str
    pos_in_sent: int
    hangul: str
    stem: Stem
    pos: str
    grammar: Iterable[Morph]


@dataclass
class Sentence:
    address: str
    sentence: str
    tokens: List[Token] = field(default_factory=list)
