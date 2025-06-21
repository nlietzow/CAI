from pickle import load
import pandas as pd
from functions.search.bm25_init import tokenize_text
import config
from pathlib import Path
from typing import List
from itertools import chain

with open(Path(__file__).parent / 'bm25_model.pkl', 'rb') as f:
    bm25 = load(f)


def bm25_search(keywords: List[str]):
    df = pd.read_json(config.corpus_file, orient='records', lines=True)

    keywords_tokenized = list(chain.from_iterable(tokenize_text(k) for k in keywords))

    scores = bm25.get_scores(keywords_tokenized)
    df['score'] = scores
    df = df.sort_values(by='score', ascending=False)
    df['rank'] = df['score'].rank(ascending=False, method='first').astype(int)
    df['type'] = 'bm25'

    return df


if __name__ == '__main__':
    inputs = ["contract dispute", "breach of contract", "damages"]
    similar_cases = bm25_search(inputs)
    print(similar_cases)
