import plotly.express as px
import pandas as pd

# Load dataset
df = pd.read_csv("feature_engineered_dataset.csv")

# Convert employee_risk to categorical (important for proper grouping)
df["employee_risk"] = df["employee_risk"].astype(str)

# Create box plot
fig = px.box(
    df,
    x="employee_risk",
    y="threat_score",
    color="employee_risk",
    title="Threat Score Distribution Across Employee Risk Levels"
)

fig.show()