from functions.search import bm25_search
from functions.search import embedding_search

import pandas as pd
from typing import List


def search(keywords: List[str]):
    # Run both searches
    bm25_results = bm25_search.bm25_search(keywords).head(10)
    embedding_results = embedding_search.embedding_search(keywords).head(10)

    # Combine without messing with score
    df = pd.concat([bm25_results, embedding_results], ignore_index=True)

    # Remove duplicates by case, keep higher ranked result (lower rank number = higher rank)
    df = df.sort_values(by="rank").drop_duplicates(subset="case", keep="first")

    # Return just the summaries of the top results
    r = []
    for _, row in df.head(10).iterrows():
        case_id = row["case"].get("Identifier", "").strip()
        if case_id:
            t = f"{case_id}: {row['summary']}"
        else:
            t = row["summary"]

        r.append(t)

    return r


if __name__ == "__main__":
    inputs = ["Environmental counterclaims"]
    results = search(inputs)
    print(results.iloc[0])  # Print the first result summary
