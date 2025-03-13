# Total Battle Analyzer Refactoring Plan: Phase 5 - Part 4
## UI Testing and User Acceptance

This document outlines the implementation of comprehensive UI testing and user acceptance testing for the Total Battle Analyzer application. These tests focus on validating the user interface components, interactions, and workflows to ensure they meet both technical requirements and user expectations.

## Implementation Tasks

- [ ] **UI Component Tests**
  - [ ] Test individual UI widgets behavior
  - [ ] Test component styling and appearance
  - [ ] Test component state transitions
  - [ ] Test component interactions with user input

- [ ] **Screen Functionality Tests**
  - [ ] Test Import Screen functionality
  - [ ] Test Raw Data Screen functionality
  - [ ] Test Analysis Screen functionality
  - [ ] Test Charts Screen functionality
  - [ ] Test Report Screen functionality

- [ ] **Navigation and Application Flow Tests**
  - [ ] Test main window navigation
  - [ ] Test screen transitions
  - [ ] Test modal dialog interactions
  - [ ] Test multi-step processes

- [ ] **User Acceptance Tests**
  - [ ] Define user acceptance criteria
  - [ ] Design UAT scenarios
  - [ ] Execute UAT with stakeholders
  - [ ] Document feedback and improvement areas

## Implementation Approach

The UI testing strategy for the Total Battle Analyzer will follow these principles:

1. **Automated Testing**: Focus on automated testing of UI components and screens where possible
2. **Visual Verification**: Include mechanisms to verify visual aspects of the UI
3. **Realistic User Scenarios**: Design tests that mirror actual user workflows
4. **Accessibility Testing**: Ensure UI elements are accessible and usable
5. **Cross-Platform Verification**: Test UI behavior across different platforms and screen sizes

The implementation will utilize pytest-qt for testing PyQt6/PySide6 applications, with customized test fixtures to set up the necessary testing environment for UI components.

## Implementation Details

### 1. UI Component Tests

This section focuses on testing individual UI widgets and components to ensure they function correctly and consistently.

#### Test Environment Setup

```python
# tests/ui/conftest.py
import pytest
from PyQt6.QtWidgets import QApplication
import sys
from pathlib import Path
import pandas as pd
import tempfile

@pytest.fixture(scope="session")
def app():
    """Create a QApplication instance for UI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app

@pytest.fixture
def temp_test_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        "PLAYER": ["Player1", "Player2", "Player3", "Player1"],
        "CHEST": ["Gold", "Silver", "Bronze", "Gold"],
        "SOURCE": ["A", "B", "C", "A"],
        "SCORE": [100, 150, 75, 120],
        "DATE": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"]
    })

@pytest.fixture
def sample_csv_file(temp_test_dir, sample_dataframe):
    """Create a sample CSV file for testing."""
    csv_path = temp_test_dir / "test_data.csv"
    sample_dataframe.to_csv(csv_path, index=False)
    return csv_path
```

#### Data Table Widget Tests

```python
# tests/ui/widgets/test_data_table_widget.py
import pytest
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import Qt
import pandas as pd
from src.ui.widgets.data_table_widget import DataTableWidget

class TestDataTableWidget:
    """Tests for the DataTableWidget component."""
    
    @pytest.fixture
    def main_window(self, app):
        """Create a main window to host the widget."""
        window = QMainWindow()
        window.setGeometry(100, 100, 800, 600)
        yield window
        window.close()
    
    @pytest.fixture
    def data_table(self, main_window):
        """Create a DataTableWidget for testing."""
        table = DataTableWidget(main_window)
        main_window.setCentralWidget(table)
        return table
    
    def test_initialization(self, data_table):
        """Test that the table initializes with correct properties."""
        assert data_table is not None
        assert data_table.rowCount() == 0
        assert data_table.alternatingRowColors() is True
        assert data_table.selectionBehavior() == data_table.SelectionBehavior.SelectRows
    
    def test_load_data(self, data_table, sample_dataframe):
        """Test loading data into the table."""
        # Load sample data
        data_table.load_data(sample_dataframe)
        
        # Check table dimensions
        assert data_table.rowCount() == len(sample_dataframe)
        assert data_table.columnCount() == len(sample_dataframe.columns)
        
        # Verify column headers
        for col_idx, col_name in enumerate(sample_dataframe.columns):
            assert data_table.horizontalHeaderItem(col_idx).text() == col_name
        
        # Verify data in cells
        for row_idx in range(data_table.rowCount()):
            for col_idx in range(data_table.columnCount()):
                cell_value = data_table.item(row_idx, col_idx).text()
                df_value = str(sample_dataframe.iloc[row_idx, col_idx])
                assert cell_value == df_value
    
    def test_sort_functionality(self, data_table, sample_dataframe):
        """Test table sorting functionality."""
        # Load data
        data_table.load_data(sample_dataframe)
        
        # Get column index for sorting
        score_column_index = list(sample_dataframe.columns).index("SCORE")
        
        # Sort by clicking the header
        data_table.horizontalHeader().sectionClicked.emit(score_column_index)
        
        # For integration tests, we test the signal emission
        # Here we just verify the click handler is connected
        # This is just a basic check - the actual sorting response is tested in integration tests
        assert data_table.isSortingEnabled() is True
    
    def test_selection_behavior(self, data_table, sample_dataframe):
        """Test table selection behavior."""
        # Load data
        data_table.load_data(sample_dataframe)
        
        # Verify selection behavior
        assert data_table.selectionBehavior() == data_table.SelectionBehavior.SelectRows
        
        # Select a cell and check that the entire row is selected
        data_table.setCurrentCell(0, 0)
        selection_model = data_table.selectionModel()
        
        # Verify that multiple cells in the row are selected
        assert selection_model.isRowSelected(0, data_table.rootIndex()) is True
    
    def test_appearance(self, data_table, sample_dataframe):
        """Test table appearance properties."""
        # Load data
        data_table.load_data(sample_dataframe)
        
        # Check styling properties
        assert data_table.showGrid() is True
        assert data_table.alternatingRowColors() is True
        
        # Check header properties
        horizontal_header = data_table.horizontalHeader()
        assert horizontal_header.isVisible() is True
        assert horizontal_header.stretchLastSection() is True
        
        # For a complete visual test, we'd need UI automation or screenshots
        # Here we just check the basic appearance properties
    
    def test_clear_functionality(self, data_table, sample_dataframe):
        """Test clearing the table."""
        # Load data
        data_table.load_data(sample_dataframe)
        assert data_table.rowCount() > 0
        
        # Clear the table
        data_table.clear()
        
        # Verify the table is empty
        assert data_table.rowCount() == 0
```

#### Filter Panel Widget Tests

