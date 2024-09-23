import streamlit as st
import google.generativeai as genai
import os
import docx2txt
import PyPDF2 as pdf
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Configure the generative AI model with the Google API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Set up the model configuration for text generation
generation_config = {
    "temperature": 0.4,
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 4096,
}

# Define safety settings for content generation
safety_settings = [
    {"category": f"HARM_CATEGORY_{category}", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
    for category in ["HARASSMENT", "HATE_SPEECH", "SEXUALLY_EXPLICIT", "DANGEROUS_CONTENT"]
]

def generate_response_from_gemini(input_text):
    # Create a GenerativeModel instance with 'gemini-pro' as the model type
    llm = genai.GenerativeModel(
        model_name="gemini-pro",
        generation_config=generation_config,
        safety_settings=safety_settings,
    )
    # Generate content based on the input text
    output = llm.generate_content(input_text)
    # Return the generated text
    return output.text

def extract_text_from_pdf_file(uploaded_file):
    # Use PdfReader to read the text content from a PDF file
    pdf_reader = pdf.PdfReader(uploaded_file)
    text_content = ""
    for page in pdf_reader.pages:
        text_content += str(page.extract_text())
    return text_content

def extract_text_from_docx_file(uploaded_file):
    # Use docx2txt to extract text from a DOCX file
    return docx2txt.process(uploaded_file)

# Prompt Template
input_prompt_template = """
As an experienced Applicant Tracking System (ATS) analyst,
with profound knowledge in technology, software engineering, data science, 
and big data engineering, your role involves evaluating resumes against job descriptions.
Recognizing the competitive job market, provide top-notch assistance for resume improvement.
Your goal is to analyze the resume against the given job description, 
assign a percentage match based on key criteria, and pinpoint missing keywords accurately.
resume:{text}
description:{job_description}
I want the response in one single string having the structure
{{"Job Description Match":"%","Missing Keywords":"","Candidate Summary":"","Experience":""}}
"""
suggestion_prompt = """
As an experienced Applicant Tracking System (ATS) analyst, 
with deep expertise in resume optimization for better alignment with job descriptions, 
your role is to provide actionable suggestions to help candidates improve their resumes.
You will thoroughly review the provided resume in comparison with the job description and 
identify key areas for improvement. Focus on enhancing the match percentage by recommending
changes in experience details, skills, and keywords, while ensuring the resume is tailored to the job description.
resume: {text}
description: {job_description}
"""

# Streamlit app

# adding animation in the background
st.markdown('''
<style>
    .navbar {
        position: sticky;
        top: 0;
        background-color: white;
        padding: 10px;
        display: flex;
        justify-content: space-around;
        width: 100%; /* Full width */
        z-index: 1000;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }

    .navbar a {
        text-decoration: none;
        color: #0000FF;
        font-weight: bold;
        padding: 10px 15px;
        font-size: 20px;
    }

    h1 {color: #ff0000; text-align: center;}
    .center-text {text-align: center; font-size: 20px; margin-bottom: 10px;}
    .textarea {width: 100%; height: 300px;}
</style>
''', unsafe_allow_html=True)

# Navbar HTML
st.markdown('''
<div class="navbar">
    <a href="#job-description">Home Page</a>
    <a href="#upload-resume">How it works</a>
    <a href="#submit">How to use</a>
</div>
''', unsafe_allow_html=True)

# Initialize Streamlit app
st.title("Tailor Your Resume With AI based on Job Description")
st.markdown('''
<style>
    h1 {color: #ff0000; text-align: center;}
    .center-button {display: flex; justify-content: center align-item:center color:blue;}
    .center-text {text-align: center; font-size: 20px; margin-bottom: 10px;}
    .textarea {width: 100%; height: 300px;}
</style>
''', unsafe_allow_html=True)
# Centered Job Description Text
st.markdown('<div class="center-text">Paste the Job Description</div>', unsafe_allow_html=True)
job_description = st.text_area("", height=300, key="job_description", help="Paste your job description here", max_chars=5000, label_visibility="collapsed")

st.markdown('<div class="center-text">Upload Your Resume</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload Here: ", type=["pdf", "docx"], help="Please upload a PDF or DOCX file")
# Centered submit button
st.markdown('<div class="center-button">', unsafe_allow_html=True)
submit_button = st.button("Submit")
st.markdown('</div>', unsafe_allow_html=True)
# Initialize session state for controlling button press behavior
if 'seek_suggestions' not in st.session_state:
    st.session_state.seek_suggestions = False

if submit_button:
    if uploaded_file is not None:
        if uploaded_file.type == "application/pdf":
            resume_text = extract_text_from_pdf_file(uploaded_file)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            resume_text = extract_text_from_docx_file(uploaded_file)
        
        response_text = generate_response_from_gemini(input_prompt_template.format(text=resume_text, job_description=job_description))

        # Extract Job Description Match percentage from the response
        match_percentage_str = response_text.split('"Job Description Match":"')[1].split('"')[0]
        match_percentage = float(match_percentage_str.rstrip('%'))

        # Extract the rest of the information from the response
        missing_keywords = response_text.split('"Missing Keywords":"')[1].split('"')[0]
        candidate_summary = response_text.split('"Candidate Summary":"')[1].split('"')[0]
        experience = response_text.split('"Experience":"')[1].split('"')[0]

        st.subheader("ATS Evaluation Result:")

        # Format and display the result
        st.markdown(f"""
        **Job Description Match:** {match_percentage}%
        
        **Missing Keywords:** {missing_keywords}
        
        **Candidate Summary:** {candidate_summary}
        
        **Experience:** {experience}
        """)

        

        # Display message based on Job Description Match percentage
        if match_percentage >= 80:
            st.markdown("### **Final Result:** Move forward with hiring")
        else:
            st.markdown("### **Final Result:** Not a Match")

        improve_button = st.button("Seek Suggestions", key='suggestion')

        # Check if the "Seek Suggestions" button is pressed
        if improve_button or st.session_state.seek_suggestions:
            st.session_state.seek_suggestions = True
            # Generate suggestions based on the resume and job description
            improvision_text = generate_response_from_gemini(suggestion_prompt.format(text=resume_text, job_description=job_description))

            # Display the suggestions in a formatted markdown
            st.markdown(f"""
            **Here are some suggestions for improvement:**  
            {improvision_text}
            """)