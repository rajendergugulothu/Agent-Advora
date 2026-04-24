"""
Content generation service.

Generates daily Instagram post drafts for financial advisors and agencies.
The content positions the advisor as a trusted expert — building credibility,
attracting clients, and educating their audience on personal finance across
every life stage and situation.

Uses a performance feedback loop: top/worst performing themes per user
are injected into the prompt so the model learns what resonates with
each advisor's specific audience over time.
"""

import json
import random

from openai import AsyncOpenAI
from supabase import AsyncClient

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)
settings = get_settings()

_openai = AsyncOpenAI(api_key=settings.openai_api_key)


# ── Theme pools ───────────────────────────────────────────────────────────────
# Organized by life stage and topic.
# 80% educational content (builds audience trust and reach).
# 20% advisor authority content (builds personal brand and drives inquiries).

THEMES_BY_CATEGORY: dict[str, list[str]] = {

    "new_job_income": [
        "what to do with your first paycheck from a new job",
        "how to set up your finances when you start a new job",
        "should you max out your 401k right away or start slow",
        "how much of your salary should go to savings vs expenses",
        "understanding your employee benefits package",
        "health insurance options when you start a new job",
        "how to negotiate your salary and why it matters for your financial future",
        "what is a W-4 and how should you fill it out",
        "the first 5 financial moves to make when you land a new job",
        "how a raise should change your budget",
        "what to do if your job has no retirement benefits",
        "side income and how it changes your taxes",
        "how to evaluate a job offer beyond just the salary",
        "what stock options and RSUs actually mean for your finances",
        "how to handle a bonus the right way",
        "what to do financially when you lose your job",
        "severance pay - what to do with it",
        "how to manage finances during a career transition",
    ],

    "budgeting_expenses": [
        "the 50-30-20 rule for budgeting explained simply",
        "how to create a personal budget that actually works",
        "zero-based budgeting - what it is and who it works for",
        "how to track your spending without it being stressful",
        "lifestyle creep - what it is and how to stop it",
        "how to cut expenses without feeling deprived",
        "fixed vs variable expenses - why the difference matters",
        "the real cost of small daily habits on your finances",
        "how to budget when your income is irregular",
        "what a money date is and why couples need one",
        "how to budget for irregular big expenses like car repairs",
        "how subscriptions are quietly draining your budget",
        "the envelope budgeting method explained",
        "how to build a budget you will actually stick to",
        "the psychology behind overspending and how to fix it",
        "how to handle unexpected expenses without going into debt",
    ],

    "savings_emergency_fund": [
        "how much money you should have in an emergency fund",
        "why an emergency fund is the foundation of any financial plan",
        "signs your emergency fund is not enough",
        "where to keep your emergency fund for best returns",
        "how to build an emergency fund when money is tight",
        "high yield savings accounts explained simply",
        "how to automate your savings and forget about it",
        "the difference between saving money and building wealth",
        "savings goals to hit before age 30, 40, and 50",
        "small savings habits that add up to big money over time",
        "sinking funds - what they are and how to use them",
        "how much cash is too much to keep in a savings account",
        "the best savings strategies for different income levels",
        "how to save money faster without earning more",
    ],

    "retirement_planning": [
        "why starting retirement savings in your 20s changes everything",
        "how much money you actually need to retire comfortably",
        "common retirement planning mistakes people make",
        "the power of compound interest for retirement savings",
        "what happens if you have no retirement plan",
        "retirement savings milestones by age",
        "what is a 401k and how does it really work",
        "traditional IRA vs Roth IRA - which is better for you",
        "how employer 401k matching works and why you should never leave it",
        "what to do with your 401k when you leave a job",
        "can you retire early - what the math actually looks like",
        "how to calculate your retirement number",
        "what social security actually pays and why you need more",
        "the 4% rule for retirement withdrawals explained",
        "how to catch up on retirement savings if you started late",
        "sequence of returns risk - the retirement danger nobody talks about",
        "what is a pension and how does it differ from a 401k",
        "how to create guaranteed income in retirement",
        "what is an annuity and who should consider one",
        "Medicare explained - what it covers and what it does not",
        "how to retire without running out of money",
        "what to do with retirement savings in your 50s",
        "pre-retirement checklist - what to do 5 years before you retire",
    ],

    "investments": [
        "investing for beginners - where to start",
        "the difference between saving and investing",
        "why staying invested during a market dip is smart",
        "how to build a simple diversified investment portfolio",
        "investment mistakes that cost people thousands",
        "what is compound interest and why it matters for investors",
        "index funds vs actively managed funds explained simply",
        "what is dollar cost averaging and why it works",
        "stocks vs bonds - what every investor should understand",
        "how much risk should you take with your investments",
        "what is an ETF and how is it different from a mutual fund",
        "how to invest when the market feels scary",
        "why time in the market beats timing the market",
        "the real impact of investment fees on your returns",
        "how to start investing with a small amount of money",
        "what is portfolio rebalancing and when should you do it",
        "dividend investing explained simply",
        "what is a brokerage account and how do you open one",
        "how to invest for a goal that is 10 years away",
        "ESG investing - what it is and how it works",
        "what is a target date fund and is it right for you",
        "crypto as part of a portfolio - what you need to know",
        "how to think about risk vs reward in investing",
        "what new investors get wrong about the stock market",
    ],

    "debt_loans": [
        "how to pay off debt faster using the avalanche method",
        "the debt snowball vs debt avalanche - which is right for you",
        "good debt vs bad debt - what is the difference",
        "how your loan interest rate really affects what you pay",
        "signs you have too much debt",
        "how to get out of a debt cycle",
        "student loan repayment strategies explained",
        "how to pay off your mortgage faster",
        "what is a debt-to-income ratio and why lenders care about it",
        "personal loans vs credit cards - when to use which",
        "how to negotiate with creditors when you are struggling",
        "what happens when you default on a loan",
        "how to use a balance transfer to pay off credit card debt",
        "the real cost of minimum credit card payments",
        "how to get out of debt on an average income",
        "what is debt consolidation and is it a good idea",
        "how to handle debt collectors the right way",
        "payday loans - why they are dangerous and what to do instead",
    ],

    "credit": [
        "understanding your credit score and why it matters",
        "the 5 factors that make up your credit score",
        "how to build credit from scratch",
        "how to fix a bad credit score step by step",
        "what hurts your credit score that you might not know about",
        "how many credit cards should you have",
        "credit utilization explained - and how to improve it",
        "hard vs soft credit inquiries - what is the difference",
        "how long negative items stay on your credit report",
        "why you should check your credit report every year",
        "how to use credit cards without going into debt",
        "the best way to use a credit card to build wealth",
        "what is a credit freeze and when should you use one",
    ],

    "taxes": [
        "tax mistakes most people make every year",
        "how to legally reduce your tax bill",
        "tax deductions you probably didn't know you could claim",
        "why tax planning is part of financial planning",
        "what to do with your tax refund to build wealth",
        "how tax brackets actually work - most people misunderstand this",
        "what is a W-2 vs a 1099 and how does it affect your taxes",
        "how contributing to a 401k lowers your tax bill",
        "tax loss harvesting explained simply",
        "the difference between a tax deduction and a tax credit",
        "how to avoid an IRS audit",
        "self-employed taxes - what you need to know",
        "capital gains tax explained - short term vs long term",
        "how to plan for taxes as a freelancer or contractor",
        "what is the standard deduction vs itemizing",
        "how to use an HSA to save on taxes",
        "inherited money and taxes - what you need to know",
        "how rental income is taxed",
        "tax planning for business owners",
        "how marriage affects your taxes",
        "how having children changes your tax situation",
    ],

    "real_estate": [
        "renting vs buying a home - how to decide what is right for you",
        "how much house can you actually afford",
        "the true costs of buying a home beyond the down payment",
        "how mortgage interest rates affect your monthly payment",
        "what is PMI and how do you avoid it",
        "how to save for a down payment faster",
        "fixed rate vs adjustable rate mortgage - which is safer",
        "what is home equity and how to use it wisely",
        "real estate as an investment - what you need to know first",
        "how to buy your first investment property",
        "what is a HELOC and when does it make sense",
        "how to prepare financially before buying a home",
        "the financial risks of buying a home you cannot afford",
        "how property taxes work and what affects them",
        "should you pay off your mortgage early or invest instead",
        "what is house hacking and how does it build wealth",
        "how to evaluate if a rental property is worth buying",
        "what happens to your mortgage if you lose your job",
        "how to refinance your mortgage the right way",
        "the hidden costs of homeownership most buyers don't see",
        "what is a real estate investment trust - REIT",
        "downsizing in retirement - financial pros and cons",
    ],

    "vehicles": [
        "buying vs leasing a car - which is better financially",
        "how to buy a car without getting ripped off",
        "how much car can you actually afford",
        "the real cost of owning a car beyond the monthly payment",
        "how car depreciation works and why it matters",
        "new car vs used car - what the numbers actually say",
        "how to negotiate the best price on a car",
        "auto loan interest rates - how to get the best deal",
        "how to save for a car purchase the smart way",
        "is it smarter to pay cash for a car or finance it",
        "how car insurance premiums are calculated",
        "when to repair vs replace your vehicle",
        "electric vehicles - financial pros and cons",
        "how having a car payment affects your financial plan",
        "what gap insurance is and when you need it",
    ],

    "insurance_health": [
        "health insurance explained - deductibles premiums and copays",
        "HMO vs PPO vs HDHP - which health plan is right for you",
        "what is an HSA and how to use it to build wealth",
        "what is an FSA and how is it different from an HSA",
        "how to choose the right health insurance plan during open enrollment",
        "what COBRA health insurance is and when it makes sense",
        "how to handle a surprise medical bill",
        "medical debt - what your options actually are",
        "what long-term care insurance covers and who needs it",
        "how to plan for healthcare costs in retirement",
        "what Medicare does and does not cover",
        "how out-of-pocket maximums work in health insurance",
        "dental and vision insurance - are they worth it",
    ],

    "insurance_life_disability": [
        "how much life insurance does your family actually need",
        "term life vs whole life vs universal life insurance",
        "what happens to your family if you die without life insurance",
        "disability insurance - the coverage most people forget about",
        "what is short-term vs long-term disability insurance",
        "how to calculate how much life insurance you need",
        "what is critical illness insurance and who needs it",
        "group life insurance vs individual life insurance",
        "what is income protection insurance",
        "why stay-at-home spouses need life insurance too",
        "the cost of waiting to get life insurance",
        "what is a life insurance beneficiary and how to choose one",
        "how life insurance fits into your overall financial plan",
        "what is accidental death and dismemberment insurance",
        "business owner life insurance options",
    ],

    "insurance_property": [
        "what homeowners insurance actually covers",
        "renters insurance - why everyone who rents needs it",
        "how to save money on homeowners insurance",
        "what flood insurance is and who needs it",
        "umbrella insurance explained - who should have it",
        "how auto insurance coverage levels work",
        "what is liability coverage and how much do you need",
        "how to file an insurance claim the right way",
        "what happens if you are underinsured when disaster strikes",
        "how bundling insurance policies saves you money",
        "what pet insurance covers and whether it is worth it",
        "how home warranties work and when they are worth it",
    ],

    "children_parenting": [
        "financial planning when you are expecting a baby",
        "the real cost of raising a child from birth to 18",
        "how to budget for a new baby",
        "childcare costs and how to plan for them",
        "financial habits to teach your kids from a young age",
        "how to open a savings account for your child",
        "should you save for your kids college or your retirement first",
        "how to teach teenagers about money management",
        "what is a custodial account and how does it work",
        "how to set up a financial head start for your newborn",
        "allowances and chores - how to teach kids the value of money",
        "the financial impact of having a second child",
        "stay-at-home parent finances - protecting the non-earning spouse",
        "how to talk to your kids about your family finances",
        "financial lessons every teenager should know before leaving home",
        "how to prepare financially for a baby on a single income",
    ],

    "education_student_loans": [
        "how to start saving for your child's education today",
        "the real cost of a college degree in 10 years",
        "what is a 529 plan and how does it work",
        "529 plan vs Roth IRA for college savings - which is better",
        "how to choose the right college savings plan",
        "student loan repayment options explained",
        "the difference between subsidized and unsubsidized student loans",
        "how student loan interest works",
        "public service loan forgiveness - who qualifies and how it works",
        "income-driven repayment plans explained",
        "how to pay off student loans faster",
        "should you refinance your student loans",
        "how student loan debt affects your financial plan",
        "financial aid explained - FAFSA and what it means",
        "community college vs university - the financial case",
        "is a college degree worth the cost in 2025",
        "how to help your child avoid graduating with too much debt",
        "trade school vs college - a financial comparison",
        "scholarships and grants - money that never needs to be repaid",
        "how to save for education on a tight budget",
    ],

    "spouse_partner_finances": [
        "how couples should handle finances together",
        "joint accounts vs separate accounts vs both - what works best",
        "how to have productive money conversations with your partner",
        "what to do financially when you get married",
        "how marriage affects your taxes and financial plan",
        "financial planning for dual income households",
        "what is a prenuptial agreement and who should consider one",
        "how to financially protect the stay-at-home spouse",
        "what happens to finances when a spouse dies",
        "how to manage money when one spouse earns significantly more",
        "financial steps to take after losing a spouse",
        "how divorce affects your financial plan and what to prepare for",
        "protecting your finances during a separation",
        "how to rebuild finances after a divorce",
        "financial planning for widows and widowers",
        "how to combine finances with a partner who has debt",
        "life insurance planning for married couples",
        "estate planning as a couple - what you both need",
        "the financial impact of a spouse becoming disabled",
    ],

    "family_life_stages": [
        "financial steps to take in your 20s",
        "financial priorities to focus on in your 30s",
        "how to get your finances right in your 40s",
        "financial planning for your 50s - what to focus on",
        "financial planning for single parents",
        "how to support aging parents financially without wrecking your own plan",
        "sandwich generation finances - raising kids and caring for parents",
        "financial planning for blended families",
        "how to talk to your parents about their finances and estate plan",
        "what to do financially after a major life change",
        "how to recover financially after a health crisis",
        "financial planning for people with disabilities",
        "how chronic illness affects your financial plan",
        "financial planning for the self-employed",
        "how to plan finances when moving to a new country",
    ],

    "wealth_building": [
        "why saving money is not the same as building wealth",
        "net worth explained - and how to grow yours",
        "what financial freedom actually looks like",
        "money habits of financially secure people",
        "how to build generational wealth",
        "building multiple streams of income",
        "what is passive income and how do you actually build it",
        "how the wealthy think about money differently",
        "the difference between earning more and keeping more",
        "assets vs liabilities - how to shift your balance sheet",
        "how to accelerate wealth building in your 30s and 40s",
        "the role of a financial plan in building long-term wealth",
        "how to turn your income into lasting wealth",
        "what net worth milestones to aim for at each age",
        "side hustle income - how to use it to build wealth faster",
        "how to build wealth on a middle class income",
    ],

    "estate_planning": [
        "why everyone needs a will regardless of how much money they have",
        "what happens to your money if you die without a will",
        "what is a power of attorney and why you need one",
        "the difference between a will and a living trust",
        "how to make sure your retirement account goes to the right person",
        "what is a beneficiary designation and why it matters",
        "estate planning for young families",
        "how to talk to your parents about estate planning",
        "what is probate and how to avoid it",
        "digital assets and estate planning - what most people miss",
        "how to leave money to your children the right way",
        "what is an executor and how to choose one",
        "how estate taxes work",
        "what is a living will and why you need one",
        "how to store and organize your important financial documents",
    ],

    "financial_mindset": [
        "how inflation quietly eats your savings",
        "financial red flags to watch out for in your 30s",
        "common money mistakes people make and how to avoid them",
        "the cost of waiting to start your financial plan",
        "why most people never achieve financial independence",
        "the psychological side of money - why we make bad financial decisions",
        "how fear of investing keeps people poor",
        "what financial security really means for your family",
        "how to stop living paycheck to paycheck",
        "money myths that are keeping you broke",
        "the real reason most people never build wealth",
        "what your financial plan should look like at every age",
        "plan A and plan B - why every family needs a backup financial plan",
        "what would happen to your finances if you could not work for 6 months",
        "financial decisions you will regret not making sooner",
        "the difference between being rich and being wealthy",
        "why financial literacy is the most valuable skill you can have",
        "how to stop making emotional financial decisions",
        "the mindset shift that separates savers from wealth builders",
    ],

    "advisor_authority": [
        "the most common financial mistake I see clients make",
        "what I wish more people understood about financial planning",
        "3 questions every person should ask before making a financial decision",
        "why most people wait too long to get a financial plan",
        "the real cost of not having a financial advisor",
        "how a financial plan changes after major life events",
        "what a financial review actually looks like",
        "signs you need to rethink your financial strategy",
        "how I help clients identify their protection gaps",
        "what financial security really means for a family",
        "the questions my clients ask that I love answering",
        "client story: how a proper plan changed a family's future",
        "5 things I tell every new client I work with",
        "why I became a financial advisor",
        "what separates people who build wealth from those who don't",
        "how I approach financial planning differently",
        "the moment that made me realize most people need a plan",
        "what my job as a financial advisor actually looks like day to day",
        "how to know if your financial advisor is actually helping you",
        "what to look for when choosing a financial advisor",
    ],
}

