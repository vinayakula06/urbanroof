# DDR Report Generator

An AI-powered system that converts property inspection + thermal PDF documents into a structured, client-ready **Detailed Diagnostic Report (DDR)** — complete with embedded images and professional formatting.

## Live Demo
🌐 **[Live App →](https://urbanroof-9vi2vlj4txpk4uw7ys8ne5.streamlit.app/)**  
📁 **[GitHub Repo →](https://github.com/vinayakula06/urbanroof)**

---

## What It Does

Accepts two PDF documents:
- **Inspection Report** — site observations, structural condition, and issue descriptions
- **Thermal Report** — temperature readings and thermal imaging findings

Produces a professional **PDF DDR** containing:
1. Cover Page & Property Summary
2. Client Details & Site Description
3. Area-wise Observations (with embedded relevant images)
4. Thermal & Visual Reference Sections (side-by-side image pairs)
5. Root Cause Analysis
6. Severity Assessment (Critical / High / Medium / Low)
7. Recommended Actions (Immediate / Short-term / Long-term)
8. Structural Condition Table (Good / Moderate / Poor)
9. Bathroom, Balcony & Terrace Input Tables
10. Analysis & Therapy Recommendations
11. Summary Table (Negative & Positive findings)
12. Additional Notes & Missing/Unclear Information

---

## System Architecture

```
User uploads PDFs (Inspection + Thermal)
             ↓
  PDF Extractor  (extractor.py — PyMuPDF)
    → Extracts full text per page
    → Extracts all images (skips tiny artifacts < 8 KB)
    → Identifies image captions from surrounding text blocks
    → Returns structured dict: {full_text, images[]}
             ↓
  AI Processor  (ai_processor.py — Hugging Face Router API)
    → Clips text to 25,000 chars per document
    → Selects up to 8 representative images
    → Calls https://router.huggingface.co/v1/chat/completions
    → Tries fallback models in order until one succeeds:
         1. meta-llama/Llama-3.3-70B-Instruct  (groq)
         2. meta-llama/Llama-3.1-8B-Instruct   (cerebras)
         3. Qwen/Qwen2.5-72B-Instruct          (novita)
         4. Qwen/Qwen2.5-72B-Instruct          (together)
         5. meta-llama/Llama-3.1-8B-Instruct   (novita)
         6. mistralai/Mistral-7B-Instruct-v0.3 (featherless-ai)
    → Returns structured DDR JSON (see schema below)
             ↓
  Report Generator  (report_generator.py — ReportLab)
    → Builds professional branded PDF
    → Renders all DDR sections with tables and styled paragraphs
    → Embeds images under the correct sections
    → Side-by-side visual + thermal image pairs
    → Structural condition checkbox table with legend
    → Outputs downloadable PDF bytes
```

---

## DDR JSON Schema (AI Output)

```json
{
  "property_summary":          { "property_name", "inspection_date", "inspector", "overview" },
  "client_details":            { "customer_name", "email", "contact_no", "case_no", "date_of_inspection", ... },
  "site_description":          { "site_address", "type_of_structure", "floors", "age_of_building", ... },
  "sources_of_leakage_summary": "string",
  "bathroom_inputs":           { "input_1_1" .. "input_1_9" },
  "balcony_inputs":            { "input_1_10" .. "input_1_18" },
  "terrace_inputs":            { "input_1_19" .. "input_1_22", "terrace_condition_*_pct" },
  "external_wall_inputs":      { "input_1_24" .. "input_1_27", "paint_type" },
  "structural_condition_items": [ { "sr", "input_type", "good", "moderate", "poor", "na", "remarks" } ],
  "analysis_therapies":        [ { "title", "description" } ],
  "further_possibilities":     "string",
  "summary_table":             { "negative_side": [...], "positive_side": [...] },
  "thermal_references":        [ { "section_id", "section_title", "image_title", "relevant_image_indices" } ],
  "visual_references":         [ { "section_id", "section_title", "description", "image_title", "relevant_image_indices" } ],
  "area_observations":         [ { "area", "observations", "thermal_findings", "relevant_image_indices" } ],
  "root_causes":               [ { "issue", "probable_cause", "supporting_evidence" } ],
  "severity_assessment":       [ { "issue", "severity", "reasoning", "affected_area", "relevant_image_indices" } ],
  "recommended_actions":       [ { "priority", "action", "area", "estimated_urgency" } ],
  "additional_notes":          [ "..." ],
  "missing_or_unclear":        [ { "field", "impact" } ],
  "image_assignments":         [ { "image_index", "section", "area_or_issue", "description" } ]
}
```

---

## Local Setup

```bash
git clone https://github.com/your-username/ddr-report-generator
cd ddr-report-generator

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

### Get a Hugging Face Token

1. Sign up / log in at [huggingface.co](https://huggingface.co)
2. Go to **Settings → Access Tokens → New Token**
3. Enable **"Make calls to Inference Providers"** permission
4. Enable at least one free provider at [huggingface.co/settings/inference-providers](https://huggingface.co/settings/inference-providers)  
   *(Cerebras, Together, Novita, Groq are all free-tier)*

```bash
# Set your HF token (optional — can also enter in the app sidebar)
$env:HF_TOKEN="hf_..."          # Windows PowerShell
export HF_TOKEN=hf_...          # macOS/Linux

streamlit run app.py
```

Then open **http://localhost:8501**

---

## Deploy to Streamlit Cloud (Free Hosting)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo, set main file as `app.py`
4. Add secret: `HF_TOKEN = "hf_..."`
5. Deploy → get a live URL

---

## Key Design Decisions

### Why Hugging Face Router API?
The HF Router (`router.huggingface.co/v1`) provides a unified OpenAI-compatible endpoint that automatically routes requests to the fastest available free inference provider (Groq, Cerebras, Together, Novita, Featherless). This means no single point of failure — if one provider is rate-limited or unavailable, the next model in the fallback list is tried automatically.

### Why multiple fallback models?
Free-tier inference providers have per-model rate limits. The fallback chain (6 models across multiple providers) ensures the app remains functional without a paid subscription.

### Why PyMuPDF for extraction?
Fastest Python PDF library; accurately extracts images with their coordinates, enabling caption detection by reading surrounding text blocks.

### Handling imperfect data
- Conflicting info between documents → explicitly flagged in output
- Missing fields → written as "Not Available" (never invented)
- Images without clear context → labeled with page/source and assigned via `image_assignments`

---

## Limitations & Future Improvements

- **Limitations:**
  - Free-tier models have token and rate limits; very large PDFs (>100 pages) may be clipped to 25,000 chars
  - Handwritten text in scans may not extract cleanly without OCR
  - Image quality dependent on source PDF resolution
  - JSON output quality varies by model; smaller models may omit some schema fields

- **Future improvements:**
  - OCR support for scanned documents (Tesseract)
  - Multi-language support
  - Web-based HTML report viewer
  - Database storage for report history
  - Batch processing of multiple property reports
  - Support for paid HF Inference Endpoints for higher quality / longer context

---

## Tech Stack

| Component | Technology |
|---|---|
| UI | Streamlit |
| PDF parsing | PyMuPDF (fitz) |
| AI analysis | Hugging Face Router API (Llama 3.3 70B, Qwen 2.5 72B, Mistral 7B) |
| HTTP client | requests |
| Report generation | ReportLab |
| Image processing | Pillow |
| Hosting | Streamlit Cloud |

---

## File Structure

```
├── app.py               # Streamlit UI — file upload, token input, PDF download
├── extractor.py         # PDF text + image extraction (PyMuPDF)
├── ai_processor.py      # HF Router API calls, fallback model logic, JSON parsing
├── report_generator.py  # ReportLab PDF builder — all DDR sections + styling
├── requirements.txt     # Python dependencies
└── README.md
