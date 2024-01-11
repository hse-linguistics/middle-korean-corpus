from dataclasses import dataclass, field
from itertools import product, groupby
from typing import Iterable, Dict, Any, Set, Tuple, Union, List

from .database import WebDBHandler
from .datamodels import HTMLToken, HTMLSentence


class WordSearch:

    def __init__(self,
                 db: WebDBHandler):
        self.db = db

    def create_token_info(self,
                          matched_tokens: Iterable[int],
                          token_info: Dict[str, Any]) -> HTMLToken:
        token = HTMLToken(
            hangul=token_info['hangul'],
            translit=token_info['translit'],
            glosses=token_info['gloss'],
            translations=token_info['translation'],
            color='blue' if token_info['token_id'] in matched_tokens else 'black'
        )
        return token

    def create_sentence_info(self,
                             matches: Iterable[Tuple[Tuple[int, int, int], ...]]):
        sentences = []
        sent_sorted_matches = sorted(matches, key=lambda x: x[0][0])
        for sent, matched_tokens in groupby(sent_sorted_matches, key=lambda x: x[0][0]):
            matched_tokens = [t[2] for group in matched_tokens for t in group]
            context = self.db.sentence_context(sent)
            sentence = HTMLSentence(
                sent_id=sent,
                left=context[0],
                right=context[1]
            )

            sent_tokens_info = self.db.sent_token_info(sent)
            for token in sent_tokens_info:
                sentence.tokens.append(self.create_token_info(matched_tokens, token))
            sentences.append(sentence)
        return sentences

    def stem_matcher(self, stem: str) -> Set[Tuple[int, int, int]]:
        matched_tokens = self.db.match_stem2(stem)
        return set(matched_tokens)

    def pos_matcher(self, pos: str) -> Set[Tuple[int, int, int]]:
        matched_tokens = self.db.match_pos(pos)
        return set(matched_tokens)

    def glosses_matcher(self, glosses: List[str]) -> Set[Tuple[int, int, int]]:
        matched_tokens = self.db.match_glosses(glosses)
        return set(matched_tokens)

    def match_qword(self, word_query: Dict[str, Any]) -> Set[Tuple[int, int, int]]:
        """
        Find tokens in database that match word_query
        Args:
            word_query:

        Returns: Set of candidate tokens (sent_id, pos_in_sent, token_id)
        """
        found_tokens = set()
        for param, value in word_query.items():
            if value:
                matcher = getattr(self, f'{param}_matcher')
                found = matcher(value)
                if not found_tokens:
                    found_tokens.update(found)
                else:
                    found_tokens.intersection_update(found)
                if len(found_tokens) == 0:
                    break
        return found_tokens

    def find_qwords_candidates(self, words_queries: Dict[str, Dict[str, Any]]) -> Dict[str, Set[Tuple[int, int, int]]]:
        word_tokens = {}
        for word, query in words_queries.items():
            word_tokens[word] = self.match_qword(query)
        return word_tokens

    def same_sent_constr(self,
                         words: Iterable[Tuple[int, int, int]]) -> bool:
        if len(set([w[0] for w in words])) == 1:
            return True
        else:
            return False

    def lindist_constr_matcher(self,
                               word1: Tuple[int, int, int],
                               word2: Tuple[int, int, int],
                               lindist: Tuple[int, int]
                               ) -> bool:
        if lindist[0] <= word2[1] - word1[1] <= lindist[1]:
            return True
        else:
            return False

    def pair_match_constraints(self,
                               word1: Tuple[int, int, int],
                               word2: Tuple[int, int, int],
                               constraints: Dict[str, Any]) -> bool:
        for param, value in constraints.items():
            constr_matcher = getattr(self, f'{param}_constr_matcher')
            if not constr_matcher(word1,
                                  word2,
                                  value):
                return False
        return True

    def group_match_constraints(self,
                                group_tokens: Tuple[Tuple[int, int, int], ...],
                                group_qwords: Tuple[Union[str, int], ...],
                                constraints: Dict[Tuple[str, str], Dict[str, Any]]) -> bool:
        if not self.same_sent_constr(group_tokens):
            return False
        for qword_pair, constr in constraints.items():
            word1 = group_tokens[group_qwords.index(qword_pair[0])]
            word2 = group_tokens[group_qwords.index(qword_pair[1])]
            if not self.pair_match_constraints(word1, word2, constr):
                return False
        return True

    def match_constraints(self,
                          qword_candidates: Dict[str, Set[Tuple[int, int, int]]],
                          constraints: Dict[Tuple[str, str], Dict[str, Any]]) -> Iterable[Tuple[Tuple[int, int, int], ...]]:
        candidates_groups = product(*qword_candidates.values())
        qwords = tuple(qword_candidates.keys())
        result_groups = []
        for group in candidates_groups:
            if self.group_match_constraints(group, qwords, constraints):
                result_groups.append(group)
        return result_groups

    def match_query(self, query: Dict[str, Dict[Any, Any]]) -> Iterable[Tuple[Tuple[int, int, int], ...]]:
        qword_candidates = self.find_qwords_candidates(query['words'])
        matches = self.match_constraints(qword_candidates, query['constraints'])
        return matches

    def search(self, query: Dict[str, Dict[Any, Any]]):
        matches = self.match_query(query)
        for match in matches:
            print(match)
        return self.create_sentence_info(matches)


if __name__ == '__main__':
    from .. import DB_PATH

    db = WebDBHandler(DB_PATH)
    search = WordSearch(db)

    ex_query = {
        'words': {
            '0': {
                'stem': '',
                'pos': 7,
                'glosses': []
            }
        },
        'constraints': {}
    }

    ex_query2 = {
        'words': {
            '0': {
                'stem': '',
                'pos': 'N',
                'glosses': []
            },
            '1': {
                'stem': '',
                'pos': 'P',
                'glosses': []
            }
        },
        'constraints': {}
    }

    ex_query3 = {
        'words': {
            '0': {
                'stem': '',
                'pos': '',
                'glosses': ['RETR', 'HONSub', 'PInd']
            },
        },
        'constraints': {}
    }
    ex_query4 = {
        'words': {
            '0': {
                'stem': '',
                'pos': '',
                'glosses': ['TOP']
            },
            '1': {
                'stem': '',
                'pos': '',
                'glosses': ['IND']
            },
        },
        'constraints': {}
    }
    ex_query5 = {
        'words': {
            '0': {
                'stem': '',
                'pos': '',
                'glosses': [3]
            },
            '1': {
                'stem': '',
                'pos': '',
                'glosses': [6]
            },
        },
        'constraints': {
            ('0', '1'): {'lindist': (1, 1)}
        }
    }
    search.search(ex_query5)