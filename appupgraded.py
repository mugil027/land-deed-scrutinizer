import streamlit as st
from PIL import Image
import fitz  # PyMuPDF
import pytesseract
import json
from openai import OpenAI
import re

# === CONFIG ===
GROQ_API_KEY = "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"  # Replace with your Groq API key
client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

# === FUNCTION: Extract text from file ===
def extract_text(file):
    if file.name.endswith(".pdf"):
        doc = fitz.open(stream=file.read(), filetype="pdf")
        full_text = " ".join(page.get_text() for page in doc)
    else:
        image = Image.open(file)
        image = image.convert("L")  # Convert to grayscale
        full_text = pytesseract.image_to_string(image, lang="kan+eng", config="--psm 6")
    return full_text

# === FUNCTION: Clean raw text ===
def clean_text(raw):
    return " ".join([line.strip() for line in raw.splitlines() if line.strip()])

# === FUNCTION: Detect Kannada text ===
def is_kannada(text):
    return bool(re.search(r'[\u0C80-\u0CFF]', text))  # Kannada Unicode range

# === FUNCTION: Detect Deed Type ===
def detect_deed_type(text):
    deed_types = ["Sale Deed", "Gift Deed", "Mortgage Deed", "Release Deed", "Lease Deed", "Partition Deed"]
    for deed in deed_types:
        if deed.lower() in text.lower():
            return deed
    return "Not Found"

# === FUNCTION: Translate Kannada to English ===
def translate_kannada_to_english(text):
    prompt = f"Translate the following Kannada legal document into English:\n\n{text}"
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content.strip()

# === FUNCTION: Extract deed info using LLM ===
def extract_deed_info(cleaned_text, detected_type):
    prompt = f"""
You are a legal assistant. Your task is to extract clearly present legal details from an Indian land deed.

The deed type detected from text is: **{detected_type}**

Please return only this markdown table:

| Field               | Detail                      |
|---------------------|-----------------------------|
| Deed Type           |                             |
| Party 1             |                             |
| Party 2             |                             |
| Survey Number       |                             |
| Location            |                             |
| Date of Execution   |                             |
| Registration Number |                             |

⚠️ Instructions:
- Do NOT guess or assume any values.
- Use the detected deed type unless the actual text clearly says otherwise.
- Replace 'Party 1' as seller/vendor/lessor/donor, and 'Party 2' as buyer/purchaser/lessee/donee based on the deed type.
- If any field is missing or unclear, write "Not Found".
- If the document was in Kannada, assume it has been translated already.

Deed Text:
{cleaned_text}
"""
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content

# === STREAMLIT UI ===
st.set_page_config(page_title="🧾 Land Deed Scrutinizer", layout="wide")

with st.container():
    st.markdown("""
        <div style='background-color: #2E7D32; padding: 1.5rem; border-radius: 10px;'>
            <h1 style='color: white; text-align: center;'>📜 Land Deed Info Extractor</h1>
            <h3 style='color: white; text-align: center;'>Built by Mugil M with ❤️ using Streamlit and Groq AI</h3>
            <p style='color: white; text-align: center;'>Upload a land deed (PDF or image) and extract structured legal information, even from Kannada documents.</p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

col1, col2 = st.columns([1, 2])

with col1:
    uploaded_file = st.file_uploader("📁 Upload Document (PDF/Image)", type=["pdf", "png", "jpg", "jpeg"])

    if uploaded_file:
        st.success(f"✅ {uploaded_file.name} uploaded successfully")

        if uploaded_file.name.endswith(".pdf"):
            st.info("📄 PDF detected")
        else:
            st.image(uploaded_file, width=300)

with col2:
    if uploaded_file:
        with st.spinner("🔍 Reading and analyzing document..."):
            raw_text = extract_text(uploaded_file)
            cleaned_text = clean_text(raw_text)

            if is_kannada(cleaned_text):
                st.info("🌐 Kannada document detected. Translating to English...")
                translated_text = translate_kannada_to_english(cleaned_text)
                final_text = translated_text
            else:
                final_text = cleaned_text

            detected_type = detect_deed_type(final_text)
            result = extract_deed_info(final_text, detected_type)

        if result:
            st.success("✅ Extraction Complete")
            st.markdown("### 🧾 Extracted Land Deed Information")
            st.markdown(result, unsafe_allow_html=True)
        else:
            st.warning("⚠️ No data extracted.")
    else:
        st.warning("📂 Please upload a land deed file to proceed.")

# === Optional Footer ===
st.markdown("""
    <hr>
    <p style='text-align: center; color: gray;'>Built by Mugil M with ❤️ using Streamlit and Groq AI</p>
""", unsafe_allow_html=True)
