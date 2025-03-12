#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple script to test the DataProcessor analysis functionality.
"""

import pandas as pd
from modules.dataprocessor import DataProcessor

def main():
    # Load the test data
    print("Loading test data file...")
    test_file = "data/test_data.csv"
    df = pd.read_csv(test_file)
    
    # Make sure DATE is in datetime format
    df['DATE'] = pd.to_datetime(df['DATE'])
    
    # Make sure SCORE is numeric
    df['SCORE'] = pd.to_numeric(df['SCORE'])
    
    print(f"Loaded {len(df)} rows.")
    print("Sample data:")
    print(df.head(3))
    print()
    
    # Analyze the data
    print("Analyzing data...")
    results = DataProcessor.analyze_data(df)
    
    # Print player totals
    print("\nPlayer Totals:")
    print(results['player_totals'])
    
    # Print chest totals
    print("\nChest Totals:")
    print(results['chest_totals'])
    
    # Print source totals
    print("\nSource Totals:")
    print(results['source_totals'])
    
    # Print player overview (this is what should appear in the Analysis tab)
    print("\nPlayer Overview:")
    print(results['player_overview'])
    
    print("\nAnalysis completed successfully!")

if __name__ == "__main__":
    main() 