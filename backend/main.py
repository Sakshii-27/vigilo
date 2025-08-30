from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from vigilo_utils import (
    update_vector_db,
    get_metadata_store,
    store_company_data,
    CompanyData,
    CompanyInfo,
    ComplianceDocument,
    ProductInfo,
    PackagingInfo,
    hash_company,
    get_latest_amendments,
    get_company_info,
    get_company_products,
    ingest_local_pdfs_from,
    get_latest_company_id,
    update_rbi_only,
    load_rbi_metadata,
    get_latest_rbi_amendments,
)
from typing import List, Dict, Optional
from fastapi import UploadFile, Form, File, HTTPException
from datetime import date
import hashlib
import json
import os
from fastapi.responses import FileResponse
from prompt_chain import AmendmentAnalyzer

app = FastAPI(title="Vigilo FSSAI Compliance API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"msg": "Vigilo FSSAI Compliance API Running 🚀"}

@app.get("/update")
def update() -> Dict[str, int]:
    count = update_vector_db()
    return {"new_entries": count}

@app.get("/update-rbi")
def update_rbi() -> Dict[str, int]:
    """Update only RBI notifications"""
    count = update_rbi_only()
    return {"new_entries": count, "source": "RBI"}

@app.get("/list-rbi")
def list_rbi_notifications() -> List[Dict]:
    """Get only RBI notifications"""
    data = load_rbi_metadata()
    if not data:
        # Attempt to populate if empty
        try:
            update_rbi_only()
            data = load_rbi_metadata()
        except Exception:
            pass
    return data

@app.get("/amendments-rbi")
def get_rbi_amendments(limit: int = 6) -> List[Dict]:
    """Get latest RBI amendments only"""
    return get_latest_rbi_amendments(limit)

@app.get("/list")
def list_notifications() -> List[Dict]:
    return get_metadata_store()

@app.get("/test-scrape")
def test_scrape():
    from vigilo_utils import scrape_fssai_notifications
    return scrape_fssai_notifications()

@app.get("/test-scrape-rbi")
def test_scrape_rbi():
    from vigilo_utils import scrape_rbi_notifications
    return scrape_rbi_notifications()

@app.get("/seed/synthetic")
def seed_synthetic() -> Dict[str, int]:
    """Ingest local PDFs from synthetic_pdfs_detailed/ for quick testing."""
    base_dir = os.path.dirname(os.path.dirname(__file__))  # project root
    dir_path = os.path.join(base_dir, "synthetic_pdfs_detailed")
    added = ingest_local_pdfs_from(dir_path)
    return {"ingested": added}

@app.post("/company/submit")
async def submit_company_data(
    # Company Info
    company_name: str = Form(...),
    address: str = Form(""),
    fssai_license: str = Form(""),
    fssai_validity: Optional[str] = Form(None),
    business_type: Optional[str] = Form(None),
    gst_number: Optional[str] = Form(None),
    
    # Legal Documents
    fssai_file: Optional[UploadFile] = File(None),
    gst_file: Optional[UploadFile] = File(None),
    audit_file: Optional[UploadFile] = File(None),
    lab_report_file: Optional[UploadFile] = File(None),
    
    # Product Details
    product_name: str = Form("Default Product"),
    product_category: str = Form("general"),
    ingredients: str = Form("{}"),  # JSON string
    nutrition: str = Form("{}"),    # JSON string
    allergens: str = Form(""),      # Comma-separated
    
    # Packaging
    label_front: Optional[UploadFile] = File(None),
    label_back: Optional[UploadFile] = File(None),
    expiry_format: str = Form("DD/MM/YYYY"),
    claims: str = Form(""),        # Comma-separated

    # Additional product documents
    ingredients_file: Optional[UploadFile] = File(None),
    nutrition_file: Optional[UploadFile] = File(None),
):
    # Save uploaded files
    def save_file(file: UploadFile) -> str:
        base_dir = os.path.dirname(__file__)
        upload_dir = os.path.join(base_dir, "data", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        path = os.path.join(upload_dir, f"{hashlib.md5(file.filename.encode()).hexdigest()}_{file.filename}")
        with open(path, 'wb') as f:
            f.write(file.file.read())
        return path

    # Prepare company data
    company_data = CompanyData(
        company_info=CompanyInfo(
            company_name=company_name,
            address=address,
            fssai_license=fssai_license,
            fssai_validity=date.fromisoformat(fssai_validity) if fssai_validity else date.today(),
            business_type=business_type or "",
            gst_number=gst_number
        ),
        legal_documents=[
            # Added conditionally below
        ],
        products=[
            ProductInfo(
                product_name=product_name,
                category=product_category,
                ingredients=json.loads(ingredients),
                nutritional_info=json.loads(nutrition),
                allergens=[a.strip() for a in allergens.split(",")] if allergens else []
            )
        ],
        packaging=[
            PackagingInfo(
                label_front_url=save_file(label_front) if label_front else "",
                label_back_url=save_file(label_back) if label_back else "",
                expiry_format=expiry_format,
                packaging_claims=[c.strip() for c in claims.split(",")] if claims else []
            )
        ]
    )

    # Add legal docs conditionally
    if fssai_file:
        company_data.legal_documents.append(ComplianceDocument(
            document_type="FSSAI License",
            file_path=save_file(fssai_file),
            issue_date=date.today()
        ))
    if gst_file:
        company_data.legal_documents.append(ComplianceDocument(
            document_type="GST Certificate",
            file_path=save_file(gst_file),
            issue_date=date.today()
        ))
    if lab_report_file:
        company_data.legal_documents.append(ComplianceDocument(
            document_type="Lab Test Report",
            file_path=save_file(lab_report_file),
            issue_date=date.today()
        ))
    if audit_file:
        company_data.legal_documents.append(ComplianceDocument(
            document_type="Audit Report",
            file_path=save_file(audit_file),
            issue_date=date.today()
        ))

    # Optional product/packaging-related PDFs
    if ingredients_file:
        company_data.legal_documents.append(ComplianceDocument(
            document_type="Ingredients Document",
            file_path=save_file(ingredients_file),
            issue_date=date.today()
        ))
    if nutrition_file:
        company_data.legal_documents.append(ComplianceDocument(
            document_type="Nutritional Information Document",
            file_path=save_file(nutrition_file),
            issue_date=date.today()
        ))

    store_company_data(company_data)
    return {"status": "success", "company_id": hash_company(company_name)}

@app.get("/compliance/check")
async def check_company_compliance(company_id: str):
    """Run the new 5-stage prompt chain for a company.

    This uses:
    - First 5 PDFs from backend/data/pdfs as amendments
    - Company info from backend/data/companies/<company_id>.json
    - First 2 and next 3 PDFs from backend/data/uploads as company docs
    Logs are saved under backend/data/logs/<company_id>/<timestamp>/
    """
    try:
        result = analyze_amendments_for_company(company_id)
        return {"status": "success", "result": result}
    except Exception as e:
        # Provide a clear error with hint
        raise HTTPException(status_code=400, detail=f"Compliance check failed: {e}")

def analyze_amendments_for_company(company_id: str) -> Dict:
    """Run the new 5-stage prompt chain using on-disk PDFs and company uploads."""
    company = get_company_info(company_id)
    if not company:
        raise ValueError("Company not found. Submit company data first.")
    uploads_dir = os.path.join(os.path.dirname(__file__), "data", "uploads")
    analyzer = AmendmentAnalyzer(company_id=company_id)
    return analyzer.run_full_chain(company, uploads_dir=uploads_dir)

@app.get("/pdf")
def get_pdf(document_id: str):
    """Return PDF file for a given document_id from metadata store."""
    try:
        meta = get_metadata_store()
        match = next((m for m in meta if (m.get("document_id") == document_id)), None)
        # If not found in FSSAI metadata, look in RBI metadata
        if not match:
            rbi_meta = load_rbi_metadata()
            match = next((m for m in rbi_meta if (m.get("document_id") == document_id)), None)
        if not match:
            raise HTTPException(status_code=404, detail="Document not found")
        path = match.get("pdf_path")
        if not path:
            raise HTTPException(status_code=404, detail="PDF file not found")
        # Resolve relative paths against backend directory
        if not os.path.isabs(path):
            base_dir = os.path.dirname(__file__)
            path = os.path.join(base_dir, path)
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="PDF file not found")
        fname = os.path.basename(path)
        return FileResponse(path, media_type="application/pdf", filename=fname)
    except HTTPException:
        raise

@app.get("/company/latest")
def latest_company():
    """Return the latest company's id and brief info. Frontend uses this to run compliance."""
    cid = get_latest_company_id()
    if not cid:
        raise HTTPException(status_code=404, detail="No companies found")
    info = get_company_info(cid)
    return {"company_id": cid, "company_info": info}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5005)