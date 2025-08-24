# Vigilo – Your AI-Powered Compliance Guardian

## Overview

**Tired of drowning in endless paperwork and chasing compliance deadlines?**  
Vigilo is here to change that. No more missed deadlines. No surprise penalties. Just seamless, automated compliance.

Vigilo is an agentic AI compliance assistant that continuously monitors official regulatory sources (e.g., FSSAI, SEBI, IT Acts) and draft bills, interprets changes in plain language, and maps them to your company’s real context using RAG and vector matching. It generates clear action items and checklists, triggers automated workflows via your existing systems (ERP/HR/Finance/Email/Slack), and maintains an audit-ready evidence trail. A customizable dashboard highlights risk, impact, and deadlines so teams catch changes early and stay compliant in real time.

## Key Features

1. **Proactive Regulation Scanning**

   - Monitors government portals, draft bills, and regulatory bodies (India & global).
   - Notifies companies of upcoming changes before enforcement deadlines.

2. **AI-Powered Summarisation & Interpretation**

   - Converts complex legal jargon into easy-to-understand summaries.
   - Provides clear, actionable insights tailored to business needs.

3. **Automated Compliance Actions**

   - Smart workflows trigger tasks, checklists, or policy updates automatically.
   - Integrates with ERP, HR, and finance tools for seamless execution.

4. **Customisable Regulatory Dashboard**

   - Sector-specific filters (finance, healthcare, pharma, legal, etc.).
   - Risk-level indicators (High / Medium / Low urgency).

5. **Audit-Ready Compliance Logs**
   - Maintains detailed evidence trails for audits.
   - Reduces preparation time & ensures transparency.

## Technical Workflow – How Vigilo Works

1. **Ingest & Classify**

   - AI scans company data (policies, contracts, product designs).
   - Classifies by domain (Food, IT, Pharma, etc.).

2. **Amendment Intelligence**

   - Continuously fetches latest regulations (FSSAI, SEBI, IT Acts).
   - Uses **RAG + LangChain** to analyze and summarize updates.

3. **Vector Matching & Relevance Check**

   - Embeds company data into a vector database.
   - Cross-matches amendments against policies, product designs, and labels to detect non-compliance risks.

4. **Layered AI Analysis (Prompt Chain)**

   - **AI-1**: Product design & labeling compliance.
   - **AI-2**: Legal contracts & policy compliance.
   - **AI-3**: Operational / HR / Finance compliance.
   - Each stage flags gaps and feeds results into the next.

5. **Roadmap Generator**

   - Produces a compliance report with actions, deadlines, and penalties avoided.
   - Powered by **LangGraph reasoning**.

6. **Proactive Alerts**
   - Real-time notifications via **MCP + Gmail API**.
   - Ensures no compliance deadlines are missed.

## Tech Stack

### 1. AI & Automation

- **LLMs**: GPT OSS / DeepSeek-r1-distill-LLaMA-70B / LLaMA models – Legal document summarization & interpretation
- **RAG**: Vector DBs (FAISS, Chroma) – Retrieve regulations & insights
- **MCP (Model Context Protocol)** – Bridge to APIs & notifications
- **LangChain / AutoGen** – Multi-agent orchestration
- **NLP Pipelines**: spaCy, Hugging Face Transformers – Rule/entity extraction

### 2. Backend & Processing

- Python / Node.js – Core logic & API integration
- FastAPI – Lightweight backend
- Celery / Airflow – Scheduling scans & checks

### 3. Data Sources & Integration

- Government portals (APIs / scraping) – Real-time regulatory updates
- Firebase – Compliance history & audit logs
- ERP / CRM / Slack / Email APIs – Compliance alerts to teams

### 4. Frontend & UX

- Next.js – Compliance monitoring dashboard
- TailwindCSS – Clean, professional UI

## ⚙️ Setup Instructions

```bash
# Clone the repo
git clone https://github.com/yourusername/vigilo.git
cd vigilo

# Install dependencies
npm install

# Run development server
npm run dev

---
✨ Stop stressing. *Start trusting Vigilo.*
Your compliance, simplified.
```
