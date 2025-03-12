# dataprocessor.py - DataProcessor class implementation
from modules.utils import *
import os
import re
import pandas as pd
import unicodedata
import ftfy
from charset_normalizer import detect
from unidecode import unidecode
import io
from pathlib import Path
import traceback

class DataProcessor:
    """Class to handle data processing logic"""
    
    # Debug flag - set to False to reduce console output
    debug = False
    
    @staticmethod
    def fix_encoding(text):
        """
        Fix encoding issues in a string using ftfy.
        
        Args:
            text (str): Text to fix
            
        Returns:
            str: Text with fixed encoding
        """
        if not isinstance(text, str):
            return str(text)
        return ftfy.fix_text(text)
    
    @staticmethod
    def normalize_unicode(text):
        """
        Normalize Unicode text to NFC form for consistent handling.
        
        Args:
            text (str): Text to normalize
            
        Returns:
            str: Normalized text
        """
        if not isinstance(text, str):
            return str(text)
        return unicodedata.normalize('NFC', text)
    
    @staticmethod
    def transliterate_text(text):
        """
        Convert umlauts to ASCII form (ä -> a, ö -> o, etc.)
        Only use this as a last resort when preserving original characters is not possible.
        
        Args:
            text (str): Text to transliterate
            
        Returns:
            str: Transliterated text
        """
        if not isinstance(text, str):
            return str(text)
        return unidecode(text)
    
    @staticmethod
    def detect_encoding(raw_data):
        """
        Detect encoding of raw data using charset-normalizer.
        
        Args:
            raw_data (bytes): Raw data to detect encoding for
            
        Returns:
            str: Detected encoding or 'utf-8' as fallback
        """
        detection_result = detect(raw_data)
        if detection_result:
            return detection_result[0].encoding
        return 'utf-8'  # Default fallback
    
    @staticmethod
    def fix_dataframe_text(df, columns=None):
        """
        Fix encoding issues in DataFrame text columns.
        
        Args:
            df (pandas.DataFrame): The DataFrame to process
            columns (list, optional): List of columns to process. If None, processes all object columns.
            
        Returns:
            pandas.DataFrame: DataFrame with fixed text encoding
        """
        # Make a copy to avoid modifying the original
        df_fixed = df.copy()
        
        # If no specific columns provided, process all object columns
        if columns is None:
            columns = df.select_dtypes(include=['object']).columns
        
        for col in columns:
            if col not in df.columns:
                if DataProcessor.debug:
                    print(f"Warning: Column {col} not found in DataFrame")
                continue
                
            # Convert to string first (handles non-string values)
            df_fixed[col] = df_fixed[col].astype(str)
            
            # Apply fixes
            df_fixed[col] = df_fixed[col].apply(DataProcessor.fix_encoding)
            df_fixed[col] = df_fixed[col].apply(DataProcessor.normalize_unicode)
            
            # Check for pattern replacements (for common mojibake patterns)
            df_fixed[col] = df_fixed[col].str.replace('Ã¤', 'ä', regex=False)
            df_fixed[col] = df_fixed[col].str.replace('Ã¶', 'ö', regex=False)
            df_fixed[col] = df_fixed[col].str.replace('Ã¼', 'ü', regex=False)
            df_fixed[col] = df_fixed[col].str.replace('Ã„', 'Ä', regex=False)
            df_fixed[col] = df_fixed[col].str.replace('Ã–', 'Ö', regex=False)
            df_fixed[col] = df_fixed[col].str.replace('Ãœ', 'Ü', regex=False)
            df_fixed[col] = df_fixed[col].str.replace('ÃŸ', 'ß', regex=False)
        
        return df_fixed
    
    @staticmethod
    def write_csv_with_umlauts(df, filepath):
        """
        Write DataFrame to CSV with UTF-8 encoding to preserve umlauts.
        
        Args:
            df (pandas.DataFrame): DataFrame to write
            filepath (str or Path): Path to write the CSV file to
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert to Path object if it's a string
            filepath = Path(filepath)
            df.to_csv(filepath, encoding='utf-8', index=False)
            if DataProcessor.debug:
                print(f"File saved to {filepath} with UTF-8 encoding")
            return True
        except Exception as e:
            if DataProcessor.debug:
                print(f"Error saving CSV: {str(e)}")
            return False
    
    @staticmethod
    def read_csv_with_encoding_fix(filepath):
        """
        Read a CSV file with automatic encoding detection and text fixing.
        
        Args:
            filepath (str or Path): Path to the CSV file
            
        Returns:
            tuple: (pandas.DataFrame, bool, str) - DataFrame with fixed text encoding, success flag, error message
        """
        # Set debug to True for troubleshooting
        DataProcessor.debug = True
        
        # Convert to Path object if it's a string
        filepath = Path(filepath)
        
        if DataProcessor.debug:
            print("=== DataProcessor.read_csv_with_encoding_fix ===")
            print(f"Processing filepath: {filepath}")
            print(f"File type: {type(filepath)}")
            print(f"Absolute filepath: {filepath.absolute()}")
        
        # Check if the file exists
        file_exists = filepath.exists()
        if not file_exists:
            error_msg = f"File not found: {filepath}"
            print(f"ERROR: {error_msg}")
            return None, False, error_msg
        
        try:
            # Get file size for debugging
            file_size = filepath.stat().st_size
            if DataProcessor.debug:
                print(f"File size: {file_size} bytes")
                
            # Check if file is empty
            if file_size == 0:
                return None, False, "File is empty"
            
            # IMPORTANT: For German text, prioritize Windows-1252 encoding
            # This is more reliable than trying to detect the encoding
            encodings_to_try = ['cp1252', 'latin1', 'utf-8', 'iso-8859-1', 'windows-1252']
            
            if DataProcessor.debug:
                print(f"Will try these encodings in order: {encodings_to_try}")
            
            # Try to read with each encoding
            df = None
            last_error = None
            
            for enc in encodings_to_try:
                try:
                    if DataProcessor.debug:
                        print(f"Trying to read with {enc}...")
                    df = pd.read_csv(filepath, encoding=enc)
                    encoding = enc
                    if DataProcessor.debug:
                        print(f"Success with {enc}")
                        print(f"DataFrame shape: {df.shape}")
                        print(f"DataFrame columns: {df.columns.tolist() if hasattr(df, 'columns') else 'None'}")
                    break
                except Exception as e:
                    last_error = e
                    if DataProcessor.debug:
                        print(f"Failed with {enc}: {str(e)}")
                    # Try with different separator
                    try:
                        if DataProcessor.debug:
                            print(f"Trying with semicolon separator and {enc}...")
                        df = pd.read_csv(filepath, encoding=enc, sep=';')
                        encoding = enc
                        if DataProcessor.debug:
                            print(f"Success with {enc} and semicolon separator")
                            print(f"DataFrame shape: {df.shape}")
                        break
                    except Exception as e:
                        last_error = e
                        if DataProcessor.debug:
                            print(f"Failed with {enc} and semicolon separator: {str(e)}")
                        continue
            
            # If all encodings failed, try manual approach
            if df is None:
                if DataProcessor.debug:
                    print("All encoding attempts failed. Trying manual file reading approach...")
                
                try:
                    # Read the entire file as binary
                    with open(filepath, 'rb') as f:
                        content = f.read()
                        if DataProcessor.debug:
                            print(f"Read entire file of size {len(content)} bytes")
                    
                    # Try each encoding manually
                    for enc in encodings_to_try:
                        try:
                            if DataProcessor.debug:
                                print(f"Trying to decode entire file with {enc}...")
                            text = content.decode(enc, errors='replace')
                            # Try to convert text to CSV using StringIO
                            if DataProcessor.debug:
                                print(f"Creating StringIO from decoded text...")
                            import io
                            csv_io = io.StringIO(text)
                            if DataProcessor.debug:
                                print(f"Reading CSV from StringIO...")
                            df = pd.read_csv(csv_io)
                            encoding = enc
                            if DataProcessor.debug:
                                print(f"Manual approach succeeded with {enc}")
                                print(f"DataFrame shape: {df.shape}")
                            break
                        except Exception as e:
                            last_error = e
                            if DataProcessor.debug:
                                print(f"Manual approach failed with {enc}: {str(e)}")
                            continue
                except Exception as e:
                    print(f"ERROR in manual file reading: {str(e)}")
                    return None, False, f"Failed with manual approach: {str(e)}"
            
            # If still no DataFrame, return error
            if df is None:
                error_msg = f"Failed to read CSV with any encoding: {str(last_error)}"
                print(f"ERROR: {error_msg}")
                return None, False, error_msg
            
            # Ensure we have the required columns
            if 'PLAYER' not in df.columns:
                error_msg = "CSV file does not contain required PLAYER column"
                print(f"ERROR: {error_msg}")
                return None, False, error_msg
            
            # Apply text fixing to text columns
            if DataProcessor.debug:
                print("Fixing encoding in text columns...")
                if 'PLAYER' in df.columns and len(df) > 0:
                    print(f"Sample before fix: {df['PLAYER'].iloc[0] if not pd.isna(df['PLAYER'].iloc[0]) else 'N/A'}")
            
            try:
                # Apply fixes to text columns using our fix_dataframe_text function
                text_columns = df.select_dtypes(include=['object']).columns
                if DataProcessor.debug:
                    print(f"Text columns to fix: {text_columns.tolist()}")
                df = DataProcessor.fix_dataframe_text(df, columns=text_columns)
            except Exception as e:
                print(f"ERROR in text fixing: {str(e)}")
                # Continue with original DataFrame if text fixing fails
                print("Continuing with original DataFrame without text fixes")
            
            if DataProcessor.debug:
                print("Text encoding fixes applied.")
                if 'PLAYER' in df.columns and len(df) > 0:
                    print(f"Sample after fix: {df['PLAYER'].iloc[0] if not pd.isna(df['PLAYER'].iloc[0]) else 'N/A'}")
                print(f"Finished processing with encoding: {encoding}")
                print(f"DataFrame has {len(df)} rows and {len(df.columns)} columns")
            
            # Drop any extra columns (keep only expected columns)
            try:
                expected_columns = ['DATE', 'PLAYER', 'SOURCE', 'CHEST', 'SCORE']
                extra_columns = [col for col in df.columns if col not in expected_columns]
                
                if extra_columns and DataProcessor.debug:
                    print(f"Dropping extra columns: {extra_columns}")
                    
                if extra_columns:
                    df = df.drop(columns=extra_columns)
            except Exception as e:
                print(f"ERROR in dropping extra columns: {str(e)}")
                # Continue with all columns if dropping fails
            
            # Reset debug flag
            DataProcessor.debug = False
            return df, True, ""
            
        except Exception as e:
            error_msg = f"Failed to load CSV file: {str(e)}"
            print(f"ERROR: {error_msg}")
            traceback.print_exc()
            # Reset debug flag
            DataProcessor.debug = False
            return None, False, error_msg
    
    @staticmethod
    def load_csv(filepath, encodings=None):
        """
        Load a CSV file and return a pandas DataFrame with enhanced error handling.
        Now uses the comprehensive encoding fix solution.
        
        Args:
            filepath (str or Path): Path to the CSV file
            encodings (list, optional): List of encodings to try. Defaults to None.
            
        Returns:
            tuple: (DataFrame, success, error_message)
        """
        # Use our new comprehensive read_csv_with_encoding_fix function
        return DataProcessor.read_csv_with_encoding_fix(filepath)
    
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
        
        # Add chest counts for player_totals
        player_counts = df.groupby('PLAYER').size().reset_index(name='CHEST_COUNT')
        player_totals = player_totals.merge(player_counts, on='PLAYER', how='left')
        
        # Calculate scores by chest type
        chest_totals = df.groupby('CHEST')['SCORE'].sum().reset_index()
        chest_totals = chest_totals.sort_values('SCORE', ascending=False)
        
        # Add chest counts for chest_totals (chest type frequency)
        chest_counts = df.groupby('CHEST').size().reset_index(name='CHEST_COUNT')
        chest_totals = chest_totals.merge(chest_counts, on='CHEST', how='left')
        
        # Calculate scores by source
        source_totals = df.groupby('SOURCE')['SCORE'].sum().reset_index()
        source_totals = source_totals.sort_values('SCORE', ascending=False)
        
        # Add chest counts for source_totals
        source_counts = df.groupby('SOURCE').size().reset_index(name='CHEST_COUNT')
        source_totals = source_totals.merge(source_counts, on='SOURCE', how='left')
        
        # Calculate scores by date
        date_totals = df.groupby('DATE')['SCORE'].sum().reset_index()
        date_totals = date_totals.sort_values('DATE')
        
        # Add chest counts for date_totals
        date_counts = df.groupby('DATE').size().reset_index(name='CHEST_COUNT')
        date_totals = date_totals.merge(date_counts, on='DATE', how='left')
        
        # Calculate average scores
        player_avg = df.groupby('PLAYER')['SCORE'].mean().reset_index()
        player_avg = player_avg.sort_values('SCORE', ascending=False)
        player_avg['SCORE'] = player_avg['SCORE'].round(2)
        
        # Most frequent chest types per player
        player_chest_freq = df.groupby(['PLAYER', 'CHEST']).size().reset_index(name='COUNT')
        
        # Create Player Overview (new)
        # Use the player_totals we already calculated with CHEST_COUNT
        player_overview = player_totals.copy()
        player_overview = player_overview.rename(columns={'SCORE': 'TOTAL_SCORE'})
        
        # Get the scores for each source type per player
        source_type_scores = df.pivot_table(
            index='PLAYER', 
            columns='SOURCE',  
            values='SCORE', 
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        # Merge source type scores with player overview
        player_overview = player_overview.merge(source_type_scores, on='PLAYER', how='left')
        
        # Sort by total score
        player_overview = player_overview.sort_values('TOTAL_SCORE', ascending=False)
        
        return {
            'player_totals': player_totals,
            'chest_totals': chest_totals,
            'source_totals': source_totals,
            'date_totals': date_totals,
            'player_avg': player_avg,
            'player_chest_freq': player_chest_freq,
            'player_overview': player_overview,
            'raw_data': df
        } 