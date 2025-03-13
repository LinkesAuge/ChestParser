# Total Battle Analyzer Refactoring Plan: Phase 5 - Part 1
## Test Strategy and Framework Setup

This document outlines the implementation of a comprehensive test strategy and framework for the Total Battle Analyzer application. It focuses on establishing the overall testing approach, setting up the necessary infrastructure, and defining testing conventions.

## Implementation Tasks

- [ ] **Define Test Strategy**
  - [ ] Document overall testing goals and approach
  - [ ] Identify testing scope and coverage targets
  - [ ] Define risk-based testing priorities
  - [ ] Document test environment requirements

- [ ] **Set Up Testing Framework**
  - [ ] Install core testing packages using UV
  - [ ] Configure pytest and related extensions
  - [ ] Create base test directory structure
  - [ ] Set up test configuration files

- [ ] **Establish Test Data Management**
  - [ ] Create test data directory structure
  - [ ] Generate sample CSV files for testing
  - [ ] Create test fixtures and factory functions
  - [ ] Implement mock data generators

- [ ] **Define Test Categories and Organization**
  - [ ] Set up unit test organization
  - [ ] Define integration test structure
  - [ ] Plan UI test organization
  - [ ] Establish performance test organization

- [ ] **Implement Test Utilities**
  - [ ] Create helper functions for common test operations
  - [ ] Implement custom test assertions
  - [ ] Create mock factory functions
  - [ ] Develop test data validation utilities

- [ ] **Set Up Continuous Integration Testing**
  - [ ] Configure automated test execution
  - [ ] Set up test coverage reporting
  - [ ] Configure test result reporting
  - [ ] Implement pre-commit hooks for testing

## Implementation Details

### 1. Define Test Strategy

#### Testing Goals Document

Create a `TEST_STRATEGY.md` document in the `tests` directory:

```markdown
# Total Battle Analyzer Test Strategy

## Testing Goals

1. **Functional Correctness**: Ensure all application features work as specified.
2. **Data Integrity**: Verify that data processing maintains accuracy and integrity.
3. **User Experience**: Validate that the UI is responsive and intuitive.
4. **Reliability**: Ensure the application is stable and handles errors gracefully.
5. **Performance**: Verify the application performs efficiently with various data sizes.

## Testing Scope

1. **In Scope**:
   - Data loading and processing functionality
   - Analysis algorithms and calculations
   - Chart generation and visualization
   - Report creation and export
   - UI components and workflows
   - Configuration management
   - Error handling and recovery

2. **Out of Scope**:
   - Third-party library internals
   - Operating system-specific features not directly used by the application
   - Performance under extreme conditions (e.g., millions of records)

## Test Coverage Targets

- **Data Layer**: 90% code coverage
- **Service Layer**: 85% code coverage
- **UI Layer**: 75% code coverage
- **Utilities**: 90% code coverage

## Risk-Based Testing Priorities

1. **High Priority**:
   - CSV import with various encodings and formats
   - Data analysis calculations
   - Chart generation accuracy
   - Configuration saving/loading

2. **Medium Priority**:
   - UI component interactions
   - Report generation
   - Export functionality
   - Filter operations

3. **Lower Priority**:
   - UI styling and appearance
   - Non-critical error messages
   - Optional features

## Test Environment Requirements

1. **Hardware**:
   - Minimum: 4GB RAM, dual-core CPU
   - Recommended: 8GB RAM, quad-core CPU

2. **Software**:
   - Windows 10/11 (primary target)
   - Python 3.9+ environment
   - All dependencies installed via UV

3. **Test Data**:
   - Small dataset: 100-500 rows
   - Medium dataset: 1,000-5,000 rows
   - Large dataset: 10,000+ rows
   - Various encodings (UTF-8, Windows-1252, Latin-1)
   - Special character test cases (German umlauts, etc.)
```

### 2. Set Up Testing Framework

#### Install Testing Packages

Use UV to install the necessary testing packages:

```bash
# Core testing packages
uv add pytest pytest-cov pytest-mock

# UI testing
uv add pytest-qt

# Performance testing
uv add pytest-benchmark

# Property-based testing
uv add hypothesis pytest-hypothesis
```

#### Configure Pytest

Create a `pytest.ini` file in the project root:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests
    integration: Integration tests
    ui: UI tests
    performance: Performance tests
    slow: Tests that take longer to run
    dataproc: Tests related to data processing
    analysis: Tests related to data analysis
    charts: Tests related to chart generation
    reports: Tests related to report generation
    config: Tests related to configuration management
