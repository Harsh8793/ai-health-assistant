





def run():
    import streamlit as st
    import os
    from dotenv import load_dotenv
    import fitz  # PyMuPDF
    import pytesseract
    from PIL import Image
    from pdf2image import convert_from_bytes
    from openai import OpenAI
    import re
    def flag_abnormalities(text):
        highlights = []
        for key, (low, high) in NORMAL_RANGES.items():
            if key.lower() in text.lower():
                try:
                
                    pattern = rf"^{key}\s+(\d+\.?\d*)"
                    matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                    for match in matches:
                        val = float(match)
                        if val < low:
                            highlights.append(f"⚠️ {key} is low ({val})")
                        elif val > high:
                            highlights.append(f"⚠️ {key} is high ({val})")
                except:
                    continue
        return highlights

    # 🛠️ Config
    #st.set_page_config(page_title="🩺 AI Health Report Assistant", layout="centered")

    # Show welcome message once per session
    if "welcomed" not in st.session_state:
        st.session_state.welcomed = True
        st.info("👋 Welcome to the AI Health Report Assistant! Upload your report and get an easy summary.")

    # Display logo/banner
    logo_path = "assests/image.png"
    import base64
    from io import BytesIO

    def image_to_base64(image):
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

    if os.path.exists(logo_path):
        image = Image.open(logo_path)
        img_base64 = image_to_base64(image)
        st.markdown(
            f"""
            <div style="text-align: center;">
                <img src="data:image/png;base64,{img_base64}" width="200">
            </div>
            """,
            unsafe_allow_html=True
        )


    st.markdown("---")


    st.title("📄 AI-Powered Health Report Assistant")
    #st.markdown("Upload your medical report (PDF). Get an AI-generated plain summary and advice.")

    # 🔐 Load API key from .env
    load_dotenv()
    API_KEY = os.getenv("API_KEY")
    client = OpenAI(api_key=API_KEY, base_url="https://openrouter.ai/api/v1")

    # 🧠 Predefined normal ranges for flagging
    NORMAL_RANGES = {
        "Hemoglobin": (13.0, 18.0),  # Assuming male, adjust if female
        "Hematocrit (PCV)": (42.0, 52.0),  # Male
        "RBC Count": (4.00, 6.50),  # x10^6/uL  
        
        # RBC Indices
        "MCV": (78.0, 94.0),        # fL
        "MCH": (26.0, 31.0),        # pg
        "MCHC": (31.0, 36.0),       # %
        "RBC Distribution Width - CV": (11.5, 14.5),  # %

        # White Blood Corpuscles
        "Total Leukocyte Count": (4000, 11000),  # /cmm
        "Neutrophils": (40, 70),     # %
        "Lymphocytes": (20, 45),     # %
        "Eosinophils": (0, 6),       # %
        "Monocytes": (2, 10),        # %
        "Basophils": (0, 1),         # %

        # Platelets
        "Platelet Count": (150000, 450000),  # /cmm
        "Mean Platelet Volume (MPV)": (6.5, 9.8),  # fL
        "PCT": (0.150, 0.500),  # %
    }


    # 📤 File uploader
    uploaded_file = st.file_uploader("Upload your medical report (PDF)", type=["pdf"])

    # 📄 PDF Extractor
    def extract_text(pdf_file):
        try:
            # Try reading as text-based PDF
            with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
                text = ""
                for page in doc:
                    text += page.get_text()
            if text.strip():
                return text
        except Exception as e:
            st.warning("Could not extract text from PDF directly. Trying OCR...")

        # Fallback to OCR for scanned images
        try:
            pdf_file.seek(0)
            images = convert_from_bytes(pdf_file.read())
            text = ""
            for image in images:
                text += pytesseract.image_to_string(image)
            return text
        except Exception as e:
            st.error(f"OCR failed: {e}")
            return ""

    # 🧠 AI Interpretation
    def generate_summary(text):
        prompt = f"""
    You are a helpful medical assistant. Analyze the medical report text and:

    1. Extract test names and values (e.g., Glucose: 180 mg/dL).
    2. Identify abnormal values based on typical healthy ranges.
    3. Explain the significance.
    4. Offer general tips as per reports and.

    Medical Report:
    {text}

    Summary:
    """
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=[
                {"role": "system", "content": "You are a medical assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()




    # 🚀 Main Logic
    if uploaded_file is not None:
        with st.spinner("🔍 Extracting report text..."):
            # text = extract_text(uploaded_file)
            if "report_text" not in st.session_state:
                st.session_state.report_text = extract_text(uploaded_file)
            text = st.session_state.report_text


        

        flagged = flag_abnormalities(text)
        if flagged:
            st.success(f"🔎 Found {len(flagged)} potential abnormal result(s) flagged below:")

            st.subheader("⚠️ Highlighted Issues")
            for issue in flagged:
                st.markdown(f"- {issue}")

        # if st.button("🧠 Analyze with AI"):
        #     with st.spinner(" Generating summary..."):
        #         # summary = generate_summary(text)
        #         if "summary_text" not in st.session_state:
        #             st.session_state.summary_text = generate_summary(text)
        #         summary = st.session_state.summary_text

        #     st.success(" Summary Complete")
        #     st.markdown("###  Plain Language Summary")
        #     st.write(summary)
        #     # st.download_button("Download Summary", summary, file_name="summary.txt")
        #     st.download_button(" Download Summary", summary, file_name="summary.txt")

        #     st.markdown("### Ask a question about your report")
        #     user_question = st.text_input("Enter your question", placeholder="e.g. What does a low MCH mean?")

        if st.button("🧠 Analyze with AI"):
            with st.spinner(" Generating summary..."):
                st.session_state.summary_text = generate_summary(text)

        # Show results if summary exists
        if "summary_text" in st.session_state:
            summary = st.session_state.summary_text

            st.success("✅ Summary Complete")
            st.markdown("### 📝 Plain Language Summary")
            st.write(summary)
            st.download_button("📥 Download Summary", summary, file_name="summary.txt")

            st.markdown("### ❓ Ask a question about your report")
            user_question = st.text_input("Enter your question", placeholder="e.g. What does a low MCH mean?")

            if user_question:
                with st.spinner("🤖 Thinking..."):
                    followup_prompt = f"""
        You are a medical assistant. The following is a medical report:

        {st.session_state.report_text}

        Summary:
        {summary}

        The user has this question about their report:
        \"{user_question}\"

        Provide a clear and medically-informed answer, in layperson terms if possible.
        """

                    response = client.chat.completions.create(
                        model="deepseek/deepseek-r1:free",
                        messages=[
                            {"role": "system", "content": "You are a medical assistant helping explain a health report."},
                            {"role": "user", "content": followup_prompt}
                        ]
                    )
                    answer = response.choices[0].message.content.strip()
                    st.markdown("### 💬 Answer to Your Question")
                    st.write(answer)


    
        st.markdown(
        "<hr><small> Built by Statistician</small>",
        unsafe_allow_html=True
    )


