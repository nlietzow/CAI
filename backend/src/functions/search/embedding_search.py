import pandas as pd
import numpy as np
import os
import config
from typing import List
from sklearn.metrics.pairwise import cosine_similarity
from langchain_google_genai import GoogleGenerativeAIEmbeddings

if not "GOOGLE_API_KEY" in os.environ or not os.environ["GOOGLE_API_KEY"].strip():
    raise ValueError("GOOGLE_API_KEY environment variable is not set or is empty.")

gemini_emb = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-exp-03-07")


def embedding_search(keywords: List[str]):
    df = pd.read_json(config.corpus_file, orient="records", lines=True).explode(
        "embeddings"
    )
    embeddings = np.stack(df.embeddings.apply(np.array))
    keyword_embeddings = np.array(gemini_emb.embed_documents(keywords))

    similarity = cosine_similarity(keyword_embeddings, embeddings).mean(axis=0)

    df["score"] = similarity
    df = df.sort_values(by="score", ascending=False).drop_duplicates(subset="case")
    df["rank"] = df["score"].rank(ascending=False, method="first").astype(int)
    df["type"] = "embedding"

    return df


if __name__ == "__main__":
    inputs = ["contract dispute", "breach of contract", "damages"]
    similar_cases = embedding_search(inputs)
    print(similar_cases)
