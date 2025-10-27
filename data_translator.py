import pandas as pd
from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException
import os

def translate_if_not_english(text):
    """
    Translates a given text to English if it's not already in English.
    """
    if not isinstance(text, str) or not text.strip():
        return text, None

    try:
        lang = detect(text)
        if lang == 'en':
            return text, 'en'
        else:
            print(f"    Translating from '{lang}'...")
            translated_text = GoogleTranslator(source='auto', target='en').translate(text)
            return translated_text, lang
    except LangDetectException:
        print("    ⚠️  Could not detect language, skipping translation.")
        return text, 'unknown'
    except Exception as e:
        print(f"    ❌ Error during translation: {e}")
        return text, 'error'

def process_and_translate_dataset(input_file="rapidapi_fused_dataset.csv", output_file="rapidapi_fused_dataset_en.csv"):
    """
    Reads a dataset, filters out rows with empty descriptions, translates
    non-English descriptions to English, and saves the result.
    """
    print(f"📖 Reading dataset: {input_file}")
    if not os.path.exists(input_file):
        print(f"❌ Error: Input file '{input_file}' not found.")
        return

    df = pd.read_csv(input_file)
    print(f"Total rows in original dataset: {len(df)}")

    # --- Step 1: Filter out rows with empty descriptions ---
    df.dropna(subset=['description'], inplace=True)
    df = df[df['description'].str.strip() != '']
    print(f"Rows after removing empty descriptions: {len(df)}")

    # --- Step 2: Translate non-English descriptions ---
    print("\n🔄 Starting translation process...")
    translations = df['description'].apply(translate_if_not_english)
    
    df['description'] = translations.apply(lambda x: x[0])
    df['original_language'] = translations.apply(lambda x: x[1])

    translated_count = df[df['original_language'].notna() & (df['original_language'] != 'en') & (df['original_language'] != 'unknown')].shape[0]
    print(f"\n✅ Translation complete. Translated {translated_count} descriptions.")

    # --- Step 3: Save the new dataset ---
    df.to_csv(output_file, index=False)
    print(f"💾 Translated dataset saved to '{output_file}'")

if __name__ == "__main__":
    # Get the directory of the current script
    script_dir = os.path.dirname(__file__)
    input_csv_path = os.path.join(script_dir, "rapidapi_fused_dataset.csv")
    output_csv_path = os.path.join(script_dir, "rapidapi_fused_dataset_en.csv")

    process_and_translate_dataset(input_file=input_csv_path, output_file=output_csv_path)