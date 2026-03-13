"""
extractor.py
Extracts text and images from inspection/thermal PDF documents using PyMuPDF.
"""

import fitz  # PyMuPDF
import base64
import io
from pathlib import Path


def extract_from_pdf(pdf_bytes: bytes, doc_label: str = "document") -> dict:
    """
    Extract all text and images from a PDF.

    Returns:
        {
            "label": str,
            "pages": [{"page_num": int, "text": str, "images": [...]}],
            "full_text": str,
            "images": [{"page": int, "index": int, "base64": str, "ext": str, "caption": str}]
        }
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    result = {
        "label": doc_label,
        "pages": [],
        "full_text": "",
        "images": []
    }

    all_text_parts = []
    img_global_index = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_text = page.get_text("text").strip()
        all_text_parts.append(f"[Page {page_num + 1}]\n{page_text}")

        page_images = []
        image_list = page.get_images(full=True)

        for img_idx, img_info in enumerate(image_list):
            xref = img_info[0]
            try:
                base_image = doc.extract_image(xref)
                img_bytes = base_image["image"]
                img_ext = base_image["ext"]

                # Skip very small images (icons/artifacts)
                if len(img_bytes) < 5000:
                    continue

                # Convert to base64
                img_b64 = base64.b64encode(img_bytes).decode("utf-8")

                # Try to find nearby text as caption
                nearby_text = _get_nearby_text(page, img_info, image_list)

                img_entry = {
                    "page": page_num + 1,
                    "index": img_global_index,
                    "base64": img_b64,
                    "ext": img_ext,
                    "bytes": img_bytes,
                    "caption": nearby_text or f"Image {img_global_index + 1} from page {page_num + 1}",
                    "doc_label": doc_label
                }

                result["images"].append(img_entry)
                page_images.append(img_global_index)
                img_global_index += 1

            except Exception:
                continue

        result["pages"].append({
            "page_num": page_num + 1,
            "text": page_text,
            "image_indices": page_images
        })

    result["full_text"] = "\n\n".join(all_text_parts)
    doc.close()
    return result


def _get_nearby_text(page, img_info, all_images) -> str:
    """Extract text near an image on the page as a potential caption."""
    try:
        # Get image bounding box from the page
        for img_block in page.get_text("dict")["blocks"]:
            if img_block.get("type") == 1:  # image block
                bbox = img_block.get("bbox", None)
                if bbox:
                    # Look for text just below the image
                    search_rect = fitz.Rect(bbox[0], bbox[3], bbox[2], bbox[3] + 40)
                    nearby = page.get_text("text", clip=search_rect).strip()
                    if nearby and len(nearby) > 3:
                        return nearby[:120]
    except Exception:
        pass
    return ""


def images_to_api_content(images: list) -> list:
    """
    Convert extracted images into Anthropic API message content format.
    Each image becomes an image content block with a text label.
    """
    content = []
    for img in images:
        ext = img["ext"].lower()
        media_type_map = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp"
        }
        media_type = media_type_map.get(ext, "image/jpeg")

        content.append({
            "type": "text",
            "text": f"[Image {img['index'] + 1} from {img['doc_label']}, Page {img['page']}] Caption: {img['caption']}"
        })
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": img["base64"]
            }
        })

    return content
