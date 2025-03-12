# Total Battle Analyzer

A desktop application for analyzing and visualizing chest data from the Total Battle game. This tool helps players track their progress, analyze chest rewards, and gain insights into their gameplay.

![Total Battle Analyzer](docs/images/app_screenshot.png)

## Features

- **CSV Data Import**: Import chest data from CSV files with support for multiple encodings
- **Raw Data View**: View and filter your raw chest data
- **Advanced Analysis**: Get statistical insights about your chest rewards
- **Data Visualization**: Generate charts to visualize your progress
- **Export Functionality**: Export filtered data and analysis results
- **Total Battle Theme**: Enjoy a dark blue and gold theme inspired by the game

## Installation

### Prerequisites

- Python 3.8 or higher
- PySide6 (Qt for Python)
- pandas
- matplotlib
- numpy

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/total-battle-analyzer.git
   cd total-battle-analyzer
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

There are several ways to run the application, each with different levels of error handling and robustness:

1. **Standard Launch**: Run the main application directly
   ```bash
   python src/total-battle-analyzer.py
   ```

2. **Simple Launcher**: Use the simple launcher for basic styling and error handling
   ```bash
   python simple_launcher.py
   ```

3. **Fixed Application Launcher**: Use the fixed launcher with automatic code patching
   ```bash
   python fixed_app.py
   ```

4. **Robust Launcher with Splash Screen**: Use the most comprehensive launcher
   ```bash
   python run_fixed_app.py
   ```

## Usage

### Importing Data

1. Launch the application using one of the methods above
2. Click on "Select CSV File" in the Import tab or use File > Import CSV
3. Select your Total Battle chest data CSV file
4. The data will be loaded and displayed in the Raw Data tab

### CSV File Format

Your CSV file should have the following columns:
- DATE: The date when the chest was opened (YYYY-MM-DD format)
- PLAYER: The player name
- SOURCE: Where the chest came from (e.g., "Level 25 Crypt")
- CHEST: The type of chest (e.g., "Fire Chest", "Rare Dragon Chest")
- SCORE: The score/value of the chest

Example:
```
DATE,PLAYER,SOURCE,CHEST,SCORE
2025-03-11,Player1,Level 25 Crypt,Fire Chest,275
2025-03-11,Player1,Level 25 rare Crypt,Rare Dragon Chest,350
2025-03-11,Player2,Level 25 Crypt,Bone Chest,275
```

### Analyzing Data

1. After importing data, navigate to the Analysis tab
2. Select an analysis view from the dropdown (e.g., "Player Overview")
3. Apply filters if needed using the filter panel
4. View the analysis results in the table

### Creating Charts

1. Navigate to the Charts tab
2. Select a chart type from the dropdown
3. Configure chart options as needed
4. The chart will be generated based on your data and settings

### Exporting Results

1. Use the export buttons in the Raw Data or Analysis tabs
2. Select a location to save your exported CSV file
3. The filtered/analyzed data will be saved to the selected location

## Troubleshooting

### CSV Import Issues

If you encounter issues importing CSV files:

1. Check that your CSV file has the required columns (DATE, PLAYER, SOURCE, CHEST, SCORE)
2. Ensure the file is properly formatted with commas as separators
3. For files with special characters (like German umlauts), try using the fixed_app.py launcher which has enhanced encoding support

### Display Issues

If the application doesn't display properly:

1. Try using one of the custom launchers (simple_launcher.py or run_fixed_app.py)
2. Ensure you have the latest version of PySide6 installed
3. Check that your system meets the minimum requirements

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Total Battle game for inspiration
- PySide6/Qt for the GUI framework
- pandas and matplotlib for data processing and visualization
