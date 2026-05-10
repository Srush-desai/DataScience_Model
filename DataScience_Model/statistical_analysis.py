# ==========================================
# STATISTICAL ANALYSIS OF DATASET
# ==========================================

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import ttest_ind

# 🔹 1. Load Dataset
df = pd.read_csv("feature_engineered_dataset.csv")

print("\nDataset Loaded Successfully!\n")
print(df.head())

# 🔹 2. Identify Numerical and Categorical Variables
num_cols = df.select_dtypes(include=['int64', 'float64']).columns
cat_cols = df.select_dtypes(include=['object', 'bool']).columns

print("\nNumerical Columns:\n", num_cols)
print("\nCategorical Columns:\n", cat_cols)

# 🔹 3. Descriptive Statistics
print("\nDescriptive Statistics:\n")
print(df[num_cols].describe())

# Additional stats
print("\nMedian Values:\n")
print(df[num_cols].median())

print("\nStandard Deviation:\n")
print(df[num_cols].std())

# 🔹 4. Correlation Analysis
corr_matrix = df[num_cols].corr()

plt.figure(figsize=(12, 8))
sns.heatmap(corr_matrix)
plt.title("Correlation Matrix")
plt.show()

# 🔹 5. Hypothesis Testing

# Example Hypothesis:
# H0: off_hours_ratio has NO effect on malicious behavior
# H1: off_hours_ratio affects malicious behavior

group_normal = df[df['is_malicious'] == 0]['off_hours_ratio']
group_malicious = df[df['is_malicious'] == 1]['off_hours_ratio']

t_stat, p_value = ttest_ind(group_normal, group_malicious)

print("\nT-Test Results:")
print("T-statistic:", t_stat)
print("P-value:", p_value)

# 🔹 6. Conclusion
if p_value < 0.05:
    print("\nResult: Reject Null Hypothesis")
    print("Conclusion: Off-hours activity significantly affects malicious behavior")
else:
    print("\nResult: Fail to Reject Null Hypothesis")
    print("Conclusion: No significant effect found")

# ==========================================
# END
# ==========================================