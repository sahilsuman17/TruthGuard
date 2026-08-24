from pathlib import Path
import os
import json
import re

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import joblib

from google import genai
from google.genai import types


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "model" / "truthguard_model.pkl"
VECTORIZER_PATH = BASE_DIR / "model" / "tfidf_vectorizer.pkl"


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="TruthGuard API",
    description="AI-powered misinformation detection and fact verification",
    version="2.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# LOAD EXISTING ML MODEL
# ============================================================

model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)


# ============================================================
# GEMINI CLIENT
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

gemini_client = None

if GEMINI_API_KEY:
    gemini_client = genai.Client(
        api_key=GEMINI_API_KEY
    )


# ============================================================
# REQUEST MODEL
# ============================================================

class NewsRequest(BaseModel):
    text: str


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "message": "TruthGuard AI API is running!",
        "status": "online",
        "gemini_enabled": gemini_client is not None
    }


# ============================================================
# GEMINI FACT CHECK
# ============================================================

def gemini_fact_check(text: str):

    if gemini_client is None:
        return None


    prompt = f"""
You are the fact-verification engine for TruthGuard.

Your job is to evaluate the factual claim contained in the user's text.

IMPORTANT:
- Do NOT judge a claim based only on wording or writing style.
- Use Google Search grounding to verify factual claims whenever useful.
- Prefer authoritative and trustworthy sources.
- Distinguish between a factual statement, opinion, prediction, satire,
  and a claim that cannot currently be verified.
- Do not call something misleading merely because it is unusual.
- If reliable evidence supports the claim, classify it as Likely Reliable.
- If reliable evidence contradicts the claim, classify it as Potentially Misleading.
- If there is insufficient evidence, classify it as Potentially Misleading
  rather than pretending certainty.
- Your confidence must represent your confidence in the classification,
  not the probability that the claim is emotionally believable.

USER CLAIM:
{text}

Return ONLY valid JSON in this exact structure:

{{
  "prediction": "Likely Reliable" or "Potentially Misleading",
  "confidence": number,
  "reason": "short explanation",
  "sources_found": true or false
}}

The confidence must be between 0 and 100.
"""


    try:

        response = gemini_client.models.generate_content(

            model="gemini-3.7-flash",

            contents=prompt,

            config=types.GenerateContentConfig(

                temperature=0.1,

                max_output_tokens=500,

                tools=[
                    types.Tool(
                        google_search=types.GoogleSearch()
                    )
                ]
            )
        )


        raw_text = response.text.strip()


        # Remove markdown JSON fences if Gemini adds them
        raw_text = re.sub(
            r"^```json\s*",
            "",
            raw_text,
            flags=re.IGNORECASE
        )

        raw_text = re.sub(
            r"\s*```$",
            "",
            raw_text
        )


        result = json.loads(raw_text)


        prediction = result.get(
            "prediction",
            "Potentially Misleading"
        )


        confidence = float(
            result.get("confidence", 50)
        )


        confidence = max(
            0,
            min(100, confidence)
        )


        reason = result.get(
            "reason",
            ""
        )


        sources_found = bool(
            result.get(
                "sources_found",
                False
            )
        )


        if prediction not in [
            "Likely Reliable",
            "Potentially Misleading"
        ]:

            prediction = "Potentially Misleading"


        if prediction == "Likely Reliable":

            real_probability = confidence
            fake_probability = 100 - confidence

        else:

            fake_probability = confidence
            real_probability = 100 - confidence


        return {

            "prediction": prediction,

            "confidence": round(
                confidence,
                2
            ),

            "fake_probability": round(
                fake_probability,
                2
            ),

            "real_probability": round(
                real_probability,
                2
            ),

            "reason": reason,

            "sources_found": sources_found,

            "verification": "Gemini AI + Google Search"

        }


    except Exception as error:

        print(
            "Gemini verification error:",
            type(error).__name__,
            str(error)
        )

        return None


# ============================================================
# ML FALLBACK
# ============================================================

def ml_prediction(text: str):

    text_vector = vectorizer.transform(
        [text]
    )


    prediction = model.predict(
        text_vector
    )[0]


    probabilities = model.predict_proba(
        text_vector
    )[0]


    fake_probability = float(
        probabilities[0]
    )

    real_probability = float(
        probabilities[1]
    )


    if prediction == 0:

        result = "Potentially Misleading"

        confidence = fake_probability

    else:

        result = "Likely Reliable"

        confidence = real_probability


    return {

        "prediction": result,

        "confidence": round(
            confidence * 100,
            2
        ),

        "fake_probability": round(
            fake_probability * 100,
            2
        ),

        "real_probability": round(
            real_probability * 100,
            2
        ),

        "verification": "ML fallback"

    }


# ============================================================
# PREDICT / VERIFY NEWS
# ============================================================

@app.post("/predict")
def predict_news(request: NewsRequest):

    text = request.text.strip()


    if not text:

        return {

            "prediction": "No Text Provided",

            "confidence": 0,

            "fake_probability": 0,

            "real_probability": 0,

            "reason": "",

            "sources_found": False,

            "verification": "None"

        }


    # --------------------------------------------------------
    # FIRST: GEMINI + GOOGLE SEARCH
    # --------------------------------------------------------

    ai_result = gemini_fact_check(
        text
    )


    if ai_result is not None:

        return ai_result


    # --------------------------------------------------------
    # FALLBACK: EXISTING ML MODEL
    # --------------------------------------------------------

    return ml_prediction(
        text
    )