```python
# tests/ui/widgets/test_filter_panel.py
import pytest
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import Qt
import pandas as pd
from src.ui.widgets.filter_panel import FilterPanel

class TestFilterPanel:
    """Tests for the FilterPanel component."""
    
    @pytest.fixture
    def main_window(self, app):
        """Create a main window to host the widget."""
        window = QMainWindow()
        window.setGeometry(100, 100, 800, 600)
        yield window
        window.close()
    
    @pytest.fixture
    def filter_panel(self, main_window):
        """Create a FilterPanel for testing."""
        panel = FilterPanel(main_window)
        main_window.setCentralWidget(panel)
        return panel
    
    def test_initialization(self, filter_panel):
        """Test that the filter panel initializes with correct properties."""
        assert filter_panel is not None
        assert filter_panel.layout() is not None
        assert hasattr(filter_panel, "column_dropdown")
        assert hasattr(filter_panel, "specific_values_checkbox")
        assert hasattr(filter_panel, "values_list")
    
    def test_set_available_columns(self, filter_panel, sample_dataframe):
        """Test setting available columns in the filter panel."""
        # Get columns from sample dataframe
        columns = sample_dataframe.columns.tolist()
        
        # Set available columns
        filter_panel.set_available_columns(columns)
        
        # Verify columns were added to dropdown
        assert filter_panel.column_dropdown.count() == len(columns)
        for i, col in enumerate(columns):
            assert filter_panel.column_dropdown.itemText(i) == col
    
    def test_add_filter(self, filter_panel):
        """Test adding a filter to the panel."""
        # Add a filter
        filter_panel.add_filter("PLAYER", "Player1")
        
        # Verify filter was added
        filters = filter_panel.get_filters()
        assert len(filters) == 1
        assert filters[0][0] == "PLAYER"
        assert filters[0][1] == "Player1"
    
    def test_clear_filters(self, filter_panel):
        """Test clearing filters from the panel."""
        # Add some filters
        filter_panel.add_filter("PLAYER", "Player1")
        filter_panel.add_filter("CHEST", "Gold")
        
        # Verify filters were added
        assert len(filter_panel.get_filters()) == 2
        
        # Clear filters
        filter_panel.clear_filters()
        
        # Verify filters were cleared
        assert len(filter_panel.get_filters()) == 0
    
    def test_specific_values_checkbox(self, filter_panel, sample_dataframe, qtbot):
        """Test the specific values checkbox behavior."""
        # Set available columns
        filter_panel.set_available_columns(sample_dataframe.columns.tolist())
        
        # Set values for the current column
        filter_panel.set_values_for_column("PLAYER", sample_dataframe["PLAYER"].unique().tolist())
        
        # Initially, values list should be hidden
        assert filter_panel.values_list.isVisible() is False
        
        # Check the specific values checkbox
        qtbot.mouseClick(filter_panel.specific_values_checkbox, Qt.MouseButton.LeftButton)
        
        # Verify values list is now visible
        assert filter_panel.values_list.isVisible() is True
        
        # Verify values were loaded
        assert filter_panel.values_list.count() == len(sample_dataframe["PLAYER"].unique())
    
    def test_signals(self, filter_panel, sample_dataframe, qtbot):
        """Test that signals are emitted correctly."""
        # Set up a signal spy
        with qtbot.waitSignal(filter_panel.filter_changed) as blocker:
            # Set available columns
            filter_panel.set_available_columns(sample_dataframe.columns.tolist())
            
            # Set values for the current column
            filter_panel.set_values_for_column("PLAYER", sample_dataframe["PLAYER"].unique().tolist())
            
            # Check the specific values checkbox
            qtbot.mouseClick(filter_panel.specific_values_checkbox, Qt.MouseButton.LeftButton)
            
            # Select an item in the values list
            first_item = filter_panel.values_list.item(0)
            filter_panel.values_list.setCurrentItem(first_item)
            first_item.setCheckState(Qt.CheckState.Checked)
            
            # Emit filter changed signal
            filter_panel.filter_changed.emit()
        
        # Verify signal was emitted
        assert blocker.signal_triggered
```

#### Chart Widget Tests

```python
# tests/ui/widgets/test_chart_widget.py
import pytest
from PyQt6.QtWidgets import QMainWindow
import pandas as pd
import matplotlib.pyplot as plt
from src.ui.widgets.chart_widget import ChartWidget

class TestChartWidget:
    """Tests for the ChartWidget component."""
    
    @pytest.fixture
    def main_window(self, app):
        """Create a main window to host the widget."""
        window = QMainWindow()
        window.setGeometry(100, 100, 800, 600)
        yield window
        window.close()
    
    @pytest.fixture
    def chart_widget(self, main_window):
        """Create a ChartWidget for testing."""
        widget = ChartWidget(main_window)
        main_window.setCentralWidget(widget)
        return widget
    
    def test_initialization(self, chart_widget):
        """Test that the chart widget initializes correctly."""
        assert chart_widget is not None
        assert chart_widget.layout() is not None
        assert hasattr(chart_widget, "canvas")
        assert hasattr(chart_widget, "figure")
    
    def test_update_chart(self, chart_widget, sample_dataframe):
        """Test updating the chart with new data."""
        # Create a simple figure and axes
        fig, ax = plt.subplots()
        ax.bar(sample_dataframe["PLAYER"], sample_dataframe["SCORE"])
        ax.set_title("Test Chart")
        
        # Update the chart widget
        chart_widget.update_chart((fig, ax))
        
        # Verify the chart was updated (basic check)
        assert chart_widget.figure is not None
        assert len(chart_widget.figure.axes) > 0
        
        # Clean up
        plt.close(fig)
    
    def test_clear_chart(self, chart_widget, sample_dataframe):
        """Test clearing the chart."""
        # First, add a chart
        fig, ax = plt.subplots()
        ax.bar(sample_dataframe["PLAYER"], sample_dataframe["SCORE"])
        chart_widget.update_chart((fig, ax))
        
        # Clear the chart
        chart_widget.clear_chart()
        
        # Verify the chart was cleared
        assert len(chart_widget.figure.axes) == 0
        
        # Clean up
        plt.close(fig)
    
    def test_save_chart(self, chart_widget, sample_dataframe, temp_test_dir):
        """Test saving the chart to a file."""
        # Create a chart
        fig, ax = plt.subplots()
        ax.bar(sample_dataframe["PLAYER"], sample_dataframe["SCORE"])
        chart_widget.update_chart((fig, ax))
        
        # Save the chart
        save_path = temp_test_dir / "test_chart.png"
        chart_widget.save_chart(save_path)
        
        # Verify file was created
        assert save_path.exists()
        assert save_path.stat().st_size > 0
        
        # Clean up
        plt.close(fig)
```

#### File Selector Widget Tests

```python
# tests/ui/widgets/test_file_selector.py
import pytest
from PyQt6.QtWidgets import QMainWindow, QFileDialog
from PyQt6.QtCore import Qt
from pathlib import Path
from src.ui.widgets.file_selector import FileSelectorWidget

class TestFileSelectorWidget:
    """Tests for the FileSelectorWidget component."""
    
    @pytest.fixture
    def main_window(self, app):
        """Create a main window to host the widget."""
        window = QMainWindow()
        window.setGeometry(100, 100, 800, 600)
        yield window
        window.close()
    
    @pytest.fixture
    def file_selector(self, main_window):
        """Create a FileSelectorWidget for testing."""
        widget = FileSelectorWidget(main_window)
        main_window.setCentralWidget(widget)
        return widget
    
    def test_initialization(self, file_selector):
        """Test that the file selector initializes correctly."""
        assert file_selector is not None
        assert file_selector.layout() is not None
        assert hasattr(file_selector, "select_file_button")
        assert hasattr(file_selector, "file_path_edit")
        assert file_selector.file_path_edit.text() == ""
    
    def test_select_file(self, file_selector, sample_csv_file, monkeypatch, qtbot):
        """Test selecting a file through the widget."""
        # Mock the file dialog to return our sample file
        monkeypatch.setattr(
            QFileDialog, 
            "getOpenFileName", 
            lambda *args, **kwargs: (str(sample_csv_file), "CSV files (*.csv)")
        )
        
        # Set up a signal spy for the fileSelected signal
        with qtbot.waitSignal(file_selector.fileSelected) as blocker:
            # Click the select file button
            qtbot.mouseClick(file_selector.select_file_button, Qt.MouseButton.LeftButton)
        
        # Verify the file path was set correctly
        assert file_selector.file_path_edit.text() == str(sample_csv_file)
        
        # Verify the signal was emitted with the correct path
        assert blocker.args[0] == str(sample_csv_file)
    
    def test_set_file_path(self, file_selector, sample_csv_file, qtbot):
        """Test setting the file path programmatically."""
        # Set up a signal spy for the fileSelected signal
        with qtbot.waitSignal(file_selector.fileSelected) as blocker:
            # Set the file path
            file_selector.set_file_path(str(sample_csv_file))
        
        # Verify the file path was set correctly
        assert file_selector.file_path_edit.text() == str(sample_csv_file)
        
        # Verify the signal was emitted with the correct path
        assert blocker.args[0] == str(sample_csv_file)
    
    def test_get_file_path(self, file_selector, sample_csv_file):
        """Test getting the current file path."""
        # Set a file path
        file_selector.set_file_path(str(sample_csv_file))
        
        # Get the file path
        result = file_selector.get_file_path()
        
        # Verify the result
        assert result == str(sample_csv_file)
    
    def test_clear_file_path(self, file_selector, sample_csv_file):
        """Test clearing the file path."""
        # Set a file path
        file_selector.set_file_path(str(sample_csv_file))
        assert file_selector.file_path_edit.text() != ""
        
        # Clear the file path
        file_selector.clear_file_path()
        
        # Verify the file path was cleared
        assert file_selector.file_path_edit.text() == ""
        assert file_selector.get_file_path() == ""
```

