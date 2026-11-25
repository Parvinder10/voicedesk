import os
import re
import json
import math
from typing import List, Tuple, Optional, Dict, Any, Set
from io import BytesIO
from pypdf import PdfReader
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.config import settings
from app.models import Organization, Document, DocumentChunk, BusinessSettings
from app.schemas.document import DocumentQueryResponse, SourceReference

# Prompt injection patterns to neutralize
INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"(?i)disregard\s+(all\s+)?(previous|prior)\s+instructions",
    r"(?i)system\s*:\s*",
    r"(?i)you\s+are\s+now\s+(in\s+)?(dan|developer|debug|god)\s+mode",
    r"(?i)reveal\s+(your|the)\s+(system|secret)\s+prompt",
    r"(?i)bypass\s+all\s+(rules|guidelines|safety)",
    r"(?i)act\s+as\s+an\s+unfiltered\s+ai"
]

STOP_WORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can",
    "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't",
    "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have",
    "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him",
    "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't",
    "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor",
    "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out",
    "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some",
    "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there",
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", "through",
    "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've",
    "were", "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while", "who",
    "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours"
}


def sanitize_text(text: str) -> str:
    """Disarms known prompt injection phrases in uploaded document text."""
    sanitized = text
    for pattern in INJECTION_PATTERNS:
        sanitized = re.sub(pattern, "[FILTERED_INSTRUCTION]", sanitized)
    return sanitized


def compute_deterministic_embedding(text: str, dim: int = 512) -> List[float]:
    """
    Stop-word filtered character-trigram and word hashing vectorizer.
    """
    raw_tokens = re.findall(r'\b[a-z]{2,}\b', text.lower())
    tokens = [t for t in raw_tokens if t not in STOP_WORDS]
    vec = [0.0] * dim
    if not tokens:
        return vec
    for token in tokens:
        # Word hash
        h_word = abs(hash(token)) % dim
        vec[h_word] += 2.0
        # Character n-grams for typo resilience
        if len(token) >= 3:
            for i in range(len(token) - 2):
                ngram = token[i:i+3]
                h_ng = abs(hash(ngram)) % dim
                vec[h_ng] += 0.5

    # Normalize vector to unit length
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    return max(0.0, min(1.0, dot))


