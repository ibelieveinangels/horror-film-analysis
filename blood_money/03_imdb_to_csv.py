import pandas as pd
import os

def convert_tsv_to_csv():
    # Define input and output paths
    input_dir = r"C:\Users\notbl\Desktop\horror-film-analysis\data\raw"
    title_basics_path = os.path.join(input_dir, "title.basics.tsv")
    title_ratings_path = os.path.join(input_dir, "title.ratings.tsv")
    
    # Output file names
    output_basics_csv = os.path.join(input_dir, "title_basics.csv")
    output_ratings_csv = os.path.join(input_dir, "title_ratings.csv")
    
    try:
        # Read the title.basics.tsv file
        print("Reading title.basics.tsv...")
        basics_df = pd.read_csv(title_basics_path, sep='\t', low_memory=False)
        print(f"Successfully read title.basics.tsv with {len(basics_df)} rows")
        
        # Save as CSV
        print("Saving title_basics.csv...")
        basics_df.to_csv(output_basics_csv, index=False)
        print("title_basics.csv saved successfully!")
        
        # Read the title.ratings.tsv file
        print("Reading title.ratings.tsv...")
        ratings_df = pd.read_csv(title_ratings_path, sep='\t', low_memory=False)
        print(f"Successfully read title.ratings.tsv with {len(ratings_df)} rows")
        
        # Save as CSV
        print("Saving title_ratings.csv...")
        ratings_df.to_csv(output_ratings_csv, index=False)
        print("title_ratings.csv saved successfully!")
        
        print("\nConversion completed successfully!")
        print(f"Files created:")
        print(f"  - {output_basics_csv}")
        print(f"  - {output_ratings_csv}")
        
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
    except pd.errors.EmptyDataError:
        print("Error: One of the TSV files is empty")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    convert_tsv_to_csv()