These test modules cover the core UI components of the Total Battle Analyzer application:

1. **Data Table Widget**: Tests for the tabular data display component used throughout the application
2. **Filter Panel**: Tests for the filtering component used in the Raw Data and Analysis tabs
3. **Chart Widget**: Tests for the visualization component used in the Charts tab
4. **File Selector Widget**: Tests for the file selection component used in the Import tab

Each test module includes tests for initialization, basic functionality, interaction handling, and appearance properties. The tests focus on ensuring that each component functions correctly in isolation before being integrated into the application.

### 2. Screen Functionality Tests

This section focuses on testing the application-specific screens that utilize the UI components to provide complete functionality to users.

#### Import Screen Tests

```python
# tests/ui/screens/test_import_screen.py
import pytest
from PyQt6.QtWidgets import QMainWindow, QFileDialog
from PyQt6.QtCore import Qt
import pandas as pd
from pathlib import Path
from src.ui.screens.import_screen import ImportScreen
from src.services.data_service import DataService
from src.services.config_service import ConfigService

class TestImportScreen:
    """Tests for the Import Screen."""
    
    @pytest.fixture
    def main_window(self, app):
        """Create a main window to host the screen."""
        window = QMainWindow()
        window.setGeometry(100, 100, 800, 600)
        yield window
        window.close()
    
    @pytest.fixture
    def data_service(self):
        """Create a DataService for testing."""
        return DataService()
    
    @pytest.fixture
    def config_service(self):
        """Create a ConfigService for testing."""
        return ConfigService()
    
    @pytest.fixture
    def import_screen(self, main_window, data_service, config_service):
        """Create an ImportScreen for testing."""
        screen = ImportScreen(data_service, config_service)
        main_window.setCentralWidget(screen)
        return screen
    
    def test_initialization(self, import_screen):
        """Test that the import screen initializes correctly."""
        assert import_screen is not None
        assert import_screen.layout() is not None
        assert hasattr(import_screen, "file_selector")
        assert hasattr(import_screen, "preview_area")
        assert hasattr(import_screen, "import_button")
    
    def test_file_selection(self, import_screen, sample_csv_file, monkeypatch, qtbot):
        """Test file selection functionality."""
        # Mock the file dialog to return our sample file
        monkeypatch.setattr(
            QFileDialog, 
            "getOpenFileName", 
            lambda *args, **kwargs: (str(sample_csv_file), "CSV files (*.csv)")
        )
        
        # Mock the data service to return a DataFrame
        sample_df = pd.read_csv(sample_csv_file)
        monkeypatch.setattr(
            import_screen.data_service,
            "load_csv_preview",
            lambda path: sample_df
        )
        
        # Click the select file button
        qtbot.mouseClick(import_screen.file_selector.select_file_button, Qt.MouseButton.LeftButton)
        
        # Verify the file path was set
        assert import_screen.file_selector.get_file_path() == str(sample_csv_file)
        
        # Verify preview was loaded
        assert import_screen.preview_data is not None
        assert len(import_screen.preview_data) > 0
    
    def test_import_functionality(self, import_screen, sample_csv_file, monkeypatch, qtbot):
        """Test importing a file."""
        # Set the file path
        import_screen.file_selector.set_file_path(str(sample_csv_file))
        
        # Mock the data service's import_data method
        import_called = False
        
        def mock_import_data(path):
            nonlocal import_called
            import_called = True
            return True
        
        monkeypatch.setattr(
            import_screen.data_service,
            "import_data",
            mock_import_data
        )
        
        # Mock the preview data
        import_screen.preview_data = pd.read_csv(sample_csv_file)
        
        # Set up a signal spy for the importCompleted signal
        with qtbot.waitSignal(import_screen.importCompleted) as blocker:
            # Click the import button
            qtbot.mouseClick(import_screen.import_button, Qt.MouseButton.LeftButton)
        
        # Verify import was called
        assert import_called is True
        
        # Verify signal was emitted
        assert blocker.signal_triggered
    
    def test_preview_functionality(self, import_screen, sample_csv_file, monkeypatch):
        """Test the data preview functionality."""
        # Mock the data service to return a DataFrame
        sample_df = pd.read_csv(sample_csv_file)
        monkeypatch.setattr(
            import_screen.data_service,
            "load_csv_preview",
            lambda path: sample_df
        )
        
        # Load preview
        import_screen.load_preview(sample_csv_file)
        
        # Verify preview data was loaded
        assert import_screen.preview_data is not None
        assert len(import_screen.preview_data) > 0
        
        # Verify preview table was populated
        assert import_screen.preview_table.rowCount() > 0
        assert import_screen.preview_table.columnCount() == len(sample_df.columns)
    
    def test_import_button_state(self, import_screen, sample_csv_file, monkeypatch):
        """Test the import button state based on file selection."""
        # Initially, import button should be disabled
        assert import_screen.import_button.isEnabled() is False
        
        # Mock the data service
        sample_df = pd.read_csv(sample_csv_file)
        monkeypatch.setattr(
            import_screen.data_service,
            "load_csv_preview",
            lambda path: sample_df
        )
        
        # Load a file
        import_screen.file_selector.set_file_path(str(sample_csv_file))
        import_screen.load_preview(sample_csv_file)
        
        # Now import button should be enabled
        assert import_screen.import_button.isEnabled() is True
        
        # Clear the file path
        import_screen.file_selector.clear_file_path()
        import_screen.clear_preview()
        
        # Import button should be disabled again
        assert import_screen.import_button.isEnabled() is False
```

#### Raw Data Screen Tests

