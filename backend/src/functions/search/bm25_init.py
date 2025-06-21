import spacy
import config
import pandas as pd
from rank_bm25 import BM25Okapi
from pickle import dump

nlp = spacy.load("en_core_web_sm")


def tokenize_text(text: str):
    doc = nlp(text)
    return [token.lemma_.lower() for token in doc if token.is_alpha and not token.is_stop]


if __name__ == '__main__':
    df = pd.read_json(config.corpus_file, orient='records', lines=True)
    corpus_tokenized = df.summary.apply(tokenize_text).tolist()
    bm25 = BM25Okapi(corpus_tokenized)
    with open('bm25_model.pkl', 'wb') as f:
        dump(bm25, f)
