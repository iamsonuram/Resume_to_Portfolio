# Resume to Portfolio Generator

A Streamlit application that converts a resume (PDF or text) into a portfolio website using a Mistral AI agent for parsing.

## File Structure

resume-to-portfolio/├── app.py                    # Streamlit application├── templates/│   └── index.html           # HTML template├── static/│   ├── style.css           # Main CSS│   ├── mediaqueries.css    # Responsive CSS│   ├── script.js           # JavaScript for menu│   └── assets/             # Image assets├── requirements.txt         # Python dependencies└── README.md               # This file

## Setup
1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd resume-to-portfolio


Install dependencies:
pip install -r requirements.txt


Ensure assets:

Place placeholder images in static/assets/ (e.g., profile-pic.jpg, arrow.png, etc.).
Images should match those referenced in index.html.


Run the application:
streamlit run app.py



Usage

Open the Streamlit app in your browser (usually at http://localhost:8501).
Upload a resume (PDF or text).
The app will process the resume using the Mistral agent and generate a portfolio.
Download the generated portfolio as a ZIP file containing index.html, CSS, JS, and assets.

Notes

The Mistral API key and agent ID are hardcoded in app.py. Replace them with your own credentials.
Placeholder images are used for projects and certifications. For production, implement dynamic image handling.
The resume PDF is not included in the ZIP; you may need to add it manually to the assets folder.

Dependencies

Python 3.8+
Streamlit
PyPDF2
Requests
Jinja2



