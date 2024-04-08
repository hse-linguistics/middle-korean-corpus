from typing import Optional, List, Tuple

from sqlmodel import Field, SQLModel, Relationship, create_engine, UniqueConstraint, Session, select


class Text(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    title: str = Field(unique=True)

    sents: List["Sentence"] = Relationship()


class Sentence(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("sent_address", "text_id", name="unique_sentence"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    text_id: int = Field(foreign_key="text.id")
    sent_address: str = Field(nullable=False)

    sent: str = Field(nullable=False)
    translation: Optional[str] = Field(default=None, nullable=True)


class POS(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)


class Gloss(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)


class Allomorph(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("gloss_id", "translit", name="unique_allomorph"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    translit: str = Field(nullable=False)
    gloss_id: int = Field(foreign_key="gloss.id")


class Grammar(SQLModel, table=True):
    token_id: int = Field(foreign_key="token.id", primary_key=True)
    allomorph_id: int = Field(foreign_key="allomorph.id", primary_key=True)

    pos_in_suffix: int = Field(nullable=False)

    token: "Token" = Relationship(back_populates="grammar")


class Stem(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    translit: str = Field(nullable=False)
    translit_syl: str = Field(unique=True, nullable=False)  # transliteration with syllables


class Token(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("sent_id", "pos_in_sent", name="unique_token"),
    )

    id: int = Field(default=None, primary_key=True)
    sent_id: int = Field(foreign_key="sentence.id")
    pos_in_sent: int = Field(nullable=False)

    hangul: str = Field(nullable=False)

    pos_id: Optional[int] = Field(default=None, foreign_key="pos.id", nullable=True)
    stem_id: Optional[int] = Field(default=None, foreign_key="stem.id", nullable=True)

    translations: Optional[List["Translation"]] = Relationship(back_populates="token")
    grammar: Optional[List[Grammar]] = Relationship(back_populates="token")


class Translation(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    token_id: int = Field(foreign_key="token.id")

    lang: str
    transl: str = Field(nullable=False)

    token: Token = Relationship(back_populates="translations")


if __name__ == '__main__':
    sqlite_file_name = "../../data/database2.db"
    sqlite_url = f"sqlite:///{sqlite_file_name}"

    engine = create_engine(sqlite_url, echo=True)
    SQLModel.metadata.create_all(engine)
