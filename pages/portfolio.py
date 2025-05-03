import streamlit as st
import PyPDF2
import requests
import json
import os
from jinja2 import Environment, FileSystemLoader
from zipfile import ZipFile
import shutil
from datetime import datetime
from PIL import Image
import io

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
    {{"title": "", "description": "", "technologies": [], "github": "", "link": "", "image": ""}}
  ],
  "experience": [
    {{"company": "", "role": "", "duration": "", "description": ""}}
  ],
  "certifications": [
    {{"title": "", "provider": "", "link": "", "image": ""}}
  ],
  "publications": [
    {{"title": "", "publisher": "", "year": "", "link": ""}}
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

def generate_portfolio(data, images):
    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('index.html')

    # Create output directory
    output_dir = "output_portfolio"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    os.makedirs(os.path.join(output_dir, "assets"), exist_ok=True)

    # Render HTML with current year
    html_content = template.render(
        name=data.get("name", "Unknown"),
        about=data.get("about", ""),
        education=data.get("education", []),
        skills=data.get("skills", {"technical": [], "soft": []}),
        projects=data.get("projects", []),
        experience=data.get("experience", []),
        certifications=data.get("certifications", []),
        publications=data.get("publications", []),
        contact=data.get("contact", {"email": "", "linkedin": "", "github": ""}),
        resume_link="resume.pdf",
        current_year=datetime.now().year
    )

    # Write HTML file
    with open(os.path.join(output_dir, "index.html"), "w") as f:
        f.write(html_content)

    # Copy static files
    for file in ["style.css", "mediaqueries.css", "script.js"]:
        src = os.path.join("static", file)
        if os.path.exists(src):
            shutil.copy(src, output_dir)
        else:
            st.warning(f"Static file {src} not found. Portfolio may be incomplete.")

    # Save uploaded images
    if images.get("profile"):
        with open(os.path.join(output_dir, "assets", "profile-pic.jpg"), "wb") as f:
            f.write(images["profile"].getbuffer())
    else:
        src = "static/assets/profile-pic.jpg"
        if os.path.exists(src):
            shutil.copy(src, os.path.join(output_dir, "assets", "profile-pic.jpg"))
        else:
            st.warning(f"Placeholder image {src} not found.")

    if images.get("about"):
        with open(os.path.join(output_dir, "assets", "about-pic.jpg"), "wb") as f:
            f.write(images["about"].getbuffer())
    else:
        src = "static/assets/about-pic.jpg"
        if os.path.exists(src):
            shutil.copy(src, os.path.join(output_dir, "assets", "about-pic.jpg"))
        else:
            st.warning(f"Placeholder image {src} not found.")

    # Save project and certificate images
    for i, project in enumerate(data["projects"]):
        img_key = f"project_{i}"
        if img_key in images and images[img_key]:
            with open(os.path.join(output_dir, "assets", f"project_{i}.jpg"), "wb") as f:
                f.write(images[img_key].getbuffer())
            project["image"] = f"assets/project_{i}.jpg"
        else:
            project["image"] = "assets/project-placeholder.png"
            src = "static/assets/project-placeholder.png"
            if os.path.exists(src):
                shutil.copy(src, os.path.join(output_dir, "assets", "project-placeholder.png"))
            else:
                st.warning(f"Placeholder image {src} not found. Using default image path.")

    for i, cert in enumerate(data["certifications"]):
        img_key = f"cert_{i}"
        if img_key in images and images[img_key]:
            with open(os.path.join(output_dir, "assets", f"cert_{i}.jpg"), "wb") as f:
                f.write(images[img_key].getbuffer())
            cert["image"] = f"assets/cert_{i}.jpg"
        else:
            cert["image"] = "assets/project-placeholder.png"
            src = "static/assets/project-placeholder.png"
            if os.path.exists(src):
                shutil.copy(src, os.path.join(output_dir, "assets", "project-placeholder.png"))
            else:
                st.warning(f"Placeholder image {src} not found. Using default image path.")

    # Copy other static assets
    for asset in ["arrow.png", "email.png", "linkedin.png", "github.png", "experience.png", "education.png", "checkmark.png", "bulb.jpg"]:
        src = os.path.join("static/assets", asset)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(output_dir, "assets", asset))
        else:
            st.warning(f"Asset {src} not found. Portfolio may be incomplete.")

    # Create ZIP file
    zip_path = "portfolio.zip"
    with ZipFile(zip_path, "w") as zipf:
        for root, _, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, output_dir)
                zipf.write(file_path, os.path.join("portfolio", arcname))

    return zip_path, html_content

