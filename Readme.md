# JobQuest AI

Your AI-powered job search assistant that helps you find, analyze, and apply for your dream jobs with intelligent automation.

## ✨ Features

- **Smart Job Search**: Scrapes multiple job boards with intelligent filtering
- **AI Cover Letters**: Generates tailored cover letters in seconds
- **Interview Prep**: Provides customized interview preparation tips
- **Salary Insights**: Gives market-appropriate salary estimates
- **Match Scoring**: Rates jobs based on your skills and preferences




https://github.com/user-attachments/assets/16547e86-7cdc-48ca-97ef-caedff499e0e





## Graph
```mermaid
graph TD
    A[User Opens Job Hunt Sidekick] --> B[Welcome & Initial Setup]
    B --> C{First Time User?}
    C -->|Yes| D[Profile Creation Flow]
    C -->|No| E[Main Conversation Interface]
    
    %% Profile Creation Flow
    subgraph ProfileFlow["Profile Creation"]
        D --> D1[Collect Personal Information]
        D1 --> D2[Collect Professional Background]
        D2 --> D3[Collect Skills & Expertise]
        D3 --> D4[Collect Job Preferences]
        D4 --> D5[Collect Location Preferences]
        D5 --> D6[Collect Salary Requirements]
        D6 --> D7[Save User Profile as JSON]
        D7 --> E
    end
    
    %% Main Conversation Interface
    E --> F{User Intent?}
    
    %% Job Search Flow
    F -->|Search Jobs| G[Activate Searcher Agent]
    G --> G1[Collect/Confirm Search Parameters]
    G1 --> G2[Query Indeed API/Web Scraping]
    G2 --> G3[Process Search Results]
    G3 --> G4[Apply Smart Filtering Algorithm]
    G4 --> G5[Score & Rank Jobs]
    G5 --> G6[Present Top Results to User]
    G6 --> H{User Action?}
    
    H -->|View More Results| G6
    H -->|Refine Search| G1
    H -->|Select Job| I[Display Detailed Job Information]
    
    %% Cover Letter Flow
    I --> J{User Action?}
    J -->|Generate Cover Letter| K[Activate Writer Agent]
    K --> K1[Analyze Job Description]
    K1 --> K2[Match User Skills to Requirements]
    K2 --> K3[Generate Personalized Cover Letter]
    K3 --> K4[Present Cover Letter to User]
    K4 --> L{User Action?}
    
    L -->|Edit Cover Letter| K5[Provide Editing Interface]
    K5 --> K4
    L -->|Save Cover Letter| K6[Save to User's Documents]
    K6 --> M[Return to Job Details]
    L -->|Apply with Cover Letter| K7[Provide Application Instructions]
    K7 --> M
    
    %% Navigation Options
    J -->|Back to Results| G6
    J -->|Save Job| N[Add to Saved Jobs]
    N --> I
    M --> I
    
    %% Other Main Menu Options
    F -->|View Saved Jobs| O[Display Saved Jobs List]
    O --> P{User Action?}
    P -->|Select Job| I
    P -->|Return to Main| E
    
    F -->|Update Profile| Q[Edit User Profile]
    Q --> Q1[Display Current Profile]
    Q1 --> Q2[Allow Edits to Profile Fields]
    Q2 --> Q3[Save Updated Profile]
    Q3 --> E
    
    F -->|Get Job Hunting Advice| R[Provide Career Guidance]
    R --> E
    
    %% Error Handling
    G2 -->|API Error| G2E[Display Error Message]
    G2E --> G1
    
    G3 -->|No Results| G3E[Suggest Broader Search]
    G3E --> G1
 ```   

## 🖠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/careercompass-ai.git
cd careercompass-ai
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Add your API keys to the .env file
```

### 🔑 API Keys Required
- **Groq API Key** (for LLM)
- **Gemini API Key** (for interview/salary insights)

## 🚀 Usage

Run the application:
```bash
streamlit run app.py
```

1. Fill in your profile information:
   - Skills
   - Professional summary
   - Job preferences

2. Click "Search Jobs" to find matching opportunities

3. Use the generated materials to apply:
   - Custom cover letters
   - Interview preparation
   - Salary benchmarks

## 🖥️ Tech Stack
- **Frontend**: Streamlit
- **Backend**: Python
- **AI Services**: Groq, Gemini
- **Web Scraping**: BeautifulSoup, Selenium

## 📂 Project Structure
```
careercompass-ai/
├── app.py                # Main application
├── README.md             # This documentation
├── requirements.txt      # Dependencies
├── .env.example          # Environment template
└── assets/               # Screenshots/demo files
```


## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.