ALL_EDUCATION_THEMES: list[tuple[str, str]] = [
    (theme, category)
    for category, themes in THEMES_BY_CATEGORY.items()
    if category != "advisor_authority"
    for theme in themes
]

ADVISOR_AUTHORITY_THEMES: list[str] = THEMES_BY_CATEGORY["advisor_authority"]


def _pick_theme(
    top_themes: list[dict],
    worst_themes: list[dict],
) -> tuple[str, str]:
    """
    Choose a theme with performance-weighted bias.

    Weights:
    - 20%: advisor authority content (personal brand)
    - 55%: top-performing themes for this user (exploit what works)
    - 25%: explore new themes from the full pool (avoid worst)
    """
    roll = random.random()

    if roll < 0.20:
        return random.choice(ADVISOR_AUTHORITY_THEMES), "authority"

    if roll < 0.75 and top_themes:
        chosen = random.choice(top_themes)
        return chosen["theme"], chosen.get("audience", "education")

    worst_set = {t["theme"] for t in worst_themes}
    pool = [(t, c) for t, c in ALL_EDUCATION_THEMES if t not in worst_set]
    if not pool:
        pool = ALL_EDUCATION_THEMES
    theme, _ = random.choice(pool)
    return theme, "education"


async def _get_performance_context(supabase: AsyncClient, user_id: str) -> dict:
    """Fetch top/worst themes for this user from the DB."""
    try:
        top = await supabase.rpc(
            "get_top_performing_themes", {"p_user_id": user_id, "p_limit": 5}
        ).execute()
        worst = await supabase.rpc(
            "get_worst_performing_themes", {"p_user_id": user_id, "p_limit": 5}
        ).execute()
        return {"top": top.data or [], "worst": worst.data or []}
    except Exception as exc:
        log.warning("performance_context_fetch_failed", user_id=user_id, error=str(exc))
        return {"top": [], "worst": []}


