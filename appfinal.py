import streamlit as st
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import os
from openai import OpenAI
import json

# === Set your Groq API key ===
GROQ_API_KEY = "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"  # Replace with your actual key
client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

# === Extract text from uploaded file ===
def extract_text(file):
    if file.name.endswith(".pdf"):
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    else:
        image = Image.open(file)
        return pytesseract.image_to_string(image)

# === Clean and format the text ===
def clean_text(raw):
    lines = raw.splitlines()
    lines = [line.strip() for line in lines if line.strip()]
    return " ".join(lines)

# === Extract key legal fields using LLM ===
def extract_deed_info(cleaned_text):
    prompt = f"""
You are an intelligent assistant specialized in Indian legal land records.

Extract the following fields from the land deed text below:

- Deed Type
- Buyer Name
- Seller Name
- Survey Number
- Location
- Date of Execution
- Registration Number

Return ONLY a valid JSON response with those fields and values.

Text:
{cleaned_text}
"""
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content

# === Streamlit UI ===
st.set_page_config(page_title="Land Deed Scrutinizer", layout="centered")
st.title("📜 Land Deed Info Extractor (Groq AI)")
st.markdown("Upload a scanned **PDF** or **image** of a land deed to extract structured legal info.")

uploaded_file = st.file_uploader("Upload your deed file", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file is not None:
    with st.spinner("🔍 Extracting text from file..."):
        raw_text = extract_text(uploaded_file)
        cleaned = clean_text(raw_text)

    with st.spinner("🤖 Analyzing with Groq's LLaMA-3 model..."):
        output = extract_deed_info(cleaned)

    try:
        parsed_output = json.loads(output)
        st.success("✅ Extraction complete!")
        st.json(parsed_output)
    except Exception as e:
        st.error("⚠️ Could not parse AI output as JSON.")
        st.text(output)
