import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report


# Load processed dataset
data = pd.read_csv("dataset/news_processed.csv")

# Features and labels
X = data["content"]
y = data["label"]

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("Training samples:", len(X_train))
print("Testing samples:", len(X_test))


# Convert text into numerical features
vectorizer = TfidfVectorizer(
    stop_words="english",
    max_features=100000
)

X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)


# Train model
model = LogisticRegression(max_iter=1000)

model.fit(X_train_tfidf, y_train)


# Make predictions
y_pred = model.predict(X_test_tfidf)


# Evaluate model
accuracy = accuracy_score(y_test, y_pred)

print("\nTruthGuard Model Results")
print("------------------------")
print("Accuracy:", round(accuracy * 100, 2), "%")

print("\nClassification Report:")
print(classification_report(
    y_test,
    y_pred,
    target_names=["Fake", "Real"]
))


# Save model and vectorizer
joblib.dump(model, "model/truthguard_model.pkl")
joblib.dump(vectorizer, "model/tfidf_vectorizer.pkl")

print("\nModel saved successfully!")
print("truthguard_model.pkl")
print("tfidf_vectorizer.pkl")