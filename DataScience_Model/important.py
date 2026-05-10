from sklearn.ensemble import RandomForestClassifier
import pandas as pd

df = pd.read_csv("cleaned_data_final.csv");
# Target
y = df["is_malicious"]

# Features (drop target)
X = df.drop("is_malicious", axis=1)

# Convert categorical if needed
X = pd.get_dummies(X, drop_first=True)

# Train model
model = RandomForestClassifier(random_state=42)
model.fit(X, y)

# Feature importance
importances = pd.Series(model.feature_importances_, index=X.columns)
importances = importances.sort_values(ascending=False)

print(importances.head(10))