def _build_performance_note(top: list[dict], worst: list[dict]) -> str:
    lines = []
    if top:
        top_names = ", ".join(f'"{t["theme"]}"' for t in top[:3])
        lines.append(
            f"High-performing themes for this advisor's audience: {top_names}. "
            "Lean toward similar angles, formats, and depth of detail."
        )
    if worst:
        worst_names = ", ".join(f'"{t["theme"]}"' for t in worst[:3])
        lines.append(
            f"These themes underperformed: {worst_names}. "
            "Avoid repeating the same approach — try a fresh angle if used."
        )
    carousel_top = [t for t in top if t.get("post_type") == "carousel"]
    if len(carousel_top) >= 2:
        lines.append(
            "Carousel posts have driven the strongest engagement for this account. "
            "Default to carousel when content fits multiple slides."
        )
    return "\n".join(lines) if lines else ""


SYSTEM_PROMPT = """You are an expert social media strategist helping financial advisors
and financial planning agencies build trust, grow their audience, and attract clients
through Instagram.

Your role is to create content that:
- Positions the advisor as a knowledgeable, trustworthy expert people want to work with
- Educates their audience on real personal finance topics that matter at every life stage
- Covers every area of financial life: new jobs, budgeting, savings, debt, credit,
  investments, retirement, real estate, vehicles, taxes, all types of insurance,
  children and education, spouse and partner finances, estate planning, and financial mindset
- Makes followers feel understood and empowered — not sold to
- Drives saves, shares, comments, and DMs from people who want to work with the advisor

Content philosophy:
- The image carries the value. Make it worth saving.
- Caption is 2-3 lines max — reinforce the image or add a soft CTA.
- Every post should make someone think "I need to show this to my partner"
  or "I should talk to a financial advisor about this."
- Strong formats: bold stat cards, myth vs fact, checklists, step-by-step tips,
  before vs after, quote cards, numbered lists, milestone charts, real scenarios with numbers.

Tone:
- Educational content: warm, clear, jargon-free, empowering.
  Like advice from a trusted friend who happens to be a finance expert.
- Authority content: confident, genuine, conversational.
  The advisor sharing real perspective — not a sales pitch.

Never sound like an advertisement. Sound like someone who genuinely cares and wants to help.

Always respond with valid JSON only. No markdown fences. No preamble."""


