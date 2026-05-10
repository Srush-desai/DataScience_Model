import plotly.express as px
import pandas as pd

# load your dataset
df = pd.read_csv("feature_engineered_dataset.csv")

# convert is_malicious to string (for better labels)
df["is_malicious"] = df["is_malicious"].astype(str)

fig = px.box(
    df,
    x="is_malicious",
    y="off_hours_ratio",
    color="is_malicious",
    title="Off Hours Ratio vs Malicious Activity"
)

fig.show()