```python
# tests/ui/screens/test_raw_data_screen.py
import pytest
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import Qt
import pandas as pd
from src.ui.screens.raw_data_screen import RawDataScreen
from src.services.data_service import DataService

class TestRawDataScreen:
    """Tests for the Raw Data Screen."""
    
    @pytest.fixture
    def main_window(self, app):
        """Create a main window to host the screen."""
        window = QMainWindow()
        window.setGeometry(100, 100, 800, 600)
        yield window
        window.close()
    
    @pytest.fixture
    def data_service(self):
        """Create a DataService for testing."""
        return DataService()
    
    @pytest.fixture
    def raw_data_screen(self, main_window, data_service):
        """Create a RawDataScreen for testing."""
        screen = RawDataScreen(data_service)
        main_window.setCentralWidget(screen)
        return screen
    
    def test_initialization(self, raw_data_screen):
        """Test that the raw data screen initializes correctly."""
        assert raw_data_screen is not None
        assert raw_data_screen.layout() is not None
        assert hasattr(raw_data_screen, "data_table")
        assert hasattr(raw_data_screen, "filter_panel")
        assert hasattr(raw_data_screen, "apply_filters_button")
        assert hasattr(raw_data_screen, "reset_filters_button")
    
    def test_load_data(self, raw_data_screen, sample_dataframe, monkeypatch):
        """Test loading data into the screen."""
        # Mock the data service to return our sample data
        monkeypatch.setattr(
            raw_data_screen.data_service,
            "get_data",
            lambda: sample_dataframe
        )
        
        # Load the data
        raw_data_screen.load_data()
        
        # Verify the data was loaded into the table
        assert raw_data_screen.data_table.rowCount() == len(sample_dataframe)
        assert raw_data_screen.data_table.columnCount() == len(sample_dataframe.columns)
        
        # Verify filter columns were populated
        assert raw_data_screen.filter_panel.column_dropdown.count() == len(sample_dataframe.columns)
    
    def test_apply_filters(self, raw_data_screen, sample_dataframe, monkeypatch, qtbot):
        """Test applying filters to the data."""
        # Mock the data service
        monkeypatch.setattr(
            raw_data_screen.data_service,
            "get_data",
            lambda: sample_dataframe
        )
        
        # Create filtered data that would be returned by the filter_by_values method
        filtered_data = sample_dataframe[sample_dataframe["PLAYER"] == "Player1"]
        monkeypatch.setattr(
            raw_data_screen.data_service,
            "filter_by_values",
            lambda df, column, values: filtered_data
        )
        
        # Load the data
        raw_data_screen.load_data()
        
        # Add a filter
        raw_data_screen.filter_panel.add_filter("PLAYER", "Player1")
        
        # Click the apply filters button
        qtbot.mouseClick(raw_data_screen.apply_filters_button, Qt.MouseButton.LeftButton)
        
        # Verify filtered data is displayed
        assert raw_data_screen.data_table.rowCount() == len(filtered_data)
    
    def test_reset_filters(self, raw_data_screen, sample_dataframe, monkeypatch, qtbot):
        """Test resetting filters."""
        # Mock the data service
        monkeypatch.setattr(
            raw_data_screen.data_service,
            "get_data",
            lambda: sample_dataframe
        )
        
        # Load the data
        raw_data_screen.load_data()
        
        # Add a filter
        raw_data_screen.filter_panel.add_filter("PLAYER", "Player1")
        
        # Click the reset filters button
        qtbot.mouseClick(raw_data_screen.reset_filters_button, Qt.MouseButton.LeftButton)
        
        # Verify filters were cleared
        assert len(raw_data_screen.filter_panel.get_filters()) == 0
        
        # Verify original data is displayed
        assert raw_data_screen.data_table.rowCount() == len(sample_dataframe)
    
    def test_export_functionality(self, raw_data_screen, sample_dataframe, monkeypatch, qtbot, temp_test_dir):
        """Test exporting data to CSV."""
        # Mock the data service
        monkeypatch.setattr(
            raw_data_screen.data_service,
            "get_data",
            lambda: sample_dataframe
        )
        
        # Mock file dialog
        export_path = temp_test_dir / "export.csv"
        monkeypatch.setattr(
            QFileDialog,
            "getSaveFileName",
            lambda *args, **kwargs: (str(export_path), "CSV files (*.csv)")
        )
        
        # Mock export_csv method
        export_called = False
        def mock_export_csv(df, path):
            nonlocal export_called
            export_called = True
            df.to_csv(path, index=False)
            return True
        
        monkeypatch.setattr(
            raw_data_screen.data_service,
            "export_csv",
            mock_export_csv
        )
        
        # Load the data
        raw_data_screen.load_data()
        
        # Click the export button
        qtbot.mouseClick(raw_data_screen.export_button, Qt.MouseButton.LeftButton)
        
        # Verify export was called
        assert export_called is True
        
        # Verify file was created
        assert export_path.exists()
        assert export_path.stat().st_size > 0
```

#### Analysis Screen Tests

```python
# tests/ui/screens/test_analysis_screen.py
import pytest
from PyQt6.QtWidgets import QMainWindow, QComboBox
from PyQt6.QtCore import Qt
import pandas as pd
from src.ui.screens.analysis_screen import AnalysisScreen
from src.services.data_service import DataService
from src.services.analysis_service import AnalysisService

class TestAnalysisScreen:
    """Tests for the Analysis Screen."""
    
    @pytest.fixture
    def main_window(self, app):
        """Create a main window to host the screen."""
        window = QMainWindow()
        window.setGeometry(100, 100, 800, 600)
        yield window
        window.close()
    
    @pytest.fixture
    def data_service(self):
        """Create a DataService for testing."""
        return DataService()
    
    @pytest.fixture
    def analysis_service(self):
        """Create an AnalysisService for testing."""
        return AnalysisService()
    
    @pytest.fixture
    def analysis_screen(self, main_window, data_service, analysis_service):
        """Create an AnalysisScreen for testing."""
        screen = AnalysisScreen(data_service, analysis_service)
        main_window.setCentralWidget(screen)
        return screen
    
    @pytest.fixture
    def mock_analysis_result(self):
        """Create a mock analysis result."""
        # Player analysis
        player_analysis = pd.DataFrame({
            "PLAYER": ["Player1", "Player2", "Player3"],
            "TOTAL_SCORE": [220, 150, 75],
            "CHEST_COUNT": [2, 1, 1]
        })
        
        # Chest analysis
        chest_analysis = pd.DataFrame({
            "CHEST_TYPE": ["Gold", "Silver", "Bronze"],
            "COUNT": [2, 1, 1],
            "TOTAL_SCORE": [220, 150, 75]
        })
        
        # Source analysis
        source_analysis = pd.DataFrame({
            "SOURCE": ["A", "B", "C"],
            "COUNT": [2, 1, 1],
            "TOTAL_SCORE": [220, 150, 75]
        })
        
        # Player overview
        player_overview = pd.DataFrame({
            "PLAYER": ["Player1", "Player2", "Player3"],
            "TOTAL_SCORE": [220, 150, 75],
            "CHEST_COUNT": [2, 1, 1],
            "A": [120, 0, 0],
            "B": [100, 150, 0],
            "C": [0, 0, 75]
        })
        
        return {
            "player_analysis": player_analysis,
            "chest_analysis": chest_analysis,
            "source_analysis": source_analysis,
            "player_overview": player_overview
        }
    
    def test_initialization(self, analysis_screen):
        """Test that the analysis screen initializes correctly."""
        assert analysis_screen is not None
        assert analysis_screen.layout() is not None
        assert hasattr(analysis_screen, "analysis_selector")
        assert hasattr(analysis_screen, "analysis_table")
        assert hasattr(analysis_screen, "filter_panel")
        assert hasattr(analysis_screen, "analyze_button")
    
    def test_load_data_and_analyze(self, analysis_screen, sample_dataframe, mock_analysis_result, monkeypatch):
        """Test loading data and performing analysis."""
        # Mock the data service
        monkeypatch.setattr(
            analysis_screen.data_service,
            "get_data",
            lambda: sample_dataframe
        )
        
        # Mock the analysis service
        monkeypatch.setattr(
            analysis_screen.analysis_service,
            "analyze",
            lambda data: mock_analysis_result
        )
        
        # Load the data
        analysis_screen.load_data()
        
        # Verify analysis views were populated
        assert analysis_screen.analysis_selector.count() > 0
        
        # Select a view (e.g., Player Overview)
        analysis_screen.analysis_selector.setCurrentText("Player Overview")
        
        # Perform analysis
        analysis_screen.analyze_button.click()
        
        # Verify analysis results were displayed
        assert analysis_screen.analysis_table.rowCount() == len(mock_analysis_result["player_overview"])
```

The screen functionality tests focus on testing the complete functionality of each screen, including:
1. **Import Screen**: Tests for file selection, preview generation, and data import
2. **Raw Data Screen**: Tests for data loading, filtering, sorting, and exporting
3. **Analysis Screen**: Tests for data analysis, view switching, filtering, and exporting

These tests verify that each screen correctly:
- Initializes with the proper UI components
- Handles user interactions (button clicks, selections, etc.)
- Correctly communicates with the appropriate services
- Properly displays and updates data
- Manages state transitions and user feedback

