import pandas as pd

# Input file
csv_file = "./example/Cubes/Population_Aargau/data_raw.csv"

# Read the CSV file
df = pd.read_csv(csv_file, sep=",")

# Set display options to avoid silent downcasting warnings
pd.set_option('future.no_silent_downcasting', True)

# Rename "ALTER_xy" columns to "age_xy"
df.rename(columns=lambda x: x.replace("ALTER_", "age_") if x.startswith("ALTER_") else x, inplace=True)

# Rename column "TOTAL" to "all"
df.rename(columns={"TOTAL": "all"}, inplace=True)

# Create a new list with all the columns that start with "age_"
age_concept_ids = [col for col in df.columns if col.startswith("age_")]

# Create names for the age concepts by replacing "age_00_04" with "Age 00 to 04"
age_concept_names_en = ["Age " + col[4:6] + " to " + col[7:9] for col in age_concept_ids]
# Special case for the last age group
age_concept_names_en[-1] = "Age 90 and older"

age_concept_names_de = ["Alter " + col[4:6] + " bis " + col[7:9] for col in age_concept_ids]
# Special case for the last age group in German
age_concept_names_de[-1] = "Alter 90 und älter"

# Create descriptions for the age concepts
age_concept_descriptions_en = ["People with age " + col[4:6] + " to " + col[7:9] + " years" for col in age_concept_ids]
# Special case for the last age group
age_concept_descriptions_en[-1] = "People with age 90 years and older"

age_concept_descriptions_de = ["Personen mit Alter " + col[4:6] + " bis " + col[7:9] + " Jahre" for col in
                               age_concept_ids]
# Special case for the last age group in German
age_concept_descriptions_de[-1] = "Personen mit Alter 90 Jahre und älter"

# Add "all" to the list of age concepts
age_concept_ids.append("all")
# Add "All ages" for the "all" column
age_concept_names_en.append("Total population")
# Add description for the "all" column
age_concept_descriptions_en.append("Total population of all ages")
age_concept_names_de.append("Gesamtbevölkerung")
age_concept_descriptions_de.append("Gesamtbevölkerung aller Altersgruppen")

# Create a DataFrame for age concepts
age_concepts_df = pd.DataFrame({
    "ageID": age_concept_ids,
    "ageName_en": age_concept_names_en,
    "ageDescription_en": age_concept_descriptions_en,
    "ageName_de": age_concept_names_de,
    "ageDescription_de": age_concept_descriptions_de
})

# Save the age concepts DataFrame to a CSV file
age_concepts_df.to_csv("./example/Cubes/Population_Aargau/age.csv", index=False)

# Create a new date column from year, month, and day columns in Format YYYY-MM-DD
df.insert(1, "date",
          df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2) + "-" + df["day"].astype(str).str.zfill(
              2))


# Create a new column for the region
def region(line):
    if line.locationType == "CANTON":
        return "C_" + str(line.bfsNr)
    elif line.locationType == "DISTRICT":
        return "D_" + str(line.bfsNr)
    elif line.locationType == "TOWNSHIP":
        return "M_" + str(line.bfsNr)


df.insert(0, "region", df.apply(region, axis=1))

# Keep only values for "region" = C_19, D_1901 and M_4001 through M_4013 (district Aarau and total of canton Aargau)
df = df[df["region"].isin(
    ["C_19", "D_1901", "M_4001", "M_4002", "M_4003", "M_4004", "M_4005",
     "M_4006", "M_4007", "M_4008", "M_4009", "M_4010", "M_4011", "M_4012", "M_4013"
    ]
)]

df = df[df["year"] > 2020]

# Drop unnecessary columns
df.drop(columns=["bfsNr", "year", "month", "day", "locationName", "locationType"], inplace=True)


# Melt data to long format
df = df.melt(id_vars=["region", "date"], var_name="group", value_name="number")

# Column number as integer
df["number"] = df["number"].astype(int)

# Add percentage column
all_df = df[df["group"] == "all"].rename(columns={"number": "all_number"})
df = df.merge(all_df[["region", "date", "all_number"]], on=["region", "date"], how="left")
df["percentage"] = round(df["number"] / df["all_number"] * 100, 4)
df.drop(columns=["all_number"], inplace=True)

# Save to CSV
df.to_csv("./example/Cubes/Population_Aargau/data.csv", index=False)
print("Saved extracted data to data.csv")
