from dataclasses import dataclass, field
from typing import Iterable, List, Optional


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


@dataclass
class HTMLToken:
    hangul: str  # 善友ㅣ러시니
    translit: str  # Sen-Wu-i=le=si=ni
    glosses: str  # N+COP=RETR=HONSub=IND
    color: str = "black"
    translations: Optional[str] = None  # Good Friend, хороший друг


@dataclass
class HTMLSentence:
    sent_id: int
    tokens: List[HTMLToken] = field(default_factory=list)
    left: Optional[str] = ''
    right: Optional[str] = ''
