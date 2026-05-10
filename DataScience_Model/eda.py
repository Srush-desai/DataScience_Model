import pandas as pd

# *****load dataset (check exact file name inside Data folder)


df = pd.read_csv("Data/unclean_insider_dataset.csv")

print(df['employee_department'].unique())
print("Shape:", df.shape)
print("\nColumns:\n", df.columns)

print("\nInfo:")
print(df.info())

print("\nMissing Values:\n", df.isnull().sum())

print("\nSample Data:")
print(df.head())
#***********Hnadling missing values 

for col in df.columns:
    if df[col].dtype == 'object':
        df[col] = df[col].fillna(df[col].mode()[0])
    else:
        df[col] = df[col].fillna(df[col].median())

print(df.isnull().sum())


#*******Remove duplicates

print("Duplicates before:", df.duplicated().sum())

df = df.drop_duplicates()

print("Duplicates after:", df.duplicated().sum())
print("New Shape:", df.shape)

#*******Fixed datatypes:

int_cols = ['is_contractor', 'employee_classification', 'has_foreign_citizenship',
            'has_criminal_record', 'has_medical_history', 'is_abroad',
            'late_exit_flag', 'entry_during_weekend', 'is_malicious']

for col in int_cols:
    df[col] = df[col].astype(int)
print(df.dtypes)
# show the particular colums datatypes as int which they should be in int not float as is malacious : 1.0 now is malacious: 1


#*****Fixed category Inconsistencies:
df['employee_department'] = df['employee_department'].replace({
    'engineering dept': 'engineering department'
})
print(df['employee_department'].unique())

#***********save cleaned dataset 
df.to_csv("outputs/cleaned_data_final.csv", index=False)