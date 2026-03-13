"""
ai_processor.py
Sends extracted document content to Hugging Face Router API and returns structured DDR JSON.
Uses the NEW router.huggingface.co/v1 endpoint (updated March 2026).
"""

import json
import re
import requests

# ── Correct HF Router endpoint (new as of 2025) ──────────────────────────────
HF_ROUTER_URL = "https://router.huggingface.co/v1/chat/completions"

# Models with :provider suffix — auto-routes to fastest free provider
HF_FALLBACK_MODELS = [
    "meta-llama/Llama-3.3-70B-Instruct:groq",
    "meta-llama/Llama-3.1-8B-Instruct:cerebras",
    "Qwen/Qwen2.5-72B-Instruct:novita",
    "Qwen/Qwen2.5-72B-Instruct:together",
    "meta-llama/Llama-3.1-8B-Instruct:novita",
    "mistralai/Mistral-7B-Instruct-v0.3:featherless-ai",
]

DDR_SYSTEM_PROMPT = """You are an expert property inspection analyst who creates Detailed Diagnostic Reports (DDR) for clients.

You will receive:
1. Text content from an Inspection Report
2. Text content from a Thermal Report
3. Image references extracted from both reports (labeled with source and page number)

Your task is to analyze all content and generate a comprehensive, client-friendly DDR.

CRITICAL RULES:
- Do NOT invent or assume facts not present in the documents
- If information conflicts between documents, explicitly mention the conflict
- If information is missing, write "Not Available"
- Use simple, clear language suitable for property owners
- Avoid duplicate points across sections

Return ONLY valid JSON, no markdown, no preamble, no explanation:

{
  "property_summary": {
    "property_name": "string or Not Available",
    "inspection_date": "string or Not Available",
    "inspector": "string or Not Available",
    "overview": "2-4 sentence plain English summary"
  },
  "client_details": {
    "customer_name": "Client name or flat number or Not Available",
    "customer_address": "Full property address or Not Available",
    "customer_email": "Email address or Not Available",
    "customer_contact": "Phone number or Not Available",
    "case_no": "Case/report number from documents or DNR-",
    "date_of_inspection": "DD/MM/YYYY or Not Available",
    "time_of_inspection": "HH:MM or Not Available",
    "inspected_by": "Inspector name or Not Available",
    "site_address": "Full site address or Not Available",
    "structure_type": "Apartment/Row House/Bungalow/etc or Not Available",
    "floors": "Number of floors or Not Available",
    "year_of_construction": "Year or Not Available",
    "building_age": "Age in years or Not Available",
    "previous_audit": "Yes/No or Not Available",
    "previous_repairs": "Yes/No or brief description or Not Available"
  },
  "area_observations": [
    {
      "area": "Area/room name",
      "observations": ["observation 1", "observation 2"],
      "thermal_findings": "Thermal data or Not Available",
      "relevant_image_indices": [0, 2]
    }
  ],
  "root_causes": [
    {
      "issue": "Issue title",
      "probable_cause": "Explanation",
      "supporting_evidence": "Evidence from documents"
    }
  ],
  "severity_assessment": [
    {
      "issue": "Issue title",
      "severity": "Critical | High | Medium | Low",
      "reasoning": "Why this severity level",
      "affected_area": "Where",
      "relevant_image_indices": []
    }
  ],
  "recommended_actions": [
    {
      "priority": "Immediate | Short-term | Long-term",
      "action": "What to do",
      "area": "Where",
      "estimated_urgency": "e.g. Within 24 hours / Within 1 month / Planned maintenance"
    }
  ],
  "additional_notes": ["Note 1", "Note 2"],
  "missing_or_unclear": [
    {
      "field": "What is missing",
      "impact": "Why it matters"
    }
  ],
  "image_assignments": [
    {
      "image_index": 0,
      "section": "area_observations | severity_assessment | root_causes | additional_notes",
      "area_or_issue": "Which area or issue this image belongs to",
      "description": "What this image shows"
    }
  ]
}"""