async def generate_post(
    supabase: AsyncClient,
    user_id: str,
    theme: str | None = None,
    audience: str | None = None,
) -> dict:
    """
    Generate a full Instagram post draft for a financial advisor.

    If theme/audience are not provided, picks them using the
    performance feedback loop specific to this user.
    """
    perf = await _get_performance_context(supabase, user_id)

    if not theme or not audience:
        theme, audience = _pick_theme(perf["top"], perf["worst"])

    performance_note = _build_performance_note(perf["top"], perf["worst"])

    if audience == "education":
        content_goal = (
            "Educate the advisor's audience on this personal finance topic. "
            "Use real numbers and relatable everyday scenarios. "
            "Make the advisor look like the expert who genuinely cares about their audience's financial wellbeing."
        )
    else:
        content_goal = (
            "Share an authentic perspective from the advisor's own point of view. "
            "Build credibility and trust — make followers feel like they already know and trust this advisor "
            "and want to reach out to work with them."
        )

    prompt = f"""Create an Instagram post for a financial advisor's account.

Theme: "{theme}"
Content goal: {content_goal}
{f'Performance context:{chr(10)}{performance_note}' if performance_note else ''}

Return a JSON object with exactly these fields:
{{
  "theme": "the theme you used",
  "audience": "{audience}",
  "hook": "Scroll-stopping first line for the caption. Make people stop and read.",
  "caption": "2-3 lines only. Reinforces the image or ends with a soft CTA like 'Save this', 'Share this with someone who needs it', or 'DM me if you have questions'.",
  "hashtags": "Space-separated hashtags, 12-18 relevant ones mixing finance topics, life stages, and advisor-specific tags",
  "image_concept": "Exact text shown on the image plus layout and style guidance (headline size, color mood, layout type)",
  "post_type": "single_image or carousel",
  "carousel_slides": [
    {{"slide_number": 1, "headline": "exact headline text on this slide", "body": "supporting text on this slide", "cta": "CTA text on last slide only — empty string on all other slides"}}
  ]
}}

Rules:
- Use real specific numbers and everyday scenarios — not vague generic advice.
- The image must be the value: someone should understand the point without reading the caption.
- For carousel: 4-6 slides with exact text for each slide.
- For single_image: return an empty array for carousel_slides.
- Make the content feel fresh, not recycled."""

    log.info("generating_post", user_id=user_id, theme=theme, audience=audience)

    response = await _openai.chat.completions.create(
        model=settings.openai_text_model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.9,
    )

    raw = (response.choices[0].message.content or "").strip()
    post = json.loads(raw)
    post.setdefault("post_type", "single_image")
    post.setdefault("carousel_slides", [])

    log.info(
        "post_generated",
        user_id=user_id,
        post_type=post["post_type"],
        theme=post["theme"],
    )
    return post
