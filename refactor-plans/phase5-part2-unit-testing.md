# Total Battle Analyzer Refactoring Plan: Phase 5 - Part 2
## Unit Testing Implementation

This document outlines the implementation of comprehensive unit tests for the Total Battle Analyzer application. Unit tests focus on testing individual components in isolation to ensure each part of the application works correctly on its own.

## Implementation Tasks

- [ ] **Data Layer Unit Tests**
  - [ ] Test DataProcessor initialization and configuration
  - [ ] Test CSV file loading with various encodings
  - [ ] Test data transformation and cleaning
  - [ ] Test analysis algorithms
  - [ ] Test data filtering and aggregation

- [ ] **Service Layer Unit Tests**
  - [ ] Test AnalysisService functionality
  - [ ] Test ChartService and visualization
  - [ ] Test ReportService and output generation
  - [ ] Test ApplicationService coordination
  - [ ] Test ConfigManager for settings management

- [ ] **UI Component Unit Tests**
  - [ ] Test base UI components
  - [ ] Test data display widgets
  - [ ] Test form controls
  - [ ] Test dialog components
  - [ ] Test screen base classes

- [ ] **Utility Function Unit Tests**
  - [ ] Test filesystem utilities
  - [ ] Test data conversion helpers
  - [ ] Test string processing functions
  - [ ] Test validation utilities
  - [ ] Test error handling functions

## Implementation Details

### 1. Data Layer Unit Tests

#### DataProcessor Tests

```python
# tests/unit/data/test_data_processor.py
import pytest
import pandas as pd
from pathlib import Path
import numpy as np
from src.modules.dataprocessor import DataProcessor

class TestDataProcessor:
    """Unit tests for the DataProcessor class."""
    
    @pytest.fixture
    def data_processor(self):
        """Create a DataProcessor instance for testing."""
        return DataProcessor(debug=False)
    
    def test_init(self, data_processor):
        """Test DataProcessor initialization."""
        assert data_processor is not None
        assert not data_processor.debug
    
    def test_read_csv_with_encoding_fix(self, data_processor, small_csv_path):
        """Test CSV file loading with encoding fixes."""
        # Load the small test CSV file
        df = data_processor.read_csv_with_encoding_fix(small_csv_path)
        
        # Check that required columns are present
        assert "DATE" in df.columns
        assert "PLAYER" in df.columns
        assert "SOURCE" in df.columns
        assert "CHEST" in df.columns
        assert "SCORE" in df.columns
        
        # Check that data was loaded
        assert not df.empty
        assert len(df) > 0
    
    def test_read_csv_with_special_chars(self, data_processor, special_chars_csv_path):
        """Test CSV loading with special characters."""
        # Load the special characters test CSV file
        df = data_processor.read_csv_with_encoding_fix(special_chars_csv_path)
        
        # Check that German characters are properly handled
        players = df["PLAYER"].unique().tolist()
        assert any("ä" in player for player in players)
        assert any("ö" in player for player in players)
        assert any("ü" in player for player in players)
    
    def test_fix_dataframe_text(self, data_processor):
        """Test text fixing in DataFrames."""
        # Create a DataFrame with problematic characters
        df = pd.DataFrame({
            "PLAYER": ["M\udcfcller", "J\udceger", "Kr\udcfcmel", "Normal"],
            "SOURCE": ["Guild", "Battle", "Event", "Arena"]
        })
        
        # Fix the text
        fixed_df = data_processor.fix_dataframe_text(df)
        
        # Check that characters were fixed
        assert "Müller" in fixed_df["PLAYER"].values
        assert "Normal" in fixed_df["PLAYER"].values
    
    def test_analyze_data(self, data_processor, sample_dataframe):
        """Test data analysis functionality."""
        # Run analysis on sample data
        analysis_results = data_processor.analyze_data(sample_dataframe)
        
        # Check that analysis results contain expected keys
        assert "player_totals" in analysis_results
        assert "chest_analysis" in analysis_results
        assert "source_analysis" in analysis_results
        
        # Check player_totals results
        player_totals = analysis_results["player_totals"]
        assert "PLAYER" in player_totals.columns
        assert "TOTAL_SCORE" in player_totals.columns
        assert "CHEST_COUNT" in player_totals.columns
        
        # Verify calculations
        player1_data = player_totals[player_totals["PLAYER"] == "Player1"]
        assert player1_data["TOTAL_SCORE"].iloc[0] == 1200  # 500 + 700
        assert player1_data["CHEST_COUNT"].iloc[0] == 2
    
    def test_analyze_chests_data(self, data_processor, sample_dataframe):
        """Test chest-specific analysis."""
        # Run chest analysis on sample data
        chest_results = data_processor.analyze_chests_data(sample_dataframe)
        
        # Check chest analysis results
        assert "CHEST" in chest_results.columns
        assert "TOTAL_SCORE" in chest_results.columns
        assert "CHEST_COUNT" in chest_results.columns
        assert "AVG_SCORE" in chest_results.columns
        
        # Verify calculations for Gold chests
        gold_data = chest_results[chest_results["CHEST"] == "Gold"]
        assert gold_data["CHEST_COUNT"].iloc[0] == 3
        assert gold_data["TOTAL_SCORE"].iloc[0] == 1800  # 500 + 700 + 600
        assert gold_data["AVG_SCORE"].iloc[0] == 600  # 1800 / 3
    
    def test_filter_by_date_range(self, data_processor, sample_dataframe):
        """Test date range filtering."""
        # Add a proper datetime column
        sample_dataframe["DATE_DT"] = pd.to_datetime(sample_dataframe["DATE"])
        
        # Filter for a specific date range
        start_date = pd.to_datetime("2023-01-02")
        end_date = pd.to_datetime("2023-01-04")
        filtered_df = data_processor.filter_by_date_range(
            sample_dataframe, start_date, end_date, "DATE_DT"
        )
        
        # Check filtered results
        assert len(filtered_df) == 3  # Only rows from Jan 2-4
        dates = pd.to_datetime(filtered_df["DATE"]).dt.strftime("%Y-%m-%d").tolist()
        assert "2023-01-02" in dates
        assert "2023-01-03" in dates
        assert "2023-01-04" in dates
        assert "2023-01-01" not in dates
        assert "2023-01-05" not in dates
    
    def test_filter_by_values(self, data_processor, sample_dataframe):
        """Test value filtering."""
        # Filter for specific players
        players = ["Player1", "Player3"]
        filtered_df = data_processor.filter_by_values(
            sample_dataframe, "PLAYER", players
        )
        
        # Check filtered results
        assert len(filtered_df) == 3  # Only Player1 and Player3 rows
        assert set(filtered_df["PLAYER"].unique()) == set(players)
        assert "Player2" not in filtered_df["PLAYER"].values
```

