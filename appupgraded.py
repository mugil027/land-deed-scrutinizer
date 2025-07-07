import streamlit as st
from PIL import Image
import fitz  # PyMuPDF
import pytesseract
from groq import Groq
from libretranslatepy import LibreTranslateAPI

# === CONFIG ===
client = Groq(api_key="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")
translator = LibreTranslateAPI("https://libretranslate.de")

# === FUNCTION: Extract text ===
def extract_text(file):
    if file.name.endswith(".pdf"):
        doc = fitz.open(stream=file.read(), filetype="pdf")
        return " ".join(page.get_text() for page in doc)
    else:
        image = Image.open(file)
        return pytesseract.image_to_string(image, lang='kan+eng')  # Use Kannada + English OCR

# === FUNCTION: Clean text ===
def clean_text(raw):
    return " ".join([line.strip() for line in raw.splitlines() if line.strip()])

# === FUNCTION: Translate Kannada to English ===
def translate_to_english(text):
    try:
        translated = translator.translate(text, source="kn", target="en")
        return translated
    except Exception as e:
        return f"Translation error: {e}"

# === FUNCTION: Extract fields using LLM ===
def extract_deed_info(cleaned_text):
    prompt = f"""
You are a legal assistant. Extract the following information from this Indian land deed text and present it in a markdown table:

- Deed Type
- Party 1 (Seller/Vendor/Lessor/Donor)
- Party 2 (Buyer/Purchaser/Lessee/Donee)
- Survey Number
- Location
- Date of Execution
- Registration Number

📄 Please return only the markdown table like this:

| Field               | Detail                      |
|---------------------|-----------------------------|
| Deed Type           | ...                         |
| Party 1             | ...                         |
| Party 2             | ...                         |
| Survey Number       | ...                         |
| Location            | ...                         |
| Date of Execution   | ...                         |
| Registration Number | ...                         |

replace party 1 as seller, vendor, lessor or donor according to the deed and replace party 2 as buyer, purchaser, lessee or donee according to the title of the deed
Text:
{cleaned_text}
"""
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content

# === STREAMLIT UI ===
st.set_page_config(page_title="📜 Land Deed Scrutinizer", layout="wide")

with st.container():
    st.markdown("""
        <div style='background-color: #2E7D32; padding: 1.5rem; border-radius: 10px;'>
            <h1 style='color: white; text-align: center;'>📜 Land Deed Info Extractor</h1>
            <h3 style='color: white; text-align: center;'>Built by Mugil M with ❤️ using Streamlit and Groq AI</h3>
            <p style='color: white; text-align: center;'>Upload a Kannada or English land deed (PDF or image) and extract structured legal information.</p>
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
            cleaned = clean_text(raw_text)

            st.markdown("#### 📝 OCR Output")
            st.code(cleaned[:1000] + "...", language='text')

            translated_text = translate_to_english(cleaned)
            st.markdown("#### 🌐 Translated Text")
            st.code(translated_text[:1000] + "...", language='text')

            result = extract_deed_info(translated_text)

        if result:
            st.success("✅ Extraction Complete")
            st.markdown("### 📜 Extracted Land Deed Information")
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
