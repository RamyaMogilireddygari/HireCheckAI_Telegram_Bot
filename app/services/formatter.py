import html
from typing import List, Dict, Any, Optional
from app.services.scoring import AnalysisResult, generate_progress_bar


class TelegramFormatter:
    @staticmethod
    def escape(text: str) -> str:
        return html.escape(str(text)) if text else ""

    @classmethod
    def welcome_message(cls) -> str:
        return (
            "👋 <b>yo! welcome to HireCheck</b>\n\n"
            "<i>Before you hit Apply, let AI hit you with the reality check.</i> 😭\n\n"
            "Send me:\n"
            "📄 <b>your resume</b> (PDF / DOCX)\n"
            "💼 <b>the job description</b> (text or file)\n\n"
            "I'll tell you:\n"
            "🎯 <b>how well you match</b>\n"
            "✅ <b>what you already have</b>\n"
            "❌ <b>what you're missing</b>\n"
            "💡 <b>what to fix next</b>\n"
            "📚 <b>what to learn</b>\n\n"
            "<i>No corporate yapping. Promise.</i> 🔥"
        )

    @classmethod
    def how_it_works_message(cls) -> str:
        return (
            "❓ <b>HOW HIRECHECK WORKS</b>\n\n"
            "1️⃣ <b>Upload Resumes</b>: Drop 1 or more resumes (PDF or DOCX). We extract your real skills & receipts.\n\n"
            "2️⃣ <b>Drop Job Description</b>: Paste the text or upload a JD PDF.\n\n"
            "3️⃣ <b>Evidence-Based AI Match</b>: We evaluate 5 objective pillars:\n"
            "   • 40% Required Skills\n"
            "   • 25% Preferred Skills\n"
            "   • 15% Real Experience\n"
            "   • 10% Education\n"
            "   • 10% Keywords / Responsibilities\n\n"
            "4️⃣ <b>Multi-Resume Battle</b>: If you upload 2+ resumes, we rank them 🥇🥈🥉 to find the strongest match!\n\n"
            "5️⃣ <b>Get Receipts & Roasts</b>: Get actionable bullet fixes, recruiter POV, and top verified courses.\n\n"
            "Ready to test your resume?"
        )

    @classmethod
    def resume_received_message(cls, filename: str, count: int) -> str:
        return (
            f"✅ <b>Resume {count} received!</b>\n"
            f"📄 <code>{cls.escape(filename)}</code>\n\n"
            "Keep them coming (upload another resume) or tap below when you're ready to drop the Job Description! 👀"
        )

    @classmethod
    def jd_prompt_message(cls, resume_count: int) -> str:
        return (
            f"💼 <b>Bet! I got your {resume_count} resume(s).</b> 👀\n\n"
            "Now drop the <b>Job Description</b>.\n\n"
            "You can:\n"
            "📝 <i>Paste the JD text right here</i>\n"
            "📄 <i>Or upload a JD PDF / DOCX file</i>"
        )

    @classmethod
    def main_result(cls, result: AnalysisResult, total_resumes: int = 1, current_idx: int = 1) -> str:
        # Format matched skills
        all_matched = result.required_skills.matched + result.preferred_skills.matched
        if all_matched:
            matched_str = "\n".join(f"• <b>{cls.escape(s)}</b>" for s in all_matched[:8])
        else:
            matched_str = "• <i>General engineering fundamentals</i>"

        # Format missing skills
        all_missing = result.required_skills.missing + result.preferred_skills.missing
        if all_missing:
            missing_str = "\n".join(f"• <b>{cls.escape(s)}</b>" for s in all_missing[:6])
        else:
            missing_str = "• <i>None! You hit all primary requirements!</i> 🎉"

        # Format courses
        courses_str = ""
        if result.courses:
            for idx, c in enumerate(result.courses[:3], 1):
                courses_str += f"{idx}️⃣ <a href=\"{c.url}\"><b>{cls.escape(c.title)}</b></a> <i>({cls.escape(c.provider)})</i>\n"
        else:
            courses_str = "1️⃣ <a href=\"https://aws.amazon.com/training/\"><b>Cloud Computing Fundamentals</b></a>\n"

        multi_header = f" <i>(Resume {current_idx} of {total_resumes})</i>" if total_resumes > 1 else ""

        return (
            f"🎯 <b>RESUME MATCH</b>{multi_header}\n\n"
            f"📄 <b>{cls.escape(result.resume_name)}</b>\n\n"
            f"<b>{result.score:.1f} / 10</b>\n"
            f"{result.verdict_emoji} <b>{cls.escape(result.verdict)}</b>\n\n"
            f"<i>{cls.escape(result.verdict_subtitle)}</i>\n\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"✅ <b>SKILLS MATCHING</b>\n\n"
            f"{matched_str}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"❌ <b>SKILLS MISSING</b>\n\n"
            f"{missing_str}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"💡 <b>WHAT NOW?</b>\n\n"
            f"{cls.escape(result.what_now)}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"📚 <b>TOP 3 COURSES FOR YOU</b>\n\n"
            f"{courses_str}\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"🚀 <b>APPLY FOR THIS ROLE?</b>\n\n"
            f"<b>{cls.escape(result.application_ready_text)}</b>\n"
            f"<i>{cls.escape(result.application_ready_reason)}</i>"
        )

    @classmethod
    def resume_battle(cls, results: List[AnalysisResult]) -> str:
        # Sort descending by score
        sorted_results = sorted(results, key=lambda x: x.score, reverse=True)
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

        lines = []
        for idx, res in enumerate(sorted_results):
            medal = medals[idx] if idx < len(medals) else f"{idx+1}️⃣"
            tag = " 🔥" if idx == 0 and res.score >= 8.0 else ""
            lines.append(f"{medal} <b>{cls.escape(res.resume_name)}</b>\n   <b>{res.score:.1f} / 10</b>{tag}")

        winner = sorted_results[0]
        return (
            "🥊 <b>RESUME BATTLE</b>\n"
            "<i>Which version matches this JD best?</i>\n\n"
            + "\n\n".join(lines)
            + "\n\n━━━━━━━━━━━━━━━━━━\n\n"
            f"🏆 <b>{cls.escape(winner.resume_name)}</b> is currently the strongest match for this role!\n\n"
            "Tap below to view full breakdown or roast the top resume."
        )

    @classmethod
    def why_score(cls, result: AnalysisResult) -> str:
        bd = result.breakdown
        req_bar = generate_progress_bar(bd.required_skills_pct, 12)
        pref_bar = generate_progress_bar(bd.preferred_skills_pct, 12)
        exp_bar = generate_progress_bar(bd.experience_pct, 12)
        edu_bar = generate_progress_bar(bd.education_pct, 12)
        kw_bar = generate_progress_bar(bd.keywords_pct, 12)

        # Summary explanation
        missing = result.required_skills.missing
        if missing:
            gap_text = f"Your biggest gaps are in <b>{cls.escape(', '.join(missing[:2]))}</b>."
        else:
            gap_text = "You match the core technical skills with strong evidence."

        return (
            f"🧠 <b>SCORE BREAKDOWN</b>\n"
            f"📄 <i>{cls.escape(result.resume_name)}</i>\n\n"
            f"<b>Required Skills</b> (40% weight)\n"
            f"<code>{req_bar}</code> <b>{bd.required_skills_pct:.0f}%</b>\n\n"
            f"<b>Preferred Skills</b> (25% weight)\n"
            f"<code>{pref_bar}</code> <b>{bd.preferred_skills_pct:.0f}%</b>\n\n"
            f"<b>Experience Depth</b> (15% weight)\n"
            f"<code>{exp_bar}</code> <b>{bd.experience_pct:.0f}%</b>\n\n"
            f"<b>Education & Credentials</b> (10% weight)\n"
            f"<code>{edu_bar}</code> <b>{bd.education_pct:.0f}%</b>\n\n"
            f"<b>Keywords & Responsibilities</b> (10% weight)\n"
            f"<code>{kw_bar}</code> <b>{bd.keywords_pct:.0f}%</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"🎯 <b>FINAL CALCULATED SCORE:</b> <b>{result.score:.1f} / 10</b>\n\n"
            f"📌 <b>In simple terms:</b>\n"
            f"{gap_text}"
        )

    @classmethod
    def roast_message(cls, result: AnalysisResult) -> str:
        roast = result.roast
        if not roast:
            roast = result.weak_bullets[0] if result.weak_bullets else None

        if not roast:
            return (
                "🔥 <b>RESUME ROAST</b>\n\n"
                "Okay bestie... your bullets are actually clean! No major cringe detected. 😭\n"
                "Keep shipping and keep receipts ready."
            )

        why_lines = "\n".join(f"✅ {cls.escape(w)}" for w in roast.why_better)
        return (
            "🔥 <b>RESUME ROAST</b>\n\n"
            "<i>Okay bestie... time for some honesty.</i> 😭\n\n"
            "💀 <b>YOUR BULLET:</b>\n"
            f"<i>\"{cls.escape(roast.original)}\"</i>\n\n"
            f"🚨 <b>Verdict:</b> {cls.escape(roast.problem)}\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "✨ <b>TRY THIS INSTEAD:</b>\n\n"
            f"<b>\"{cls.escape(roast.improved)}\"</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "🧠 <b>Why it's 10x better:</b>\n\n"
            f"{why_lines}\n\n"
            "<i>Now THAT has receipts. 🧾</i>"
        )

    @classmethod
    def biggest_gap_message(cls, result: AnalysisResult) -> str:
        gap = result.biggest_gap
        course_str = ""
        if gap.course:
            course_str = (
                f"\n━━━━━━━━━━━━━━━━━━\n\n"
                f"📚 <b>RECOMMENDED FIX COURSE:</b>\n"
                f"👉 <a href=\"{gap.course['url']}\"><b>{cls.escape(gap.course['title'])}</b></a> <i>({cls.escape(gap.course.get('provider', 'Free Tutorial'))})</i>\n"
            )

        return (
            f"🚨 <b>BIGGEST GAP</b>\n\n"
            f"🎯 <b>{cls.escape(gap.skill)}</b>\n"
            f"Priority: <b>🔥 {cls.escape(gap.priority)}</b>\n\n"
            f"{cls.escape(gap.reason)}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"⚡ <b>HOW TO FIX THIS FIRST:</b>\n\n"
            f"{cls.escape(gap.how_to_fix)}"
            f"{course_str}"
        )

    @classmethod
    def receipts_message(cls, result: AnalysisResult) -> str:
        if not result.receipts:
            return "🧾 <b>RECEIPTS</b>\n\nNo specific receipts extracted yet."

        items_str = []
        for r in result.receipts[:6]:
            icon = "✅" if r.status == "MATCHED" else ("⚠️" if r.status == "PARTIAL" else "❌")
            items_str.append(
                f"{icon} <b>{cls.escape(r.skill)}</b> <i>({r.status})</i>\n"
                f"Evidence: <i>\"{cls.escape(r.evidence)}\"</i>\n"
                f"Confidence: <b>{cls.escape(r.confidence)}</b>"
            )

        return (
            f"🧾 <b>SHOW RECEIPTS</b>\n"
            f"<i>Evidence found in {cls.escape(result.resume_name)}:</i>\n\n"
            + "\n\n━━━━━━━━━━━━━━━━━━\n\n".join(items_str)
        )

    @classmethod
    def recruiter_pov_message(cls, result: AnalysisResult) -> str:
        pov = result.recruiter_pov
        return (
            "👀 <b>RECRUITER POV</b>\n\n"
            "💚 <b>First impression:</b>\n"
            f"<i>\"{cls.escape(pov.first_impression)}\"</i>\n\n"
            "👀 <b>Then:</b>\n"
            f"<i>\"{cls.escape(pov.then)}\"</i>\n\n"
            "🚨 <b>Concerns:</b>\n"
            f"<i>\"{cls.escape(pov.concerns)}\"</i>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📌 <b>Recruiter Verdict:</b>\n"
            f"{cls.escape(pov.takeaway)}"
        )

    @classmethod
    def glow_up_message(cls, result: AnalysisResult) -> str:
        bullets = result.weak_bullets or ([result.roast] if result.roast else [])
        if not bullets:
            return "🪞 <b>RESUME GLOW-UP</b>\n\nYour bullets look crisp!"

        b = bullets[0]
        return (
            "🪞 <b>RESUME GLOW-UP</b>\n\n"
            "💀 <b>BEFORE:</b>\n"
            f"<i>\"{cls.escape(b.original)}\"</i>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "🔥 <b>AFTER:</b>\n"
            f"<b>\"{cls.escape(b.improved)}\"</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "✨ <b>WHAT CHANGED:</b>\n"
            "• Active engineering verbs ↑\n"
            "• Technical specificity ↑\n"
            "• Zero fake fluff ↑"
        )

    @classmethod
    def skill_dna_message(cls, result: AnalysisResult) -> str:
        dna = result.skill_dna
        if not dna:
            return "🧬 <b>SKILL DNA</b>\n\nAnalyzing skill distribution..."

        lines = []
        for cat in dna:
            c_bar = generate_progress_bar(cat.candidate_pct, 8)
            j_bar = generate_progress_bar(cat.jd_pct, 8)
            lines.append(
                f"<b>{cls.escape(cat.category)}</b>\n"
                f"You: <code>{c_bar}</code> {cat.candidate_pct}%\n"
                f"JD:  <code>{j_bar}</code> {cat.jd_pct}%"
            )

        match_score = int(round(result.score * 10))
        return (
            "🧬 <b>YOUR SKILL DNA vs JOB DNA</b>\n\n"
            + "\n\n".join(lines)
            + "\n\n━━━━━━━━━━━━━━━━━━\n\n"
            f"🎯 <b>OVERALL DNA MATCH:</b> <b>{match_score}%</b> 🔥"
        )

    @classmethod
    def cap_check_message(cls, result: AnalysisResult) -> str:
        caps = result.cap_checks
        if not caps:
            return "🕵️ <b>CAP CHECK</b>\n\nNo exaggerated claims detected in your resume!"

        lines = []
        for c in caps:
            lines.append(
                f"🎯 <b>Claim:</b> <i>\"{cls.escape(c.claim)}\"</i>\n"
                f"Verdict: <b>{cls.escape(c.verdict)}</b>\n"
                f"💡 <i>{cls.escape(c.suggestion)}</i>"
            )

        return (
            "🕵️ <b>CAP CHECK</b>\n"
            "<i>Detecting exaggerated buzzwords vs actual receipts</i> 👀\n\n"
            + "\n\n━━━━━━━━━━━━━━━━━━\n\n".join(lines)
        )