#### CSV Parsing Tests

```python
# tests/unit/data/test_csv_parser.py
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import os

class TestCSVParsing:
    """Tests for CSV parsing functionality."""
    
    def test_multiple_encodings(self, data_processor):
        """Test CSV loading with different encodings."""
        # Create temporary files with different encodings
        with tempfile.TemporaryDirectory() as tmp_dir:
            # UTF-8 file
            utf8_path = Path(tmp_dir) / "utf8.csv"
            with open(utf8_path, 'w', encoding='utf-8') as f:
                f.write("DATE,PLAYER,SOURCE,CHEST,SCORE\n")
                f.write("2023-01-01,Müller,Guild,Gold,500\n")
            
            # Windows-1252 file
            cp1252_path = Path(tmp_dir) / "cp1252.csv"
            with open(cp1252_path, 'w', encoding='cp1252') as f:
                f.write("DATE,PLAYER,SOURCE,CHEST,SCORE\n")
                f.write("2023-01-01,Müller,Guild,Gold,500\n")
            
            # ISO-8859-1 file
            latin1_path = Path(tmp_dir) / "latin1.csv"
            with open(latin1_path, 'w', encoding='latin-1') as f:
                f.write("DATE,PLAYER,SOURCE,CHEST,SCORE\n")
                f.write("2023-01-01,Müller,Guild,Gold,500\n")
            
            # Test loading with each encoding
            utf8_df = data_processor.read_csv_with_encoding_fix(utf8_path)
            cp1252_df = data_processor.read_csv_with_encoding_fix(cp1252_path)
            latin1_df = data_processor.read_csv_with_encoding_fix(latin1_path)
            
            # All files should load correctly
            assert not utf8_df.empty
            assert not cp1252_df.empty
            assert not latin1_df.empty
            
            # Check for proper character handling
            assert "Müller" in utf8_df["PLAYER"].values
            assert "Müller" in cp1252_df["PLAYER"].values
            assert "Müller" in latin1_df["PLAYER"].values
    
    def test_different_separators(self, data_processor):
        """Test CSV loading with different separators."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Comma separator
            comma_path = Path(tmp_dir) / "comma.csv"
            with open(comma_path, 'w') as f:
                f.write("DATE,PLAYER,SOURCE,CHEST,SCORE\n")
                f.write("2023-01-01,Player1,Guild,Gold,500\n")
            
            # Semicolon separator
            semicolon_path = Path(tmp_dir) / "semicolon.csv"
            with open(semicolon_path, 'w') as f:
                f.write("DATE;PLAYER;SOURCE;CHEST;SCORE\n")
                f.write("2023-01-01;Player1;Guild;Gold;500\n")
            
            # Test loading with each separator
            comma_df = data_processor.read_csv_with_encoding_fix(comma_path)
            semicolon_df = data_processor.read_csv_with_encoding_fix(semicolon_path)
            
            # Both files should load correctly
            assert not comma_df.empty
            assert not semicolon_df.empty
            assert len(comma_df.columns) == 5
            assert len(semicolon_df.columns) == 5
            
            # Both should have the same data
            assert "Player1" in comma_df["PLAYER"].values
            assert "Player1" in semicolon_df["PLAYER"].values
```

