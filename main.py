from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import anthropic
import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="Pathly API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# --- Models ---

class UserProfile(BaseModel):
    full_name: str
    passport_country: str
    residence_country: str
    visa_type: Optional[str] = None
    visa_expiry: Optional[str] = None
    immigration_status: str  # e.g. "student", "work permit", "PR", "citizen", "visitor"
    other_visas: Optional[List[str]] = []  # e.g. ["US B1/B2 valid until 2026", "UK visitor visa"]

class TripCheckRequest(BaseModel):
    profile: UserProfile
    query: str  # e.g. "Can I fly Toronto -> Amsterdam -> Lagos?" or just "I want to go to London"

class PathwayRequest(BaseModel):
    profile: UserProfile
    target_country: str  # e.g. "Canada", "UK", "USA"
    pathway_type: str = "PR"  # "PR" or "citizenship"

# --- System prompt builder ---

def build_system_prompt(profile: UserProfile) -> str:
    visas = ", ".join(profile.other_visas) if profile.other_visas else "none listed"
    return f"""You are Pathly, a world-class immigration and travel intelligence assistant.

The user's immigration profile is:
- Name: {profile.full_name}
- Passport: {profile.passport_country}
- Country of Residence: {profile.residence_country}
- Current Immigration Status: {profile.immigration_status}
- Current Visa Type: {profile.visa_type or 'N/A'}
- Current Visa Expiry: {profile.visa_expiry or 'N/A'}
- Other Valid Visas/Documents: {visas}

Your job is to give PERSONALIZED, ACCURATE, and SPECIFIC advice based on THIS person's exact documents and status.

CRITICAL RULES:
1. Always check EVERY country on a route including transit/layover countries — not just the final destination.
2. Flag Schengen zone rules carefully — transiting through two Schengen countries on a single trip may require specific visas.
3. Always mention if transit visa requirements differ from entry visa requirements.
4. If recommending flight routes, suggest 2-3 specific realistic options (e.g. Air Canada YYZ->LHR direct, or KLM via Amsterdam).
5. Always end with: the official government website link for the destination country's visa info, and a note to verify with an immigration professional for complex cases.
6. Be warm, clear, and direct. No legal jargon. Speak like a knowledgeable friend.
7. If you're not 100% certain about a specific rule, say so clearly and direct them to the official source.
8. Format your response with clear sections using emoji headers for readability."""


def _first_text_from_message(message) -> str:
    for block in message.content:
        if getattr(block, "type", None) == "text" and getattr(block, "text", None):
            return block.text
        if getattr(block, "text", None):
            return block.text
    raise ValueError("Claude returned no text block (unexpected content layout).")


def _error_detail(exc: Exception) -> str:
    msg = str(exc).strip()
    if msg:
        return msg
    return f"{type(exc).__name__} (no message) — check server logs"

# --- Routes ---

@app.get("/")
def root():
    return {"message": "Pathly API is live ✈️"}

@app.post("/check-trip")
def check_trip(request: TripCheckRequest):
    try:
        system = build_system_prompt(request.profile)
        prompt = f"""The user wants help with this travel situation:

"{request.query}"

Please analyze this fully:
1. ✅ What they CAN do with their current documents
2. ⚠️ Any restrictions, visa requirements, or transit rules they need to know
3. 🛫 Recommended flight routes that work for their document situation (if asking for recommendations)
4. 📋 Exact documents they need to carry for each country on the route
5. 🔗 Official government links to verify requirements
6. 💡 Any tips or warnings specific to their situation"""

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )
        return {"result": _first_text_from_message(message)}
    except Exception as e:
        logger.exception("check_trip failed")
        raise HTTPException(status_code=500, detail=_error_detail(e))


@app.post("/pathway-finder")
def pathway_finder(request: PathwayRequest):
    try:
        system = build_system_prompt(request.profile)
        prompt = f"""The user wants to find {request.pathway_type} pathways in {request.target_country}.

Based on their specific immigration profile, please provide:
1. 🛤️ All available {request.pathway_type} pathways they may qualify for
2. ✅ Eligibility requirements for each pathway
3. ⏱️ Estimated processing times
4. 📋 Key documents typically required
5. 💰 Approximate costs/fees
6. 🔗 Official government application links
7. 👨‍💼 Recommendation on whether to use an immigration lawyer/consultant for this pathway
8. ⚠️ Any red flags or disqualifiers based on their current profile they should know about

Be specific and realistic. If their profile makes certain pathways unlikely, say so kindly and redirect to better options."""

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )
        return {"result": _first_text_from_message(message)}
    except Exception as e:
        logger.exception("pathway_finder failed")
        raise HTTPException(status_code=500, detail=_error_detail(e))