```

#### Create Test Directory Structure

Set up the test directory structure:

```bash
mkdir -p tests/unit
mkdir -p tests/unit/data
mkdir -p tests/unit/services
mkdir -p tests/unit/ui
mkdir -p tests/unit/utils

mkdir -p tests/integration
mkdir -p tests/integration/data_services
mkdir -p tests/integration/services_ui
mkdir -p tests/integration/end_to_end

mkdir -p tests/ui
mkdir -p tests/ui/screens
mkdir -p tests/ui/widgets
mkdir -p tests/ui/dialogs

mkdir -p tests/performance
mkdir -p tests/data
```

Create base `__init__.py` files in each directory to ensure proper importing:

```bash
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
touch tests/ui/__init__.py
touch tests/performance/__init__.py
```

### 3. Establish Test Data Management

#### Create Test Data Files

Generate sample CSV files with various characteristics:

```python
# tests/data/generate_test_data.py
import csv
import random
from pathlib import Path
from datetime import datetime, timedelta

def generate_small_dataset(output_path):
    """Generate a small dataset (100 rows) with basic data."""
    players = ["Player1", "Player2", "Player3", "Player4", "Player5"]
    sources = ["Guild", "Battle", "Event", "Arena", "Quest"]
    chests = ["Gold", "Silver", "Bronze", "Diamond", "Platinum"]
    
    rows = []
    for _ in range(100):
        date = (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d")
        row = {
            "DATE": date,
            "PLAYER": random.choice(players),
            "SOURCE": random.choice(sources),
            "CHEST": random.choice(chests),
            "SCORE": random.randint(100, 1000)
        }
        rows.append(row)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["DATE", "PLAYER", "SOURCE", "CHEST", "SCORE"])
        writer.writeheader()
        writer.writerows(rows)

def generate_special_chars_dataset(output_path):
    """Generate a dataset with German characters to test encoding handling."""
    players = ["Müller", "Jäger", "Schröder", "Krümelmonster", "Feldjäger"]
    sources = ["Guild", "Battle", "Event", "Arena", "Quest"]
    chests = ["Gold", "Silver", "Bronze", "Diamond", "Platinum"]
    
    rows = []
    for _ in range(100):
        date = (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d")
        row = {
            "DATE": date,
            "PLAYER": random.choice(players),
            "SOURCE": random.choice(sources),
            "CHEST": random.choice(chests),
            "SCORE": random.randint(100, 1000)
        }
        rows.append(row)
    
    # UTF-8 version
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["DATE", "PLAYER", "SOURCE", "CHEST", "SCORE"])
        writer.writeheader()
        writer.writerows(rows)
    
    # Windows-1252 version
    with open(output_path.replace('.csv', '_cp1252.csv'), 'w', newline='', encoding='cp1252') as f:
        writer = csv.DictWriter(f, fieldnames=["DATE", "PLAYER", "SOURCE", "CHEST", "SCORE"])
        writer.writeheader()
        writer.writerows(rows)

def generate_medium_dataset(output_path):
    """Generate a medium dataset (1000 rows) with more players and variation."""
    players = [f"Player{i}" for i in range(1, 21)]
    sources = ["Guild", "Battle", "Event", "Arena", "Quest", "Daily", "Weekly", "Boss", "Expedition", "Tournament"]
    chests = ["Gold", "Silver", "Bronze", "Diamond", "Platinum", "Wooden", "Iron", "Steel", "Crystal", "Legendary"]
    
    rows = []
    for _ in range(1000):
        date = (datetime.now() - timedelta(days=random.randint(0, 90))).strftime("%Y-%m-%d")
        row = {
            "DATE": date,
            "PLAYER": random.choice(players),
            "SOURCE": random.choice(sources),
            "CHEST": random.choice(chests),
            "SCORE": random.randint(100, 5000)
        }
        rows.append(row)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["DATE", "PLAYER", "SOURCE", "CHEST", "SCORE"])
        writer.writeheader()
        writer.writerows(rows)

def generate_all_test_datasets():
    """Generate all test datasets."""
    data_dir = Path(__file__).parent
    data_dir.mkdir(exist_ok=True)
    
    generate_small_dataset(data_dir / "small_dataset.csv")
    generate_special_chars_dataset(data_dir / "special_chars.csv")
    generate_medium_dataset(data_dir / "medium_dataset.csv")
    
    print(f"Test datasets generated in {data_dir}")

if __name__ == "__main__":
    generate_all_test_datasets()
```

#### Create Test Fixtures

Implement pytest fixtures for common test components:

```python
# tests/conftest.py
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil
from PySide6.QtWidgets import QApplication

