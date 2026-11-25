from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_org
from app.models import Document, Organization
from app.schemas.document import DocumentResponse, DocumentQueryRequest, DocumentQueryResponse
from app.services.rag_service import RAGService

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base & RAG"])


@router.get("/documents", response_model=List[DocumentResponse])
def list_documents(
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Retrieve all uploaded knowledge documents and indexing statuses for the organization."""
    return db.query(Document).filter_by(organization_id=org.id).order_by(Document.created_at.desc()).all()


@router.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    Upload a document (PDF, TXT, MD, CSV) for RAG processing.
    Extracts text, applies prompt-injection defense sanitization, chunks content,
    generates embeddings, and indexes into the tenant vector store.
    """
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    # Max 20MB
    if len(file_bytes) > 20 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds maximum 20MB limit.")

    try:
        doc = RAGService.index_document(
            db=db,
            org=org,
            filename=file.filename or "uploaded_document.txt",
            file_bytes=file_bytes
        )
        return doc
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Indexing failed: {str(e)}")


@router.delete("/documents/{id}", status_code=status.HTTP_200_OK)
def delete_document(
    id: str,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Delete a document and purge all associated vector chunks from the index."""
    doc = db.query(Document).filter_by(id=id, organization_id=org.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    # Remove physical file if present
    import os
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass

    db.delete(doc)
    db.commit()
    return {"message": "Document deleted and chunks purged.", "id": id}


@router.post("/query", response_model=DocumentQueryResponse)
def query_knowledge_base(
    query_in: DocumentQueryRequest,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    Perform semantic search and generate context-grounded response from
    the organization's indexed knowledge base. Never hallucinates ungrounded details.
    """
    return RAGService.answer_query(
        db=db,
        org=org,
        query=query_in.query,
        top_k=query_in.top_k
    )


@router.post("/reindex/{id}", response_model=DocumentResponse)
def reindex_document(
    id: str,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """Re-index an existing document from its stored file."""
    import os
    doc = db.query(Document).filter_by(id=id, organization_id=org.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Original physical file not found on server.")

    with open(doc.file_path, "rb") as f:
        file_bytes = f.read()

    # Clear old chunks
    from app.models import DocumentChunk
    db.query(DocumentChunk).filter_by(document_id=doc.id).delete()
    db.commit()

    try:
        updated_doc = RAGService.index_document(
            db=db,
            org=org,
            filename=doc.filename,
            file_bytes=file_bytes
        )
        return updated_doc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Re-indexing failed: {str(e)}")
