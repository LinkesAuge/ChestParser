# dataprocessor.py - DataProcessor class implementation
from modules.utils import *
import os
import re
import pandas as pd
import unicodedata

class DataProcessor:
    """Class to handle data processing logic"""
    
    # Debug flag - set to False to reduce console output
    debug = False
    
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
        if DataProcessor.debug:
            print("=== DataProcessor.load_csv ===")
            print(f"Processing filepath: {filepath}")
            print(f"Type of filepath: {type(filepath)}")
        
        # Check if the file exists
        file_exists = os.path.exists(filepath)
        if not file_exists:
            return None, False, f"File not found: {filepath}"
        
        # Get file size
        file_size = os.path.getsize(filepath)
        if DataProcessor.debug:
            print(f"File size: {file_size} bytes")
                
        # Check if file is empty
        if file_size == 0:
            return None, False, "File is empty"

        # Simple approach: Just use latin1 which handles German characters well
        # Latin1 (ISO-8859-1) is the most reliable for German text with umlauts
        encoding_to_use = 'cp1252'
        
        try:
            if DataProcessor.debug:
                print(f"Using encoding: {encoding_to_use}")
            
            # Try to read with latin1 encoding
            df = pd.read_csv(filepath, encoding=encoding_to_use)
            
            if 'PLAYER' not in df.columns:
                if DataProcessor.debug:
                    print(f"Missing PLAYER column, trying with other encodings")
                
                # If latin1 fails to find expected columns, try these as fallbacks
                fallback_encodings = ['cp1252', 'latin1', 'utf-8']
                for enc in fallback_encodings:
                    try:
                        df = pd.read_csv(filepath, encoding=enc)
                        if 'PLAYER' in df.columns:
                            if DataProcessor.debug:
                                print(f"Successfully loaded with fallback encoding: {enc}")
                            break
                    except Exception:
                        continue
            
            # If still no PLAYER column, return error
            if 'PLAYER' not in df.columns:
                return None, False, "CSV file does not contain required PLAYER column"
            
        except Exception as e:
            if DataProcessor.debug:
                print(f"Failed with {encoding_to_use}: {str(e)}")
            
            # Try with cp1252 as fallback
            try:
                df = pd.read_csv(filepath, encoding='cp1252')
                if DataProcessor.debug:
                    print("Fallback to cp1252 successful")
            except Exception as e:
                if DataProcessor.debug:
                    print(f"Fallback failed: {str(e)}")
                return None, False, f"Failed to load CSV: {str(e)}"
        
        if DataProcessor.debug:
            print(f"Successfully loaded CSV with encoding: {encoding_to_use}")
            print("Sample of player names (no processing applied):")
            print(df['PLAYER'].head(10).tolist())
        
        # Process PLAYER column minimally (just handle NaN values)
        if 'PLAYER' in df.columns:
            # Handle NaN values
            df['PLAYER'] = df['PLAYER'].fillna('')
        
        # Drop any extra columns (keep only expected columns)
        expected_columns = ['DATE', 'PLAYER', 'SOURCE', 'CHEST', 'SCORE']
        extra_columns = [col for col in df.columns if col not in expected_columns]
        
        if extra_columns and DataProcessor.debug:
            print(f"Dropping extra columns: {extra_columns}")
            
        if extra_columns:
            df = df.drop(columns=extra_columns)
        
        if DataProcessor.debug:
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