### 2. Service Layer Unit Tests

#### AnalysisService Tests

```python
# tests/unit/services/test_analysis_service.py
import pytest
import pandas as pd
import numpy as np
from src.services.analysis_service import AnalysisService
from src.models.analysis_result import AnalysisResult

class TestAnalysisService:
    """Unit tests for the AnalysisService class."""
    
    @pytest.fixture
    def analysis_service(self):
        """Create an AnalysisService instance for testing."""
        return AnalysisService()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        return pd.DataFrame({
            "DATE": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-02", "2023-01-03"],
            "PLAYER": ["Player1", "Player2", "Player1", "Player3", "Player2"],
            "SOURCE": ["Guild", "Battle", "Event", "Guild", "Event"],
            "CHEST": ["Gold", "Silver", "Gold", "Bronze", "Gold"],
            "SCORE": [500, 300, 700, 200, 600]
        })
    
    def test_init(self, analysis_service):
        """Test AnalysisService initialization."""
        assert analysis_service is not None
    
    def test_analyze(self, analysis_service, sample_data):
        """Test the analyze method."""
        # Run analysis
        result = analysis_service.analyze(sample_data)
        
        # Check the result type
        assert isinstance(result, AnalysisResult)
        
        # Check that the result contains the expected data
        assert result.player_analysis is not None
        assert result.chest_analysis is not None
        assert result.source_analysis is not None
        assert result.date_analysis is not None
    
    def test_analyze_players(self, analysis_service, sample_data):
        """Test player analysis."""
        # Analyze player data
        player_df = analysis_service.analyze_players(sample_data)
        
        # Check result structure
        assert "PLAYER" in player_df.columns
        assert "TOTAL_SCORE" in player_df.columns
        assert "CHEST_COUNT" in player_df.columns
        assert "AVG_SCORE" in player_df.columns
        
        # Check player calculations
        player1 = player_df[player_df["PLAYER"] == "Player1"]
        assert player1["TOTAL_SCORE"].iloc[0] == 1200  # 500 + 700
        assert player1["CHEST_COUNT"].iloc[0] == 2
        assert player1["AVG_SCORE"].iloc[0] == 600  # 1200 / 2
        
        # Check player ranking
        assert player_df["TOTAL_SCORE"].iloc[0] >= player_df["TOTAL_SCORE"].iloc[1]
    
    def test_analyze_chests(self, analysis_service, sample_data):
        """Test chest analysis."""
        # Analyze chest data
        chest_df = analysis_service.analyze_chests(sample_data)
        
        # Check result structure
        assert "CHEST" in chest_df.columns
        assert "TOTAL_SCORE" in chest_df.columns
        assert "CHEST_COUNT" in chest_df.columns
        
        # Check chest calculations
        gold = chest_df[chest_df["CHEST"] == "Gold"]
        assert gold["CHEST_COUNT"].iloc[0] == 3
        assert gold["TOTAL_SCORE"].iloc[0] == 1800  # 500 + 700 + 600
    
    def test_analyze_sources(self, analysis_service, sample_data):
        """Test source analysis."""
        # Analyze source data
        source_df = analysis_service.analyze_sources(sample_data)
        
        # Check result structure
        assert "SOURCE" in source_df.columns
        assert "TOTAL_SCORE" in source_df.columns
        assert "CHEST_COUNT" in source_df.columns
        
        # Check source calculations
        guild = source_df[source_df["SOURCE"] == "Guild"]
        assert guild["CHEST_COUNT"].iloc[0] == 2
        assert guild["TOTAL_SCORE"].iloc[0] == 700  # 500 + 200
    
    def test_analyze_dates(self, analysis_service, sample_data):
        """Test date analysis."""
        # Analyze date data
        date_df = analysis_service.analyze_dates(sample_data)
        
        # Check result structure
        assert "DATE" in date_df.columns
        assert "TOTAL_SCORE" in date_df.columns
        assert "CHEST_COUNT" in date_df.columns
        
        # Check date calculations
        jan2 = date_df[date_df["DATE"] == "2023-01-02"]
        assert jan2["CHEST_COUNT"].iloc[0] == 2
        assert jan2["TOTAL_SCORE"].iloc[0] == 500  # 300 + 200
```