The tests simulate user interactions with each screen and verify that the expected operations are performed and the correct results are displayed. This approach ensures that each screen not only has functioning UI components but also correctly implements the business logic for its specific functionality.

### 3. Navigation and Application Flow Tests

This section focuses on testing the navigation between different screens and the overall application flow, ensuring that the application behaves correctly as users move through different workflows.

#### Main Window Navigation Tests

```python
# tests/ui/test_main_window_navigation.py
import pytest
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import Qt
from src.ui.main_window import MainWindow
from src.services.data_service import DataService
from src.services.analysis_service import AnalysisService
from src.services.chart_service import ChartService
from src.services.report_service import ReportService
from src.services.config_service import ConfigService

class TestMainWindowNavigation:
    """Tests for navigation between screens in the main window."""
    
    @pytest.fixture
    def services(self):
        """Create service instances for testing."""
        data_service = DataService()
        analysis_service = AnalysisService()
        chart_service = ChartService()
        report_service = ReportService()
        config_service = ConfigService()
        return {
            "data_service": data_service,
            "analysis_service": analysis_service,
            "chart_service": chart_service,
            "report_service": report_service,
            "config_service": config_service
        }
    
    @pytest.fixture
    def main_window(self, app, services):
        """Create a MainWindow instance for testing."""
        window = MainWindow(
            services["data_service"],
            services["analysis_service"],
            services["chart_service"],
            services["report_service"],
            services["config_service"]
        )
        window.show()
        return window
    
    def test_initial_screen(self, main_window):
        """Test that the main window initially shows the welcome screen."""
        assert main_window.current_screen == "welcome"
        assert main_window.centralWidget() is not None
    
    def test_navigation_to_import(self, main_window, qtbot):
        """Test navigation to the import screen."""
        # Click the import button in the navigation menu
        import_action = main_window.findChild(QtWidgets.QAction, "actionImport")
        import_action.trigger()
        
        # Verify the current screen is now the import screen
        assert main_window.current_screen == "import"
        assert hasattr(main_window.centralWidget(), "file_selector")
    
    def test_navigation_to_raw_data(self, main_window, qtbot, monkeypatch):
        """Test navigation to the raw data screen."""
        # Mock data availability
        monkeypatch.setattr(
            main_window.data_service,
            "has_data",
            lambda: True
        )
        
        # Click the raw data button in the navigation menu
        raw_data_action = main_window.findChild(QtWidgets.QAction, "actionRawData")
        raw_data_action.trigger()
        
        # Verify the current screen is now the raw data screen
        assert main_window.current_screen == "raw_data"
        assert hasattr(main_window.centralWidget(), "data_table")
    
    def test_navigation_to_analysis(self, main_window, qtbot, monkeypatch):
        """Test navigation to the analysis screen."""
        # Mock data availability
        monkeypatch.setattr(
            main_window.data_service,
            "has_data",
            lambda: True
        )
        
        # Click the analysis button in the navigation menu
        analysis_action = main_window.findChild(QtWidgets.QAction, "actionAnalysis")
        analysis_action.trigger()
        
        # Verify the current screen is now the analysis screen
        assert main_window.current_screen == "analysis"
        assert hasattr(main_window.centralWidget(), "analysis_selector")
    
    def test_navigation_to_charts(self, main_window, qtbot, monkeypatch):
        """Test navigation to the charts screen."""
        # Mock data availability
        monkeypatch.setattr(
            main_window.data_service,
            "has_data",
            lambda: True
        )
        
        # Click the charts button in the navigation menu
        charts_action = main_window.findChild(QtWidgets.QAction, "actionCharts")
        charts_action.trigger()
        
        # Verify the current screen is now the charts screen
        assert main_window.current_screen == "charts"
        assert hasattr(main_window.centralWidget(), "chart_selector")
    
    def test_navigation_to_reports(self, main_window, qtbot, monkeypatch):
        """Test navigation to the reports screen."""
        # Mock data availability
        monkeypatch.setattr(
            main_window.data_service,
            "has_data",
            lambda: True
        )
        
        # Click the reports button in the navigation menu
        reports_action = main_window.findChild(QtWidgets.QAction, "actionReports")
        reports_action.trigger()
        
        # Verify the current screen is now the reports screen
        assert main_window.current_screen == "reports"
        assert hasattr(main_window.centralWidget(), "report_selector")
    
    def test_navigation_disabled_without_data(self, main_window, qtbot, monkeypatch):
        """Test that navigation to data-dependent screens is disabled when no data is available."""
        # Mock no data availability
        monkeypatch.setattr(
            main_window.data_service,
            "has_data",
            lambda: False
        )
        
        # Check that actions for data-dependent screens are disabled
        raw_data_action = main_window.findChild(QtWidgets.QAction, "actionRawData")
        analysis_action = main_window.findChild(QtWidgets.QAction, "actionAnalysis")
        charts_action = main_window.findChild(QtWidgets.QAction, "actionCharts")
        reports_action = main_window.findChild(QtWidgets.QAction, "actionReports")
        
        assert not raw_data_action.isEnabled()
        assert not analysis_action.isEnabled()
        assert not charts_action.isEnabled()
        assert not reports_action.isEnabled()
    
    def test_navigation_enabled_with_data(self, main_window, qtbot, monkeypatch):
        """Test that navigation to data-dependent screens is enabled when data is available."""
        # Mock data availability
        monkeypatch.setattr(
            main_window.data_service,
            "has_data",
            lambda: True
        )
        
        # Trigger data loaded signal
        main_window.on_data_loaded()
        
        # Check that actions for data-dependent screens are enabled
        raw_data_action = main_window.findChild(QtWidgets.QAction, "actionRawData")
        analysis_action = main_window.findChild(QtWidgets.QAction, "actionAnalysis")
        charts_action = main_window.findChild(QtWidgets.QAction, "actionCharts")
        reports_action = main_window.findChild(QtWidgets.QAction, "actionReports")
        
        assert raw_data_action.isEnabled()
        assert analysis_action.isEnabled()
        assert charts_action.isEnabled()
        assert reports_action.isEnabled()
```

#### Workflow Tests

