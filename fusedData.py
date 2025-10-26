import pandas as pd
import os
import glob

def combine_api_csv_files(path=".", prefix="rapidapi_apis", output_filename="rapidapi_fused_dataset.csv"):
    """
    Combines all CSV files in a given path that start with a specific prefix
    into a single CSV file, removing duplicates.

    Args:
        path (str): The directory to search for CSV files.
        prefix (str): The prefix of the CSV files to combine.
        output_filename (str): The name of the output combined CSV file.
    """
    # Use glob to find all files matching the pattern
    search_pattern = os.path.join(path, f"{prefix}*.csv")
    csv_files = glob.glob(search_pattern)

    if not csv_files:
        print(f"No CSV files with prefix '{prefix}' found in '{path}'.")
        return

    print(f"Found {len(csv_files)} files to merge:")
    for f in csv_files:
        print(f"  - {os.path.basename(f)}")

    # List to hold dataframes
    df_list = []

    for file in csv_files:
        try:
            df = pd.read_csv(file)
            df_list.append(df)
        except Exception as e:
            print(f"Could not read {file}. Error: {e}")

    if not df_list:
        print("No dataframes were created. Aborting.")
        return

    # Concatenate all dataframes in the list
    combined_df = pd.concat(df_list, ignore_index=True)
    print(f"\nTotal rows before deduplication: {len(combined_df)}")

    # Drop duplicate APIs based on the 'name' column
    combined_df.drop_duplicates(subset=['name'], keep='first', inplace=True)
    print(f"Total unique rows after deduplication: {len(combined_df)}")

    # Save the final dataframe to a new CSV file
    combined_df.to_csv(output_filename, index=False)
    print(f"\n✅ Successfully merged all files into '{output_filename}'")

if __name__ == "__main__":
    # Run the function on the current directory
    current_directory = os.path.dirname(__file__)
    combine_api_csv_files(path=current_directory)