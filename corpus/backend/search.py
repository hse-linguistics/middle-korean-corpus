from typing import Iterable, Dict, Any

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
                             matched_tokens: Iterable[int]) -> Iterable[HTMLSentence]:
        matched_sents = self.db.select_sentences(matched_tokens)

        sentences = []
        for sent in matched_sents:
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

    def match_tokens(self, search_params) -> Iterable[int]:
        stem = search_params['query']
        matched_tokens = self.db.match_stem(stem)
        return matched_tokens

    def search(self, search_params):
        matched_tokens = self.match_tokens(search_params)
        sentences = self.create_sentence_info(matched_tokens)
        return sentences