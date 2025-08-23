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

@app.get("/list")
def list_notifications() -> List[Dict]:
    return get_metadata_store()

@app.get("/test-scrape")
def test_scrape():
    from vigilo_utils import scrape_fssai_notifications
    return scrape_fssai_notifications()

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
    claims: str = Form("")        # Comma-separated
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

    store_company_data(company_data)
    return {"status": "success", "company_id": hash_company(company_name)}

@app.get("/compliance/check")
async def check_company_compliance(company_id: str):
    """Endpoint triggering the full analysis pipeline"""
    try:
        analysis = analyze_amendments_for_company(company_id)
        return {"status": "success", "analysis": analysis}
    except Exception as e:
        # Fallback: return a minimal analysis using raw amendments without LLM
        try:
            amendments = get_latest_amendments(limit=5)
            company = get_company_info(company_id) or {"name": company_id}
            # naive summaries
            detailed = []
            for a in amendments:
                content = a.get("content", "")
                summary = (content[:400] + "...") if len(content) > 400 else content
                detailed.append({
                    "title": a.get("title", "Amendment"),
                    "date": a.get("date", ""),
                    "summary": summary,
                    "actions": [
                        "Review amendment text",
                        "Assess applicability to your products/processes",
                        "Update SOP/labels if required"
                    ]
                })
            fallback = {
                "analysis_steps": [
                    {"stage": "fallback", "note": f"LLM unavailable: {str(e)}"}
                ],
                "initial_amendments": len(amendments),
                "relevant_amendments": len(detailed),
                "compliance_plan": {
                    "status": "partial",
                    "notes": "LLM analysis unavailable; provided heuristic summaries",
                    "next_steps": [
                        "Enable GROQ_API_KEY and rerun for detailed plan",
                        "Manually validate listed actions"
                    ]
                },
                "detailed_amendments": detailed
            }
            return {"status": "success", "analysis": fallback}
        except Exception as inner:
            raise HTTPException(status_code=400, detail=f"Compliance check failed: {inner}")

def analyze_amendments_for_company(company_id: str) -> Dict:
    """Run the full prompt chain against latest amendments and company data"""
    # 1) Load data
    amendments = get_latest_amendments(limit=5)
    company = get_company_info(company_id)
    products = get_company_products(company_id)
    if not company:
        raise ValueError("Company not found. Submit company data first.")
    if not amendments:
        # allow empty to still run with mock minimal to avoid crash
        amendments = [{
            "title": "No Amendments Found",
            "date": "",
            "content": "",
        }]
    # 2) Run chain
    analyzer = AmendmentAnalyzer()
    results = analyzer.run_full_analysis(
        amendments=amendments,
        company_data=company,
        products=products[:4] if products else []
    )
    return results

@app.get("/pdf")
def get_pdf(document_id: str):
    """Return PDF file for a given document_id from metadata store."""
    try:
        meta = get_metadata_store()
        match = next((m for m in meta if (m.get("document_id") == document_id)), None)
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving PDF: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)