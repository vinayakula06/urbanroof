"""
app.py
Streamlit web app for DDR (Detailed Diagnostic Report) Generation.
"""

import streamlit as st
import os
import json
import traceback
from extractor import extract_from_pdf
from ai_processor import generate_ddr
from report_generator import generate_pdf

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DDR Report Generator",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg, #1A2E4A 0%, #2C5282 100%);
    color: white;
    padding: 2rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    text-align: center;
}
.step-card {
    background: #F5F7FA;
    border: 1px solid #D0D7E3;
    border-radius: 8px;
    padding: 1rem;
    margin: 0.5rem 0;
}
.success-box {
    background: #D4EDDA;
    border: 1px solid #C3E6CB;
    border-radius: 8px;
    padding: 1rem;
    color: #155724;
}
.error-box {
    background: #F8D7DA;
    border: 1px solid #F5C6CB;
    border-radius: 8px;
    padding: 1rem;
    color: #721C24;
}
.info-box {
    background: #CCE5FF;
    border: 1px solid #B8DAFF;
    border-radius: 8px;
    padding: 0.8rem;
    color: #004085;
    font-size: 0.9em;
}
.stat-card {
    background: white;
    border: 1px solid #D0D7E3;
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h2 style="margin:0;font-size:1.6rem;">🏠 DDR Report Generator</h2>
    <p style="margin:0.5rem 0 0;opacity:0.85;font-size:0.95rem;">
        AI-powered Detailed Diagnostic Report from Inspection + Thermal Data
    </p>
</div>
""", unsafe_allow_html=True)


# ── Sidebar: API key ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    api_key = st.text_input(
        "Hugging Face API Token",
        type="password",
        help="Use a Hugging Face token like hf_...",
        value=os.environ.get("HF_TOKEN", "") or os.environ.get("HUGGINGFACEHUB_API_TOKEN", "")
    )
    st.caption("Your key is not stored anywhere.")

    st.markdown("---")
    st.markdown("### 📋 How it works")
    st.markdown("""
1. Upload both PDF documents
2. Click **Generate DDR**
3. AI extracts & merges all data
4. Download your professional report
""")
    st.markdown("---")
    st.markdown("### 📌 DDR Sections")
    for i, s in enumerate([
        "Property Issue Summary",
        "Area-wise Observations",
        "Probable Root Cause",
        "Severity Assessment",
        "Recommended Actions",
        "Additional Notes",
        "Missing / Unclear Info"
    ], 1):
        st.caption(f"{i}. {s}")


# ── File uploads ──────────────────────────────────────────────────────────────
st.markdown("### 📁 Upload Documents")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""<div class="step-card">
        <b>📋 Inspection Report</b><br>
        <small>Main site inspection document with observations and issue descriptions</small>
    </div>""", unsafe_allow_html=True)
    inspection_file = st.file_uploader(
        "Upload Inspection PDF",
        type=["pdf"],
        key="inspection",
        label_visibility="collapsed"
    )

with col2:
    st.markdown("""<div class="step-card">
        <b>🌡️ Thermal Report</b><br>
        <small>Thermal imaging document with temperature readings and findings</small>
    </div>""", unsafe_allow_html=True)
    thermal_file = st.file_uploader(
        "Upload Thermal PDF",
        type=["pdf"],
        key="thermal",
        label_visibility="collapsed"
    )

# Show doc stats once uploaded
if inspection_file or thermal_file:
    st.markdown("### 📊 Document Preview")
    stat_cols = st.columns(2)

    if inspection_file:
        with stat_cols[0]:
            st.markdown(f"""<div class="stat-card">
                <b>📋 Inspection Report</b><br>
                <span style="color:#27AE60;font-size:1.1rem;">✓ Loaded</span><br>
                <small>{inspection_file.name}</small><br>
                <small>{round(inspection_file.size/1024, 1)} KB</small>
            </div>""", unsafe_allow_html=True)

    if thermal_file:
        with stat_cols[1]:
            st.markdown(f"""<div class="stat-card">
                <b>🌡️ Thermal Report</b><br>
                <span style="color:#27AE60;font-size:1.1rem;">✓ Loaded</span><br>
                <small>{thermal_file.name}</small><br>
                <small>{round(thermal_file.size/1024, 1)} KB</small>
            </div>""", unsafe_allow_html=True)


# ── Generate button ───────────────────────────────────────────────────────────
st.markdown("---")

ready = inspection_file is not None and thermal_file is not None and bool(api_key)

