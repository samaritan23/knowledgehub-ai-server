import json

from openai import OpenAI

from knowledgehub.config import OPENAI_API_KEY, OPENAI_CHAT_MODEL
from knowledgehub.search import Passage, search

REFUSAL = "not in your documents"


def ask_question(question: str) -> dict:
    text = question.strip()
    if not text:
        raise ValueError("question is missing")
    found = search(text)
    if found.refused:
        return {"status": "refused", "answer": REFUSAL, "citations": []}

    answer, cited_ids = _write_answer(text, found.passages)
    if answer.strip().lower() == REFUSAL:
        return {"status": "refused", "answer": REFUSAL, "citations": []}

    allowed = {passage.chunk_id: passage for passage in found.passages}
    citations = [
        {
            "chunk_id": allowed[chunk_id].chunk_id,
            "filename": allowed[chunk_id].filename,
            "page": allowed[chunk_id].page,
            "text": allowed[chunk_id].text,
        }
        for chunk_id in cited_ids
        if chunk_id in allowed
    ]
    return {"status": "answered", "answer": answer, "citations": citations}


def _write_answer(question: str, passages: list[Passage]) -> tuple[str, list[str]]:
    labeled = "\n\n".join(
        f"id: {passage.chunk_id}\nfile: {passage.filename}\npage: {passage.page}\n{passage.text}"
        for passage in passages
    )
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_CHAT_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Answer only from the passages. "
                    "Respond as JSON with keys answer and chunk_ids. "
                    "chunk_ids is a list of the passage ids you used. "
                    f'If the passages do not contain the answer, set answer to "{REFUSAL}" '
                    "and chunk_ids to an empty list."
                ),
            },
            {
                "role": "user",
                "content": f"Question: {question}\n\nPassages:\n{labeled}",
            },
        ],
    )
    content = response.choices[0].message.content or ""
    payload = json.loads(content)
    answer = str(payload.get("answer", "")).strip()
    chunk_ids = [str(chunk_id) for chunk_id in payload.get("chunk_ids", [])]
    return answer, chunk_ids
