# HireCheck AI 🤖

> AI-powered resume and job description compatibility analyzer available through Telegram.

[![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)](https://www.python.org/)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram)](https://telegram.org/)
[![Gemini](https://img.shields.io/badge/AI-Gemini-8E75B2)](https://ai.google.dev/)
[![Railway](https://img.shields.io/badge/Deployed-Railway-purple)](https://railway.app/)

## 🚀 Try HireCheck AI

**[Open HireCheck AI on Telegram](https://t.me/HireCheckAI_bot)**

Upload your resume, provide a job description, and get an AI-assisted compatibility analysis with actionable suggestions.

---

## 📌 Overview

HireCheck AI is a Telegram-based AI application designed to help job seekers understand how well their resume matches a specific job description.

The bot analyzes:

- Required skills
- Preferred skills
- Experience
- Education
- Keywords and responsibilities

It then generates a compatibility score and highlights areas that can be improved.

The application is designed to make resume analysis simple and accessible directly through Telegram.

---

## ✨ Features

### 📄 Resume Analysis

Upload a resume in a supported document format and extract relevant information for analysis.

### 💼 Job Description Analysis

Provide a job description and identify the skills, requirements, responsibilities, and keywords expected for the role.

### 📊 Compatibility Score

Generate a compatibility score based on multiple job-matching factors.

### 🧠 AI-Powered Analysis

Uses an AI provider to analyze resume and job-description information and generate meaningful feedback.

### 💡 Skill Gap Suggestions

Highlights missing or weak areas and provides suggestions for improving job compatibility.

### 📚 Learning Recommendations

Provides relevant learning/course recommendations based on identified skill gaps.

### 🤖 Telegram Interface

No separate web application is required. Users can interact with HireCheck AI directly through Telegram.

### 🔐 Environment-Based Configuration

API keys and bot credentials are stored through environment variables rather than hard-coded into the source code.

### 🧪 Testing

The project includes automated tests for important application components.

---

## 🧮 Compatibility Analysis

The compatibility analysis considers the following factors:

| Factor | Weight |
|---|---:|
| Required Skills | 40% |
| Preferred Skills | 25% |
| Experience | 15% |
| Education | 10% |
| Keywords & Responsibilities | 10% |

The final result is presented as a compatibility score along with suggestions for improvement.

---

## 🔄 How It Works

```text
User
  │
  ▼
Telegram Bot
  │
  ├── Upload Resume
  │
  ├── Provide Job Description
  │
  ▼
Document Parser
  │
  ▼
Resume + JD Analysis
  │
  ├── Required Skills
  ├── Preferred Skills
  ├── Experience
  ├── Education
  └── Keywords / Responsibilities
  │
  ▼
Scoring Engine
  │
  ▼
AI Analysis
  │
  ▼
Compatibility Score
  │
  ▼
Suggestions + Recommendations
  │
  ▼
Telegram Response