# Global fixtures
@pytest.fixture(scope="session")
def app():
    """Create QApplication for the entire test session."""
    app = QApplication.instance() or QApplication([])
    yield app

@pytest.fixture
def temp_test_dir():
    """Create a temporary test directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

@pytest.fixture
def test_data_dir():
    """Fixture to get the path to the test data directory."""
    return Path(__file__).parent / "data"

@pytest.fixture
def small_csv_path(test_data_dir):
    """Fixture to get the path to the small CSV test file."""
    csv_path = test_data_dir / "small_dataset.csv"
    if not csv_path.exists():
        pytest.skip(f"Test data file not found: {csv_path}")
    return csv_path

@pytest.fixture
def medium_csv_path(test_data_dir):
    """Fixture to get the path to the medium CSV test file."""
    csv_path = test_data_dir / "medium_dataset.csv"
    if not csv_path.exists():
        pytest.skip(f"Test data file not found: {csv_path}")
    return csv_path

@pytest.fixture
def special_chars_csv_path(test_data_dir):
    """Fixture to get the path to the special characters CSV test file."""
    csv_path = test_data_dir / "special_chars.csv"
    if not csv_path.exists():
        pytest.skip(f"Test data file not found: {csv_path}")
    return csv_path

@pytest.fixture
def sample_dataframe():
    """Create a sample pandas DataFrame for testing."""
    data = {
        "DATE": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05"],
        "PLAYER": ["Player1", "Player2", "Player1", "Player3", "Player2"],
        "SOURCE": ["Guild", "Battle", "Event", "Guild", "Event"],
        "CHEST": ["Gold", "Silver", "Gold", "Bronze", "Gold"],
        "SCORE": [500, 300, 700, 200, 600]
    }
    return pd.DataFrame(data)

@pytest.fixture
def config_dir(temp_test_dir):
    """Create a temporary config directory."""
    config_dir = temp_test_dir / "config"
    config_dir.mkdir(exist_ok=True)
    return config_dir

# Import and data fixtures can be added here
```

### 4. Define Test Categories and Organization

Create base test files for each category:

```python
# tests/unit/data/test_data_processor.py
import pytest
from src.modules.dataprocessor import DataProcessor

class TestDataProcessor:
    """Unit tests for the DataProcessor class."""
    
    def test_init(self):
        """Test initialization of DataProcessor."""
        data_processor = DataProcessor()
        assert data_processor is not None
    
    def test_read_csv_with_encoding_fix(self, small_csv_path):
        """Test CSV reading with encoding fixes."""
        # Test implementation will go here
        pass
    
    def test_fix_dataframe_text(self, sample_dataframe):
        """Test text fixing in DataFrame."""
        # Test implementation will go here
        pass
    
    def test_analyze_data(self, sample_dataframe):
        """Test data analysis functionality."""
        # Test implementation will go here
        pass
```

```python
# tests/unit/services/test_analysis_service.py
import pytest
from src.services.analysis_service import AnalysisService

class TestAnalysisService:
    """Unit tests for the AnalysisService class."""
    
    def test_init(self):
        """Test initialization of AnalysisService."""
        # Test implementation will go here
        pass
    
    def test_analyze_player_data(self, sample_dataframe):
        """Test player data analysis."""
        # Test implementation will go here
        pass
    
    def test_analyze_chest_data(self, sample_dataframe):
        """Test chest data analysis."""
        # Test implementation will go here
        pass
```

```python
# tests/unit/services/test_chart_service.py
import pytest
import matplotlib.pyplot as plt
from src.visualization.charts.chart_service import ChartService

class TestChartService:
    """Unit tests for the ChartService class."""
    
    @pytest.fixture
    def chart_service(self):
        """Fixture to create a ChartService instance."""
        # Test implementation will go here
        pass
    
    def test_create_bar_chart(self, chart_service, sample_dataframe):
        """Test bar chart creation."""
        # Test implementation will go here
        plt.close('all')  # Clean up matplotlib figures
```

```python
# tests/integration/data_services/test_data_analysis_integration.py
import pytest

class TestDataAnalysisIntegration:
    """Integration tests for data processing and analysis services."""
    
    def test_load_and_analyze_workflow(self, small_csv_path):
        """Test the complete workflow from loading CSV to generating analysis."""
        # Test implementation will go here
        pass
```

```python
# tests/ui/screens/test_import_screen.py
import pytest
from PySide6.QtCore import Qt
from src.ui.screens.import_screen import ImportScreen

class TestImportScreen:
    """Tests for the ImportScreen class."""
    
    @pytest.fixture
    def import_screen(self, app):
        """Fixture to create an ImportScreen instance."""
        screen = ImportScreen()
        return screen
    
    def test_file_selection(self, import_screen, qtbot, small_csv_path):
        """Test file selection functionality."""
        # Test implementation will go here
        pass
```

### 5. Implement Test Utilities

Create helper utilities for testing:

```python
# tests/utils/test_helpers.py
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

def assert_dataframes_equal(df1, df2, check_dtype=True, check_index=True):
    """
    Custom assertion to compare two DataFrames for equality.
    
    Args:
        df1: First DataFrame
        df2: Second DataFrame
        check_dtype: Whether to check data types
        check_index: Whether to check index values
    """
    # Check shape
    assert df1.shape == df2.shape, f"DataFrame shapes differ: {df1.shape} vs {df2.shape}"
    
    # Check column names
    assert set(df1.columns) == set(df2.columns), f"Column names differ: {set(df1.columns)} vs {set(df2.columns)}"
    
    # Reorder columns to match for easier comparison
    df2 = df2[df1.columns]
    
    # Check index if required
    if check_index:
        assert df1.index.equals(df2.index), f"DataFrame indices differ"
    
    # Check data values
    for col in df1.columns:
        s1 = df1[col]
        s2 = df2[col]
        
        if pd.api.types.is_numeric_dtype(s1) and pd.api.types.is_numeric_dtype(s2):
            # For numeric data, allow small differences
            assert np.allclose(s1.fillna(0), s2.fillna(0), rtol=1e-5, atol=1e-8), f"Values in column {col} differ"
        else:
            # For non-numeric data, compare directly
            assert s1.equals(s2), f"Values in column {col} differ"
    
    # Check dtypes if required
    if check_dtype:
        for col in df1.columns:
            assert pd.api.types.is_dtype_equal(df1[col].dtype, df2[col].dtype), \
                f"Data types differ for column {col}: {df1[col].dtype} vs {df2[col].dtype}"

def create_test_csv(data, path):
    """
    Create a CSV file with the given data for testing.
    
    Args:
        data: Dictionary or DataFrame of data to write
        path: Path to write the CSV file
    
    Returns:
        Path to the created CSV file
    """
    if isinstance(data, dict):
        df = pd.DataFrame(data)
    else:
        df = data
    
    path = Path(path)
    df.to_csv(path, index=False)
    return path

def mock_matplotlib_figure():
    """
    Create a mock matplotlib figure for testing.
    
    Returns:
        A matplotlib Figure object
    """
    import matplotlib.pyplot as plt
    return plt.figure()
```

### 6. Set Up Continuous Integration Testing

Create a GitHub Actions workflow file for automated testing:

```yaml
# .github/workflows/tests.yml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install uv
        uv pip install -e .
        uv pip install pytest pytest-cov pytest-mock
    
    - name: Generate test data
      run: |
        python tests/data/generate_test_data.py
    
    - name: Run tests
      run: |
        pytest --cov=src tests/ --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v1
      with:
        file: ./coverage.xml
        fail_ci_if_error: false
```

Create a `.pre-commit-config.yaml` file for pre-commit hooks:

```yaml
# .pre-commit-config.yaml
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files

-   repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
    -   id: flake8
        additional_dependencies: [flake8-docstrings]

-   repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
    -   id: isort

-   repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
    -   id: black

-   repo: local
    hooks:
    -   id: pytest-check
        name: pytest-check
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

## Part 1 Validation

Once you have completed the implementation of the test strategy and framework setup, you should validate it through the following steps:

1. **Framework Validation**:
   - [ ] Run `pytest --collect-only` to verify test collection works
   - [ ] Ensure all test directories are correctly structured
   - [ ] Verify pytest configuration is loaded correctly

2. **Test Data Validation**:
   - [ ] Generate test data files using the data generation script
   - [ ] Verify special character handling in test data files
   - [ ] Confirm all required test fixtures can be instantiated

3. **Testing Utilities Validation**:
   - [ ] Run a sample test using the custom assertion functions
   - [ ] Verify mock object creation works as expected
   - [ ] Test the continuous integration setup locally

## Feedback Request

After implementing the test strategy and framework, please provide feedback on:

1. Is the testing approach comprehensive enough for the application's needs?
2. Are there additional test categories or tools that should be considered?
3. Is the test data generation adequate for covering different usage scenarios?
4. Does the continuous integration setup align with the project's deployment practices?
5. Are there any performance concerns with the current testing approach?

Once this feedback is incorporated, we can proceed to Part 2: Unit Testing implementation. 