#### ChartService Tests

```python
# tests/unit/services/test_chart_service.py
import pytest
import pandas as pd
import matplotlib.pyplot as plt
from src.visualization.charts.chart_service import ChartService
from src.visualization.charts.chart_configuration import ChartConfiguration

class TestChartService:
    """Unit tests for the ChartService class."""
    
    @pytest.fixture
    def chart_service(self):
        """Create a ChartService instance for testing."""
        return ChartService()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        return pd.DataFrame({
            "Category": ["A", "B", "C", "D", "E"],
            "Value": [10, 25, 15, 30, 20]
        })
    
    @pytest.fixture
    def chart_config(self):
        """Create a chart configuration for testing."""
        return ChartConfiguration(
            chart_type="bar",
            title="Test Chart",
            x_label="Category",
            y_label="Value",
            show_values=True,
            theme="dark"
        )
    
    def test_init(self, chart_service):
        """Test ChartService initialization."""
        assert chart_service is not None
    
    def test_create_bar_chart(self, chart_service, sample_data, chart_config):
        """Test bar chart creation."""
        # Create a bar chart
        fig, ax = chart_service.create_bar_chart(
            sample_data, "Category", "Value", chart_config
        )
        
        # Check that figure and axes were created
        assert fig is not None
        assert ax is not None
        
        # Check chart properties
        assert ax.get_title() == "Test Chart"
        assert ax.get_xlabel() == "Category"
        assert ax.get_ylabel() == "Value"
        
        # Clean up
        plt.close(fig)
    
    def test_create_pie_chart(self, chart_service, sample_data, chart_config):
        """Test pie chart creation."""
        # Create a pie chart
        fig, ax = chart_service.create_pie_chart(
            sample_data, "Category", "Value", chart_config
        )
        
        # Check that figure and axes were created
        assert fig is not None
        assert ax is not None
        
        # Check chart properties
        assert ax.get_title() == "Test Chart"
        
        # Clean up
        plt.close(fig)
    
    def test_create_line_chart(self, chart_service, chart_config):
        """Test line chart creation."""
        # Create sample time series data
        data = pd.DataFrame({
            "Date": pd.date_range(start="2023-01-01", periods=5),
            "Value": [10, 15, 13, 17, 20]
        })
        
        # Create a line chart
        fig, ax = chart_service.create_line_chart(
            data, "Date", "Value", chart_config
        )
        
        # Check that figure and axes were created
        assert fig is not None
        assert ax is not None
        
        # Check chart properties
        assert ax.get_title() == "Test Chart"
        assert ax.get_xlabel() == "Date"
        assert ax.get_ylabel() == "Value"
        
        # Clean up
        plt.close(fig)
    
    def test_apply_theme(self, chart_service, sample_data, chart_config):
        """Test theme application."""
        # Create a chart with a theme
        fig, ax = chart_service.create_bar_chart(
            sample_data, "Category", "Value", chart_config
        )
        
        # Check that theme was applied
        if chart_config.theme == "dark":
            assert fig.get_facecolor() == (0.1, 0.15, 0.25, 1.0)  # Dark blue
        
        # Clean up
        plt.close(fig)
    
    def test_save_chart(self, chart_service, sample_data, chart_config, temp_test_dir):
        """Test chart saving functionality."""
        # Create a chart
        fig, ax = chart_service.create_bar_chart(
            sample_data, "Category", "Value", chart_config
        )
        
        # Save the chart
        save_path = temp_test_dir / "test_chart.png"
        chart_service.save_chart(fig, save_path)
        
        # Check that file was created
        assert save_path.exists()
        assert save_path.stat().st_size > 0
        
        # Clean up
        plt.close(fig)
```