class RAGService:
    @staticmethod
    def extract_text(file_bytes: bytes, filename: str) -> str:
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".pdf":
            try:
                reader = PdfReader(BytesIO(file_bytes))
                text_parts = []
                for idx, page in enumerate(reader.pages):
                    page_text = page.extract_text() or ""
                    text_parts.append(page_text)
                return "\n\n".join(text_parts).strip()
            except Exception as e:
                raise ValueError(f"Failed to extract text from PDF: {str(e)}")
        elif ext in [".txt", ".md", ".csv"]:
            try:
                return file_bytes.decode("utf-8", errors="replace").strip()
            except Exception as e:
                raise ValueError(f"Failed to decode text file: {str(e)}")
        else:
            raise ValueError(f"Unsupported file format '{ext}'. Allowed formats: .pdf, .txt, .md")

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """Recursive sliding-window chunking respecting sentence/paragraph boundaries."""
        if not text:
            return []
        
        paragraphs = text.split("\n\n")
        chunks: List[str] = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(current_chunk) + len(para) <= chunk_size:
                current_chunk = f"{current_chunk}\n\n{para}".strip()
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                if len(para) > chunk_size:
                    words = para.split(" ")
                    sub_chunk = ""
                    for word in words:
                        if len(sub_chunk) + len(word) + 1 <= chunk_size:
                            sub_chunk = f"{sub_chunk} {word}".strip()
                        else:
                            chunks.append(sub_chunk)
                            sub_chunk = word
                    if sub_chunk:
                        current_chunk = sub_chunk
                else:
                    current_chunk = para

        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    @staticmethod
    def generate_embedding(text: str) -> List[float]:
        """Generates embedding via OpenAI if key is set, otherwise deterministic vector."""
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("sk-"):
            try:
                import openai
                client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                resp = client.embeddings.create(
                    input=text[:4000],
                    model=settings.OPENAI_EMBEDDING_MODEL
                )
                return resp.data[0].embedding
            except Exception:
                pass
        return compute_deterministic_embedding(text)

    @classmethod
    def index_document(
        cls,
        db: Session,
        org: Organization,
        filename: str,
        file_bytes: bytes
    ) -> Document:
        # 1. Extract text
        raw_text = cls.extract_text(file_bytes, filename)
        if not raw_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Extracted text is empty. Please upload a document with readable content."
            )

        # 2. Sanitize against prompt injections
        clean_text = sanitize_text(raw_text)

        # 3. Save physical file copy
        org_upload_dir = os.path.join(settings.UPLOAD_DIR, org.id)
        os.makedirs(org_upload_dir, exist_ok=True)
        saved_path = os.path.join(org_upload_dir, f"{os.urandom(6).hex()}_{filename}")
        with open(saved_path, "wb") as f:
            f.write(file_bytes)

        # 4. Create Document record
        ext = os.path.splitext(filename)[1].lower().replace(".", "")
        doc = Document(
            organization_id=org.id,
            filename=filename,
            file_path=saved_path,
            file_type=ext or "txt",
            file_size_bytes=len(file_bytes),
            status="processing"
        )
        db.add(doc)
        db.flush()

        # 5. Chunk text
        chunks = cls.chunk_text(clean_text)
        doc.chunk_count = len(chunks)

        # 6. Generate embeddings and persist chunks
        for idx, chunk_content in enumerate(chunks):
            emb = cls.generate_embedding(chunk_content)
            chunk_rec = DocumentChunk(
                organization_id=org.id,
                document_id=doc.id,
                chunk_index=idx,
                content=chunk_content,
                token_count=len(chunk_content.split()),
                embedding_json=json.dumps(emb)
            )
            db.add(chunk_rec)

        doc.status = "indexed"
        db.commit()
        db.refresh(doc)
        return doc

    @classmethod
    def search_knowledge_base(
        cls,
        db: Session,
        org: Organization,
        query: str,
        top_k: int = 4
    ) -> Tuple[List[Tuple[DocumentChunk, float]], float]:
        """Tenant-isolated semantic search over document chunks."""
        query_emb = cls.generate_embedding(query)

        # Query all chunks for this organization
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.organization_id == org.id
        ).all()

        if not chunks:
            return [], 0.0

        # Also extract meaningful non-stop query words to check keyword relevance
        raw_q_tokens = re.findall(r'\b[a-z]{3,}\b', query.lower())
        q_tokens = [t for t in raw_q_tokens if t not in STOP_WORDS]

        scored_chunks: List[Tuple[DocumentChunk, float]] = []
        for c in chunks:
            if not c.embedding_json:
                continue
            emb = json.loads(c.embedding_json)
            cos_sim = cosine_similarity(query_emb, emb)

            # Check if query keywords appear in chunk
            c_text_lower = c.content.lower()
            keyword_hits = sum(1 for t in q_tokens if t in c_text_lower)
            keyword_ratio = (keyword_hits / len(q_tokens)) if q_tokens else 0.0

            # Composite confidence score
            combined_score = 0.6 * cos_sim + 0.4 * keyword_ratio
            scored_chunks.append((c, combined_score))

        # Sort by similarity descending
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        top_matches = scored_chunks[:top_k]
        highest_score = top_matches[0][1] if top_matches else 0.0
        return top_matches, highest_score

    @classmethod
    def answer_query(
        cls,
        db: Session,
        org: Organization,
        query: str,
        top_k: int = 4
    ) -> DocumentQueryResponse:
        matches, best_score = cls.search_knowledge_base(db, org, query, top_k)

        # Strict threshold check: If no matches or score is below relevance threshold, acknowledge limitation
        if not matches or best_score < 0.30:
            settings_rec = db.query(BusinessSettings).filter_by(organization_id=org.id).first()
            transfer_phone = settings_rec.human_transfer_phone if settings_rec else None
            contact_str = f" at {transfer_phone}" if transfer_phone else ""
            
            return DocumentQueryResponse(
                query=query,
                answer=(
                    f"I apologize, but I do not have specific verified information regarding that in our business records. "
                    f"I would be delighted to connect you with our staff team{contact_str} who can assist you directly."
                ),
                sources=[],
                has_answer=False,
                is_fallback=True
            )

        sources: List[SourceReference] = []
        context_parts = []
        for chunk, score in matches:
            doc = db.query(Document).filter_by(id=chunk.document_id).first()
            fname = doc.filename if doc else "Document"
            snippet = chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content
            sources.append(
                SourceReference(
                    document_id=chunk.document_id,
                    filename=fname,
                    chunk_index=chunk.chunk_index,
                    score=round(score, 3),
                    snippet=snippet
                )
            )
            context_parts.append(f"Source: {fname}\n{chunk.content}")

        joined_context = "\n\n---\n\n".join(context_parts)

        # Generate answer using OpenAI LLM if configured
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("sk-"):
            try:
                import openai
                client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                prompt = f"""You are the AI voice receptionist for {org.name}.
Answer the caller's inquiry strictly and solely using the provided business document context below.
Rules:
- NEVER invent or assume prices, policies, or facts not mentioned in the context.
- If the exact answer is not in the context, explicitly state that you don't have that information.
- Keep the response clear, professional, concise, and suitable for spoken dialogue.

<verified_context>
{joined_context}
</verified_context>

Caller Question: {query}
"""
                resp = client.chat.completions.create(
                    model=settings.OPENAI_CHAT_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a helpful, factual AI receptionist."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=250
                )
                answer = resp.choices[0].message.content.strip()
                return DocumentQueryResponse(
                    query=query,
                    answer=answer,
                    sources=sources,
                    has_answer=True,
                    is_fallback=False
                )
            except Exception:
                pass

        # Fallback synthesis directly from top context chunks
        top_chunk = matches[0][0].content
        synthesized_answer = (
            f"Based on our official records: {top_chunk}"
        )
        return DocumentQueryResponse(
            query=query,
            answer=synthesized_answer,
            sources=sources,
            has_answer=True,
            is_fallback=True
        )
