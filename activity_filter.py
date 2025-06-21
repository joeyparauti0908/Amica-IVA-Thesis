import pandas as pd

#  Read in the original CSV of activities
df = pd.read_csv('activiteiten.csv', encoding='utf-8')

# Count how many activities (rows) we have before cleaning
before = len(df)

# Remove any exact duplicate rows
df = df.drop_duplicates()

# Count how many activities (rows) remain after removing duplicated
after = len(df)

#Write the cleaned dataframe to a new CSV
df.to_csv('activiteiten_clean.csv', index=False, encoding='utf-8')

print(f"There are {before - after} duplicate rows; After removing them {after} unique activities remain.")
