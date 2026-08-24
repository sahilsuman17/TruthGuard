import pandas as pd

# Load datasets
fake = pd.read_csv("dataset/Fake.csv")
real = pd.read_csv("dataset/True.csv")

# Add labels
fake["label"] = 0
real["label"] = 1

# Combine datasets
data = pd.concat([fake, real], ignore_index=True)

# Keep only useful columns
data = data[["title", "text", "label"]]

# Remove missing values
data = data.dropna()

# Combine title and article text
data["content"] = data["title"] + " " + data["text"]

# Shuffle the dataset
data = data.sample(frac=1, random_state=42).reset_index(drop=True)

# Save processed dataset
data.to_csv("dataset/news_processed.csv", index=False)

print("Dataset prepared successfully!")
print("Total articles:", len(data))
print(data["label"].value_counts())