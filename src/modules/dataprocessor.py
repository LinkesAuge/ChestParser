# dataprocessor.py - DataProcessor class implementation
from modules.utils import *
import os
import re
import pandas as pd

class DataProcessor:
    """Class to handle data processing logic"""
    
    # Debug flag
    debug = True
    
    @staticmethod
    def load_csv(filepath, encodings=None):
        """
        Load a CSV file and return a pandas DataFrame with enhanced error handling.
        
        Args:
            filepath (str): Path to the CSV file
            encodings (list, optional): List of encodings to try. Defaults to None.
            
        Returns:
            tuple: (DataFrame, success, error_message)
        """
        print("=== DataProcessor.load_csv ===")
        print(f"Processing filepath: {filepath}")
        print(f"Type of filepath: {type(filepath)}")
        print(f"DataProcessor.load_csv: Processing {filepath}")
        
        # Check if the file exists
        file_exists = os.path.exists(filepath)
        print(f"File exists check: {file_exists}")
        
        if not file_exists:
            return None, False, f"File not found: {filepath}"
        
        # Get file size
        file_size = os.path.getsize(filepath)
        print(f"File size: {file_size} bytes")
                
        # Check if file is empty
        if file_size == 0:
            return None, False, "File is empty"
            
        # Try to detect file encoding by reading the first few bytes
        try:
            with open(filepath, 'rb') as f:
                raw_data = f.read(min(file_size, 1024))  # Read first 1KB or entire file
                print(f"First bytes: {raw_data[:50]}")  # Only print first 50 bytes
                print(f"First bytes (hex): {raw_data.hex()[:50]}")  # Show first 50 hex chars
                
                # Check if it looks like binary data
                is_likely_text = all(b in range(32, 127) or b in (9, 10, 13) for b in raw_data[:20])
                print(f"First bytes look like valid ASCII/text data: {is_likely_text}")
                
                # Look for signs of German umlauts in the file
                has_umlauts = any(b in [196, 214, 220, 223, 228, 246, 252] for b in raw_data)
                
                # Also check for garbled umlaut patterns (e.g., 'Ã¤' instead of 'ä')
                garbled_patterns = [b'\xc3\xa4', b'\xc3\xb6', b'\xc3\xbc', b'\xc3\x9f']
                has_garbled_umlauts = any(pattern in raw_data for pattern in garbled_patterns)
                
                if has_umlauts:
                    print("Detected potential German umlauts in extended content")
                if has_garbled_umlauts:
                    print("Detected garbled German umlaut patterns")
                    
                # If German characters are detected, prioritize German-friendly encodings
                if has_umlauts or has_garbled_umlauts:
                    encodings = ['latin1', 'cp1252', 'iso-8859-1', 'windows-1252', 'utf-8', 'utf-8-sig']
                    print("Using German-prioritized encodings due to detected umlauts")
                else:
                    encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1', 'windows-1252', 'utf-8-sig']
                    print("Using default encoding list")
        except Exception as e:
            log_error("Error reading file for encoding detection", e)
            encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1', 'windows-1252', 'utf-8-sig']
            print("Using default encoding list due to error")
        
        # Variables to hold errors from all attempts
        all_errors = []
        df = None
        successful_encoding = None
        
        # Try different encodings
        for encoding in encodings:
            try:
                print(f"Trying to load with encoding: {encoding}")
                df = pd.read_csv(filepath, encoding=encoding)
                successful_encoding = encoding
                print(f"Successfully loaded with encoding: {encoding}")
                break
            except UnicodeDecodeError as e:
                log_error(f"Failed with encoding {encoding}", e)
            except Exception as e:
                log_error(f"Error with encoding {encoding}", e)
        
        if df is None:
            return None, False, "Failed to load CSV with any of the attempted encodings"
            
        # Print DataFrame info
        print(f"DataFrame shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        
        if len(df) > 0:
            print(f"First row: {list(df.iloc[0])}")
            print("\nSample data (first 5 rows):")
            print(df.head())
        
        # Detect and fix encoding issues with German umlauts
        if 'PLAYER' in df.columns:
            # Check for garbled umlauts (common signs of encoding mismatch)
            sample_players = df['PLAYER'].head(100).astype(str).tolist()
            has_garbled_umlauts = any(re.search(r'([Ã][¤äö]|[Ã][–Ö]|[Ã][¼ü]|[ÃŸß])', player) for player in sample_players)
            
            # Special chars that would suggest proper encoding or garbled chars
            has_umlauts = any(re.search(r'[äöüÄÖÜß]', player) for player in sample_players)
            
            if has_garbled_umlauts:
                print("Data contains garbled German umlauts (encoding mismatch detected)")
                # Find examples of garbled text
                for player in sample_players:
                    if re.search(r'([Ã][¤äö]|[Ã][–Ö]|[Ã][¼ü]|[ÃŸß])', player):
                        correct_player = player
                        # Try to fix common patterns
                        correct_player = correct_player.replace('Ã¤', 'ä')
                        correct_player = correct_player.replace('Ã¶', 'ö')
                        correct_player = correct_player.replace('Ã¼', 'ü')
                        correct_player = correct_player.replace('Ã„', 'Ä')
                        correct_player = correct_player.replace('Ã–', 'Ö')
                        correct_player = correct_player.replace('Ãœ', 'Ü')
                        correct_player = correct_player.replace('ÃŸ', 'ß')
                        print(f"Found misencoded '{player}' - this should be '{correct_player}'")
                
                print("Attempting to fix encoding for the PLAYER column")
                # Apply corrections to the whole column
                df['PLAYER'] = df['PLAYER'].str.replace('Ã¤', 'ä', regex=True)
                df['PLAYER'] = df['PLAYER'].str.replace('Ã¶', 'ö', regex=True)
                df['PLAYER'] = df['PLAYER'].str.replace('Ã¼', 'ü', regex=True)
                df['PLAYER'] = df['PLAYER'].str.replace('Ã„', 'Ä', regex=True)
                df['PLAYER'] = df['PLAYER'].str.replace('Ã–', 'Ö', regex=True)
                df['PLAYER'] = df['PLAYER'].str.replace('Ãœ', 'Ü', regex=True)
                df['PLAYER'] = df['PLAYER'].str.replace('ÃŸ', 'ß', regex=True)
            
            print(f"Data contains German umlauts (properly formatted or garbled): {has_umlauts or has_garbled_umlauts}")
        
        # Drop any extra columns (if default columns are defined)
        expected_columns = ['DATE', 'PLAYER', 'SOURCE', 'CHEST', 'SCORE']
        extra_columns = [col for col in df.columns if col not in expected_columns]
        
        if extra_columns:
            print(f"Dropping extra columns: {extra_columns}")
            df = df.drop(columns=extra_columns)
        
        print("=== CSV loaded successfully ===")
        return df, True, ""
    
    @staticmethod
    def analyze_data(df):
        """
        Process data according to requirements and return processed DataFrames.
        
        Args:
            df (pandas.DataFrame): The raw data to analyze
            
        Returns:
            dict: Dictionary containing various analysis results
        """
        # Calculate total score per player (main goal)
        player_totals = df.groupby('PLAYER')['SCORE'].sum().reset_index()
        player_totals = player_totals.sort_values('SCORE', ascending=False)
        
        # Calculate scores by chest type
        chest_totals = df.groupby('CHEST')['SCORE'].sum().reset_index()
        chest_totals = chest_totals.sort_values('SCORE', ascending=False)
        
        # Calculate scores by source
        source_totals = df.groupby('SOURCE')['SCORE'].sum().reset_index()
        source_totals = source_totals.sort_values('SCORE', ascending=False)
        
        # Calculate scores by date
        date_totals = df.groupby('DATE')['SCORE'].sum().reset_index()
        date_totals = date_totals.sort_values('DATE')
        
        # Calculate average scores
        player_avg = df.groupby('PLAYER')['SCORE'].mean().reset_index()
        player_avg = player_avg.sort_values('SCORE', ascending=False)
        player_avg['SCORE'] = player_avg['SCORE'].round(2)
        
        # Calculate number of chests per player
        player_counts = df.groupby('PLAYER').size().reset_index(name='COUNT')
        player_counts = player_counts.sort_values('COUNT', ascending=False)
        
        # Most frequent chest types per player
        player_chest_freq = df.groupby(['PLAYER', 'CHEST']).size().reset_index(name='COUNT')
        
        # Create Player Overview (new)
        # Start with base player data: total score and chest count
        player_overview = player_totals.merge(player_counts, on='PLAYER')
        player_overview = player_overview.rename(columns={'SCORE': 'TOTAL_SCORE', 'COUNT': 'CHEST_COUNT'})
        
        # Get the scores for each source type per player (instead of chest type)
        source_type_scores = df.pivot_table(
            index='PLAYER', 
            columns='SOURCE',  # Changed from CHEST to SOURCE
            values='SCORE', 
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        # Merge source type scores with player overview
        player_overview = player_overview.merge(source_type_scores, on='PLAYER')
        
        # Sort by total score
        player_overview = player_overview.sort_values('TOTAL_SCORE', ascending=False)
        
        return {
            'player_totals': player_totals,
            'chest_totals': chest_totals,
            'source_totals': source_totals,
            'date_totals': date_totals,
            'player_avg': player_avg,
            'player_counts': player_counts,
            'player_chest_freq': player_chest_freq,
            'player_overview': player_overview,  # Add the new view
            'raw_data': df
        } 