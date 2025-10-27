import pandas as pd
import os

def clean_descriptions(input_file="rapidapi_fused_dataset_en.csv", output_file="rapidapi_fused_dataset_clean.csv"):
    """
    Reads a dataset, filters out rows with descriptions that are empty or
    contain less than two words, and saves the cleaned data.

    Args:
        input_file (str): The path to the input CSV file.
        output_file (str): The path to save the cleaned CSV file.
    """
    print(f"🧹 Reading and cleaning dataset: {input_file}")

    if not os.path.exists(input_file):
        print(f"❌ Error: Input file '{input_file}' not found.")
        return

    try:
        df = pd.read_csv(input_file)
        initial_rows = len(df)
        print(f"Total rows in original dataset: {initial_rows}")

        # Filter out rows where the description is null, empty, or has less than two words
        df.dropna(subset=['description'], inplace=True)
        df = df[df['description'].str.split().str.len() >= 2]

        final_rows = len(df)
        rows_removed = initial_rows - final_rows
        print(f"Rows after cleaning: {final_rows} ({rows_removed} rows removed)")

        # Save the cleaned dataset
        df.to_csv(output_file, index=False)
        print(f"✅ Cleaned dataset saved to '{output_file}'")

    except Exception as e:
        print(f"❌ An error occurred during cleaning: {e}")

if __name__ == "__main__":
    clean_descriptions()