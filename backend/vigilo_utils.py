import os
import requests
from bs4 import BeautifulSoup
import pdfplumber
from datetime import datetime
from typing import List, Dict
import hashlib
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
import re
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import date

class CompanyInfo(BaseModel):
    company_name: str
    address: str
    fssai_license: str
    fssai_validity: date
    business_type: str  # manufacturer/distributor/importer/retailer
    gst_number: Optional[str] = None
    incorporation_number: Optional[str] = None

class ProductInfo(BaseModel):
    product_name: str
    category: str
    ingredients: Dict[str, Optional[float]]  # {ingredient: percentage}
    nutritional_info: Dict[str, str]  # {nutrient: value}
    allergens: List[str]
    batch_number: Optional[str] = None

class PackagingInfo(BaseModel):
    label_front_url: str  # Path to stored image/PDF
    label_back_url: str
    expiry_format: str  # e.g. "DD/MM/YYYY"
    packaging_claims: List[str]  # ["organic", "gluten-free", etc.]

class ComplianceDocument(BaseModel):
    document_type: str  # e.g. "FSSAI License", "Lab Test Report"
    file_path: str
    issue_date: date
    expiry_date: Optional[date] = None
    verified: bool = False

class CompanyData(BaseModel):
    company_info: CompanyInfo
    legal_documents: List[ComplianceDocument]
    products: List[ProductInfo]
    packaging: List[PackagingInfo]
    optional_data: Optional[Dict[str, str]] = None  # For ads/supplier info


# Configuration (absolute paths under backend/data)
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
PDF_DIR = os.path.join(DATA_DIR, "pdfs")
METADATA_FILE = os.path.join(DATA_DIR, "metadata.json")
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize vector stores
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_store = Chroma(
    collection_name="fssai_notifications",
    embedding_function=embeddings,
    persist_directory="data/vector_db"
)

# Company data stored as JSON only (no vector DB per requirements)

def load_metadata() -> List[Dict]:
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_metadata(metadata: List[Dict]):
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

def get_pdf_filename(url: str, title: str) -> str:
    """Generate consistent PDF filename from URL and title"""
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    # Clean title to make it filesystem-safe
    clean_title = re.sub(r'[^\w\-_\. ]', '_', title)[:50]
    return f"{clean_title}_{url_hash}.pdf"

def extract_date_from_text(text: str) -> str:
    """Extract date from text like '[Uploaded on : 14-08-2025]'"""
    match = re.search(r'\[Uploaded on : (\d{2}-\d{2}-\d{4})\]', text)
    if match:
        return match.group(1)
    return "Unknown"

def scrape_fssai_notifications() -> List[Dict]:
    """Scrape FSSAI notifications page for PDF documents"""
    base_url = "https://www.fssai.gov.in/notifications.php"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        notifications = []
        
        # First page
        notifications.extend(scrape_fssai_page(base_url, headers))
        
        # If you want to scrape multiple pages, you can add pagination here
        # For example, to scrape first 3 pages:
        # for page in range(2, 4):
        #     url = f"{base_url}?pages={page}"
        #     notifications.extend(scrape_fssai_page(url, headers))
        
        return notifications
        
    except Exception as e:
        print(f"Error scraping FSSAI notifications: {e}")
        return []

def scrape_fssai_page(url: str, headers: dict) -> List[Dict]:
    """Scrape a single FSSAI notifications page"""
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        notifications = []
        
        # Find all notification groups
        for group in soup.select(".grouptr12"):
            # Extract the title and date from the strong tag
            strong_tag = group.find("p").find("strong")
            if not strong_tag:
                continue
                
            full_text = strong_tag.get_text(strip=True)
            
            # Extract title (remove the ♦ symbol if present)
            title = full_text.split('♦')[-1].strip()
            
            # Extract date from the text
            date = extract_date_from_text(full_text)
            
            # Find all PDF links in this group
            for link in group.select("a[href$='.pdf']"):
                pdf_url = link["href"]
                
                # Make absolute URL if relative
                if not pdf_url.startswith("http"):
                    pdf_url = f"https://www.fssai.gov.in/{pdf_url.lstrip('/')}"
                
                notifications.append({
                    "title": title,
                    "pdf_url": pdf_url,
                    "date": date,
                    "source": "FSSAI"
                })
        
        return notifications
        
    except Exception as e:
        print(f"Error scraping FSSAI page {url}: {e}")
        return []

