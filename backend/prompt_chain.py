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

# Load environment (try project root .env.local and default env)
backend_dir = os.path.dirname(__file__)
project_root_env = os.path.abspath(os.path.join(backend_dir, "..", ".env.local"))
load_dotenv(dotenv_path=project_root_env)
load_dotenv(dotenv_path=os.path.join(backend_dir, ".env.local"))
API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=API_KEY) if API_KEY else None

# Model Configuration (Groq-supported)
# Use one strong, widely available model for all stages to simplify parsing.
MODEL_ANALYSIS = "meta-llama/llama-guard-4-12b"
MODEL_DETAILS = "openai/gpt-oss-120b"
MODEL_COMPLIANCE = "openai/gpt-oss-20b"
MODEL_OPTIMIZE = "deepseek-r1-distill-llama-70b"

class AmendmentAnalyzer:
    def __init__(self):
        self.stage_outputs = {}
        self.current_amendments = []
    
    @staticmethod
    def _strip_to_json(text: str) -> str:
        """Attempt to extract a JSON object/array from a possibly wrapped reply."""
        if text is None:
            return "{}"
        t = text.strip()
        # Remove code fences if present
        if t.startswith("```"):
            t = "\n".join([line for line in t.splitlines() if not line.strip().startswith("```")])
        # Heuristic: slice from first '{' or '[' to last '}' or ']'
        start = min([pos for pos in [t.find('{'), t.find('[')] if pos != -1] or [0])
        end = max(t.rfind('}'), t.rfind(']'))
        if end != -1 and end >= start:
            return t[start:end+1]
        return t
        
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
                temperature=temperature
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
SKIP HINDI CONTENT
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
        try:
            result = json.loads(self._strip_to_json(response))
            self.current_amendments = result["amendments"]
            return result["amendments"]
        except json.JSONDecodeError:
            self.log_stage("ERROR", "Failed to parse amendment analysis JSON")
            raise

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
        try:
            result = json.loads(self._strip_to_json(response))
            self.log_stage("STAGE 2", f"Filtered to {len(result['amendments'])} potentially relevant amendments")
            self.current_amendments = result["amendments"]
            return result["amendments"]
        except json.JSONDecodeError:
            self.log_stage("ERROR", "Failed to parse company filter JSON")
            raise

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
        self.log_stage("STAGE 3", "Processed product-level impacts")
        try:
            result = json.loads(self._strip_to_json(response))
            self.current_amendments = result["amendments"]
            return result["amendments"]
        except json.JSONDecodeError:
            self.log_stage("ERROR", "Failed to parse product compliance JSON")
            raise

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
        self.log_stage("STAGE 4", "Generated final compliance plan")
        try:
            return json.loads(self._strip_to_json(response))
        except json.JSONDecodeError:
            self.log_stage("ERROR", "Failed to parse compliance plan JSON")
            raise

    def run_full_analysis(
        self, 
        amendments: List[Dict], 
        company_data: Dict, 
        products: List[Dict]
    ) -> Dict:
        """Execute complete analysis pipeline"""
        self.log_stage("START", f"Beginning analysis for {company_data['name']}")
        
        # Stage 1: Amendment analysis
        try:
            analyzed_amendments = self.analyze_latest_amendments(amendments)
        except Exception as e:
            self.log_stage("STAGE 1", f"Error: {e}. Proceeding with raw amendments summaries.")
            analyzed_amendments = [
                {
                    "title": a.get("title", "Untitled"),
                    "summary": (a.get("content", "")[:200] + "...") if a.get("content") else a.get("title", ""),
                    "requirements": [],
                    "affected_businesses": [],
                    "impact": "Medium"
                }
                for a in amendments[:5]
            ]
            self.current_amendments = analyzed_amendments
        
        # Stage 2: Company profile filter
        try:
            profile_filtered = self.filter_by_company_profile(company_data)
        except Exception as e:
            self.log_stage("STAGE 2", f"Error: {e}. Proceeding without additional filtering.")
            profile_filtered = self.current_amendments
        
        # Stage 3: Product compliance check
        try:
            product_checked = self.check_product_compliance(products)
        except Exception as e:
            self.log_stage("STAGE 3", f"Error: {e}. Proceeding without product-level impacts.")
            product_checked = []
            for a in self.current_amendments:
                a_copy = dict(a)
                a_copy["product_impacts"] = []
                product_checked.append(a_copy)
            self.current_amendments = product_checked
        
        # Stage 4: Final compliance plan
        try:
            compliance_plan = self.generate_compliance_plan()
        except Exception as e:
            self.log_stage("STAGE 4", f"Error: {e}. Returning heuristic plan.")
            # Heuristic minimal plan
            timeline = [{"timeframe": "Immediate (1-2 weeks)", "actions": []}]
            for a in self.current_amendments:
                timeline[0]["actions"].append({
                    "department": "Legal",
                    "task": f"Review amendment: {a.get('title', '')}",
                    "amendments": [a.get('title', '')],
                    "steps": ["Review text", "Assess product impact", "Update documents if required"],
                    "urgency": a.get('impact', 'Medium')
                })
            compliance_plan = {"compliance_plan": {"timeline": timeline, "summary": {"critical_items": 0, "high_priority": 0, "total_actions": sum(len(t['actions']) for t in timeline)}}}
        
        self.log_stage("COMPLETE", "Analysis finished successfully!!!")
        
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