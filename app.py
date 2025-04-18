import streamlit as st
from autogen import AssistantAgent, UserProxyAgent
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import os
from groq import Groq
import time
from fake_useragent import UserAgent
from dotenv import load_dotenv
import random
import urllib.parse
import requests
from bs4 import BeautifulSoup
import logging
import google.generativeai as genai
from typing import Dict, Any
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Groq Client
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    st.error("Please set your GROQ_API_KEY in the environment variables!")
    st.stop()

client = Groq(api_key=groq_api_key)

# Initialize Gemini
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    st.error("Please set your GEMINI_API_KEY in the environment variables!")
    st.stop()

genai.configure(api_key=gemini_api_key)
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

# --- Fixed AutoGen Configuration ---
def setup_autogen():
    """Configure and return AutoGen agents with proper LLM config"""
    # Correct Groq LLM configuration
    llm_config = {
        "config_list": [
            {
                "model": "llama-3.3-70b-versatile",  # Updated to correct model name
                "api_key": groq_api_key,
                "base_url": "https://api.groq.com/openai/v1",
                "api_type": "openai",  # Important: This tells AutoGen to use OpenAI-compatible API
                "price": [0.0, 0.0]
            }
        ],
        "temperature": 0.7,
        "timeout": 120,
    }

    # Configure the assistant
    assistant = AssistantAgent(
        name="CareerCoach",
        llm_config=llm_config,
        system_message="""
        You are a professional cover letter writer specializing in tech jobs.
        Generate tailored 3-paragraph cover letters with:
        1. Introduction showing enthusiasm
        2. Middle highlighting relevant skills
        3. Closing with call to action
        
        Key requirements:
        - Professional but approachable tone
        - Under 400 words
        - Highlight top 3 relevant skills
        - Personalized for the specific company
        - No generic templates
        """
    )
    
    user_proxy = UserProxyAgent(
    name="Candidate",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=3,  # Increased from 1
    code_execution_config=False,
    default_auto_reply="Please generate the cover letter now.",
    llm_config=False
    )
    
    return assistant, user_proxy

# --- Web Scraping Function ---
def scrape_linkedin_jobs(query, location="remote", max_results=5):
    """Scrape job listings from LinkedIn"""
    try:
        base_url = f"https://www.linkedin.com/jobs/search?keywords={urllib.parse.quote(query)}&location={urllib.parse.quote(location)}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        response = requests.get(base_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        jobs = []
        job_cards = soup.find_all('div', class_='base-card')
        
        for card in job_cards[:max_results]:
            try:
                jobs.append({
                    "title": card.find('h3', class_='base-search-card__title').text.strip(),
                    "company": card.find('h4', class_='base-search-card__subtitle').text.strip(),
                    "summary": f"Location: {card.find('span', class_='job-search-card__location').text.strip()}",
                    "url": card.find('a', class_='base-card__full-link')['href'].split('?')[0]
                })
            except Exception as e:
                logger.warning(f"Error parsing job card: {e}")
                
        if jobs:
            return jobs
            
    except Exception as e:
        logger.warning(f"Simple scraping failed: {e}")

    # Selenium fallback
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument(f'user-agent={UserAgent().random}')
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    try:
        driver.get(f"https://www.linkedin.com/jobs/search?keywords={urllib.parse.quote(query)}&location={urllib.parse.quote(location)}")
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "jobs-search__results-list")))
        
        for _ in range(2):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        jobs = []
        for card in driver.find_elements(By.CSS_SELECTOR, "li.jobs-search-results__list-item")[:max_results]:
            try:
                card.click()
                time.sleep(1)
                jobs.append({
                    "title": card.find_element(By.CSS_SELECTOR, "h3.base-search-card__title").text.strip(),
                    "company": card.find_element(By.CSS_SELECTOR, "h4.base-search-card__subtitle").text.strip(),
                    "summary": f"Location: {card.find_element(By.CSS_SELECTOR, 'span.job-search-card__location').text.strip()}",
                    "url": card.find_element(By.CSS_SELECTOR, "a.base-card__full-link").get_attribute("href").split('?')[0]
                })
            except Exception as e:
                logger.warning(f"Error processing job card: {e}")
                
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        jobs = []
    finally:
        driver.quit()

    return jobs or [
        {
            "title": f"{query} at TechCorp",
            "company": "TechCorp",
            "summary": f"A {query.lower()} role requiring {query.split()[0]} skills.",
            "url": f"https://www.linkedin.com/jobs/view/{random.randint(1000000, 9999999)}"
        } for _ in range(max_results)
    ]

