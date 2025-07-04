import streamlit as st
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import os
import json
from openai import OpenAI
from fpdf import FPDF

# === Groq API Setup ===
GROQ_API_KEY = "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"  # Replace with your Groq API key
client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

# === Helper: Extract text from uploaded file ===
def extract_text(uploaded_file):
    file_type = uploaded_file.name.split(".")[-1].lower()
    text = ""
    if file_type == "pdf":
        with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
    elif file_type in ["png", "jpg", "jpeg"]:
        image = Image.open(uploaded_file)
        text = pytesseract.image_to_string(image)
    return text

# === Helper: Extract info using LLM ===
def extract_deed_info(text):
    prompt = f"""
You are a legal AI assistant. Extract the following structured info from this land deed text:
- Deed Type
- Party 1 (Seller/Vendor/Lessor/Donor)
- Party 2 (Buyer/Purchaser/Lessee/Donee)
- Survey Number
- Location
- Date of Execution
- Registration Number

Return the output as raw JSON.

{text}
"""
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    try:
        content = response.choices[0].message.content
        return json.loads(content)
    except:
        return None

# === Helper: Download PDF with extracted info ===
def generate_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Land Deed Extracted Info", ln=True, align="C")
    pdf.ln(10)
    for k, v in data.items():
        pdf.set_font("Arial", "B", 12)
        pdf.cell(60, 10, txt=f"{k}:", ln=False)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(120, 10, txt=str(v))
        pdf.ln(2)
    return pdf.output(dest="S").encode("latin1")

# === Streamlit App ===
st.set_page_config(page_title="Land Deed Extractor", layout="centered")
st.markdown("""
    <div style="background-color:#2e7d32;padding:20px;border-radius:10px">
    <h1 style="color:white;text-align:center;">📜 Land Deed Info Extractor</h1>
    <p style="color:white;text-align:center;">Upload a land deed and extract structured legal data in a user-friendly format.</p>
    </div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("📁 Upload Document (PDF/Image)", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    st.success(f"{uploaded_file.name} uploaded successfully ✅")
    raw_text = extract_text(uploaded_file)
    extracted = extract_deed_info(raw_text)

    if extracted:
        col1, col2 = st.columns(2)
        for i, (key, val) in enumerate(extracted.items()):
            with col1 if i % 2 == 0 else col2:
                st.markdown(f"""
                    <div style="background-color:#f0f4c3;padding:10px;border-radius:8px;margin-bottom:10px">
                    <b>{key}:</b><br>{val}
                    </div>
                """, unsafe_allow_html=True)

        # PDF Download
        pdf_bytes = generate_pdf(extracted)
        st.download_button(
            label="📥 Download Extracted Info as PDF",
            data=pdf_bytes,
            file_name="deed_info.pdf",
            mime="application/pdf"
        )
    else:
        st.error("⚠️ Could not parse result as JSON. Try a different document or improve text clarity.")