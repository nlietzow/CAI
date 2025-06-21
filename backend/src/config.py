from pathlib import Path

data_dir = Path(__file__).parent.parent / "data"
corpus_file = data_dir / "all_cases.jsonl"

corpus_file.exists()
print(corpus_file)
