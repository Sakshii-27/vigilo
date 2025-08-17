import os
from dotenv import load_dotenv
from groq import Groq
from typing import List, Dict, Optional
import json
from datetime import datetime
import textwrap
from vigilo_utils import (
    get_latest_amendments,
    get_company_info,
    get_company_products,
    get_company_documents,
    extract_text_from_file
)

# Load environment
load_dotenv(dotenv_path=".env.local")
API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=API_KEY) if API_KEY else None

# Model Configuration
MODEL_ANALYSIS = "deepseek-r1-distill-llama-70b"  # For initial amendment analysis
MODEL_DETAILS = "openai/gpt-oss-120b"      # For company-specific analysis
MODEL_COMPLIANCE = "openai/gpt-oss-120b"       # For detailed compliance checks
MODEL_OPTIMIZE = "meta-llama/llama-prompt-guard-2-22m"  # For final optimization

class AmendmentAnalyzer:
    def __init__(self):
        self.stage_outputs = {}
        self.current_amendments = []
        
    def log_stage(self, stage_name: str, message: str):
        """Log stage progress with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {stage_name.upper()}: {message}"
        print(log_entry)
        self.stage_outputs[stage_name] = self.stage_outputs.get(stage_name, []) + [log_entry]

    def call_groq(self, prompt: str, model: str, temperature: float = 0.3) -> str:
        """Make API call to Groq with specified model"""
        try:
            if client is None:
                # Fallback: return a minimal JSON placeholder so pipeline continues
                self.log_stage("WARN", "GROQ API key missing — using local fallback response")
                # Heuristic: return empty amendments array wrapper
                return json.dumps({"amendments": []})
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model,
                temperature=temperature,
                max_tokens=4000
            )
            return response.choices[0].message.content
        except Exception as e:
            self.log_stage("ERROR", f"Groq API call failed: {str(e)}")
            raise

    def analyze_latest_amendments(self, amendments: List[Dict]) -> List[Dict]:
        """Stage 1: Analyze and summarize latest amendments"""
        self.log_stage("STAGE 1", "Starting analysis of 5 latest amendments")
        
        amendment_texts = "\n\n".join([
            f"### {a['title']}\nDate: {a['date']}\n{a['content'][:2000]}..."
            for a in amendments[:5]
        ])
        
        prompt = f"""**Task**: Analyze these latest FSSAI amendments and provide concise summaries focusing on key compliance requirements.

**Amendments**:
{amendment_texts}

**Instructions**:
1. For each amendment, extract:
   - Purpose/scope (1 sentence)
   - Key requirements (3-5 bullet points)
   - Affected business types (manufacturer/distributor/etc.)
   - Potential impact level (High/Medium/Low)
