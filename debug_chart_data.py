import pandas as pd
import sys
import matplotlib.pyplot as plt

# Mock data that mirrors what would be in the application
# Create a sample dataframe
df = pd.DataFrame({
    'PLAYER': ['Player1', 'Player2', 'Player3', 'Player1', 'Player2'],
    'SCORE': [100, 200, 300, 150, 250],
    'CHEST': ['Golden', 'Silver', 'Bronze', 'Golden', 'Golden'],
    'SOURCE': ['Guild', 'Battle', 'Event', 'Event', 'Guild'],
    'DATE': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05']
})

# Convert date and score columns
df['DATE'] = pd.to_datetime(df['DATE'])
df['SCORE'] = pd.to_numeric(df['SCORE'])

print("Original Data:")
print(df)
print("\n")

# This is a simplified version of the DataProcessor.analyze_data method
def analyze_data(df):
    """Process data according to requirements and return processed DataFrames."""
    print("Running analyze_data with dataframe of shape:", df.shape)
    
    # Calculate total score per player
    player_totals = df.groupby('PLAYER')['SCORE'].sum().reset_index()
    player_totals = player_totals.sort_values('SCORE', ascending=False)
    
    # Add chest counts for player_totals
    player_counts = df.groupby('PLAYER').size().reset_index(name='CHEST_COUNT')
    player_totals = player_totals.merge(player_counts, on='PLAYER', how='left')
    
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
        'player_overview': player_overview
    }

# Run the analysis
results = analyze_data(df)

# Print player totals and overview
print("Player Totals columns:", results['player_totals'].columns.tolist())
print("Player Totals data:")
print(results['player_totals'])
print("\n")

print("Player Overview columns:", results['player_overview'].columns.tolist())
print("Player Overview data:")
print(results['player_overview'])
print("\n")

# Simulate the _get_chart_data method for player data
def get_chart_data(data_category, analysis_results):
    print(f"Getting chart data for category: {data_category}")
    
    if data_category == "PLAYER":
        if 'player_totals' in analysis_results:
            data = analysis_results['player_totals'].copy()
            print(f"Player data columns: {data.columns.tolist()}")
            print(f"Player data sample:\n{data.head(3)}")
            return data
    return None

# Simulate the _create_bar_chart method
def create_bar_chart(data, category_column, measure):
    print(f"Creating bar chart with: category_column={category_column}, measure={measure}")
    
    if measure not in data.columns:
        print(f"ERROR: Measure '{measure}' not found in columns: {data.columns.tolist()}")
        return None
    
    # Create a simple plot
    plt.figure(figsize=(10, 6))
    plt.bar(data[category_column], data[measure])
    plt.title(f"{category_column} by {measure}")
    plt.xlabel(category_column)
    plt.ylabel(measure)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    print("Bar chart created successfully")
    
    # Save the plot to a file
    plt.savefig("debug_chart.png")
    print("Chart saved to debug_chart.png")
    return True

# Test the chart creation with both player_totals and player_overview
data_sources = {
    "PLAYER": ["SCORE", "CHEST_COUNT"],
    "PLAYER OVERVIEW": ["TOTAL_SCORE", "CHEST_COUNT", "Battle", "Event", "Guild"]
}

# Test chart creation with player_totals (SCORE, CHEST_COUNT)
print("\n=== Testing chart creation with player_totals ===")
player_data = get_chart_data("PLAYER", results)
if player_data is not None:
    for measure in data_sources["PLAYER"]:
        print(f"\nAttempting to create chart with measure: {measure}")
        create_bar_chart(player_data, "PLAYER", measure)

# Test chart creation with player_overview (different column set)
print("\n=== Testing chart creation with player_overview ===")
if 'player_overview' in results:
    player_overview_data = results['player_overview'].copy()
    for measure in data_sources["PLAYER OVERVIEW"]:
        print(f"\nAttempting to create chart with measure: {measure}")
        create_bar_chart(player_overview_data, "PLAYER", measure) 