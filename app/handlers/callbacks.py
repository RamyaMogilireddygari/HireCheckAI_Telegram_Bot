import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from app.session import session_manager
from app.services.formatter import TelegramFormatter
from app.services.local_analyzer import LocalAnalyzer
from app.services.ai_service import AIService
from app.handlers.keyboards import (
    welcome_keyboard,
    resume_uploaded_keyboard,
    main_result_keyboard,
    battle_keyboard,
    subview_back_keyboard,
)

logger = logging.getLogger(__name__)

SAMPLE_RESUME_TEXT = """
Candidate: Alex Chen
Email: alex.chen@example.com | GitHub: github.com/alexchen | Portfolio: alexchen.dev

SUMMARY:
Passionate Software Engineer with 2+ years of hands-on experience building machine learning models and scalable web applications using Python and React.

TECHNICAL SKILLS:
- Languages: Python, JavaScript, SQL, HTML/CSS
- ML / Data: Machine Learning, Pandas, Scikit-learn, NumPy, Data Cleaning, Data Visualization
- Web & APIs: React, Node.js, REST APIs, JSON
- Tools: Git, GitHub, VS Code, Linux

EXPERIENCE:
AI/ML Engineering Intern — TechNova Solutions (Jan 2023 – Dec 2023)
• Worked on machine learning projects and data pipelines.
• Built an NLP pipeline using Python and Scikit-learn for text classification.
• Developed REST APIs to serve machine learning model predictions to frontend applications.
• Collaborated with engineering teams to integrate analytics dashboards.

PROJECTS:
1. Customer Churn Prediction Engine
• Built a classification model using Python, Pandas, and Scikit-learn to predict user churn.
• Processed and cleaned over 50,000 user activity records.

2. AI Resume Analyzer & Matcher
• Created a text processing app using Python and REST APIs.
• Extracted key skills and computed similarity metrics between resumes and job postings.

3. E-Commerce Web Application
• Built a responsive web app using React and Node.js with product catalog and shopping cart.

EDUCATION:
Bachelor of Technology in Computer Science & Engineering
Apex Institute of Technology, Graduated 2023 (GPA: 3.8/4.0)
"""

