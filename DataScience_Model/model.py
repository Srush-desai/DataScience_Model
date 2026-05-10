# ================================
# INSIDER THREAT DETECTION MODEL
# ================================

# 🔹 1. Import Libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# 🔹 2. Load Dataset
df = pd.read_csv("feature_engineered_dataset.csv")

print("Dataset Loaded Successfully!\n")
print(df.head())

# 🔹 3. Check Missing Values
print("\nMissing Values:\n", df.isnull().sum())

# 🔹 4. Define Features & Target
X = df.drop("is_malicious", axis=1)
y = df["is_malicious"]

# 🔹 5. Train-Test Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print("\nData Split Completed!")
print("Training samples:", X_train.shape)
print("Testing samples:", X_test.shape)

# 🔹 6. Train Model
model = RandomForestClassifier(n_estimators=100, random_state=42)

model.fit(X_train, y_train)

import pickle

# Save model
pickle.dump(model, open("model.pkl", "wb"))

print("Model saved successfully!")

print("\nModel Training Completed!")

# 🔹 7. Prediction
y_pred = model.predict(X_test)

# 🔹 8. Evaluation Metrics
accuracy = accuracy_score(y_test, y_pred)

print("\nModel Evaluation:")
print("Accuracy:", accuracy)

print("\nClassification Report:\n")
print(classification_report(y_test, y_pred))

# 🔹 9. Confusion Matrix
cm = confusion_matrix(y_test, y_pred)

plt.figure(figsize=(6,4))
sns.heatmap(cm, annot=True, fmt='d')
plt.title("Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.show()

# 🔹 10. Feature Importance
importance = model.feature_importances_
features = X.columns

feature_importance_df = pd.DataFrame({
    "Feature": features,
    "Importance": importance
})

# Sort features
feature_importance_df = feature_importance_df.sort_values(
    by="Importance", ascending=False
)

print("\nTop Important Features:\n")
print(feature_importance_df.head(10))

# 🔹 11. Plot Feature Importance
plt.figure(figsize=(10,6))
sns.barplot(
    x="Importance",
    y="Feature",
    data=feature_importance_df.head(10)
)
plt.title("Top 10 Important Features")
plt.show()

# ================================
# END OF CODE
# ================================