def download_pdf(url: str, filename: str) -> str:
    """Download PDF if not already exists"""
    path = os.path.join(PDF_DIR, filename)
    if not os.path.exists(path):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            r = requests.get(url, headers=headers, stream=True)
            r.raise_for_status()
            with open(path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        except Exception as e:
            print(f"Error downloading PDF {url}: {e}")
            return ""
    return path

def extract_text_from_pdf(path: str) -> str:
    """Extract text from PDF with error handling"""
    if not os.path.exists(path):
        return ""
        
    text = ""
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error extracting text from {path}: {e}")
    return text.strip()

def extract_text_from_file(path: str) -> str:
    """Best-effort text extraction for different file types.
    - PDF: use pdfplumber
    - TXT: read as text
    - Others: return empty string
    """
    if not path or not os.path.exists(path):
        return ""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(path)
    if ext in [".txt", ".md", ".csv"]:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""
    # Image/Docx OCR not implemented in this basic version
    return ""

def chunk_text(text: str, metadata: Dict) -> List[Document]:
    """Split text into chunks with metadata"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    
    chunks = text_splitter.split_text(text)
    documents = []
    for i, chunk in enumerate(chunks):
        doc_metadata = metadata.copy()
        doc_metadata["chunk"] = i
        documents.append(Document(page_content=chunk, metadata=doc_metadata))
    return documents

def update_vector_db() -> int:
    """Update vector DB with new notifications"""
    print("Starting update process...")
    existing_metadata = load_metadata()
    print(f"Existing metadata count: {len(existing_metadata)}")
    existing_urls = {item["pdf_url"] for item in existing_metadata}
    
    notifications = scrape_fssai_notifications()
    print(f"Found {len(notifications)} notifications")
    
    new_count = 0
    
    for notification in notifications:
        print(f"\nProcessing notification: {notification['title']}")
        
        if notification["pdf_url"] in existing_urls:
            print("Already exists, skipping")
            continue
            
        # Download and process new notification
        filename = get_pdf_filename(notification["pdf_url"], notification["title"])
        print(f"Downloading PDF to {filename}")
        pdf_path = download_pdf(notification["pdf_url"], filename)
        
        if not pdf_path:
            print("Failed to download PDF")
            continue
            
        print("Extracting text from PDF")
        text = extract_text_from_pdf(pdf_path)
        if not text:
            print("No text extracted")
            continue
            
        # Prepare metadata
        metadata = {
            "title": notification["title"],
            "date": notification["date"],
            "source": notification["source"],
            "pdf_url": notification["pdf_url"],
            "pdf_path": pdf_path,
            "document_id": hashlib.md5(notification["pdf_url"].encode()).hexdigest()
        }
        
        print("Chunking text and adding to vector store")
        documents = chunk_text(text, metadata)
        vector_store.add_documents(documents)
        
        # Update metadata
        existing_metadata.append(metadata)
        new_count += 1
        print("Successfully processed")
    
    if new_count > 0:
        print(f"Saving {new_count} new entries")
        save_metadata(existing_metadata)
        vector_store.persist()
    
    return new_count

def get_metadata_store() -> List[Dict]:
    """Get all stored metadata"""
    return load_metadata()

def _parse_date(d: str) -> datetime:
    # Try common formats used in scraping (e.g., "14-08-2025")
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(d, fmt)
        except Exception:
            continue
    return datetime.min

def get_latest_amendments(limit: int = 6) -> List[Dict]:
    """Return latest amendments with full text content by reading stored PDFs.
    Output: [{title, date, content, id}]
    """
    meta = load_metadata()
    # Sort by parsed date descending; unknown at end
    meta_sorted = sorted(meta, key=lambda m: _parse_date(m.get("date", "")), reverse=True)
    results: List[Dict] = []
    for m in meta_sorted[:limit]:
        content = extract_text_from_pdf(m.get("pdf_path", ""))
        results.append({
            "title": m.get("title", ""),
            "date": m.get("date", "Unknown"),
            "content": content,
            "id": m.get("document_id") or hashlib.md5(m.get("pdf_url", "").encode()).hexdigest()
        })
    return results

def _load_company_json(company_id: str) -> Optional[Dict]:
    path = os.path.join(DATA_DIR, "companies", f"{company_id}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return None
    return None


def sanitize_metadata(d: Dict) -> Dict:
    """Convert complex metadata values into primitives acceptable by Chroma (str/int/float/bool/None).
    - dates/datetimes -> ISO string
    - lists/dicts -> JSON string
    - others left as-is
    """
    out: Dict = {}
    for k, v in (d or {}).items():
        try:
            if v is None:
                out[k] = None
            elif isinstance(v, (date, datetime)):
                out[k] = v.isoformat()
            elif isinstance(v, (list, dict)):
                out[k] = json.dumps(v)
            else:
                out[k] = v
        except Exception:
            out[k] = str(v)
    return out

def get_company_info(company_id: str) -> Optional[Dict]:
    """Return normalized company info dict used by prompt chain"""
    data = _load_company_json(company_id)
    if not data:
        return None
    ci = data.get("company_info", {})
    optional = data.get("optional_data") or {}
    return {
        "name": ci.get("company_name", ""),
        "business_type": ci.get("business_type", ""),
        "description": optional.get("business_description", ""),
        "fssai_license": ci.get("fssai_license", ""),
        "fssai_validity": ci.get("fssai_validity", "")
    }

def get_company_products(company_id: str) -> List[Dict]:
    """Return simplified list of products expected by prompt chain"""
    data = _load_company_json(company_id) or {}
    products = data.get("products", [])
    packaging = data.get("packaging", [])
    claims_all = []
    for p in packaging:
        claims_all.extend(p.get("packaging_claims", []) or [])
    simplified = []
    for p in products:
        ingredients = list((p.get("ingredients") or {}).keys())
        simplified.append({
            "name": p.get("product_name", "Product"),
            "category": p.get("category", ""),
            "ingredients": ingredients,
            "allergens": p.get("allergens", []) or [],
            "claims": claims_all or []
        })
    return simplified

def get_company_documents(company_id: str) -> List[str]:
    """Return list of stored legal document file paths for a company"""
    data = _load_company_json(company_id) or {}
    docs = []
    for d in data.get("legal_documents", []) or []:
        if d.get("file_path"):
            docs.append(d["file_path"])
    return docs

def ingest_local_pdfs_from(dir_path: str) -> int:
    """Ingest all PDFs from a local directory as amendments with today's date.
    Returns number of new entries added.
    """
    if not os.path.isdir(dir_path):
        return 0
    existing = load_metadata()
    existing_urls = {m.get("pdf_url") for m in existing}
    new_count = 0
    for fname in os.listdir(dir_path):
        if not fname.lower().endswith(".pdf"):
            continue
        fpath = os.path.join(dir_path, fname)
        # Create a pseudo URL to dedupe
        pseudo_url = f"file://{os.path.abspath(fpath)}"
        if pseudo_url in existing_urls:
            continue
        title = os.path.splitext(fname)[0].replace('_', ' ')
        metadata = {
            "title": title,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "source": "LOCAL",
            "pdf_url": pseudo_url,
            "pdf_path": fpath,
            "document_id": hashlib.md5(pseudo_url.encode()).hexdigest(),
        }
        text = extract_text_from_pdf(fpath)
        if not text:
            continue
        docs = chunk_text(text, metadata)
        vector_store.add_documents(docs)
        existing.append(metadata)
        new_count += 1
    if new_count:
        save_metadata(existing)
        vector_store.persist()
    return new_count

def store_company_data(company_data: CompanyData):
    """Store company data as JSON only (no vector DB)."""
    # Ensure uploads in JSON refer to absolute paths where possible
    save_company_json(company_data)

def hash_company(name: str) -> str:
    return hashlib.md5(name.encode()).hexdigest()

def save_company_json(company_data: CompanyData):
    """Store complete structured data for retrieval under backend/data/companies"""
    path = os.path.join(DATA_DIR, "companies", f"{hash_company(company_data.company_info.company_name)}.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(company_data.model_dump_json(indent=2))