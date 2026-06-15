from auth import register_user, login_user
import streamlit as st
from openai import OpenAI
from PyPDF2 import PdfReader
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import re
from fpdf import FPDF

# PDF REPORT FUNCTION
def create_pdf(content):

    pdf = FPDF()

    pdf.add_page()

    pdf.set_font(
        "Arial",
        size=12
    )

    content = content.encode(
        "latin-1",
        "replace"
    ).decode("latin-1")

    pdf.multi_cell(
        0,
        10,
        content
    )

    file_name = "report.pdf"

    pdf.output(file_name)

    return file_name


# PAGE CONFIG (FIRST STREAMLIT COMMAND)

st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="🤖",
    layout="wide"
)
st.markdown("""
<style>

.main{
    background-color:#0E1117;
}

.stButton>button{
    width:100%;
    height:50px;
    border-radius:10px;
    font-size:18px;
}

.stTextInput>div>div>input{
    border-radius:10px;
}

</style>
""", unsafe_allow_html=True)


# LOAD ENV VARIABLES

load_dotenv()


# OPENROUTER CLIENT

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)


# DATABASE CONNECTION

DATABASE_URL = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:"
    f"{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:"
    f"{os.getenv('DB_PORT')}/"
    f"{os.getenv('DB_NAME')}"
)

engine = create_engine(DATABASE_URL)


# LOGIN SESSION

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


# LOGIN / REGISTER PAGE

if not st.session_state.logged_in:

    menu = st.sidebar.selectbox(
        "Menu",
        ["Login", "Register"]
    )

    if menu == "Register":

        st.title(" Register")

        username = st.text_input("Username")

        email = st.text_input("Email")

        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button("Register"):

            try:

                register_user(
                    engine,
                    username,
                    email,
                    password
                )

                st.success(
                    "Registration Successful! Please Login."
                )

            except Exception as e:
                st.error(str(e))

    elif menu == "Login":

        st.title("🤖 AI Resume Analyzer")

        st.markdown("""
        ### Optimize Your Resume with AI
        """)

        email = st.text_input("Email")

        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button("Login"):

            if login_user(
                engine,
                email,
                password
            ):

                st.session_state.logged_in = True
                st.rerun()

            else:

                st.error(
                    "Invalid Email or Password"
                )

    st.stop()


# LOGOUT BUTTON

st.sidebar.success("Logged In")
st.subheader(" Dashboard")

with engine.connect() as conn:

    result = conn.execute(
        text("SELECT COUNT(*) FROM resumes")
    )

    total_resumes = result.scalar()

col1,col2,col3 = st.columns(3)

with col1:
    st.metric(
        "Total Analyses",
        total_resumes
    )

with col2:
    st.metric(
        "AI Model",
        "GPT-4o"
    )

with col3:
    st.metric(
        "Status",
        "Active"
    )

if st.sidebar.button("Logout"):

    st.session_state.logged_in = False
    st.rerun()


# MAIN APP

st.title(" AI Resume Analyzer")

st.write(
    "Upload your resume and get AI-powered feedback."
)

uploaded_file = st.file_uploader(
    "Upload Resume PDF",
    type=["pdf"]
)

if uploaded_file:

    try:

        pdf = PdfReader(uploaded_file)

        resume_text = ""

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:
                resume_text += page_text
        st.write(
            "Characters Extracted:",
            len(resume_text)
        )

        st.success(
            "Resume Uploaded Successfully!"
        )
        with st.expander(
            " Resume Preview"
        ):

            st.text_area(
                "Extracted Text",
                resume_text,
                height=300
            )

        job_description = st.text_area(
            "Paste Job Description (Optional)"
        )
        if st.button("Analyze Resume"):

            with st.spinner(
                "Analyzing Resume..."
            ):

                prompt = f"""
                You are an ATS Resume Expert.

                Analyze this resume.

                Return EXACTLY in this format:

                ATS Score: 78

                ## Strengths

                ## Weaknesses

                ## Missing Skills

                ## Suggested Improvements

                ## Interview Questions

                Job Description:
                {job_description}

                Resume:
                {resume_text}
                """

                response = client.chat.completions.create(
                    model="openai/gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )

                analysis = (
                    response
                    .choices[0]
                    .message
                    .content
                )
                match = re.search(
                    r"ATS Score\s*:?\s*(\d+)",
                    analysis,
                    re.IGNORECASE
                )

                if match:

                    score = int(match.group(1))

                    st.metric(
                        "ATS Score",
                        f"{score}/100"
                    )

                    st.progress(score)

                st.subheader(
                    " Analysis Result"
                )

                st.write(
                    analysis
                )
                pdf_file = create_pdf(
                    analysis
                )

                with open(
                    pdf_file,
                    "rb"
                ) as file:

                    st.download_button(
                        label="📥 Download Report",
                        data=file,
                        file_name="Resume_Report.pdf",
                        mime="application/pdf"
                    )

                # SAVE TO DATABASE

                with engine.connect() as conn:

                    conn.execute(
                        text("""
                        INSERT INTO resumes
                        (filename, analysis)
                        VALUES
                        (:filename, :analysis)
                        """),
                        {
                            "filename": uploaded_file.name,
                            "analysis": analysis
                        }
                    )

                    conn.commit()

                st.success(
                    " Analysis Saved to TiDB!"
                )

    except Exception as e:

        st.error(
            f"Error: {e}"
        )
# -----------------------------
# RESUME HISTORY
# -----------------------------

st.subheader("📂 Previous Analyses")

with engine.connect() as conn:

    result = conn.execute(
        text("""
        SELECT filename
        FROM resumes
        ORDER BY id DESC
        LIMIT 10
        """)
    )

    rows = result.fetchall()

    for row in rows:
        st.write("📄", row.filename)