def generate_ddr(
    inspection_text: str,
    thermal_text: str,
    all_images: list,
    api_key: str
) -> dict:
    if not api_key or not api_key.startswith("hf_"):
        raise ValueError(
            "Invalid API key. Provide a Hugging Face token starting with 'hf_'.\n"
            "Get one free at: https://huggingface.co/settings/tokens"
        )

    inspection_clip, thermal_clip, filtered_images = _prepare_inputs(
        inspection_text=inspection_text,
        thermal_text=thermal_text,
        all_images=all_images,
    )

    raw_text = _call_hf_router(
        inspection_text=inspection_clip,
        thermal_text=thermal_clip,
        all_images=all_images,
        filtered_images=filtered_images,
        api_key=api_key,
    )

    return _parse_json(raw_text)


def _prepare_inputs(inspection_text: str, thermal_text: str, all_images: list):
    MAX_TEXT_CHARS = 25_000
    MAX_IMAGES = 8

    filtered_images = []
    if all_images:
        qualified = [img for img in all_images if len(img.get("bytes", b"")) > 8000]
        if not qualified:
            qualified = all_images
        if len(qualified) > MAX_IMAGES:
            step = len(qualified) / MAX_IMAGES
            filtered_images = [qualified[int(i * step)] for i in range(MAX_IMAGES)]
        else:
            filtered_images = qualified

    return (
        inspection_text[:MAX_TEXT_CHARS],
        thermal_text[:MAX_TEXT_CHARS],
        filtered_images,
    )


def _build_prompt(inspection_text, thermal_text, all_images, filtered_images):
    image_context = ""
    if filtered_images:
        lines = [
            f"[Image {idx}] source={img.get('doc_label','doc')} "
            f"page={img.get('page','?')} caption={img.get('caption','N/A')}"
            for idx, img in enumerate(filtered_images)
        ]
        image_context = (
            f"\n\n=== DOCUMENT IMAGES ({len(filtered_images)} of {len(all_images)} total) ===\n"
            + "\n".join(lines)
        )

    return (
        f"=== INSPECTION REPORT ===\n\n{inspection_text}\n\n"
        f"=== THERMAL REPORT ===\n\n{thermal_text}"
        f"{image_context}\n\n"
        "Generate the complete DDR JSON now. Return ONLY the JSON object, nothing else."
    )


def _call_hf_router(inspection_text, thermal_text, all_images, filtered_images, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    user_prompt = _build_prompt(inspection_text, thermal_text, all_images, filtered_images)

    errors = []
    for model in HF_FALLBACK_MODELS:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": DDR_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 3000,
        }

        try:
            resp = requests.post(HF_ROUTER_URL, headers=headers, json=payload, timeout=180)
        except requests.exceptions.Timeout:
            errors.append(f"{model} → timeout")
            continue
        except requests.exceptions.ConnectionError as e:
            errors.append(f"{model} → connection error: {str(e)[:80]}")
            continue

        if resp.status_code == 200:
            text = _extract_text(resp.json())
            if text:
                return text
            errors.append(f"{model} → empty response")
            continue

        if resp.status_code == 401:
            raise ValueError(
                "Token rejected (401). Make sure your HF token has "
                "'Make calls to Inference Providers' permission enabled.\n"
                "https://huggingface.co/settings/tokens"
            )

        if resp.status_code in (402, 403):
            errors.append(f"{model} → {resp.status_code} (need to enable provider in HF settings)")
            continue

        if resp.status_code == 429:
            errors.append(f"{model} → 429 rate limited, trying next")
            continue

        if resp.status_code == 503:
            errors.append(f"{model} → 503 model loading")
            continue

        errors.append(f"{model} → {resp.status_code}: {resp.text[:150]}")

    raise ValueError(
        "All models failed. Errors:\n"
        + "\n".join(f"  • {e}" for e in errors)
        + "\n\nTo fix:\n"
        "  1. Go to https://huggingface.co/settings/inference-providers\n"
        "  2. Enable at least one provider (Nebius, Together, or Cerebras are free)\n"
        "  3. Make sure your token has 'Make calls to Inference Providers' checked"
    )


def _extract_text(data: dict) -> str:
    choices = data.get("choices", [])
    if choices:
        content = choices[0].get("message", {}).get("content", "")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            return "".join(b.get("text", "") for b in content if isinstance(b, dict)).strip()
    for key in ("generated_text", "text"):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def _parse_json(raw_text: str) -> dict:
    text = re.sub(r"^```json\s*", "", raw_text.strip())
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

    raise ValueError(
        f"Model did not return valid JSON.\nFirst 500 chars:\n{raw_text[:500]}"
    )