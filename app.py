import streamlit as st
import PyPDF2  # Using PyPDF2 as confirmed installed
import requests
import json
import os
from jinja2 import Environment, FileSystemLoader
from zipfile import ZipFile
import shutil
from datetime import datetime

# Mistral API configuration
MISTRAL_API_KEY = "3xrYGjlTES48wSapMhxVsDhnPHvN9fNB"
MISTRAL_AGENT_ID = "ag:79ec7e4f:20250423:resume-parsing-assistant:5f14339e"
MISTRAL_API_URL = "https://api.mistral.ai/v1/agents/completions"

def call_mistral_agent(resume_text):
    prompt = f"""
You are a resume parsing assistant. Given the following resume text, extract and return structured data as JSON in this format:

{{
  "name": "Full name of the person",
  "about": "Short 2–3 line summary.",
  "education": [
    {{"degree": "", "institution": "", "year": ""}}
  ],
  "skills": {{
    "technical": ["Python", "SQL", "OpenCV"],
    "soft": ["Leadership", "Teamwork"]
  }},
  "projects": [
    {{"title": "", "description": "", "technologies": [], "github": "", "link": ""}}
  ],
  "experience": [
    {{"company": "", "role": "", "duration": "", "description": ""}}
  ],
  "certifications": [
    {{"title": "", "provider": "", "link": ""}}
  ],
  "contact": {{
    "email": "",
    "phone": "",
    "linkedin": "",
    "github": ""
  }}
}}

ONLY return valid JSON. Here's the resume:
\"\"\"{resume_text}\"\"\"
"""
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "agent_id": MISTRAL_AGENT_ID,
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = requests.post(MISTRAL_API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            try:
                raw = response.json()["choices"][0]["message"]["content"]
                data = json.loads(raw)
                return data
            except (json.JSONDecodeError, KeyError) as e:
                st.error(f"JSON decoding failed: {str(e)}")
                return {}
        else:
            st.error(f"Mistral API Error: {response.status_code} — {response.text}")
            return {}
    except Exception as e:
        st.error(f"Mistral API Request Failed: {str(e)}")
        return {}

def extract_text_from_pdf(file):
    try:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        st.error(f"Failed to extract text from PDF: {str(e)}")
        return ""

def generate_portfolio(data):
    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('index.html')

    # Create output directory
    output_dir = "output_portfolio"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    # Render HTML with current year
    html_content = template.render(
        name=data.get("name", "Unknown"),
        about=data.get("about", ""),
        education=data.get("education", []),
        skills=data.get("skills", {"technical": [], "soft": []}),
        projects=data.get("projects", []),
        experience=data.get("experience", []),
        certifications=data.get("certifications", []),
        contact=data.get("contact", {"email": "", "linkedin": "", "github": ""}),
        resume_link="resume.pdf",  # Placeholder; assumes resume is included
        current_year=datetime.now().year  # Pass current year
    )

    # Write HTML file
    with open(os.path.join(output_dir, "index.html"), "w") as f:
        f.write(html_content)

    # Copy static files
    shutil.copy("static/style.css", output_dir)
    shutil.copy("static/mediaqueries.css", output_dir)
    shutil.copy("static/script.js", output_dir)
    shutil.copytree("static/assets", os.path.join(output_dir, "assets"), dirs_exist_ok=True)  # Allow overwriting existing directory

    # Create ZIP file
    zip_path = "portfolio.zip"
    with ZipFile(zip_path, "w") as zipf:
        for root, _, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, output_dir)
                zipf.write(file_path, os.path.join("portfolio", arcname))

    return zip_path

# Streamlit UI
st.title("Resume to Portfolio Generator")
st.write("Upload your resume (PDF or text) to generate a portfolio website.")

uploaded_file = st.file_uploader("Choose a resume file", type=["pdf", "txt"])

if uploaded_file:
    # Extract text
    if uploaded_file.type == "application/pdf":
        resume_text = extract_text_from_pdf(uploaded_file)
    else:
        resume_text = uploaded_file.read().decode("utf-8")

    if resume_text:
        st.write("Processing resume...")
        # Call Mistral agent
        data = call_mistral_agent(resume_text)
        if data:
            st.success("Resume parsed successfully!")
            st.json(data)  # Display parsed data for debugging

            # Generate portfolio
            zip_path = generate_portfolio(data)
            with open(zip_path, "rb") as f:
                st.download_button(
                    label="Download Portfolio",
                    data=f,
                    file_name="portfolio.zip",
                    mime="application/zip"
                )
        else:
            st.error("Failed to parse resume. Please try again.")