# Streamlit UI
st.title("Resume to Portfolio Generator")
st.write("Upload your resume (PDF or text) to generate a portfolio website.")

# Initialize session state
if "data" not in st.session_state:
    st.session_state.data = None
if "images" not in st.session_state:
    st.session_state.images = {}
if "step" not in st.session_state:
    st.session_state.step = "upload"

# Step 1: Upload resume
if st.session_state.step == "upload":
    uploaded_file = st.file_uploader("Choose a resume file", type=["pdf", "txt"])
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            resume_text = extract_text_from_pdf(uploaded_file)
        else:
            resume_text = uploaded_file.read().decode("utf-8")
        if resume_text:
            st.write("Processing resume...")
            data = call_mistral_agent(resume_text)
            if data:
                # Initialize image fields for projects and certifications
                for i, project in enumerate(data.get("projects", [])):
                    project["image"] = "assets/project-placeholder.png"
                for i, cert in enumerate(data.get("certifications", [])):
                    cert["image"] = "assets/project-placeholder.png"
                st.session_state.data = data
                st.session_state.step = "edit"
                st.success("Resume parsed successfully! Please review and edit the details below.")
            else:
                st.error("Failed to parse resume. Please try again.")

# Step 2: Edit parsed data
if st.session_state.step == "edit":
    st.header("Review and Edit Resume Details")

    # Form for editing data
    with st.form("edit_form"):
        # Name
        st.subheader("Personal Info")
        st.session_state.data["name"] = st.text_input("Name", st.session_state.data.get("name", ""))
        st.session_state.data["about"] = st.text_area("About", st.session_state.data.get("about", ""))

        # Contact
        st.subheader("Contact")
        contact = st.session_state.data["contact"]
        contact["email"] = st.text_input("Email", contact.get("email", ""))
        contact["phone"] = st.text_input("Phone", contact.get("phone", ""))
        contact["linkedin"] = st.text_input("LinkedIn", contact.get("linkedin", ""))
        contact["github"] = st.text_input("GitHub", contact.get("github", ""))

        # Education
        st.subheader("Education")
        for i, edu in enumerate(st.session_state.data["education"]):
            with st.expander(f"Education {i+1}"):
                edu["degree"] = st.text_input(f"Degree {i+1}", edu.get("degree", ""), key=f"edu_degree_{i}")
                edu["institution"] = st.text_input(f"Institution {i+1}", edu.get("institution", ""), key=f"edu_inst_{i}")
                edu["year"] = st.text_input(f"Year {i+1}", edu.get("year", ""), key=f"edu_year_{i}")

        # Skills
        st.subheader("Skills")
        skills = st.session_state.data["skills"]
        skills["technical"] = st.multiselect("Technical Skills", skills.get("technical", []), skills.get("technical", []), key="tech_skills")
        skills["soft"] = st.multiselect("Soft Skills", skills.get("soft", []), skills.get("soft", []), key="soft_skills")

        # Experience
        st.subheader("Experience")
        for i, exp in enumerate(st.session_state.data["experience"]):
            with st.expander(f"Experience {i+1}"):
                exp["company"] = st.text_input(f"Company {i+1}", exp.get("company", ""), key=f"exp_company_{i}")
                exp["role"] = st.text_input(f"Role {i+1}", exp.get("role", ""), key=f"exp_role_{i}")
                exp["duration"] = st.text_input(f"Duration {i+1}", exp.get("duration", ""), key=f"exp_duration_{i}")
                exp["description"] = st.text_area(f"Description {i+1}", exp.get("description", ""), key=f"exp_desc_{i}")

        # Projects
        st.subheader("Projects")
        for i, proj in enumerate(st.session_state.data["projects"]):
            with st.expander(f"Project {i+1}"):
                proj["title"] = st.text_input(f"Title {i+1}", proj.get("title", ""), key=f"proj_title_{i}")
                proj["description"] = st.text_area(f"Description {i+1}", proj.get("description", ""), key=f"proj_desc_{i}")
                proj["technologies"] = st.multiselect(f"Technologies {i+1}", proj.get("technologies", []), proj.get("technologies", []), key=f"proj_tech_{i}")
                proj["github"] = st.text_input(f"GitHub {i+1}", proj.get("github", ""), key=f"proj_github_{i}")
                proj["link"] = st.text_input(f"Link {i+1}", proj.get("link", ""), key=f"proj_link_{i}")
                uploaded_image = st.file_uploader(f"Project Image {i+1}", type=["jpg", "png"], key=f"project_{i}")
                if uploaded_image:
                    st.session_state.images[f"project_{i}"] = uploaded_image
                    proj["image"] = f"assets/project_{i}.jpg"
                # Display current image if available
                img_key = f"project_{i}"
                if img_key in st.session_state.images and st.session_state.images[img_key]:
                    st.image(st.session_state.images[img_key], caption=f"Current Project {i+1} Image", width=100)

        # Certifications
        st.subheader("Certifications")
        for i, cert in enumerate(st.session_state.data["certifications"]):
            with st.expander(f"Certification {i+1}"):
                cert["title"] = st.text_input(f"Title {i+1}", cert.get("title", ""), key=f"cert_title_{i}")
                cert["provider"] = st.text_input(f"Provider {i+1}", cert.get("provider", ""), key=f"cert_provider_{i}")
                cert["link"] = st.text_input(f"Link {i+1}", cert.get("link", ""), key=f"cert_link_{i}")
                uploaded_image = st.file_uploader(f"Certificate Image {i+1}", type=["jpg", "png"], key=f"cert_{i}")
                if uploaded_image:
                    st.session_state.images[f"cert_{i}"] = uploaded_image
                    cert["image"] = f"assets/cert_{i}.jpg"
                # Display current image if available
                img_key = f"cert_{i}"
                if img_key in st.session_state.images and st.session_state.images[img_key]:
                    st.image(st.session_state.images[img_key], caption=f"Current Certification {i+1} Image", width=100)

        # Publications
        st.subheader("Publications")
        for i, pub in enumerate(st.session_state.data["publications"]):
            with st.expander(f"Publication {i+1}"):
                pub["title"] = st.text_input(f"Title {i+1}", pub.get("title", ""), key=f"pub_title_{i}")
                pub["publisher"] = st.text_input(f"Publisher {i+1}", pub.get("publisher", ""), key=f"pub_publisher_{i}")
                pub["year"] = st.text_input(f"Year {i+1}", pub.get("year", ""), key=f"pub_year_{i}")
                pub["link"] = st.text_input(f"Link {i+1}", pub.get("link", ""), key=f"pub_link_{i}")

        # Image uploads for profile and about
        st.subheader("Profile and About Images")
        uploaded_profile = st.file_uploader("Profile Picture", type=["jpg", "png"], key="profile_image")
        if uploaded_profile:
            st.session_state.images["profile"] = uploaded_profile
        if st.session_state.images.get("profile"):
            st.image(st.session_state.images["profile"], caption="Current Profile Picture", width=100)

        uploaded_about = st.file_uploader("About Picture", type=["jpg", "png"], key="about_image")
        if uploaded_about:
            st.session_state.images["about"] = uploaded_about
        if st.session_state.images.get("about"):
            st.image(st.session_state.images["about"], caption="Current About Picture", width=100)

        # Submit button
        st.form_submit_button("Preview Portfolio")

    # Add and Delete buttons outside the form, at the bottom
    st.subheader("Manage Entries")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Add Education"):
            st.session_state.data["education"].append({"degree": "", "institution": "", "year": ""})
            st.rerun()
        if st.button("Add Skill"):
            st.session_state.data["skills"]["technical"].append("")
            st.session_state.data["skills"]["soft"].append("")
            st.rerun()
        if st.button("Add Experience"):
            st.session_state.data["experience"].append({"company": "", "role": "", "duration": "", "description": ""})
            st.rerun()
    with col2:
        if st.button("Add Project"):
            st.session_state.data["projects"].append({"title": "", "description": "", "technologies": [], "github": "", "link": "", "image": "assets/project-placeholder.png"})
            st.rerun()
        if st.button("Add Certification"):
            st.session_state.data["certifications"].append({"title": "", "provider": "", "link": "", "image": "assets/project-placeholder.png"})
            st.rerun()
        if st.button("Add Publication"):
            st.session_state.data["publications"].append({"title": "", "publisher": "", "year": "", "link": ""})
            st.rerun()

    # Delete buttons for education, experience, and projects
    st.subheader("Delete Entries")
    if st.session_state.data["education"]:
        st.write("Delete Education")
        for i, edu in enumerate(st.session_state.data["education"]):
            if st.button(f"Delete Education {i+1}: {edu.get('degree', 'Untitled')}", key=f"delete_edu_{i}"):
                st.session_state.data["education"].pop(i)
                st.rerun()
    if st.session_state.data["experience"]:
        st.write("Delete Experience")
        for i, exp in enumerate(st.session_state.data["experience"]):
            if st.button(f"Delete Experience {i+1}: {exp.get('role', 'Untitled')} at {exp.get('company', '')}", key=f"delete_exp_{i}"):
                st.session_state.data["experience"].pop(i)
                st.rerun()
    if st.session_state.data["projects"]:
        st.write("Delete Projects")
        for i, proj in enumerate(st.session_state.data["projects"]):
            if st.button(f"Delete Project {i+1}: {proj.get('title', 'Untitled')}", key=f"delete_proj_{i}"):
                # Remove associated image from session state
                img_key = f"project_{i}"
                if img_key in st.session_state.images:
                    del st.session_state.images[img_key]
                st.session_state.data["projects"].pop(i)
                # Reindex project images to maintain consistency
                new_images = {}
                for j, p in enumerate(st.session_state.data["projects"]):
                    old_key = f"project_{j}"
                    new_key = f"project_{j}"
                    if old_key in st.session_state.images:
                        new_images[new_key] = st.session_state.images[old_key]
                st.session_state.images = {k: v for k, v in st.session_state.images.items() if not k.startswith("project_")}
                st.session_state.images.update(new_images)
                st.rerun()
    if st.session_state.data["certifications"]:
        st.write("Delete Certifications")
        for i, cert in enumerate(st.session_state.data["certifications"]):
            if st.button(f"Delete Certification {i+1}: {cert.get('title', 'Untitled')}", key=f"delete_cert_{i}"):
                # Remove associated image from session state
                img_key = f"cert_{i}"
                if img_key in st.session_state.images:
                    del st.session_state.images[img_key]
                st.session_state.data["certifications"].pop(i)
                # Reindex certification images to maintain consistency
                new_images = {}
                for j, c in enumerate(st.session_state.data["certifications"]):
                    old_key = f"cert_{j}"
                    new_key = f"cert_{j}"
                    if old_key in st.session_state.images:
                        new_images[new_key] = st.session_state.images[old_key]
                st.session_state.images = {k: v for k, v in st.session_state.images.items() if not k.startswith("cert_")}
                st.session_state.images.update(new_images)
                st.rerun()