#### ReportService Tests

```python
# tests/unit/services/test_report_service.py
import pytest
from pathlib import Path
from src.visualization.reports.report_service import ReportService
from src.visualization.reports.html_report_service import HTMLReportService

class TestReportService:
    """Unit tests for the ReportService abstract class and implementations."""
    
    @pytest.fixture
    def html_report_service(self):
        """Create an HTMLReportService instance for testing."""
        return HTMLReportService()
    
    def test_html_service_init(self, html_report_service):
        """Test HTMLReportService initialization."""
        assert html_report_service is not None
        assert isinstance(html_report_service, ReportService)
    
    def test_create_report(self, html_report_service):
        """Test report creation."""
        # Create a simple report
        report_content = html_report_service.create_report(
            title="Test Report",
            sections=[],
            header_content="Test Header",
            footer_content="Test Footer"
        )
        
        # Check report content
        assert "<title>Test Report</title>" in report_content
        assert "Test Header" in report_content
        assert "Test Footer" in report_content
    
    def test_create_section(self, html_report_service):
        """Test section creation."""
        # Create a section
        section_content = html_report_service.create_section(
            title="Test Section",
            content="Test Content"
        )
        
        # Check section content
        assert "<h2>Test Section</h2>" in section_content
        assert "Test Content" in section_content
    
    def test_create_table(self, html_report_service, sample_dataframe):
        """Test table creation."""
        # Create a table
        table_content = html_report_service.create_table(
            sample_dataframe,
            title="Test Table"
        )
        
        # Check table content
        assert "<h3>Test Table</h3>" in table_content
        assert "<table" in table_content
        assert "PLAYER" in table_content
        assert "SCORE" in table_content
    
    def test_export_report(self, html_report_service, temp_test_dir):
        """Test report export functionality."""
        # Create a simple report
        report_content = html_report_service.create_report(
            title="Test Report",
            sections=["<p>Test Section</p>"],
            header_content="Test Header",
            footer_content="Test Footer"
        )
        
        # Export the report
        export_path = temp_test_dir / "test_report.html"
        html_report_service.export_report(report_content, export_path)
        
        # Check that file was created
        assert export_path.exists()
        assert export_path.stat().st_size > 0
        
        # Check file content
        with open(export_path, "r") as f:
            file_content = f.read()
            assert "<title>Test Report</title>" in file_content
            assert "Test Section" in file_content
```

### 3. UI Component Unit Tests

#### Basic Widget Tests