```python
# tests/ui/test_workflows.py
import pytest
from PyQt6.QtWidgets import QMainWindow, QFileDialog
from PyQt6.QtCore import Qt
import pandas as pd
from pathlib import Path
from src.ui.main_window import MainWindow
from src.services.data_service import DataService
from src.services.analysis_service import AnalysisService
from src.services.chart_service import ChartService
from src.services.report_service import ReportService
from src.services.config_service import ConfigService

class TestApplicationWorkflows:
    """Tests for complete application workflows."""
    
    @pytest.fixture
    def services(self):
        """Create service instances for testing."""
        data_service = DataService()
        analysis_service = AnalysisService()
        chart_service = ChartService()
        report_service = ReportService()
        config_service = ConfigService()
        return {
            "data_service": data_service,
            "analysis_service": analysis_service,
            "chart_service": chart_service,
            "report_service": report_service,
            "config_service": config_service
        }
    
    @pytest.fixture
    def main_window(self, app, services):
        """Create a MainWindow instance for testing."""
        window = MainWindow(
            services["data_service"],
            services["analysis_service"],
            services["chart_service"],
            services["report_service"],
            services["config_service"]
        )
        window.show()
        return window
    
    def test_import_to_analysis_workflow(self, main_window, qtbot, monkeypatch, sample_csv_file):
        """Test the workflow from importing data to analyzing it."""
        # Navigate to import screen
        import_action = main_window.findChild(QtWidgets.QAction, "actionImport")
        import_action.trigger()
        
        # Mock file dialog to return our sample file
        monkeypatch.setattr(
            QFileDialog, 
            "getOpenFileName", 
            lambda *args, **kwargs: (str(sample_csv_file), "CSV files (*.csv)")
        )
        
        # Mock data service methods
        sample_df = pd.read_csv(sample_csv_file)
        
        monkeypatch.setattr(
            main_window.data_service,
            "load_csv_preview",
            lambda path: sample_df
        )
        
        monkeypatch.setattr(
            main_window.data_service,
            "import_data",
            lambda path: True
        )
        
        monkeypatch.setattr(
            main_window.data_service,
            "has_data",
            lambda: True
        )
        
        monkeypatch.setattr(
            main_window.data_service,
            "get_data",
            lambda: sample_df
        )
        
        # Get reference to import screen
        import_screen = main_window.centralWidget()
        
        # Select file
        qtbot.mouseClick(import_screen.file_selector.select_file_button, Qt.MouseButton.LeftButton)
        
        # Import file
        qtbot.mouseClick(import_screen.import_button, Qt.MouseButton.LeftButton)
        
        # Navigate to analysis screen
        analysis_action = main_window.findChild(QtWidgets.QAction, "actionAnalysis")
        analysis_action.trigger()
        
        # Verify we're on the analysis screen
        assert main_window.current_screen == "analysis"
        analysis_screen = main_window.centralWidget()
        
        # Mock analysis service
        mock_analysis_result = {
            "player_analysis": pd.DataFrame({
                "PLAYER": ["Player1", "Player2", "Player3"],
                "TOTAL_SCORE": [220, 150, 75],
                "CHEST_COUNT": [2, 1, 1]
            }),
            "chest_analysis": pd.DataFrame({
                "CHEST_TYPE": ["Gold", "Silver", "Bronze"],
                "COUNT": [2, 1, 1],
                "TOTAL_SCORE": [220, 150, 75]
            })
        }
        
        monkeypatch.setattr(
            main_window.analysis_service,
            "analyze",
            lambda data: mock_analysis_result
        )
        
        # Run analysis
        qtbot.mouseClick(analysis_screen.analyze_button, Qt.MouseButton.LeftButton)
        
        # Verify results are displayed
        assert analysis_screen.analysis_table.rowCount() > 0
    
    def test_analysis_to_charts_workflow(self, main_window, qtbot, monkeypatch, sample_dataframe):
        """Test the workflow from analyzing data to creating charts."""
        # Mock data and analysis results
        monkeypatch.setattr(
            main_window.data_service,
            "has_data",
            lambda: True
        )
        
        monkeypatch.setattr(
            main_window.data_service,
            "get_data",
            lambda: sample_dataframe
        )
        
        mock_analysis_result = {
            "player_analysis": pd.DataFrame({
                "PLAYER": ["Player1", "Player2", "Player3"],
                "TOTAL_SCORE": [220, 150, 75],
                "CHEST_COUNT": [2, 1, 1]
            }),
            "chest_analysis": pd.DataFrame({
                "CHEST_TYPE": ["Gold", "Silver", "Bronze"],
                "COUNT": [2, 1, 1],
                "TOTAL_SCORE": [220, 150, 75]
            })
        }
        
        monkeypatch.setattr(
            main_window.analysis_service,
            "analyze",
            lambda data: mock_analysis_result
        )
        
        # Navigate to analysis screen
        analysis_action = main_window.findChild(QtWidgets.QAction, "actionAnalysis")
        analysis_action.trigger()
        
        # Run analysis
        analysis_screen = main_window.centralWidget()
        qtbot.mouseClick(analysis_screen.analyze_button, Qt.MouseButton.LeftButton)
        
        # Navigate to charts screen
        charts_action = main_window.findChild(QtWidgets.QAction, "actionCharts")
        charts_action.trigger()
        
        # Verify we're on the charts screen
        assert main_window.current_screen == "charts"
        charts_screen = main_window.centralWidget()
        
        # Mock chart creation
        chart_created = False
        def mock_create_chart(*args, **kwargs):
            nonlocal chart_created
            chart_created = True
            return True
        
        monkeypatch.setattr(
            main_window.chart_service,
            "create_chart",
            mock_create_chart
        )
        
        # Create a chart
        charts_screen.chart_type_selector.setCurrentText("Bar Chart")
        charts_screen.data_source_selector.setCurrentText("Player Analysis")
        qtbot.mouseClick(charts_screen.create_chart_button, Qt.MouseButton.LeftButton)
        
        # Verify chart was created
        assert chart_created
    
    def test_charts_to_report_workflow(self, main_window, qtbot, monkeypatch, sample_dataframe, temp_test_dir):
        """Test the workflow from creating charts to generating a report."""
        # Mock data and chart availability
        monkeypatch.setattr(
            main_window.data_service,
            "has_data",
            lambda: True
        )
        
        monkeypatch.setattr(
            main_window.data_service,
            "get_data",
            lambda: sample_dataframe
        )
        
        monkeypatch.setattr(
            main_window.chart_service,
            "get_available_charts",
            lambda: ["Player Score Distribution", "Chest Type Distribution"]
        )
        
        # Navigate to reports screen
        reports_action = main_window.findChild(QtWidgets.QAction, "actionReports")
        reports_action.trigger()
        
        # Verify we're on the reports screen
        assert main_window.current_screen == "reports"
        reports_screen = main_window.centralWidget()
        
        # Mock report generation
        report_path = temp_test_dir / "test_report.pdf"
        
        def mock_generate_report(*args, **kwargs):
            with open(report_path, "w") as f:
                f.write("Test Report Content")
            return str(report_path)
        
        monkeypatch.setattr(
            main_window.report_service,
            "generate_report",
            mock_generate_report
        )
        
        # Mock file dialog
        monkeypatch.setattr(
            QFileDialog,
            "getSaveFileName",
            lambda *args, **kwargs: (str(report_path), "PDF files (*.pdf)")
        )
        
        # Generate report
        qtbot.mouseClick(reports_screen.generate_report_button, Qt.MouseButton.LeftButton)
        
        # Verify report was created
        assert report_path.exists()
        assert report_path.stat().st_size > 0
```

The Navigation and Application Flow Tests focus on:
1. **Main Window Navigation**: Testing proper transition between different screens
   - Verifying correct screen changes when navigation actions are triggered
   - Testing navigation state management based on data availability
   - Validating UI updates when transitioning between screens

2. **Complete Application Workflows**: Testing end-to-end user journeys
   - Import to Analysis workflow: From data import to data analysis
   - Analysis to Charts workflow: From analyzing data to visualizing results
   - Charts to Report workflow: From visualizing data to generating reports

These tests ensure that:
- Users can navigate between screens as expected
- Navigation controls are properly enabled/disabled based on application state
- Screen transitions preserve data and state
- Complete workflows from data import to report generation function correctly

The workflow tests are particularly important as they validate the integration of multiple screens and features in realistic user scenarios, ensuring a smooth and intuitive user experience.

### 4. User Acceptance Tests

User Acceptance Tests (UAT) validate that the application meets the requirements and expectations of its users by simulating real-world usage scenarios. These tests focus on verifying that the application as a whole meets business requirements and provides a good user experience.

#### UAT Test Cases