# Step 3: Preview portfolio
if st.session_state.step == "preview":
    st.header("Portfolio Preview")
    st.write("Review the final details and images below. Click 'Generate Portfolio' to download the ZIP file.")
    
    # Display data summary
    st.subheader("Data Summary")
    st.json(st.session_state.data)

    # Display uploaded images
    st.subheader("Uploaded Images")
    if st.session_state.images.get("profile"):
        st.image(st.session_state.images["profile"], caption="Profile Picture", width=200)
    if st.session_state.images.get("about"):
        st.image(st.session_state.images["about"], caption="About Picture", width=200)
    for i, proj in enumerate(st.session_state.data["projects"]):
        img_key = f"project_{i}"
        if img_key in st.session_state.images and st.session_state.images[img_key]:
            st.image(st.session_state.images[img_key], caption=f"Project {i+1}: {proj['title']}", width=200)
        elif proj["image"] == "assets/project-placeholder.png":
            st.write(f"Project {i+1}: Using placeholder image")
    for i, cert in enumerate(st.session_state.data["certifications"]):
        img_key = f"cert_{i}"
        if img_key in st.session_state.images and st.session_state.images[img_key]:
            st.image(st.session_state.images[img_key], caption=f"Certification {i+1}: {cert['title']}", width=200)
        elif cert["image"] == "assets/project-placeholder.png":
            st.write(f"Certification {i+1}: Using placeholder image")

    # Generate portfolio
    if st.button("Generate Portfolio"):
        try:
            zip_path, _ = generate_portfolio(st.session_state.data, st.session_state.images)
            with open(zip_path, "rb") as f:
                st.download_button(
                    label="Download Portfolio",
                    data=f,
                    file_name="portfolio.zip",
                    mime="application/zip"
                )
            st.success("Portfolio generated successfully!")
            st.session_state.step = "upload"  # Reset for next use
            st.session_state.data = None
            st.session_state.images = {}
        except Exception as e:
            st.error(f"Failed to generate portfolio: {str(e)}")
