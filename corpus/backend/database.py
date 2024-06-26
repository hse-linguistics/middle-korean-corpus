from contextlib import contextmanager
import os
from typing import Union, Tuple, Iterable, List
import sqlite3


from .datamodels import Sentence, Stem, Morph


class DBHandler:

    conn = None

    def __init__(self,
                 db_path: Union[str, os.PathLike]):
        try:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
        except sqlite3.OperationalError:
            raise sqlite3.OperationalError(db_path)

    def __del__(self):
        self.conn.close()

    @contextmanager
    def transaction(self, raise_exception: bool = False):
        try:
            yield self.conn
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            if raise_exception:
                raise e
            else:
                print(f"Error during query execution: {e.__class__.__name__} - {str(e)}")
        except Exception as e:
            self.conn.close()
            raise e

    @staticmethod
    def dict_factory(cursor: sqlite3.Cursor, row):
        fields = [column[0] for column in cursor.description]
        return {key: value for key, value in zip(fields, row)}

    @staticmethod
    def one_column_factory(cursor: sqlite3.Cursor, row):
        return row[0]


class DBFiller(DBHandler):

    def _add_pos(self, pos: str, commit: bool = True) -> Tuple[int, ]:
        cur = self.conn.execute("""
        INSERT INTO pos (name)
        VALUES (?)
        RETURNING id""", (pos, ))
        if commit:
            self.conn.commit()
        return cur.fetchone()

    def get_pos_id(self, pos: str, commit: bool = True) -> int:
        cur = self.conn.execute("""
        SELECT id
        FROM pos
        WHERE name=(?)""", (pos, ))
        pos_id = cur.fetchone()
        if not pos_id:
            pos_id = self._add_pos(pos, commit)
        return pos_id[0]

    def _add_gloss(self, gloss: str, commit: bool = True) -> Tuple[int, ]:
        cur = self.conn.execute("""
        INSERT INTO gloss (name)
        VALUES (?)
        RETURNING id""", (gloss, ))
        if commit:
            self.conn.commit()
        return cur.fetchone()

    def get_gloss_id(self, gloss: str, commit: bool = True) -> int:
        cur = self.conn.execute("""
        SELECT id
        FROM gloss
        WHERE name=(?)""", (gloss, ))
        gloss_id = cur.fetchone()
        if not gloss_id:
            gloss_id = self._add_gloss(gloss, commit)
        return gloss_id[0]

    def _add_allomorph(self,
                       translit: str,
                       gloss_id: int,
                       commit: bool = True) -> Tuple[int, ]:
        cur = self.conn.execute("""
        INSERT INTO allomorph (translit, gloss_id) 
        VALUES (?, ?)
        RETURNING id""", (translit, gloss_id))
        if commit:
            self.conn.commit()
        return cur.fetchone()

    def get_allomorph_id(self,
                         translit: str,
                         gloss: str,
                         commit: bool = True) -> int:
        gloss_id = self.get_gloss_id(gloss, commit)
        cur = self.conn.execute("""
        SELECT id
        FROM allomorph
        WHERE gloss_id = (?) AND translit = (?)""", (gloss_id, translit))
        allomorph_id = cur.fetchone()
        if not allomorph_id:
            allomorph_id = self._add_allomorph(translit, gloss_id, commit)
        return allomorph_id[0]

    def add_grammar(self,
                    token_id: int,
                    morph: Morph,
                    pos_in_suffix: int,
                    commit: bool = True):
        allomorph_id = self.get_allomorph_id(morph.translit, morph.gloss, commit)
        self.conn.execute("""
        INSERT INTO grammar (token_id, pos_in_suffix, allomorph_id) 
        VALUES (?, ?, ?)""", (token_id, pos_in_suffix, allomorph_id))
        if commit:
            self.conn.commit()

    def _add_stem(self,
                  stem: Stem,
                  commit: bool = True) -> Tuple[int, ]:
        cur = self.conn.execute("""
        INSERT INTO stem (translit, translit_syl, en, ru) 
        VALUES (:translit, :translit_syl, :en, :ru)
        RETURNING id""", vars(stem))
        if commit:
            self.conn.commit()
        return cur.fetchone()

    def get_stem_id(self,
                    stem: Stem,
                    commit: bool = True) -> int:
        cur = self.conn.execute("""
        SELECT id 
        FROM stem
        WHERE translit = (?)""", (stem.translit, ))
        stem_id = cur.fetchone()
        if not stem_id:
            stem_id = self._add_stem(stem, commit)
        return stem_id[0]

    def add_token_info(self,
                       sent_address: int,
                       pos_in_sent: int,
                       hangul: str,
                       stem: Stem,
                       pos: str,
                       grammar: Iterable[Morph],
                       commit: bool = True):
        stem_id = self.get_stem_id(stem, commit=commit)
        pos_id = self.get_pos_id(pos, commit=commit)
        cur = self.conn.execute("""
        INSERT INTO token (sent_id, pos_in_sent, stem_id, pos_id, hangul) 
        VALUES ((SELECT id FROM sentence WHERE address = ?), 
        ?, ?, ?, ?)
        RETURNING id""", (sent_address, pos_in_sent, stem_id, pos_id, hangul))
        token_id = cur.fetchone()[0]
        for i, gram in enumerate(grammar):
            self.add_grammar(token_id, gram, i, commit=commit)
        if commit:
            self.conn.commit()

    def add_sentence(self,
                     sent: Sentence):
        self.conn.execute("""
        INSERT or IGNORE INTO sentence (address, sent) 
        VALUES (?, ?)""", (sent.address, sent.sentence))
        self.conn.commit()

    def add_sentence_tokens(self,
                            sent: Sentence):
        with self.transaction():
            for token in sent.tokens:
                self.add_token_info(**vars(token), commit=False)


class WebDBHandler(DBHandler):
    def get_pos_tags(self):
        cur = self.conn.execute("""
        SELECT *
        FROM pos""")
        return cur.fetchall()

    def get_glosses(self):
        cur = self.conn.execute("""
        SELECT *
        FROM gloss""")
        return cur.fetchall()

    def match_stem(self, stem: str) -> Iterable[int]:
        cur = self.conn.execute("""
        SELECT token.id
        FROM stem
        LEFT JOIN token
        ON token.stem_id = stem.id
        WHERE translit = (?)""", (stem,))
        cur.row_factory = self.one_column_factory
        return cur.fetchall()

    def select_sentences(self, token_ids: List[int]) -> Iterable[int]:
        qmark_args = ", ".join("?" for t in token_ids)

        query = f"""
        SELECT sentence.id
        FROM sentence
        JOIN token
        ON sentence.id = token.sent_id
        WHERE token.id IN ({qmark_args})"""

        cur = self.conn.execute(query, token_ids)
        cur.row_factory = self.one_column_factory
        return cur.fetchall()

    def sentence_context(self, sent_id: int):
        cur = self.conn.execute("""
        SELECT sentence.sent
        FROM sentence
        WHERE sentence.id = (?) - 1""", (sent_id,))
        left = cur.fetchone()

        cur = self.conn.execute("""
                SELECT sentence.sent
                FROM sentence
                WHERE sentence.id = (?) + 1""", (sent_id,))
        right = cur.fetchone()
        return left, right

    def sent_token_info(self, sent_id: int) -> List[dict]:
        cur = self.conn.execute("""
        SELECT * 
        FROM tokens_view
        WHERE sent_id = (?)""", (sent_id, ))
        cur.row_factory = self.dict_factory
        return cur.fetchall()