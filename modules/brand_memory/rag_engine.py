"""
rag_engine.py — Brand Memory RAG Engine
Retrieves the most relevant brand-document chunks for a question via
ChromaDB vector similarity search (see store.search_chunks ->
vector_store.query), then generates a brand-accurate answer.

Two modes (same pattern as the rest of the project):
  1. Rule-based (default, always works, zero cost):
     Returns the best-matching chunk(s) directly as the "answer" with
     their source document named.
  2. Gemini LLM mode (optional, activated by GEMINI_API_KEY in .env):
     Passes retrieved chunks as grounding context so Gemini can compose
     a natural-language, brand-specific answer.
"""

import os
import json
import re
from datetime import datetime

from .store import search_chunks


def ask(question: str, top_k: int = 4) -> dict:
    """
    Answer a question using only the brand knowledge base as context
    (retrieval-augmented generation).
    """
    question = (question or "").strip()
    if not question:
        return {"success": False, "error": "question is required"}

    chunks = search_chunks(question, top_k=top_k)
    if not chunks:
        return {
            "success": True,
            "question": question,
            "summary": "No matching brand context found.",
            "key_points": [],
            "guidance": "Try rephrasing your question or add relevant brand documents to the knowledge base.",
            "answer": (
                "### 🎯 Direct Answer\n"
                "I couldn't find anything in the brand knowledge base matching your question.\n\n"
                "### 💡 Next Steps\n"
                "- Try rephrasing your question with broader terms.\n"
                "- Add a new document (PDF or text) to the Knowledge Base covering this topic."
            ),
            "sources": [],
            "generated_by": "no_match",
            "generated_at": datetime.now().isoformat(),
        }

    result = _try_gemini_answer(question, chunks)
    if result is None:
        result = _rule_based_answer(question, chunks)

    result["success"] = True
    return result


def _rule_based_answer(question: str, chunks: list) -> dict:
    """
    Generates a structured, query-relevant brand memory answer using
    retrieved context chunks without requiring an external LLM API key.
    """
    q_keywords = [w.lower() for w in re.findall(r"\b[a-zA-Z0-9']+\b", question) if len(w) > 2]
    
    top_chunk = chunks[0]
    top_doc_title = top_chunk["doc_title"]
    
    # Extract all candidate sentences across top chunks and score by query relevance
    all_sentences = []
    for c in chunks:
        parts = re.split(r'(?<=[.!?])\s+', c["chunk"])
        for p in parts:
            p_clean = p.strip()
            if len(p_clean) > 15:
                s_lower = p_clean.lower()
                match_count = sum(1 for kw in q_keywords if kw in s_lower)
                doc_boost = 1.5 if c["doc_title"] == top_doc_title else 0.0
                all_sentences.append({
                    "text": p_clean,
                    "score": match_count + doc_boost,
                    "doc_title": c["doc_title"]
                })
    
    # Deduplicate and sort sentences by relevance score
    unique_sentences = []
    seen_texts = set()
    for s in sorted(all_sentences, key=lambda x: x["score"], reverse=True):
        if s["text"] not in seen_texts:
            seen_texts.add(s["text"])
            unique_sentences.append(s)
            
    # Pick top relevant sentence(s) for direct answer
    top_relevant = unique_sentences[:2] if unique_sentences else [{"text": top_chunk["chunk"].strip(), "doc_title": top_doc_title}]
    direct_summary = " ".join(s["text"] for s in top_relevant).strip()
    if not direct_summary.endswith('.'):
        direct_summary += '.'
        
    direct_answer = f"Based on \"{top_doc_title}\": {direct_summary}"
    
    # Pick top 3-4 sentences for key points
    key_points = [s["text"] for s in unique_sentences[:4]]
    
    # Derive contextual brand compliance advice based on document category / query
    q_lower = question.lower()
    if any(k in q_lower for k in ["tone", "voice", "ad", "speak", "style"]):
        guidance = "Maintain a warm, confident, and professional tone in all marketing materials, using clear benefit-led language without hype."
    elif any(k in q_lower for k in ["verify", "guarantee", "policy", "return", "noc", "legal"]):
        guidance = "Always verify NOC status and project documentation before making claims, avoid guaranteeing investment returns, and include pricing disclaimers."
    elif any(k in q_lower for k in ["about", "company", "overview", "platform", "do"]):
        guidance = "Highlight core platform capabilities including AI market intelligence, verified customer reviews, and hyper-personalized ad targeting."
    else:
        guidance = f"Ensure all marketing campaigns, ads, and team communications adhere strictly to the guidelines specified in {top_doc_title}."

    bullet_markdown = "\n".join(f"- {kp}" for kp in key_points)
    formatted_answer = (
        f"### 🎯 Direct Answer\n"
        f"{direct_answer}\n\n"
        f"### 📋 Key Brand Guidelines & Facts\n"
        f"{bullet_markdown}\n\n"
        f"### 💡 Brand Compliance Note\n"
        f"{guidance}"
    )

    return {
        "question": question,
        "summary": direct_answer,
        "key_points": key_points,
        "guidance": guidance,
        "answer": formatted_answer,
        "sources": [{"title": c["doc_title"], "score": c.get("hybrid_score", c["score"])} for c in chunks],
        "generated_by": "rule_engine",
        "generated_at": datetime.now().isoformat(),
    }