```python
# tests/unit/ui/test_widgets.py
import pytest
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, Signal
from src.ui.widgets.data_table import DataTableWidget
from src.ui.widgets.file_selector import FileSelectorWidget

class TestDataTableWidget:
    """Tests for the DataTableWidget."""
    
    @pytest.fixture
    def data_table(self, app):
        """Create a DataTableWidget instance for testing."""
        return DataTableWidget()
    
    def test_init(self, data_table):
        """Test widget initialization."""
        assert data_table is not None
        assert hasattr(data_table, 'table_view')
    
    def test_set_model(self, data_table, sample_dataframe):
        """Test setting the data model."""
        # Set the model with sample data
        data_table.set_data(sample_dataframe)
        
        # Check that model is set
        assert data_table.table_view.model() is not None
        
        # Check model data
        model = data_table.table_view.model()
        assert model.rowCount() == len(sample_dataframe)
        assert model.columnCount() == len(sample_dataframe.columns)
    
    def test_sorting(self, data_table, sample_dataframe, qtbot):
        """Test table sorting functionality."""
        # Set the model with sample data
        data_table.set_data(sample_dataframe)
        
        # Get the header
        header = data_table.table_view.horizontalHeader()
        
        # Click on the SCORE column header to sort
        score_column = sample_dataframe.columns.get_loc("SCORE")
        qtbot.mouseClick(header.viewport(), Qt.LeftButton, pos=header.sectionPosition(score_column) + 5)
        
        # Check that sorting was applied
        proxy_model = data_table.table_view.model()
        assert proxy_model.sortColumn() == score_column
    
    def test_filtering(self, data_table, sample_dataframe):
        """Test table filtering functionality."""
        # Set the model with sample data
        data_table.set_data(sample_dataframe)
        
        # Apply a filter for Player1
        data_table.set_filter("PLAYER", ["Player1"])
        
        # Check filtered data
        model = data_table.table_view.model()
        assert model.rowCount() < len(sample_dataframe)
        
        # Check that only Player1 rows are visible
        for row in range(model.rowCount()):
            player_idx = sample_dataframe.columns.get_loc("PLAYER")
            player_value = model.index(row, player_idx).data()
            assert player_value == "Player1"

class TestFileSelectorWidget:
    """Tests for the FileSelectorWidget."""
    
    @pytest.fixture
    def file_selector(self, app):
        """Create a FileSelectorWidget instance for testing."""
        return FileSelectorWidget(file_types="CSV files (*.csv)")
    
    def test_init(self, file_selector):
        """Test widget initialization."""
        assert file_selector is not None
        assert hasattr(file_selector, 'select_button')
    
    def test_signals(self, file_selector):
        """Test that signals are properly defined."""
        assert hasattr(file_selector, 'fileSelected')
        assert isinstance(file_selector.fileSelected, Signal)
    
    def test_set_recent_files(self, file_selector):
        """Test setting recent files."""
        # Set recent files
        recent_files = ["/path/to/file1.csv", "/path/to/file2.csv"]
        file_selector.set_recent_files(recent_files)
        
        # Check that recent files were added
        assert hasattr(file_selector, 'recent_files_menu')
        assert file_selector.recent_files_menu.actions()[0].text() == "file1.csv"
        assert file_selector.recent_files_menu.actions()[1].text() == "file2.csv"
```

#### Screen Tests

```python
# tests/unit/ui/test_screens.py
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from src.ui.screens.base_screen import BaseScreen
from src.ui.screens.import_screen import ImportScreen

class TestBaseScreen:
    """Tests for the BaseScreen class."""
    
    @pytest.fixture
    def base_screen(self, app):
        """Create a BaseScreen instance for testing."""
        return BaseScreen()
    
    def test_init(self, base_screen):
        """Test screen initialization."""
        assert base_screen is not None
        assert hasattr(base_screen, 'layout')
    
    def test_load_data(self, base_screen):
        """Test loading data into the screen."""
        # Load test data
        test_data = {"key": "value"}
        base_screen.load_data(test_data)
        
        # Check that data was stored
        assert hasattr(base_screen, '_data')
        assert base_screen._data == test_data
    
    def test_clear(self, base_screen):
        """Test screen clearing."""
        # Load test data
        test_data = {"key": "value"}
        base_screen.load_data(test_data)
        
        # Clear the screen
        base_screen.clear()
        
        # Check that data was cleared
        assert base_screen._data == {}

class TestImportScreen:
    """Tests for the ImportScreen class."""
    
    @pytest.fixture
    def import_screen(self, app):
        """Create an ImportScreen instance for testing."""
        return ImportScreen()
    
    def test_init(self, import_screen):
        """Test screen initialization."""
        assert import_screen is not None
        assert hasattr(import_screen, 'file_selector')
    
    def test_load_data(self, import_screen):
        """Test loading data into the screen."""
        # Load test data
        test_data = {"recent_files": ["/path/to/file.csv"]}
        import_screen.load_data(test_data)
        
        # Check that data was passed to file selector
        assert hasattr(import_screen.file_selector, 'recent_files_menu')
        assert len(import_screen.file_selector.recent_files_menu.actions()) > 0
```

### 4. Utility Function Unit Tests

#### Helper Function Tests