if not ready:
    missing = []
    if not inspection_file: missing.append("Inspection PDF")
    if not thermal_file: missing.append("Thermal PDF")
    if not api_key: missing.append("API Key (in sidebar)")
    st.markdown(f"""<div class="info-box">
        ℹ️ Still needed: <b>{', '.join(missing)}</b>
    </div>""", unsafe_allow_html=True)

generate_btn = st.button(
    "🚀 Generate DDR Report",
    disabled=not ready,
    use_container_width=True,
    type="primary"
)

if generate_btn:
    try:
        # Step 1: Extract PDFs
        with st.status("Processing documents...", expanded=True) as status:

            st.write("📖 Extracting Inspection Report...")
            inspection_data = extract_from_pdf(inspection_file.read(), "Inspection Report")
            st.write(f"   ✓ {len(inspection_data['pages'])} pages, {len(inspection_data['images'])} images found")

            st.write("🌡️ Extracting Thermal Report...")
            thermal_data = extract_from_pdf(thermal_file.read(), "Thermal Report")
            st.write(f"   ✓ {len(thermal_data['pages'])} pages, {len(thermal_data['images'])} images found")

            all_images = inspection_data["images"] + thermal_data["images"]
            st.write(f"   📸 Total images to embed: {len(all_images)}")

            # Step 2: AI Analysis
            st.write("🤖 Running AI analysis (this may take 30-60 seconds)...")
            ddr_data = generate_ddr(
                inspection_text=inspection_data["full_text"],
                thermal_text=thermal_data["full_text"],
                all_images=all_images,
                api_key=api_key
            )
            st.write("   ✓ AI analysis complete")

            # Step 3: Generate PDF
            st.write("📄 Building professional PDF report...")
            pdf_bytes = generate_pdf(ddr_data, all_images)
            st.write("   ✓ PDF generated successfully")

            status.update(label="✅ DDR Report ready!", state="complete", expanded=False)

        # ── Results display ────────────────────────────────────────────────
        st.markdown("""<div class="success-box">
            <b>✅ Report generated successfully!</b> Download below.
        </div>""", unsafe_allow_html=True)

        st.markdown("### 📥 Download Report")
        prop_name = ddr_data.get("property_summary", {}).get("property_name", "Property")
        filename = f"DDR_{prop_name.replace(' ', '_')}.pdf"

        st.download_button(
            label="⬇️ Download DDR Report (PDF)",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )

        # ── Preview key findings ───────────────────────────────────────────
        st.markdown("### 🔍 Report Summary Preview")

        with st.expander("📋 Property Summary", expanded=True):
            prop = ddr_data.get("property_summary", {})
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Property", prop.get("property_name", "N/A"))
                st.metric("Inspection Date", prop.get("inspection_date", "N/A"))
            with c2:
                st.metric("Inspector", prop.get("inspector", "N/A"))
                st.metric("Total Issues", len(ddr_data.get("severity_assessment", [])))
            st.info(prop.get("overview", ""))

        with st.expander("⚠️ Severity Summary"):
            severities = ddr_data.get("severity_assessment", [])
            for s in severities:
                sev = s.get("severity", "Unknown")
                color_map = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
                icon = color_map.get(sev, "⚪")
                st.markdown(f"{icon} **{s.get('issue', '')}** — {sev}")

        with st.expander("🔧 Top Recommended Actions"):
            actions = ddr_data.get("recommended_actions", [])
            for a in actions[:5]:
                priority = a.get("priority", "")
                p_icon = {"Immediate": "🚨", "Short-term": "⚡", "Long-term": "📅"}.get(priority, "▸")
                st.markdown(f"{p_icon} **[{priority}]** {a.get('area', '')}: {a.get('action', '')}")

        with st.expander("❓ Missing Information"):
            missing_items = ddr_data.get("missing_or_unclear", [])
            if missing_items:
                for m in missing_items:
                    st.markdown(f"• **{m.get('field', '')}** — {m.get('impact', '')}")
            else:
                st.success("All information was available in the source documents.")

        # Raw JSON for debugging
        with st.expander("🔬 Raw JSON (for inspection)"):
            st.json(ddr_data)

    except Exception as e:
        st.markdown(f"""<div class="error-box">
            <b>❌ Error:</b> {str(e)}<br><br>
            <details><summary>Technical details</summary>
            <pre>{traceback.format_exc()}</pre>
            </details>
        </div>""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("DDR Generator · Built with Hugging Face models · All findings based solely on uploaded documents")
