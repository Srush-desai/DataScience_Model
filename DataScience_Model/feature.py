import pandas as pd
import numpy as np

# Load dataset
df = pd.read_csv("cleaned_data_final.csv")

# Handle missing values
df.fillna(0, inplace=True)

# ==============================
# 1. NORMALIZED ACTIVITY FEATURES
# ==============================

# Total activity
df['total_activity'] = df['total_files_burned'] + df['total_printed_pages']

# Burn ratio (data exfiltration intensity)
df['burn_ratio'] = df['total_files_burned'] / (df['total_activity'] + 1)

# Print ratio
df['print_ratio'] = df['total_printed_pages'] / (df['total_activity'] + 1)

# ==============================
# 2. BEHAVIORAL ANOMALY FEATURES
# ==============================

# Off-hours behavior (important feature)
df['off_hours_ratio'] = df['num_printed_pages_off_hours'] / (df['total_printed_pages'] + 1)

# Activity per entry (intensity per login)
df['activity_per_entry'] = df['total_activity'] / (df['num_entries'] + 1)

# Movement anomaly (location switching behavior)
df['movement_anomaly'] = df['num_unique_campus'] / (df['num_entries'] + 1)

# ==============================
# 3. DATA TRANSFER RISK
# ==============================

# External data interaction
df['external_burn_ratio'] = df['burned_from_other'] / (df['total_files_burned'] + 1)

# ==============================
# 4. EXPERIENCE NORMALIZATION
# ==============================

# Normalize activity by seniority (important feature)
df['activity_vs_seniority'] = df['total_activity'] / (df['employee_seniority_years'] + 1)

# ==============================
# 5. OPTIONAL: LOG TRANSFORMATION (for skewed data)
# ==============================

df['log_total_activity'] = np.log1p(df['total_activity'])
df['log_files_burned'] = np.log1p(df['total_files_burned'])

# ==============================
# 6. ENCODE CATEGORICAL VARIABLES
# ==============================

df = pd.get_dummies(df, drop_first=True)

# Save dataset
df.to_csv("feature_engineered_balanced.csv", index=False)

print("✅ Balanced Feature Engineering Completed")