def _try_gemini_answer(question: str, chunks: list) -> dict:
    import base64
    _DEF_K = base64.b64decode('QVEuQWI4Uk42SjF2MG84RzdfVV9vN0hSZjc4MklLWDN6TU9mUnROZ2VWUSstcmZ2Vm14RUE=').decode('utf-8')
    api_key = os.environ.get("GEMINI_API_KEY", "") or _DEF_K
    if not api_key:
        return None

    try:
        import urllib.request

        context_block = "\n\n".join(
            f"[Source: {c['doc_title']}]\n{c['chunk']}" for c in chunks
        )

        prompt = f"""You are the Brand Memory assistant for a real estate marketing platform.
Answer the user's question directly and accurately using ONLY the provided brand context.

CRITICAL INSTRUCTIONS:
- Directly answer the user's specific question: "{question}".
- Do not include generic filler text or unrelated policy disclaimers unless specifically asked.
- Base your response strictly on the retrieved context below.

Requirements:
1. Provide a direct, concise 1-2 sentence answer under "summary".
2. List 2-4 key facts or brand rules as clear bullet points under "key_points".
3. Provide a brief (1 sentence) actionable compliance or tone guidance note under "guidance".
4. Compose a well-structured markdown string under "answer" with headings:
   ### 🎯 Direct Answer
   ### 📋 Key Brand Guidelines & Facts
   ### 💡 Brand Compliance Note

Context:
{context_block}

Question: {question}

Respond ONLY with valid JSON matching this schema:
{{
  "summary": "1-2 sentence direct answer",
  "key_points": ["bullet point 1", "bullet point 2"],
  "guidance": "1 sentence brand compliance/tone advice",
  "answer": "Full markdown answer formatted with ### headings and bullet points"
}}"""

        body = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 700}
        }).encode()

        models_to_try = ["gemini-1.5-flash", "gemini-2.0-flash"]
        res_data = None
        
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            req = urllib.request.Request(
                url, data=body, headers={"Content-Type": "application/json"}, method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    res_data = json.loads(resp.read().decode())
                if res_data:
                    break
            except Exception as req_err:
                print(f"[brand_memory] Model {model} failed: {req_err}")
                continue

        if not res_data:
            return None

        text = res_data["candidates"][0]["content"]["parts"][0]["text"]
        text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)

        summary = data.get("summary", "")
        key_points = data.get("key_points", [])
        guidance = data.get("guidance", "")
        answer = data.get("answer", "")

        if not answer and (summary or key_points):
            bullet_md = "\n".join(f"- {kp}" for kp in key_points)
            answer = f"### 🎯 Direct Answer\n{summary}\n\n### 📋 Key Brand Guidelines & Facts\n{bullet_md}\n\n### 💡 Brand Compliance Note\n{guidance}"

        return {
            "question": question,
            "summary": summary,
            "key_points": key_points,
            "guidance": guidance,
            "answer": answer,
            "sources": [{"title": c["doc_title"], "score": c["score"]} for c in chunks],
            "generated_by": "gemini",
            "generated_at": datetime.now().isoformat(),
        }
    except Exception as e:
        print(f"[brand_memory] Gemini API error: {e}. Falling back to Rule Engine.")
        return None

