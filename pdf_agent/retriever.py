import re


def keyword_score(chunk_text, question_words):

    chunk_lower = chunk_text.lower()
    score = 0

    for word in question_words:
        if word in chunk_lower:
            score += chunk_lower.count(word)

    return score


def retrieve_relevant_chunks(question, chunks, top_k=4):

    stopwords = {
        "the", "is", "are", "a", "an", "of", "in", "on", "for", "to",
        "what", "how", "does", "do", "which", "was", "were", "and", "or"
    }

    question_words = [
        w for w in re.findall(r"\w+", question.lower())
        if w not in stopwords and len(w) > 2
    ]

    if not question_words:
        return chunks[:top_k]

    scored = [(keyword_score(c["text"], question_words), c) for c in chunks]
    scored.sort(key=lambda x: x[0], reverse=True)

    top_chunks = [c for score, c in scored if score > 0][:top_k]

    if not top_chunks:
        top_chunks = chunks[:top_k]

    return top_chunks