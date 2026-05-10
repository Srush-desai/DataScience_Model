import plotly.express as px
import pandas as pd

# Load dataset
df = pd.read_csv("feature_engineered_dataset.csv")

# Convert for better labeling
df["is_malicious"] = df["is_malicious"].astype(str)

# Create violin plot
fig = px.violin(
    df,
    x="is_malicious",
    y="off_hours_ratio",
    color="is_malicious",
    box=True,          # shows mini box plot inside
    points="all",      # shows all data points
    title="Violin Plot: Off Hours Ratio vs Malicious Activity"
)

fig.show()