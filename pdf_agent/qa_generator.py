import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_answer(question, relevant_chunks, chat_history=None):

    context = "\n\n---\n\n".join(
        f"[Page {c['pages'][0]}]\n{c['text']}" for c in relevant_chunks
    )

    history_text = ""

    if chat_history:
        recent = chat_history[-3:]
        for chat in recent:
            history_text += f"Q: {chat['question']}\nA: {chat['answer']}\n\n"

    system_prompt = (
        "You are a helpful assistant answering questions about a PDF document. "
        "Answer ONLY using the provided context below. If the answer isn't in "
        "the context, say you couldn't find that information in the document. "
        "Cite the page number(s) you used, like (Page 3). Keep answers concise."
    )

    user_prompt = (
        f"Context from the PDF:\n{context}\n\n"
        f"Previous conversation:\n{history_text}\n"
        f"Question: {question}\n\n"
        "Answer:"
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0
    )

    return response.choices[0].message.content.strip()