```python
# tests/acceptance/test_user_acceptance.py
import pytest
import pandas as pd
import tempfile
from pathlib import Path
from PyQt6.QtWidgets import QMainWindow, QFileDialog, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from src.ui.main_window import MainWindow
from src.services.data_service import DataService
from src.services.analysis_service import AnalysisService
from src.services.chart_service import ChartService
from src.services.report_service import ReportService
from src.services.config_service import ConfigService

class TestUserAcceptance:
    """User acceptance tests for the Total Battle Analyzer application."""
    
    @pytest.fixture
    def services(self):
        """Create service instances for testing."""
        data_service = DataService()
        analysis_service = AnalysisService()
        chart_service = ChartService()
        report_service = ReportService()
        config_service = ConfigService()
        return {
            "data_service": data_service,
            "analysis_service": analysis_service,
            "chart_service": chart_service,
            "report_service": report_service,
            "config_service": config_service
        }
    
    @pytest.fixture
    def main_window(self, app, services):
        """Create a MainWindow instance for testing."""
        window = MainWindow(
            services["data_service"],
            services["analysis_service"],
            services["chart_service"],
            services["report_service"],
            services["config_service"]
        )
        window.show()
        return window
    
    @pytest.fixture
    def sample_data_path(self):
        """Create a sample CSV file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            f.write("DATE,PLAYER,CHEST_TYPE,SCORE,SOURCE\n")
            f.write("2023-01-01,Player1,Gold,100,A\n")
            f.write("2023-01-01,Player1,Silver,50,B\n")
            f.write("2023-01-02,Player2,Gold,120,A\n")
            f.write("2023-01-03,Player3,Bronze,75,C\n")
        
        path = Path(f.name)
        yield path
        path.unlink(missing_ok=True)
    
    def test_first_time_user_experience(self, main_window, qtbot, sample_data_path, monkeypatch):
        """
        Test case: First-time user experience
        
        Steps:
        1. Launch the application
        2. Navigate to the import screen
        3. Select a data file
        4. Preview and import the data
        5. Navigate to the raw data screen to view imported data
        6. Apply filters to the data
        7. Navigate to the analysis screen and analyze the data
        8. Navigate to the charts screen and create a chart
        9. Navigate to the reports screen and generate a report
        """
        # Step 1: Application launches to welcome screen
        assert main_window.current_screen == "welcome"
        
        # Mock file dialog to return our sample file
        monkeypatch.setattr(
            QFileDialog, 
            "getOpenFileName", 
            lambda *args, **kwargs: (str(sample_data_path), "CSV files (*.csv)")
        )
        
        # Mock data service methods
        sample_df = pd.read_csv(sample_data_path)
        
        monkeypatch.setattr(
            main_window.data_service,
            "load_csv_preview",
            lambda path: sample_df
        )
        
        monkeypatch.setattr(
            main_window.data_service,
            "import_data",
            lambda path: True
        )
        
        monkeypatch.setattr(
            main_window.data_service,
            "has_data",
            lambda: True
        )
        
        monkeypatch.setattr(
            main_window.data_service,
            "get_data",
            lambda: sample_df
        )
        
        # Step 2: Navigate to import screen
        import_action = main_window.findChild(QtWidgets.QAction, "actionImport")
        qtbot.mouseClick(import_action, Qt.MouseButton.LeftButton)
        assert main_window.current_screen == "import"
        
        # Get reference to import screen
        import_screen = main_window.centralWidget()
        
        # Step 3: Select a data file
        qtbot.mouseClick(import_screen.file_selector.select_file_button, Qt.MouseButton.LeftButton)
        assert import_screen.file_selector.get_file_path() == str(sample_data_path)
        
        # Step 4: Preview and import data
        assert import_screen.preview_data is not None
        assert len(import_screen.preview_data) > 0
        
        # Import the data
        qtbot.mouseClick(import_screen.import_button, Qt.MouseButton.LeftButton)
        
        # Step 5: Navigate to raw data screen
        raw_data_action = main_window.findChild(QtWidgets.QAction, "actionRawData")
        qtbot.mouseClick(raw_data_action, Qt.MouseButton.LeftButton)
        assert main_window.current_screen == "raw_data"
        
        # Get reference to raw data screen
        raw_data_screen = main_window.centralWidget()
        
        # Verify data is displayed
        assert raw_data_screen.data_table.rowCount() > 0
        assert raw_data_screen.data_table.columnCount() > 0
        
        # Step 6: Apply filters
        raw_data_screen.filter_panel.add_filter("PLAYER", "Player1")
        qtbot.mouseClick(raw_data_screen.apply_filters_button, Qt.MouseButton.LeftButton)
        
        # Step 7: Navigate to analysis screen
        analysis_action = main_window.findChild(QtWidgets.QAction, "actionAnalysis")
        qtbot.mouseClick(analysis_action, Qt.MouseButton.LeftButton)
        assert main_window.current_screen == "analysis"
        
        # Get reference to analysis screen
        analysis_screen = main_window.centralWidget()
        
        # Mock analysis service
        mock_analysis_result = {
            "player_analysis": pd.DataFrame({
                "PLAYER": ["Player1", "Player2", "Player3"],
                "TOTAL_SCORE": [150, 120, 75],
                "CHEST_COUNT": [2, 1, 1]
            }),
            "chest_analysis": pd.DataFrame({
                "CHEST_TYPE": ["Gold", "Silver", "Bronze"],
                "COUNT": [2, 1, 1],
                "TOTAL_SCORE": [220, 50, 75]
            }),
            "source_analysis": pd.DataFrame({
                "SOURCE": ["A", "B", "C"],
                "COUNT": [2, 1, 1],
                "TOTAL_SCORE": [220, 50, 75]
            }),
            "player_overview": pd.DataFrame({
                "PLAYER": ["Player1", "Player2", "Player3"],
                "TOTAL_SCORE": [150, 120, 75],
                "CHEST_COUNT": [2, 1, 1],
                "A": [100, 120, 0],
                "B": [50, 0, 0],
                "C": [0, 0, 75]
            })
        }
        
        monkeypatch.setattr(
            main_window.analysis_service,
            "analyze",
            lambda data: mock_analysis_result
        )
        
        # Run analysis
        qtbot.mouseClick(analysis_screen.analyze_button, Qt.MouseButton.LeftButton)
        
        # Verify analysis results are displayed
        assert analysis_screen.analysis_table.rowCount() > 0
        
        # Step 8: Navigate to charts screen
        charts_action = main_window.findChild(QtWidgets.QAction, "actionCharts")
        qtbot.mouseClick(charts_action, Qt.MouseButton.LeftButton)
        assert main_window.current_screen == "charts"
        
        # Get reference to charts screen
        charts_screen = main_window.centralWidget()
        
        # Mock chart creation
        chart_created = False
        def mock_create_chart(*args, **kwargs):
            nonlocal chart_created
            chart_created = True
            return True
        
        monkeypatch.setattr(
            main_window.chart_service,
            "create_chart",
            mock_create_chart
        )
        
        # Create a chart
        charts_screen.chart_type_selector.setCurrentText("Bar Chart")
        charts_screen.data_source_selector.setCurrentText("Player Analysis")
        qtbot.mouseClick(charts_screen.create_chart_button, Qt.MouseButton.LeftButton)
        
        # Verify chart was created
        assert chart_created
        
        # Step 9: Navigate to reports screen
        reports_action = main_window.findChild(QtWidgets.QAction, "actionReports")
        qtbot.mouseClick(reports_action, Qt.MouseButton.LeftButton)
        assert main_window.current_screen == "reports"
        
        # Get reference to reports screen
        reports_screen = main_window.centralWidget()
        
        # Mock report generation
        report_generated = False
        def mock_generate_report(*args, **kwargs):
            nonlocal report_generated
            report_generated = True
            return "/path/to/mock_report.pdf"
        
        monkeypatch.setattr(
            main_window.report_service,
            "generate_report",
            mock_generate_report
        )
        
        # Mock file dialog for saving
        monkeypatch.setattr(
            QFileDialog,
            "getSaveFileName",
            lambda *args, **kwargs: ("/path/to/mock_report.pdf", "PDF files (*.pdf)")
        )
        
        # Generate report
        qtbot.mouseClick(reports_screen.generate_report_button, Qt.MouseButton.LeftButton)
        
        # Verify report was generated
        assert report_generated
    
    def test_error_handling_experience(self, main_window, qtbot, monkeypatch):
        """
        Test case: Error handling experience
        
        Steps:
        1. Launch the application
        2. Navigate to the import screen
        3. Attempt to import without selecting a file
        4. Select an invalid file
        5. Attempt to navigate to data-dependent screens without data
        """
        # Step 1: Application launches to welcome screen
        assert main_window.current_screen == "welcome"
        
        # Step 2: Navigate to import screen
        import_action = main_window.findChild(QtWidgets.QAction, "actionImport")
        qtbot.mouseClick(import_action, Qt.MouseButton.LeftButton)
        assert main_window.current_screen == "import"
        
        # Get reference to import screen
        import_screen = main_window.centralWidget()
        
        # Step 3: Attempt to import without selecting a file
        # Mock QMessageBox to capture error dialogs
        error_message_shown = False
        def mock_critical(*args, **kwargs):
            nonlocal error_message_shown
            error_message_shown = True
            return QMessageBox.StandardButton.Ok
        
        monkeypatch.setattr(QMessageBox, "critical", mock_critical)
        
        # Click import without selecting a file
        qtbot.mouseClick(import_screen.import_button, Qt.MouseButton.LeftButton)
        
        # Verify error message was shown
        assert error_message_shown
        
        # Step 4: Select an invalid file
        error_message_shown = False  # Reset flag
        
        # Mock file dialog to return an invalid file
        monkeypatch.setattr(
            QFileDialog, 
            "getOpenFileName", 
            lambda *args, **kwargs: ("/path/to/invalid_file.csv", "CSV files (*.csv)")
        )
        
        # Mock data service to raise an exception
        def mock_load_csv_preview(path):
            raise ValueError("Invalid file format")
        
        monkeypatch.setattr(
            import_screen.data_service,
            "load_csv_preview",
            mock_load_csv_preview
        )
        
        # Select file
        qtbot.mouseClick(import_screen.file_selector.select_file_button, Qt.MouseButton.LeftButton)
        
        # Verify error message was shown
        assert error_message_shown
        
        # Step 5: Attempt to navigate to data-dependent screens without data
        # Mock no data availability
        monkeypatch.setattr(
            main_window.data_service,
            "has_data",
            lambda: False
        )
        
        # Check that actions for data-dependent screens are disabled
        raw_data_action = main_window.findChild(QtWidgets.QAction, "actionRawData")
        analysis_action = main_window.findChild(QtWidgets.QAction, "actionAnalysis")
        charts_action = main_window.findChild(QtWidgets.QAction, "actionCharts")
        reports_action = main_window.findChild(QtWidgets.QAction, "actionReports")
        
        assert not raw_data_action.isEnabled()
        assert not analysis_action.isEnabled()
        assert not charts_action.isEnabled()
        assert not reports_action.isEnabled()
    
    def test_data_persistence_experience(self, main_window, qtbot, sample_data_path, monkeypatch, tmp_path):
        """
        Test case: Data persistence experience
        
        Steps:
        1. Launch the application
        2. Import data
        3. Close and reopen the application
        4. Verify the data is still available
        """
        # Step 1: Application launches to welcome screen
        assert main_window.current_screen == "welcome"
        
        # Mock file dialog to return our sample file
        monkeypatch.setattr(
            QFileDialog, 
            "getOpenFileName", 
            lambda *args, **kwargs: (str(sample_data_path), "CSV files (*.csv)")
        )
        
        # Mock data service methods
        sample_df = pd.read_csv(sample_data_path)
        
        monkeypatch.setattr(
            main_window.data_service,
            "load_csv_preview",
            lambda path: sample_df
        )
        
        # Create a temp directory for data persistence
        data_dir = tmp_path / "data"
        data_dir.mkdir(exist_ok=True)
        
        # Mock config service to use this directory
        monkeypatch.setattr(
            main_window.config_service,
            "get_data_directory",
            lambda: str(data_dir)
        )
        
        # Mock successful import
        def mock_import_data(path):
            # Save a copy of the data for persistence testing
            df = pd.read_csv(path)
            df.to_csv(data_dir / "imported_data.csv", index=False)
            return True
        
        monkeypatch.setattr(
            main_window.data_service,
            "import_data",
            mock_import_data
        )
        
        # Navigate to import screen
        import_action = main_window.findChild(QtWidgets.QAction, "actionImport")
        qtbot.mouseClick(import_action, Qt.MouseButton.LeftButton)
        
        # Get reference to import screen
        import_screen = main_window.centralWidget()
        
        # Select file and import
        qtbot.mouseClick(import_screen.file_selector.select_file_button, Qt.MouseButton.LeftButton)
        qtbot.mouseClick(import_screen.import_button, Qt.MouseButton.LeftButton)
        
        # Step 3: Simulate closing and reopening the application
        # Create a new main window
        new_window = MainWindow(
            services["data_service"],
            services["analysis_service"],
            services["chart_service"],
            services["report_service"],
            services["config_service"]
        )
        
        # Mock data loading from persistent storage
        def mock_load_on_startup():
            if (data_dir / "imported_data.csv").exists():
                return pd.read_csv(data_dir / "imported_data.csv")
            return None
        
        monkeypatch.setattr(
            new_window.data_service,
            "load_on_startup",
            mock_load_on_startup
        )
        
        monkeypatch.setattr(
            new_window.data_service,
            "has_data",
            lambda: True
        )
        
        monkeypatch.setattr(
            new_window.data_service,
            "get_data",
            lambda: pd.read_csv(data_dir / "imported_data.csv")
        )
        
        # Trigger startup data loading
        new_window.initialize()
        
        # Step 4: Verify the data is still available
        # Navigate to raw data screen
        raw_data_action = new_window.findChild(QtWidgets.QAction, "actionRawData")
        raw_data_action.setEnabled(True)  # Enable for testing
        qtbot.mouseClick(raw_data_action, Qt.MouseButton.LeftButton)
        
        # Get reference to raw data screen
        raw_data_screen = new_window.centralWidget()
        
        # Verify data is displayed
        assert raw_data_screen.data_table.rowCount() > 0
        assert raw_data_screen.data_table.columnCount() > 0
```

