import pandas as pd
from langdetect import detect, LangDetectException
import os
from collections import Counter

def get_language_if_not_english(text):
    """
    Detects if a given text is not in English.
    Returns the language code if not English, otherwise None.
    """
    if not isinstance(text, str) or not text.strip():
        return None
    try:
        lang = detect(text)
        if lang != 'en':
            return lang
    except LangDetectException:
        # langdetect can fail on short/ambiguous text. Consider it unknown.
        return 'unknown'
    return None


def analyze_fused_dataset(csv_file="rapidapi_fused_dataset.csv", output_file="statistics_report.txt"):
    """
    Analyzes the fused dataset to generate statistics about the APIs.
    """
    print(f"📊 Analyzing '{csv_file}'...")

    if not os.path.exists(csv_file):
        print(f"❌ Error: The file '{csv_file}' was not found.")
        return

    try:
        df = pd.read_csv(csv_file)
        total_apis = len(df)

        # 1. Number of APIs per category
        apis_per_category = df['category'].value_counts()

        # 2. Number of empty names or descriptions
        empty_names = df['name'].isnull().sum()
        # Fill NaN in description to handle empty strings consistently
        empty_descriptions = df['description'].fillna('').str.strip().eq('').sum()

        # 3. Detect language and find non-English entries
        df['language'] = df['description'].apply(get_language_if_not_english)
        non_english_entries = df[df['language'].notna()]
        non_english_count = len(non_english_entries)

        # Count languages
        language_counts = non_english_entries['language'].value_counts()

        # Prepare the detailed list of non-English APIs
        non_english_details = non_english_entries[['name', 'language']]

        # 4. Save results to a .txt file
        print(f"💾 Saving analysis to '{output_file}'...")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("RapidAPI Fused Dataset Analysis\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Total APIs Analyzed: {total_apis}\n\n")

            f.write("--- APIs per Category ---\n")
            f.write(apis_per_category.to_string())
            f.write("\n\n")

            f.write("--- Data Quality ---\n")
            f.write(f"Entries with empty 'name': {empty_names}\n")
            f.write(f"Entries with empty 'description': {empty_descriptions}\n\n")

            f.write("--- Language Analysis ---\n")
            f.write(f"Total entries with non-English descriptions: {non_english_count}\n\n")
            f.write("--- Language Breakdown ---\n")
            f.write(language_counts.to_string())
            f.write("\n\n")

            f.write("--- Non-English API Details ---\n")
            for index, row in non_english_details.iterrows():
                f.write(f"Row {index}: {row['name']} - Language: {row['language']}\n")


        print("✅ Analysis complete!")

    except Exception as e:
        print(f"❌ An error occurred during analysis: {e}")

if __name__ == "__main__":
    # Get the directory of the current script
    script_dir = os.path.dirname(__file__)
    # Construct the full path to the CSV file
    csv_path = os.path.join(script_dir, "rapidapi_fused_dataset_clean.csv")
    output_path = os.path.join(script_dir, "statistics_report_en_clean.txt")
    
    analyze_fused_dataset(csv_file=csv_path, output_file=output_path)