from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from vigilo_utils import update_vector_db, get_metadata_store
from typing import List, Dict

app = FastAPI(title="Vigilo FSSAI Compliance API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)