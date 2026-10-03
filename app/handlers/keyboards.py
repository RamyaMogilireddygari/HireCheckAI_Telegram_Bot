from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import Optional


def welcome_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🚀 Let's Go", callback_data="nav_upload")],
        [
            InlineKeyboardButton("❓ How It Works", callback_data="nav_how_it_works"),
            InlineKeyboardButton("📊 Sample Result", callback_data="nav_sample_demo")
        ],
        [InlineKeyboardButton("🎨 Change Vibe (Gen-Z 🔥)", callback_data="nav_vibe")]
    ]
    return InlineKeyboardMarkup(keyboard)


def resume_uploaded_keyboard(count: int) -> InlineKeyboardMarkup:
    buttons = []
    if count >= 1:
        buttons.append([InlineKeyboardButton("💼 I'm Done — Drop Job Description", callback_data="nav_jd_prompt")])
    buttons.append([
        InlineKeyboardButton("📄 Add Another Resume", callback_data="nav_upload_more"),
        InlineKeyboardButton("🔄 Clear & Restart", callback_data="nav_reset")
    ])
    return InlineKeyboardMarkup(buttons)


def main_result_keyboard(
    is_multi: bool = False,
    current_resume_id: int = 1,
    total_resumes: int = 1
) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("🔍 Why Score?", callback_data=f"view_why_score_{current_resume_id}"),
            InlineKeyboardButton("🔥 Roast Me", callback_data=f"view_roast_{current_resume_id}")
        ],
        [
            InlineKeyboardButton("🚨 Biggest Gap", callback_data=f"view_biggest_gap_{current_resume_id}"),
            InlineKeyboardButton("🧾 Receipts", callback_data=f"view_receipts_{current_resume_id}")
        ],
        [
            InlineKeyboardButton("👀 Recruiter POV", callback_data=f"view_recruiter_{current_resume_id}"),
            InlineKeyboardButton("🪞 Glow-Up", callback_data=f"view_glowup_{current_resume_id}")
        ],
        [
            InlineKeyboardButton("🧬 Skills DNA", callback_data=f"view_dna_{current_resume_id}"),
            InlineKeyboardButton("🕵️ Cap Check", callback_data=f"view_cap_{current_resume_id}")
        ]
    ]

    if is_multi and total_resumes > 1:
        keyboard.append([
            InlineKeyboardButton("🥊 Resume Battle", callback_data="view_battle"),
            InlineKeyboardButton(f"📄 Next Resume ({current_resume_id}/{total_resumes})", callback_data=f"nav_next_resume_{current_resume_id}")
        ])

    keyboard.append([
        InlineKeyboardButton("🔄 New Check / Start Over", callback_data="nav_reset")
    ])

    return InlineKeyboardMarkup(keyboard)


def battle_keyboard(winner_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🔍 View Top Resume Analysis →", callback_data=f"view_main_{winner_id}")],
        [
            InlineKeyboardButton("🔥 Roast Top One", callback_data=f"view_roast_{winner_id}"),
            InlineKeyboardButton("🚨 Biggest Gap", callback_data=f"view_biggest_gap_{winner_id}")
        ],
        [InlineKeyboardButton("🔄 New Check / Start Over", callback_data="nav_reset")]
    ]
    return InlineKeyboardMarkup(keyboard)


def subview_back_keyboard(current_resume_id: int, current_view: str = "score") -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Match Result", callback_data=f"view_main_{current_resume_id}")]
    ]

    # Contextual quick jumps
    quick_jumps = []
    if current_view != "roast":
        quick_jumps.append(InlineKeyboardButton("🔥 Roast", callback_data=f"view_roast_{current_resume_id}"))
    if current_view != "why_score":
        quick_jumps.append(InlineKeyboardButton("🔍 Why Score?", callback_data=f"view_why_score_{current_resume_id}"))
    if current_view != "biggest_gap":
        quick_jumps.append(InlineKeyboardButton("🚨 Gap", callback_data=f"view_biggest_gap_{current_resume_id}"))

    if quick_jumps:
        keyboard.append(quick_jumps[:3])

    return InlineKeyboardMarkup(keyboard)
