#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to verify the Analysis tab functionality.
This script directly processes test data using DataProcessor and displays the results
to simulate what should appear in the Analysis tab.
"""

import pandas as pd
from modules.dataprocessor import DataProcessor

def print_separator(title):
    """Print a separator with a title."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def main():
    print_separator("LOADING TEST DATA")
    
    # Load the test data
    test_file = "data/test_data.csv"
    df = pd.read_csv(test_file)
    
    # Make sure DATE is in datetime format
    df['DATE'] = pd.to_datetime(df['DATE'])
    
    # Make sure SCORE is numeric
    df['SCORE'] = pd.to_numeric(df['SCORE'])
    
    print(f"Loaded {len(df)} rows with columns: {df.columns.tolist()}")
    print("\nSample data:")
    print(df.head(3))
    
    print_separator("ANALYZING DATA WITH DataProcessor")
    
    # Analyze the data
    results = DataProcessor.analyze_data(df)
    
    # Print all available analysis types
    print("Available analysis result types:")
    for key in results.keys():
        if isinstance(results[key], pd.DataFrame):
            print(f"  - {key}: DataFrame with shape {results[key].shape}")
        else:
            print(f"  - {key}: {type(results[key])}")
    
    print_separator("PLAYER OVERVIEW")
    print("This should be the default view in the Analysis tab.")
    player_overview = results['player_overview']
    print(f"\nShape: {player_overview.shape}")
    print(f"Columns: {player_overview.columns.tolist()}")
    print("\nFull Player Overview data:")
    print(player_overview)
    
    print_separator("PLAYER TOTALS")
    print("This is what should display when selecting 'Player Totals' in the Analysis tab.")
    player_totals = results['player_totals']
    print(f"\nShape: {player_totals.shape}")
    print(f"Columns: {player_totals.columns.tolist()}")
    print("\nFull Player Totals data:")
    print(player_totals)
    
    print_separator("CHEST TOTALS")
    print("This is what should display when selecting 'Chest Totals' in the Analysis tab.")
    chest_totals = results['chest_totals']
    print(f"\nShape: {chest_totals.shape}")
    print(f"Columns: {chest_totals.columns.tolist()}")
    print("\nFull Chest Totals data:")
    print(chest_totals)
    
    print_separator("SOURCE TOTALS")
    print("This is what should display when selecting 'Source Totals' in the Analysis tab.")
    source_totals = results['source_totals']
    print(f"\nShape: {source_totals.shape}")
    print(f"Columns: {source_totals.columns.tolist()}")
    print("\nFull Source Totals data:")
    print(source_totals)
    
    print_separator("DATE TOTALS")
    print("This is what should display when selecting 'Date Totals' in the Analysis tab.")
    date_totals = results['date_totals']
    print(f"\nShape: {date_totals.shape}")
    print(f"Columns: {date_totals.columns.tolist()}")
    print("\nFull Date Totals data:")
    print(date_totals)
    
    print_separator("VERIFICATION CRITERIA")
    print("The Analysis tab should be displaying processed data, NOT raw data.")
    print("Here's what to check:")
    print("1. Player Overview should show total scores and chest counts for each player")
    print("2. Player Overview should also show a breakdown of scores by source for each player")
    print("3. Player Totals should only show the player name and total score")
    print("4. Chest Totals should show the total score for each chest type")
    print("5. Source Totals should show the total score for each source type")
    print("6. Date Totals should show the total score for each date")
    print("7. These views should be selected from analysis_results, not just aggregate on raw data")
    
    print_separator("TEST COMPLETE")

if __name__ == "__main__":
    main() 