SAMPLE_JD_TEXT = """
Role: AI/ML Software Engineer
Company: CloudScale AI
Location: Remote / Hybrid

ABOUT THE ROLE:
We are looking for an AI/ML Engineer to build, deploy, and scale machine learning systems and intelligent APIs in production.

REQUIRED QUALIFICATIONS:
• Strong programming proficiency in Python.
• Practical hands-on experience in Machine Learning and data science (Pandas, Scikit-learn).
• Solid understanding of relational databases and SQL.
• Hands-on experience with Docker containerization.
• Practical cloud infrastructure experience with Amazon Web Services (AWS - EC2, S3, Lambda).

PREFERRED QUALIFICATIONS:
• Experience with FastAPI or Flask for high-performance microservices.
• Familiarity with Kubernetes and container orchestration.
• Experience with modern frontend frameworks like React.

RESPONSIBILITIES:
• Build end-to-end machine learning pipelines from preprocessing to model validation.
• Package ML models into Docker containers and deploy on AWS cloud.
• Develop scalable REST APIs and collaborate with product teams.
• Maintain high code quality, automated testing, and CI/CD workflows.
"""


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data:
        return

    await query.answer()
    data = query.data
    user = update.effective_user
    if not user:
        return

    session = session_manager.get_session(user.id)

    # 1. Navigation callbacks
    if data == "nav_upload" or data == "nav_upload_more":
        session.active_view = "awaiting_resume"
        msg = (
            "📄 <b>Drop your resume below!</b>\n\n"
            "Supported formats: <b>PDF</b> (recommended) or <b>DOCX</b>.\n"
            "<i>You can upload up to 5 resumes to compare them!</i>"
        )
        await query.edit_message_text(
            text=msg,
            parse_mode=ParseMode.HTML,
            reply_markup=welcome_keyboard()
        )
        return

    if data == "nav_how_it_works":
        await query.edit_message_text(
            text=TelegramFormatter.how_it_works_message(),
            parse_mode=ParseMode.HTML,
            reply_markup=welcome_keyboard(),
            disable_web_page_preview=True
        )
        return

    if data == "nav_sample_demo":
        # Load sample demo session
        session.clear()
        session.add_resume(filename="Alex_Resume_ML.pdf", text=SAMPLE_RESUME_TEXT)
        session.set_jd(text=SAMPLE_JD_TEXT, source_type="text")

        loading_msg = await query.edit_message_text(
            "🧠 <i>Analyzing sample candidate vs AI/ML Job Description...</i>",
            parse_mode=ParseMode.HTML
        )

        analysis = await AIService.analyze_resume(
            resume_text=SAMPLE_RESUME_TEXT,
            jd_text=SAMPLE_JD_TEXT,
            resume_name="Alex_Resume_ML.pdf",
            resume_id=1
        )
        session.results[1] = analysis
        session.current_resume_id = 1
        session.active_view = "main"

        main_text = TelegramFormatter.main_result(analysis, total_resumes=1, current_idx=1)
        await query.edit_message_text(
            text=main_text,
            parse_mode=ParseMode.HTML,
            reply_markup=main_result_keyboard(is_multi=False, current_resume_id=1, total_resumes=1),
            disable_web_page_preview=True
        )
        return

    if data == "nav_vibe":
        vibes = ["genz", "clean", "spicy"]
        curr_idx = vibes.index(session.vibe) if session.vibe in vibes else 0
        next_vibe = vibes[(curr_idx + 1) % len(vibes)]
        session.vibe = next_vibe

        vibe_names = {
            "genz": "Gen-Z Career Bestie 🔥💅 (Default)",
            "clean": "Pinterest Minimalist 🌸✨",
            "spicy": "Savage Reality Check 💀🌶️"
        }
        msg = (
            f"🎨 <b>Vibe updated!</b>\n\n"
            f"Current Vibe: <b>{vibe_names[next_vibe]}</b>\n\n"
            "Ready to test your resume?"
        )
        await query.edit_message_text(
            text=msg,
            parse_mode=ParseMode.HTML,
            reply_markup=welcome_keyboard()
        )
        return

    if data == "nav_jd_prompt":
        session.active_view = "awaiting_jd"
        msg = TelegramFormatter.jd_prompt_message(len(session.resumes))
        await query.edit_message_text(
            text=msg,
            parse_mode=ParseMode.HTML
        )
        return

    if data == "nav_reset":
        session_manager.reset_session(user.id)
        msg = (
            "🔄 <b>Session cleared!</b>\n\n"
            "Send me your resume (PDF/DOCX) or tap below to get started."
        )
        await query.edit_message_text(
            text=msg,
            parse_mode=ParseMode.HTML,
            reply_markup=welcome_keyboard()
        )
        return

    # 2. Results & Detailed Views
    # Resolve target resume_id
    target_id = session.current_resume_id or 1
    if "_" in data:
        parts = data.split("_")
        if parts[-1].isdigit():
            target_id = int(parts[-1])
            session.current_resume_id = target_id

    result = session.results.get(target_id)
    if not result and session.results:
        result = next(iter(session.results.values()))
        target_id = result.resume_id
        session.current_resume_id = target_id

    if not result:
        await query.edit_message_text(
            "⚠️ <b>No active analysis found.</b>\n\n"
            "Please upload your resume to start!",
            parse_mode=ParseMode.HTML,
            reply_markup=welcome_keyboard()
        )
        return

    total_resumes = len(session.results)
    is_multi = total_resumes > 1

    # Main view
    if data.startswith("view_main"):
        session.active_view = "main"
        # Find index in results
        keys = list(session.results.keys())
        curr_idx = keys.index(target_id) + 1 if target_id in keys else 1
        main_text = TelegramFormatter.main_result(result, total_resumes=total_resumes, current_idx=curr_idx)
        await query.edit_message_text(
            text=main_text,
            parse_mode=ParseMode.HTML,
            reply_markup=main_result_keyboard(is_multi=is_multi, current_resume_id=target_id, total_resumes=total_resumes),
            disable_web_page_preview=True
        )
        return

    # Score breakdown
    if data.startswith("view_why_score"):
        session.active_view = "why_score"
        score_text = TelegramFormatter.why_score(result)
        await query.edit_message_text(
            text=score_text,
            parse_mode=ParseMode.HTML,
            reply_markup=subview_back_keyboard(target_id, current_view="why_score")
        )
        return

    # Roast
    if data.startswith("view_roast"):
        session.active_view = "roast"
        roast_text = TelegramFormatter.roast_message(result)
        await query.edit_message_text(
            text=roast_text,
            parse_mode=ParseMode.HTML,
            reply_markup=subview_back_keyboard(target_id, current_view="roast")
        )
        return

    # Biggest gap
    if data.startswith("view_biggest_gap"):
        session.active_view = "biggest_gap"
        gap_text = TelegramFormatter.biggest_gap_message(result)
        await query.edit_message_text(
            text=gap_text,
            parse_mode=ParseMode.HTML,
            reply_markup=subview_back_keyboard(target_id, current_view="biggest_gap"),
            disable_web_page_preview=True
        )
        return

    # Receipts
    if data.startswith("view_receipts"):
        session.active_view = "receipts"
        receipts_text = TelegramFormatter.receipts_message(result)
        await query.edit_message_text(
            text=receipts_text,
            parse_mode=ParseMode.HTML,
            reply_markup=subview_back_keyboard(target_id, current_view="receipts")
        )
        return

    # Recruiter POV
    if data.startswith("view_recruiter"):
        session.active_view = "recruiter"
        rec_text = TelegramFormatter.recruiter_pov_message(result)
        await query.edit_message_text(
            text=rec_text,
            parse_mode=ParseMode.HTML,
            reply_markup=subview_back_keyboard(target_id, current_view="recruiter")
        )
        return

    # Glow-Up
    if data.startswith("view_glowup"):
        session.active_view = "glowup"
        glow_text = TelegramFormatter.glow_up_message(result)
        await query.edit_message_text(
            text=glow_text,
            parse_mode=ParseMode.HTML,
            reply_markup=subview_back_keyboard(target_id, current_view="glowup")
        )
        return

    # Skill DNA
    if data.startswith("view_dna"):
        session.active_view = "dna"
        dna_text = TelegramFormatter.skill_dna_message(result)
        await query.edit_message_text(
            text=dna_text,
            parse_mode=ParseMode.HTML,
            reply_markup=subview_back_keyboard(target_id, current_view="dna")
        )
        return

    # Cap Check
    if data.startswith("view_cap"):
        session.active_view = "cap"
        cap_text = TelegramFormatter.cap_check_message(result)
        await query.edit_message_text(
            text=cap_text,
            parse_mode=ParseMode.HTML,
            reply_markup=subview_back_keyboard(target_id, current_view="cap")
        )
        return

    # Resume battle
    if data == "view_battle":
        session.active_view = "battle"
        battle_text = TelegramFormatter.resume_battle(list(session.results.values()))
        winner = sorted(session.results.values(), key=lambda x: x.score, reverse=True)[0]
        await query.edit_message_text(
            text=battle_text,
            parse_mode=ParseMode.HTML,
            reply_markup=battle_keyboard(winner.resume_id)
        )
        return

    # Cycle next resume
    if data.startswith("nav_next_resume"):
        keys = list(session.results.keys())
        if keys:
            curr_pos = keys.index(target_id) if target_id in keys else 0
            next_pos = (curr_pos + 1) % len(keys)
            next_id = keys[next_pos]
            session.current_resume_id = next_id
            next_result = session.results[next_id]
            main_text = TelegramFormatter.main_result(next_result, total_resumes=total_resumes, current_idx=next_pos + 1)
            await query.edit_message_text(
                text=main_text,
                parse_mode=ParseMode.HTML,
                reply_markup=main_result_keyboard(is_multi=is_multi, current_resume_id=next_id, total_resumes=total_resumes),
                disable_web_page_preview=True
            )
        return