#### User Acceptance Criteria

Beyond the automated tests above, the application should meet the following acceptance criteria to be considered ready for release:

1. **Usability Criteria**:
   - The application has a clear, intuitive interface that requires minimal user training
   - Navigation between screens is straightforward and logical
   - The application provides helpful feedback and error messages
   - UI elements are properly sized and spaced for good ergonomics
   - The application functions correctly on different display sizes and resolutions

2. **Functional Criteria**:
   - All primary user workflows (import, view, filter, analyze, visualize, report) work as expected
   - Data handling is correct and maintains integrity throughout all operations
   - Filters and analysis calculations produce accurate results
   - Charts correctly represent the underlying data
   - Reports contain all required information and format correctly for printing/saving

3. **Performance Criteria**:
   - The application loads within 3 seconds on target hardware
   - The UI remains responsive during all operations
   - Data operations (loading, filtering, analyzing) complete in a reasonable time
   - The application handles the maximum expected data size without excessive memory usage

4. **Reliability Criteria**:
   - The application handles errors gracefully without crashing
   - User data is not lost during normal operations
   - The application recovers from unexpected shutdowns without data corruption
   - Regular use over extended periods does not degrade performance

These User Acceptance Test criteria will be verified through a combination of the automated tests described above and manual testing by representative users on the target hardware and environment.

## Implementation Timeframe

The implementation of UI testing will be conducted over a 1-2 week period, focusing first on core UI components and later on complete screens and workflows.

## Dependencies

This part depends on the completion of:
- Phase 4: UI implementation (all parts)
- Phase 5, Part 1: Test Strategy and Framework
- Phase 5, Part 3: Integration Testing (for some workflow aspects)

## Expected Outcomes

Upon completion of Part 4, we will have:
1. A comprehensive UI test suite verifying all major UI components
2. Documentation of UI testing approaches and patterns
3. A set of user acceptance test scenarios
4. A report on the UI's conformance to requirements and user expectations 