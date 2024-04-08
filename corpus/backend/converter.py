import os
from typing import Union, Type, TextIO, List

import pandas as pd

from sqlmodel import Session, select, create_engine
from hypua2jamo import translate

from models import Text, Sentence, Token, POS, Stem, Gloss, Allomorph, Grammar, Translation


class CSV2Database:
    def __init__(self,
                 db: Session,
                 sent_id_col: str = 'ADDRESS',
                 token_hangul_col: str = 'KOR',
                 pos_col: str = 'WClass',
                 stem_col: str = 'ОСНОВА',
                 grammar_col: str = 'Gr',
                 gloss_col: str = 'GLOSS',
                 en_transl_col: str = 'TRANS',
                 ru_transl_col: str = 'RUS',
                 sent_transl_col: str = 'SentTrans'):
        self.db = db

        self.sent_id_col = sent_id_col
        self.token_hangul_col = token_hangul_col
        self.pos_col = pos_col
        self.stem_col = stem_col
        self.grammar_col = grammar_col
        self.gloss_col = gloss_col
        self.en_transl_col = en_transl_col
        self.ru_transl_col = ru_transl_col
        self.sent_transl_col = sent_transl_col

    def __add_or_get(self,
                     schema: Type[Union[POS, Stem, Gloss, Allomorph]],
                     inst: Union[POS, Stem, Gloss, Allomorph],
                     get_keys: List[str]) -> Union[POS, Stem, Gloss, Allomorph]:
        statement = select(schema)
        for k in get_keys:
            statement = statement.where(getattr(schema, k) == getattr(inst, k))
        found = self.db.exec(statement).first()
        if found:
            return found

        self.db.add(inst)
        self.db.flush()
        self.db.refresh(inst)
        return inst

    def _add_token_transl(self,
                          token_id: int,
                          token_row: pd.Series):
        if token_row[self.en_transl_col]:
                self.db.add(Translation(
                    token_id=token_id,
                    lang='en',
                    transl=token_row[self.en_transl_col]
                ))
        if token_row[self.ru_transl_col]:
                self.db.add(Translation(
                    token_id=token_id,
                    lang='ru',
                    transl=token_row[self.ru_transl_col]
                ))
        self.db.flush()

    def _add_grammar_info(self,
                          token_id: int,
                          grammar_string: str,
                          gloss_string: str):
        i = 0
        for morpheme, gloss in zip(grammar_string.split('='), gloss_string.split('+')):
            print(i)
            gloss_id = self.__add_or_get(
                schema=Gloss,
                inst=Gloss(name=gloss),
                get_keys=['name']
            ).id
            allomorph_id = self.__add_or_get(
                schema=Allomorph,
                inst=Allomorph(translit=morpheme, gloss_id=gloss_id),
                get_keys=['translit', 'gloss_id']
            ).id
            grammar = Grammar(
                token_id=token_id,
                allomorph_id=allomorph_id,
                pos_in_suffix=i
            )
            self.db.add(grammar)
            i += 1
        self.db.flush()

    def _add_token_info(self,
                        token_pos_in_sent: int,
                        token_row: pd.Series) -> Token:

        sent_id = token_row[self.sent_id_col]
        hangul = translate(token_row[self.token_hangul_col])
        token = Token(
            sent_id=sent_id,
            pos_in_sent=token_pos_in_sent,
            hangul=hangul
        )

        if token_row[self.pos_col]:
            pos_id = self.__add_or_get(
                schema=POS,
                inst=POS(name=token_row[self.pos_col]),
                get_keys=['name']
            ).id
            token.pos_id = pos_id

        if token_row[self.stem_col]:
            stem = token_row[self.stem_col]
            stem_id = self.__add_or_get(
                schema=Stem,
                inst=Stem(translit=stem.replace('-', ''),
                          translit_syl=stem),
                get_keys=['translit_syl']
            ).id
            token.stem_id = stem_id

        self.db.add(token)
        self.db.flush()
        self.db.refresh(token)

        self._add_token_transl(token.id, token_row)
        if token_row[self.grammar_col] and token_row[self.gloss_col]:
            self._add_grammar_info(token.id, token_row[self.grammar_col], token_row[self.gloss_col])

        return token

    def _add_text(self,
                  text: Text) -> Text:
        self.db.add(text)
        self.db.flush()
        self.db.refresh(text)
        return text

    def put_in_db(self,
                  fp: Union[str, os.PathLike, TextIO]):
        data = pd.read_csv(fp, sep='\t', header=0, keep_default_na=False)
        with self.db:
            text = self._add_text(Text(title=fp.name))

            for i, idx in data.groupby(self.sent_id_col).groups.items():
                sentence_data = data.loc[idx].reset_index(drop=True)
                sentence_tokens = []
                for j, row in sentence_data.iterrows():
                    added_token = self._add_token_info(token_pos_in_sent=j, token_row=row)
                    sentence_tokens.append(added_token.hangul)

                sentence = Sentence(
                    text_id=text.id,
                    sent_address=i,
                    sent=' '.join(sentence_tokens),
                    translation=sentence_data.loc[0, self.sent_transl_col]
                )
                self.db.add(sentence)
            self.db.commit()


if __name__ == '__main__':
    filepath = input('Enter path to csv: ')
    db_path = input('Enter path to database: ')

    sqlite_url = f"sqlite:///{db_path}"

    engine = create_engine(sqlite_url, echo=True)
    db = Session(engine)

    converter = CSV2Database(db=db)

    with open(filepath) as fp:
        converter.put_in_db(fp)