# --- Job Filtering ---
def filter_jobs(jobs, skills, query):
    """Filter and score jobs based on relevance"""
    filtered = []
    primary_skill = query.split()[0].lower()
    
    for job in jobs:
        content = f"{job['title']} {job['summary']}".lower()
        if primary_skill not in content:
            continue
            
        score = 3 + sum(1 for skill in skills if skill.lower() in content)
        score -= sum(1 for tech in (["python", "c++", "javascript"] if primary_skill != "python" else ["java", "c#"]) if tech in content)
        
        if score > 0:
            job["match_score"] = min(5, score)
            filtered.append(job)
            
    return sorted(filtered, key=lambda x: x["match_score"], reverse=True)

# --- AutoGen Powered Cover Letter Generator ---
def generate_cover_letter(job, skills, bio):
    """Generate cover letter using AutoGen"""
    try:
        assistant, user_proxy = setup_autogen()
        
        prompt = f"""
        JOB DETAILS:
        - Position: {job['title']}
        - Company: {job['company']}
        - Description: {job['summary']}
        
        CANDIDATE PROFILE:
        - Skills: {', '.join(skills)}
        - Experience: {bio}
        
        INSTRUCTIONS:
        1. Focus on the most relevant 3 skills
        2. Structure in 3 paragraphs:
           - Introduction: Express enthusiasm
           - Body: Highlight qualifications
           - Closing: Call to action
        3. Keep under 400 words
        4. Professional but approachable tone
        5. Personalized for the company
        """
        
        # Initiate chat and suppress automatic reply
        user_proxy.initiate_chat(
            assistant,
            message=prompt,
            clear_history=True,
            silent=True  # Suppress automatic replies
        )
        
        # Get the assistant's first response only
        chat_history = assistant.chat_messages[user_proxy]
        if chat_history:
            return chat_history[-1]["content"]
        return "Could not generate cover letter."
        
    except Exception as e:
        logger.error(f"Error in cover letter generation: {e}")
        return f"Error generating cover letter: {str(e)}"

# --- Gemini Functions ---
def get_interview_tips(job_title, company, skills):
    """Get interview tips using Gemini"""
    prompt = f"""
    Provide interview preparation tips for a {job_title} position at {company}.
    Candidate skills: {', '.join(skills)}
    
    Format:
    1. Technical preparation (3 bullet points)
    2. Behavioral preparation (3 bullet points)
    3. Company-specific tips (2 bullet points)
    
    Keep it professional and actionable.
    """
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error generating interview tips: {e}")
        return f"Could not generate interview tips: {str(e)}"

def get_salary_estimate(job_title, location, requirements):
    """Get salary estimates using Gemini"""
    prompt = f"""
    Provide salary range estimates for a {job_title} position in {location}.
    Requirements: {requirements}
    
    Include:
    - Entry-level range
    - Mid-career range
    - Senior-level range
    - Factors affecting compensation
    
    Be specific and cite sources if possible.
    """
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error generating salary estimate: {e}")
        return f"Could not generate salary estimate: {str(e)}"
    


with open("job.png", "rb") as image_file:
    base64_string = base64.b64encode(image_file.read()).decode()
    page_icon = f"data:image/png;base64,{base64_string}"

# --- Streamlit UI ---
st.set_page_config(
    page_title="JobQuest",
    layout="wide",
    page_icon=page_icon
)

# Custom CSS for a professional yet user-friendly aesthetic design with transparent buttons
# High Contrast CSS
st.markdown("""
    <style>
    /* Base styles */
    html, body, .stApp {
        background: #ffffff !important;
        color: #000000 !important;
        font-family: Arial, sans-serif;
    }
    
    /* Force all text black */
    h1, h2, h3, h4, h5, h6, p, div, span, label {
        color: #000000 !important;
    }
    
    /* Sidebar */
    .stSidebar {
        background: #f0f2f6 !important;
        border-right: 1px solid #d1d5db !important;
    }
    
    /* Input fields */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #d1d5db !important;
    }
    
    /* Buttons */
    .stButton>button {
        background: #2563eb !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
    }
    
    /* Job cards */
    .job-card {
        background: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
    }
    
    .job-title {
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 4px;
    }
    
    .company-name {
        color: #2563eb !important;
        font-weight: bold;
        margin-bottom: 4px;
    }
    
    .job-summary {
        color: #4b5563 !important;
        margin-bottom: 8px;
    }
    
    .match-badge {
        background: #10b981 !important;
        color: white !important;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
        margin-right: 8px;
    }
    
    .view-job-btn {
        background: transparent !important;
        color: #2563eb !important;
        border: 1px solid #2563eb !important;
        padding: 4px 12px !important;
        font-size: 14px !important;
        border-radius: 4px !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab"] {
        color: #000000 !important;
        font-weight: bold !important;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: #2563eb !important;
        color: white !important;
    }
    
    /* Success message */
    .stAlert.st-success {
        background: #d1fae5 !important;
        border-left: 4px solid #10b981 !important;
    }
    </style>
""", unsafe_allow_html=True)


