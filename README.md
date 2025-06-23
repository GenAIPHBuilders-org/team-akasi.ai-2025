# Akasi.ai | Your AI Guardian of Health and Wellness

<div align="center">
  <img src="https://myibryztojuymfqdybzy.supabase.co/storage/v1/object/public/akasi-images/images/akasi-logo-1.png" alt="Akasi.ai Logo" width="300" />
</div>

## 🧠 About Akasi.ai
**Akasi.ai** is an AI-powered health management solution that serves as your personal health guardian. We help Filipinos better manage chronic health conditions by bringing order to the chaos of health management - from tracking medications and diet to providing personalized insights and reminders.

## Project Overview
This repository contains the work of Team Akasi.ai for the GenAI PHBuilders Hackathon 2025. We're creating an AI-powered health management solution focused on helping Filipinos better manage chronic health conditions.

## This isn't just an idea for us - we're patient zero! 🙂

<div align="center">
  <h3>Meet the team behind akasi.ai</h3>
  
  <table>
    <tr>
      <td align="center">
        <img src="https://myibryztojuymfqdybzy.supabase.co/storage/v1/object/public/akasi-images/images/prof-pic-jen.jpg" width="80" height="80" alt="Jenrica"/>
        <br>
        <b>Jenrica</b>
        <p>Systems Engineer with PCOS<br>Currently works at a Cybersecurity Tech Company</p>
        <a href="https://www.linkedin.com/in/jenrica-ann-decafe">
          <img src="https://img.shields.io/badge/LinkedIn-Connect-blue?style=flat-square&logo=linkedin" alt="LinkedIn"/>
        </a>
      </td>
      <td align="center">
        <img src="https://myibryztojuymfqdybzy.supabase.co/storage/v1/object/public/akasi-images/images/prof-pic-emman.jpg" width="80" height="80" alt="Emman"/>
        <br>
        <b>Emman</b>
        <p>Electronics Engineer with gut health issues<br>Built multiple AI solutions</p>
        <a href="https://www.linkedin.com/in/engrebi">
          <img src="https://img.shields.io/badge/LinkedIn-Connect-blue?style=flat-square&logo=linkedin" alt="LinkedIn"/>
        </a>
      </td>
    </tr>
  </table>
</div>


## 🛠️ Tech Stack & Architecture

Akasi.ai leverages a modern tech stack to deliver an intelligent and responsive health management experience. Our architecture is designed around a multi-agent system to handle various aspects of health data processing and user interaction.

