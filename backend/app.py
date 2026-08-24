from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib


# Project root
BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "model" / "truthguard_model.pkl"
VECTORIZER_PATH = BASE_DIR / "model" / "tfidf_vectorizer.pkl"


app = FastAPI(
    title="TruthGuard API",
    description="Intelligent Misinformation Detection System",
    version="1.0"
)


# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Load trained model
model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)


class NewsRequest(BaseModel):
    text: str


@app.get("/")
def home():
    return {
        "message": "TruthGuard API is running!",
        "status": "online"
    }


@app.post("/predict")
def predict_news(request: NewsRequest):

    text = request.text.strip()

    if not text:
        return {
            "prediction": "No Text Provided",
            "confidence": 0,
            "fake_probability": 0,
            "real_probability": 0
        }

    # Convert text to TF-IDF
    text_vector = vectorizer.transform([text])

    # Prediction
    prediction = model.predict(text_vector)[0]

    # Prediction probabilities
    probabilities = model.predict_proba(text_vector)[0]

    fake_probability = float(probabilities[0])
    real_probability = float(probabilities[1])

    if prediction == 0:

        result = "Potentially Misleading"
        confidence = fake_probability

    else:

        result = "Likely Reliable"
        confidence = real_probability


    return {
        "prediction": result,
        "confidence": round(confidence * 100, 2),
        "fake_probability": round(fake_probability * 100, 2),
        "real_probability": round(real_probability * 100, 2)
    }