with open("job.png", "rb") as image_file:
    base64_string = base64.b64encode(image_file.read()).decode()
    logo = f'<img src="data:image/png;base64,{base64_string}" alt="JobQuest Logo" style="vertical-align:middle; height:60px; margin-right:10px;">'

# Update the title with larger image and text
st.markdown(f"{logo} <b style='font-size: 2.5em; color: #2c3e50;'>JobQuest AI</b>", unsafe_allow_html=True)

st.subheader("Your Intelligent Job Search Navigator")

# Sidebar
with st.sidebar:
    st.header("Your Profile")
    skills_input = st.text_input("Skills (comma separated)", "Java, Spring Boot, SQL")
    bio = st.text_area("Professional Summary", "3 years of experience in Java development with Spring Framework.")
    query = st.text_input("Job Title", "Java Developer")
    location = st.text_input("Location", "Remote")
    search_button = st.button("🔍 Search Jobs", type="primary")

# Initialize session state
if 'jobs' not in st.session_state:
    st.session_state.jobs = []
if 'selected_job' not in st.session_state:
    st.session_state.selected_job = None
if 'cover_letter' not in st.session_state:
    st.session_state.cover_letter = ""
if 'interview_tips' not in st.session_state:
    st.session_state.interview_tips = ""
if 'salary_estimate' not in st.session_state:
    st.session_state.salary_estimate = ""

# Job Search
if search_button:
    with st.spinner("Searching for jobs..."):
        skills = [s.strip() for s in skills_input.split(",")]
        st.session_state.jobs = filter_jobs(
            scrape_linkedin_jobs(query, location),
            skills,
            query
        )
        st.session_state.selected_job = None
        st.session_state.cover_letter = ""
        st.session_state.interview_tips = ""
        st.session_state.salary_estimate = ""

# Display Results
if st.session_state.jobs:
    st.success(f"Found {len(st.session_state.jobs)} matching jobs!")
    
    for i, job in enumerate(st.session_state.jobs):
        with st.expander(f"{job['title']} at {job['company']} (Match: {job.get('match_score', 0)}/5)"):
            st.write(f"**Summary**: {job['summary']}")
            st.write(f"**Link**: [Apply Here]({job['url']})")
            
            tab1, tab2, tab3 = st.tabs(["Cover Letter", "Interview Prep", "Salary Guide"])
            
            with tab1:
                if st.button("✍️ Generate Cover Letter", key=f"cover_{i}"):
                    with st.spinner("Drafting your cover letter..."):
                        st.session_state.selected_job = job
                        st.session_state.cover_letter = generate_cover_letter(
                            job,
                            [s.strip() for s in skills_input.split(",")],
                            bio
                        )
                    st.rerun()
                
                if st.session_state.selected_job == job and st.session_state.cover_letter:
                    st.text_area("Your Cover Letter", st.session_state.cover_letter, height=300, key=f"letter_{i}")
                    st.download_button(
                        "📥 Download",
                        st.session_state.cover_letter,
                        file_name=f"cover_letter_{job['company']}.txt",
                        key=f"download_{i}"
                    )
            
            with tab2:
                if st.button("💡 Get Interview Tips", key=f"interview_{i}"):
                    with st.spinner("Preparing interview strategy..."):
                        st.session_state.selected_job = job
                        st.session_state.interview_tips = get_interview_tips(
                            job['title'],
                            job['company'],
                            [s.strip() for s in skills_input.split(",")]
                        )
                    st.rerun()
                
                if st.session_state.selected_job == job and st.session_state.interview_tips:
                    st.write(st.session_state.interview_tips)
            
            with tab3:
                if st.button("💰 Salary Estimate", key=f"salary_{i}"):
                    with st.spinner("Analyzing market rates..."):
                        st.session_state.selected_job = job
                        st.session_state.salary_estimate = get_salary_estimate(
                            job['title'],
                            location,
                            job['summary']
                        )
                    st.rerun()
                
                if st.session_state.selected_job == job and st.session_state.salary_estimate:
                    st.write(st.session_state.salary_estimate)


# Empty State
else:
    st.markdown("""
        <div style="text-align: center; padding: 40px 0; color: #4b5563;">
            <h3>Ready to find your dream job?</h3>
            <p>Fill out your profile and click "Find Matching Jobs" to get started</p>
        </div>
    """, unsafe_allow_html=True)


# Reset
if st.button("🔄 Reset Search"):
    st.session_state.jobs = []
    st.session_state.selected_job = None
    st.session_state.cover_letter = ""
    st.session_state.interview_tips = ""
    st.session_state.salary_estimate = ""
    st.rerun()