![Akasi.ai Architecture](https://pcygqqevesxpeeyxxfjw.supabase.co/storage/v1/object/public/users/Medical%20Docs/user_1/akasi.ai%20Pitch%20Deck%20-%20Agentic%20AI%20Hackathon%202025%20(6).png)


### Core Technologies

**Platform Framework:** FastHTML - The entire platform is built using FastHTML, allowing for rapid development of dynamic web applications purely in Python.

**AI Agent Framework:** LangGraph - We use LangGraph to build and orchestrate our multi-agent AI system, managing complex workflows for health information processing.
- **Agent 1:** Responsible for empathetically gathering health information from the user.
- **Agent 2:** Formats the gathered information into a structured and usable form for the Health Diary and platform display. (IN DEVELOPMENT PHASE)

**Large Language Model (LLM):** Claude 3.5 Sonnet v2 via AWS Bedrock - Powers the intelligence of our AI agents, enabling natural language understanding and generation.

### Frontend Styling
- **Tailwind CSS** - A utility-first CSS framework for rapidly building custom user interfaces.
- **DaisyUI** - A component library for Tailwind CSS to accelerate UI development.
- **Standard JS and CSS** for additional interactivity and custom styling.

### Backend (Database & Authentication)
**Supabase** - Provides robust backend services including a PostgreSQL database, user authentication, and storage.

### Simplified Architecture Overview

Below is a simplified overview of our multi-agent architecture:

```
User Input → Agent 1 (Info Gathering with Tools like Medical Doc Summarizer) → LangGraph Workflows (UI Controller, LLM Journal Entry) → Agent 2 (Data Formatting & Health Diary Building with Supabase Tool) → Akasi.ai Dashboard
```



## 🗺️ Development Roadmap

### Current State & Next Steps
The current implementation represents the **foundational architecture** of our multi-agent AI system. While the core features are currently bare bones, they effectively demonstrate the **power and potential of AI agents** in healthcare management. Our development trajectory focuses on evolving from this proof-of-concept into a production-ready, enterprise-grade health platform.

### Core Platform Features
- [x] **Complete Authentication System** - Secure user registration, login, and session management powered by Supabase  
- [x] **Intuitive User Interface** - Modern, responsive design using TailwindCSS and DaisyUI with exceptional user experience  
- [x] **Multi-Step Onboarding** - Seamless user journey from personal information collection to wellness journal setup  
- [x] **HTMX-Powered Reactive UI** - Dynamic, app-like experience without page reloads  
- [x] **Wellness Journal System** - Complete CRUD operations for health tracking and symptom logging  
- [x] **Speech Bubble Chat Interface** - Refined onboarding experience with intuitive conversation flow  
- [x] **Body Scanner Visualization** - Interactive SVG-based anatomy system with AI-controlled animations  

### Agent 1 - Health Information Orchestrator
- [x] **Empathetic Health Information Gathering** - Structured conversations designed to organize health management chaos  
- [x] **Medical Image Analysis** - Image summarization for comprehensive health records  
- [x] **Systematic Wellness Journal Population** - Targeted questioning to build complete health profiles  
- [x] **Interactive Body Scanner Integration** - AI-controlled visual feedback based on conversation context  
- [x] **Multi-modal Input Support** - Text, images, and document processing capabilities  
- [x] **LangGraph Workflow Implementation** - Multi-agent system architecture with state management  

### Currently In Development
- [ ] **Agent 2 - Health Data Processor** - Second AI agent for intelligent health data processing  
- [ ] **Main Dashboard CRUD Features** - Complete health metrics tracking and visualization  
- [ ] **Medication Management System** - Reminder systems and adherence tracking  
- [ ] **Agent 1 Optimizations** - Enhanced response accuracy and better context understanding  
- [ ] **Health Data Export Tools** - Reporting and data portability features  
- [ ] **Integration Layer** - Connecting traditional CRUD operations with Agent 2's intelligent processing  
- [ ] **Core Evaluation Framework for our AI Agents** - Implementing comprehensive test criteria for multi-agent system evaluation from both functionality and security perspectives, including jailbreak resistance and privacy compliance testing   

### Critical Infrastructure & Security
- [ ] **Healthcare-Grade Security** - Enhanced database security measures for healthcare data protection standards  


### Production Readiness & Compliance
- [ ] **🏆 NPC Registration Preparation** - Compliance with Philippine data privacy regulations for healthcare applications  
- [ ] **🏆 One-Click Deployment** - Containerized deployment with comprehensive documentation for open source use.  

### Platform Expansion
- [ ] **Healthcare Provider Integration** - Professional tools and API ecosystem  
- [ ] **Open Source Release** - Feature-complete platform with community contribution guidelines  
- [ ] **Proactive Health Features** - Automated reminders, health alerts, and preventive care suggestions


## 🗺️ AI Agent Evaluation & Quality Assurance:
Rigorous evaluation is critical for healthcare AI,  we're implementing comprehensive testing methodologies to ensure both Agent 1 and Agent 2 are reliable, measurable, and continuously improving rather than relying on unpredictable "AI magic." 

Our evaluation implementation includes conversation quality metrics (information extraction accuracy, completion rates, and boundary compliance), user intent analysis to optimize conversation flows for common scenarios, performance benchmarking with structured testing and defined SLAs, and iterative optimization through data-driven improvements based on real user interaction patterns and feedback loops.





---

## 🔐 Environment Variables

This project uses environment variables to securely manage external service credentials and configurations.

Create a `.env` file at the root of the project with the following keys:

```bash
# Supabase - DONT WORRY THIS IS A DISPOSABLE SUPABASE INSTANCE YOU CAN USE OUR  KEYS
SUPABASE_URL_NEW="https://pcygqqevesxpeeyxxfjw.supabase.co"
SUPABASE_ANON_KEY_NEW="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBjeWdxcWV2ZXN4cGVleXh4Zmp3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY4Njc3NzMsImV4cCI6MjA2MjQ0Mzc3M30.HRKiFi4z4Z3x0A7zuUEbeFbQT5NhVBEssvdWZR_iUHU"

# AWS Bedrock
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key

```

## 🚀 Getting Started: Installation Guide

Follow these steps to get Akasi.ai running on your local machine:

### ⚠️ **Prerequisites: AWS Bedrock Setup Required**

**Important:** Akasi.ai currently requires AWS Bedrock for AI functionality. We haven't yet enabled support for other LLM providers through OpenRouter, so AWS Bedrock is mandatory for the application to work.

**Before proceeding with installation, you must:**

1. **Create an AWS Account** (if you don't have one)
2. **Enable AWS Bedrock Service** in your AWS account
3. **Request Access to Anthropic Models** in AWS Bedrock:
   - Claude 3.5 Sonnet v2 (primary model)
   - Claude 3.7 Sonnet (for image analysis)
   - Claude 4 variants (if available in your region)
4. **Set up IAM Permissions** for Bedrock access
5. **Generate AWS Access Keys** with appropriate Bedrock permissions

**AWS Setup Steps:**
- Navigate to AWS Bedrock console
- Request model access for Anthropic Claude models
- Create IAM user/role with `bedrock:InvokeModel` permissions
- Generate access keys for your application

Once AWS Bedrock is properly configured, add your AWS credentials to the environment variables as specified in the Environment Variables section.

### 1. Fork the Repository (Optional but Recommended for Contribution)
If you plan to contribute or experiment, start by forking this repository to your own GitHub account.

### 2. Clone the Repository
Clone the repository to your local machine:

```bash
git clone https://github.com/GenAIPHBuilders-org/team-akasi.ai-2025.git
cd team-akasi.ai-2025
```

### 3. Create and Activate a Python Virtual Environment
It's highly recommended to use a virtual environment to manage project dependencies.

```bash
# Create a virtual environment (e.g., named 'venv')
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 4. Install Dependencies
Install all the required packages listed in requirements.txt:

```bash
pip install -r requirements.txt
```

### 5. Set Up Environment Variables
Create a `.env` file in the root directory of the project. Copy the contents from `.env.example` (if provided) or add the necessary variables as specified in the "Environment Variables" section below.

### 6. Run the Application
Once the dependencies are installed and environment variables are set, you can run the application:

```bash
python main.py
```

The application should now be running, and you can access it as indicated by the FastHTML server output (usually http://127.0.0.1:8000).

### Test User Credentials
You can log in with the following test user:
- **Email:** testuser1@gmail.com
- **Password:** test1234




## Join Us
We're looking for partners to help us build akasi.ai:
- Early testers with chronic health conditions
- Healthcare professionals interested in innovation
- Mentors who understand both health and technology

## License
This project is licensed under the MIT License - see the LICENSE file for details.