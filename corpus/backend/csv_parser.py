import os
from typing import Union

import pandas as pd
from hypua2jamo import translate

from .datamodels import Sentence, Token, Stem, Morph
from .database import DBFiller


class AnnotParser:

    def __init__(self,
                 address_col: str,
                 token_col: str,
                 stem_col: str,
                 en_stem_col: str,
                 ru_stem_col: str,
                 pos_col: str,
                 grammar_col: str,
                 gloss_col: str):
        self.address = address_col
        self.token = token_col
        self.stem = stem_col
        self.en = en_stem_col
        self.ru = ru_stem_col
        self.pos = pos_col
        self.gr = grammar_col
        self.gloss = gloss_col

        self.sentences = []

    def parse(self,
              filepath: Union[os.PathLike, str]):
        data = pd.read_csv(filepath, header=0, keep_default_na=False)
        for i, idx in data.groupby(self.address).groups.items():
            sentence_info = data.loc[idx]
            sentence = Sentence(i, translate(' '.join(sentence_info[self.token])))
            for j, row in sentence_info.iterrows():
                token = Token(
                    sent_address=i,
                    pos_in_sent=j,
                    hangul=translate(str(row[self.token])),
                    stem=Stem(
                        translit=''.join(row[self.stem].split('-')),
                        translit_syl=row[self.stem],
                        en=row[self.en],
                        ru=row[self.ru]),
                    pos=row[self.pos],
                    grammar=[Morph(*morph) for morph in zip(row[self.gr].split('='), row[self.gloss].split('+')) if
                             morph[0] and morph[1]]
                )
                sentence.tokens.append(token)
            self.sentences.append(sentence)

    def to_database(self,
                    db: DBFiller):
        for sent in self.sentences:
            db.add_sentence(sent)
            db.add_sentence_tokens(sent)


if __name__ == '__main__':
    from corpus import DB_PATH

    example_path = '/Users/viktoriaknazkova/Desktop/me/study/github_repos/middle-korean-corpus/data/korean_example.csv'
    parser = AnnotParser(address_col='ADDRESS',
                         token_col='KOR',
                         stem_col='ОСНОВА',
                         en_stem_col='TRANS',
                         ru_stem_col='RUS',
                         pos_col='WClass',
                         gloss_col='GLOSS',
                         grammar_col='Gr')

    parser.parse(example_path)

    db = DBFiller(DB_PATH)
    parser.to_database(db)