```python
# tests/unit/utils/test_helpers.py
import pytest
from pathlib import Path
import tempfile
import pandas as pd
from src.utils.helpers import (
    ensure_directory_exists,
    is_valid_csv,
    generate_export_filename,
    sanitize_filename
)

class TestHelperFunctions:
    """Tests for helper utility functions."""
    
    def test_ensure_directory_exists(self, temp_test_dir):
        """Test directory creation."""
        # Test path
        test_dir = temp_test_dir / "test_subdir" / "nested"
        
        # Ensure directory exists
        ensure_directory_exists(test_dir)
        
        # Check that directory was created
        assert test_dir.exists()
        assert test_dir.is_dir()
    
    def test_is_valid_csv(self, small_csv_path):
        """Test CSV validation."""
        # Test with valid CSV
        assert is_valid_csv(small_csv_path)
        
        # Test with invalid file
        with tempfile.NamedTemporaryFile(suffix=".txt") as tmp:
            tmp.write(b"This is not a CSV file")
            tmp.flush()
            assert not is_valid_csv(Path(tmp.name))
    
    def test_generate_export_filename(self):
        """Test export filename generation."""
        # Test basic filename generation
        filename = generate_export_filename("analysis", "csv")
        
        # Check format
        assert filename.endswith(".csv")
        assert "analysis" in filename
        assert "_" in filename  # Should include timestamp
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Test with invalid characters
        filename = "Test: File? With* Invalid~ Characters!"
        sanitized = sanitize_filename(filename)
        
        # Check sanitization
        assert ":" not in sanitized
        assert "?" not in sanitized
        assert "*" not in sanitized
        assert "~" not in sanitized
        assert "!" not in sanitized
```

#### Config Manager Tests

```python
# tests/unit/utils/test_config_manager.py
import pytest
import json
from pathlib import Path
from src.utils.configuration import ConfigManager

class TestConfigManager:
    """Tests for the ConfigManager class."""
    
    @pytest.fixture
    def config_manager(self, temp_test_dir):
        """Create a ConfigManager instance for testing."""
        config_dir = temp_test_dir / "config"
        config_dir.mkdir(exist_ok=True)
        return ConfigManager(config_dir=config_dir)
    
    def test_init(self, config_manager):
        """Test ConfigManager initialization."""
        assert config_manager is not None
        assert hasattr(config_manager, 'config_dir')
        assert hasattr(config_manager, 'settings')
    
    def test_set_get_setting(self, config_manager):
        """Test setting and getting configuration values."""
        # Set a test setting
        config_manager.set_setting("test_key", "test_value")
        
        # Get the setting
        value = config_manager.get_setting("test_key")
        
        # Check value
        assert value == "test_value"
    
    def test_get_nonexistent_setting(self, config_manager):
        """Test getting a nonexistent setting with default value."""
        # Get a nonexistent setting with default
        value = config_manager.get_setting("nonexistent", default="default_value")
        
        # Check that default was returned
        assert value == "default_value"
    
    def test_save_load_config(self, config_manager):
        """Test saving and loading configuration."""
        # Set some test settings
        config_manager.set_setting("test_key1", "test_value1")
        config_manager.set_setting("test_key2", 123)
        
        # Save the configuration
        config_manager.save_config()
        
        # Create a new config manager to test loading
        new_config = ConfigManager(config_dir=config_manager.config_dir)
        
        # Check that settings were loaded
        assert new_config.get_setting("test_key1") == "test_value1"
        assert new_config.get_setting("test_key2") == 123
    
    def test_clear_settings(self, config_manager):
        """Test clearing settings."""
        # Set some test settings
        config_manager.set_setting("test_key", "test_value")
        
        # Clear settings
        config_manager.clear_settings()
        
        # Check that settings were cleared
        assert config_manager.get_setting("test_key", None) is None
```

## Part 2 Validation

Once you have completed the implementation of unit tests, you should validate them through the following steps:

1. **Test Coverage Validation**:
   - [ ] Run tests with coverage: `pytest --cov=src tests/unit/`
   - [ ] Verify test coverage for each component meets targets
   - [ ] Identify any significant gaps in coverage

2. **Test Quality Validation**:
   - [ ] Check that tests are properly isolated
   - [ ] Ensure tests don't have dependencies on external resources
   - [ ] Verify tests use appropriate fixtures and mocks

3. **Code Quality Validation**:
   - [ ] Run tests with code style checks: `pytest --flake8`
   - [ ] Ensure test code follows project conventions
   - [ ] Verify docstrings and comments are clear and helpful

## Feedback Request

After implementing the unit tests, please provide feedback on:

1. Do the unit tests provide adequate coverage of critical functionality?
2. Are there any edge cases or specialized scenarios that should be tested?
3. Is the balance between thoroughness and practicality appropriate?
4. Are the tests well-structured and maintainable?
5. Do the tests provide good examples of how components should be used?

Once this feedback is incorporated, we can proceed to Part 3: Integration Testing implementation. 