2. Maintain original amendment titles for reference
3. Skip Hindi content if present
4. Output in this JSON format:
{{
  "amendments": [
    {{
      "title": "Original title",
      "summary": "Brief purpose",
      "requirements": ["list", "of", "key", "points"],
      "affected_businesses": ["list"],
      "impact": "High/Medium/Low"
    }}
  ]
}}"""
        
        # If API client missing, create a simple deterministic summary
        if client is None:
            self.log_stage("STAGE 1", "Using local fallback analysis for amendments")
            summaries = []
            for a in amendments[:5]:
                summaries.append({
                    "title": a.get("title", "Untitled"),
                    "summary": (a.get("content", "")[:200] + '...') if a.get("content") else a.get("title", ""),
                    "requirements": [],
                    "affected_businesses": [],
                    "impact": "Medium"
                })
            self.current_amendments = summaries
            return summaries

        response = self.call_groq(prompt, MODEL_ANALYSIS)
        self.log_stage("STAGE 1", "Received amendment analysis")
        # Try robust JSON parsing with extraction and a single retry
        parsed = self._parse_model_json(response, prompt, MODEL_ANALYSIS)
        if parsed and isinstance(parsed, dict) and parsed.get("amendments"):
            self.current_amendments = parsed["amendments"]
            return parsed["amendments"]
        # Fallback to deterministic local summaries if parsing failed
        self.log_stage("WARN", "Falling back to local amendment summaries due to parse failure")
        summaries = []
        for a in amendments[:5]:
            summaries.append({
                "title": a.get("title", "Untitled"),
                "summary": (a.get("content", "")[:200] + '...') if a.get("content") else a.get("title", ""),
                "requirements": [],
                "affected_businesses": [],
                "impact": "Medium"
            })
        self.current_amendments = summaries
        return summaries

    def filter_by_company_profile(self, company_data: Dict) -> List[Dict]:
        """Stage 2: Filter amendments relevant to company's basic profile"""
        self.log_stage("STAGE 2", f"Filtering for {company_data['name']}")
        
        amendments_text = "\n\n".join([
            f"### {a['title']}\n{a['summary']}\nAffects: {', '.join(a['affected_businesses'])}"
            for a in self.current_amendments
        ])
        
        prompt = f"""**Task**: Identify which amendments potentially affect {company_data['name']} based on their business profile.

**Company Profile**:
- Name: {company_data['name']}
- Type: {company_data['business_type']}
- Operations: {company_data['description']}
- FSSAI License: {company_data['fssai_license']} (Valid until {company_data['fssai_validity']})

**Amendments**:
{amendments_text}

**Instructions**:
1. Analyze each amendment against the company profile
2. Return ONLY amendments that COULD apply (even if uncertain)
3. For each relevant amendment, add:
   - 'relevance_reason': 1-sentence explanation
   - 'potential_impact': Brief note
4. Maintain all original amendment data
5. Output in same JSON format with added fields"""
        
        if client is None:
            self.log_stage("STAGE 2", "Using local fallback filter for company profile")
            filtered = []
            for a in self.current_amendments:
                filtered.append({**a, "relevance_reason": f"Potentially relevant to {company_data.get('business_type', 'company')}", "potential_impact": a.get('impact', 'Medium')})
            self.current_amendments = filtered
            return filtered

        response = self.call_groq(prompt, MODEL_DETAILS)
        self.log_stage("STAGE 2", "Received company filter response")
        parsed = self._parse_model_json(response, prompt, MODEL_DETAILS)
        if parsed and isinstance(parsed, dict) and parsed.get("amendments"):
            self.current_amendments = parsed["amendments"]
            return parsed["amendments"]
        self.log_stage("WARN", "Company filter parse failed; returning current amendments as-is")
        return self.current_amendments

    def check_product_compliance(self, products: List[Dict]) -> List[Dict]:
        """Stage 3: Check amendments against product details"""
        self.log_stage("STAGE 3", f"Checking {len(products)} products")
        
        products_text = "\n\n".join([
            f"### {p['name']}\nCategory: {p['category']}\n"
            f"Ingredients: {', '.join(p['ingredients'])}\n"
            f"Allergens: {', '.join(p['allergens'])}\n"
            f"Claims: {', '.join(p['claims'])}"
            for p in products
        ])
        
        amendments_text = "\n\n".join([
            f"### {a['title']}\n{a['summary']}\nRequirements:\n- " + 
            "\n- ".join(a['requirements'])
            for a in self.current_amendments
        ])
        
        prompt = f"""**Task**: Analyze how amendments affect specific products.

**Products**:
{products_text}

**Amendments**:
{amendments_text}

**Instructions**:
1. For each amendment-product pair:
   - Identify specific conflicts/requirements
   - Note any ingredient/allergen/claim issues
2. Add new 'product_impacts' array to each amendment containing:
   - product_name
   - affected_aspects: ["ingredients", "claims", etc.]
   - required_changes: Specific actions needed
3. Maintain all previous data
4. Output in enhanced JSON format"""
        
        if client is None:
            self.log_stage("STAGE 3", "Using local fallback product compliance checks")
            product_checked = []
            for a in self.current_amendments:
                a_copy = dict(a)
                a_copy["product_impacts"] = []
                for p in products:
                    a_copy["product_impacts"].append({
                        "product_name": p.get('name', 'Product'),
                        "affected_aspects": [],
                        "required_changes": []
                    })
                product_checked.append(a_copy)
            self.current_amendments = product_checked
            return product_checked

        response = self.call_groq(prompt, MODEL_COMPLIANCE, temperature=0.5)
        self.log_stage("STAGE 3", "Received product compliance response")
        parsed = self._parse_model_json(response, prompt, MODEL_COMPLIANCE)
        if parsed and isinstance(parsed, dict) and parsed.get("amendments"):
            self.current_amendments = parsed["amendments"]
            return parsed["amendments"]
        self.log_stage("WARN", "Product compliance parse failed; returning current amendments as-is")
        return self.current_amendments

    def generate_compliance_plan(self) -> Dict:
        """Stage 4: Generate final compliance action plan"""
        self.log_stage("STAGE 4", "Generating final compliance plan")
        
        amendments_text = "\n\n".join([
            f"### {a['title']}\n" +
            f"Summary: {a['summary']}\n" +
            (f"Product Impacts:\n- " + "\n- ".join(
                f"{pi['product_name']}: {pi['required_changes']}" 
                for pi in a.get('product_impacts', [])
            ) if a.get('product_impacts') else "No product impacts") + "\n" +
            f"Relevance: {a.get('relevance_reason', 'Not specified')}"
            for a in self.current_amendments
        ])
        
        prompt = f"""**Task**: Create prioritized compliance action plan.

**Relevant Amendments**:
{amendments_text}

**Instructions**:
1. Group actions by department (Legal, Product, Packaging etc.)
2. For each action:
   - Specify deadline if mentioned in amendment
   - Note urgency level (Critical/High/Medium)
   - Provide concrete steps
3. Include amendment references for each action
4. Output in this format:
{{
  "compliance_plan": {{
    "timeline": [
      {{
        "timeframe": "Immediate (1-2 weeks)",
        "actions": [
          {{
            "department": "Legal",
            "task": "Update FSSAI license",
            "amendments": ["Amendment 1 title"],
            "steps": ["File Form X", "Submit lab reports"],
            "urgency": "Critical"
          }}
        ]
      }}
    ],
    "summary": {{
      "critical_items": 3,
      "high_priority": 2,
      "total_actions": 5
    }}
  }}
}}"""
        
        if client is None:
            self.log_stage("STAGE 4", "Using local fallback to generate compliance plan")
            # Build a minimal plan referencing titles
            timeline = [
                {
                    "timeframe": "Immediate (1-2 weeks)",
                    "actions": []
                }
            ]
            for a in self.current_amendments:
                timeline[0]["actions"].append({
                    "department": "Legal",
                    "task": f"Review amendment: {a.get('title', '')}",
                    "amendments": [a.get('title', '')],
                    "steps": ["Review text", "Assess product impact", "Update documents if required"],
                    "urgency": a.get('impact', 'Medium')
                })
            plan = {"compliance_plan": {"timeline": timeline, "summary": {"critical_items": 0, "high_priority": 0, "total_actions": sum(len(t['actions']) for t in timeline)}}}
            return plan

        response = self.call_groq(prompt, MODEL_OPTIMIZE)
        self.log_stage("STAGE 4", "Received final compliance plan response")
        parsed = self._parse_model_json(response, prompt, MODEL_OPTIMIZE)
        if parsed and isinstance(parsed, dict):
            return parsed
        self.log_stage("WARN", "Compliance plan parse failed; returning minimal plan")
        return {"compliance_plan": {"status": "partial", "notes": "Parsing failed"}}

    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """Extract the first JSON object from arbitrary text by matching braces."""
        if not text or '{' not in text:
            return None
        start = text.find('{')
        depth = 0
        for i in range(start, len(text)):
            ch = text[i]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    candidate = text[start:i+1]
                    return candidate
        return None

    def _parse_model_json(self, response_text: str, original_prompt: str, model: str) -> Optional[Dict]:
        """Attempt to parse JSON from model response robustly; retry once with a stricter instruction if needed."""
        # 1) Direct parse
        try:
            return json.loads(response_text)
        except Exception:
            pass

        # 2) Strip common markdown/code fences and try again
        cleaned = response_text.strip()
        if cleaned.startswith('```') and cleaned.endswith('```'):
            cleaned = '\n'.join(cleaned.split('\n')[1:-1]).strip()
            try:
                return json.loads(cleaned)
            except Exception:
                pass

        # 3) Extract first JSON object substring
        try:
            candidate = self._extract_json_from_text(response_text)
            if candidate:
                return json.loads(candidate)
        except Exception:
            pass

        # 4) Retry once with an explicit instruction to return only JSON
        try:
            retry_prompt = original_prompt + "\n\nIMPORTANT: Respond ONLY with the valid JSON object that matches the schema above, and nothing else."
            retry_resp = self.call_groq(retry_prompt, model)
            # try same parsing steps on retry_resp
            try:
                return json.loads(retry_resp)
            except Exception:
                # try extraction
                cand = self._extract_json_from_text(retry_resp)
                if cand:
                    return json.loads(cand)
        except Exception as e:
            self.log_stage("ERROR", f"Retry parse attempt failed: {e}")

        # 5) Log the raw response for debugging
        self.log_stage("DEBUG", f"Raw model response (non-JSON): {response_text[:1000]}")
        return None

    def run_full_analysis(
        self, 
        amendments: List[Dict], 
        company_data: Dict, 
        products: List[Dict]
    ) -> Dict:
        """Execute complete analysis pipeline"""
        self.log_stage("START", f"Beginning analysis for {company_data['name']}")
        
        # Stage 1: Amendment analysis
        analyzed_amendments = self.analyze_latest_amendments(amendments)
        
        # Stage 2: Company profile filter
        profile_filtered = self.filter_by_company_profile(company_data)
        
        # Stage 3: Product compliance check
        product_checked = self.check_product_compliance(products)
        
        # Stage 4: Final compliance plan
        compliance_plan = self.generate_compliance_plan()
        
        self.log_stage("COMPLETE", "Analysis finished successfully")
        
        return {
            "analysis_steps": self.stage_outputs,
            "initial_amendments": len(amendments),
            "relevant_amendments": len(product_checked),
            "compliance_plan": compliance_plan,
            "detailed_amendments": product_checked
        }

# Example Usage
if __name__ == "__main__":
    analyzer = AmendmentAnalyzer()
    
    # Mock data - replace with actual data loading
    mock_amendments = [
        {
            "title": "Food Safety (Packaging) Amendment 2025",
            "date": "2025-08-15",
            "content": "New rules for recycled plastics in food packaging..."
        },
        # Add 4 more mock amendments
    ]
    
    mock_company = {
        "name": "Healthy Foods Inc",
        "business_type": "manufacturer",
        "description": "Organic snack manufacturing",
        "fssai_license": "ABCD123456",
        "fssai_validity": "2026-12-31"
    }
    
    mock_products = [
        {
            "name": "Organic Protein Bars",
            "category": "snacks",
            "ingredients": ["organic dates", "pea protein", "almonds"],
            "allergens": ["nuts"],
            "claims": ["organic", "gluten-free"]
        }
    ]
    
    results = analyzer.run_full_analysis(
        amendments=mock_amendments,
        company_data=mock_company,
        products=mock_products
    )
    
    print("\nFinal Compliance Plan:")
    print(json.dumps(results["compliance_plan"], indent=2))