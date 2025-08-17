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

# Configuration
PDF_DIR = "data/pdfs"
METADATA_FILE = "data/metadata.json"
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)

# Initialize vector store
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_store = Chroma(
    collection_name="fssai_notifications",
    embedding_function=embeddings,
    persist_directory="data/vector_db"
)

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