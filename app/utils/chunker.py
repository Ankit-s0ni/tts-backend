import re
from typing import List


def chunk_text(text: str, max_chars: int = 500) -> List[str]:
    """Simple chunker that keeps sentence boundaries where possible.

    Splits text into sentences using punctuation, then groups sentences into
    chunks of up to `max_chars` characters.
    """
    if not text:
        return []

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Split into sentences (simple heuristic)
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks: List[str] = []
    current = []
    cur_len = 0

    for sent in sentences:
        s = sent.strip()
        if not s:
            continue
        if cur_len + len(s) + (1 if cur_len else 0) <= max_chars:
            current.append(s)
            cur_len += len(s) + (1 if cur_len else 0)
        else:
            if current:
                chunks.append(" ".join(current))
            # if single sentence is longer than max_chars, break it
            if len(s) > max_chars:
                for i in range(0, len(s), max_chars):
                    chunks.append(s[i : i + max_chars])
                current = []
                cur_len = 0
            else:
                current = [s]
                cur_len = len(s)

    if current:
        chunks.append(" ".join(current))

    return chunks
