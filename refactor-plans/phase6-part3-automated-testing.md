# Phase 6 Part 3: Automated Testing Pipeline

## Overview

This document outlines the third part of Phase 6, which focuses on implementing a comprehensive automated testing pipeline for the Total Battle Analyzer application. Building upon the CI/CD strategy established in Part 1 and the continuous integration implementation in Part 2, this part will create a robust, automated testing infrastructure that ensures the application's quality and reliability throughout the development lifecycle.

## Implementation Tasks

### 1. Testing Pipeline Architecture

- [ ] Design testing pipeline workflow
- [ ] Define testing stages and dependencies
- [ ] Create testing environments configuration
- [ ] Implement test data management
- [ ] Set up test reporting infrastructure

### 2. Unit Testing Automation

- [ ] Configure automated unit test execution
- [ ] Implement test parameterization for edge cases
- [ ] Set up mocking and stubbing for external dependencies
- [ ] Configure code coverage reporting and enforcement
- [ ] Implement unit test performance optimization

### 3. Integration Testing Automation

- [ ] Configure automated integration test execution
- [ ] Set up database fixtures and test data
- [ ] Implement API testing automation
- [ ] Configure integration test environment management
- [ ] Set up integration test reporting

### 4. UI and Acceptance Testing Automation

- [ ] Set up automated UI test execution
- [ ] Implement visual regression testing
- [ ] Configure browser/system testing environments
- [ ] Set up user acceptance test automation
- [ ] Implement performance and load testing automation

## Detailed Implementation

### 1. Testing Pipeline Architecture

#### 1.1 Testing Pipeline Workflow

The automated testing pipeline will follow a sequential workflow with specific stages and quality gates:

```mermaid
graph TD
    A[Code Changes] --> B[Unit Tests]
    B --> C{Pass?}
    C -->|Yes| D[Integration Tests]
    C -->|No| Z[Fail Build]
    D --> E{Pass?}
    E -->|Yes| F[UI Tests]
    E -->|No| Z
    F --> G{Pass?}
    G -->|Yes| H[Acceptance Tests]
    G -->|No| Z
    H --> I{Pass?}
    I -->|Yes| J[Performance Tests]
    I -->|No| Z
    J --> K{Pass?}
    K -->|Yes| L[Security Tests]
    K -->|No| Z
    L --> M{Pass?}
    M -->|Yes| N[Deployment Ready]
    M -->|No| Z
```

This workflow will be implemented as a GitHub Actions workflow with job dependencies:

```yaml
# .github/workflows/testing-pipeline.yml
name: Testing Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      # Unit test steps here
    
  integration-tests:
    needs: unit-tests
    runs-on: ubuntu-latest
    steps:
      # Integration test steps here
    
  ui-tests:
    needs: integration-tests
    runs-on: ubuntu-latest
    steps:
      # UI test steps here
    
  acceptance-tests:
    needs: ui-tests
    runs-on: ubuntu-latest
    steps:
      # Acceptance test steps here
    
  performance-tests:
    needs: acceptance-tests
    runs-on: ubuntu-latest
    steps:
      # Performance test steps here
    
  security-tests:
    needs: performance-tests
    runs-on: ubuntu-latest
    steps:
      # Security test steps here
```

#### 1.2 Testing Environments Configuration

We'll define specific environments for different testing stages:

1. **Unit Testing Environment**
   - Minimal environment with mocks for external dependencies
   - In-memory database for data-related tests
   - Configurable via environment variables

2. **Integration Testing Environment**
   - Containerized environment with actual dependencies
   - Test database with predefined schemas and data
   - Network isolation for controlled testing

3. **UI Testing Environment**
   - Headless browser environment (using Xvfb for Linux)
   - Virtual display configuration
   - Screenshot capture capability

4. **Performance Testing Environment**
   - Isolated environment with controlled resources
   - Load generation tools
   - Metrics collection infrastructure

The environment configurations will be stored in the repository:

```yaml
# config/test-environments/unit.yml
database:
  type: in-memory
  init_script: tests/fixtures/init_db.sql

dependencies:
  external_apis: mock
  file_system: virtual

# config/test-environments/integration.yml
database:
  type: postgres
  host: localhost
  port: 5432
  name: test_db
  init_script: tests/fixtures/init_db.sql

dependencies:
  external_apis: containerized
  file_system: isolated

# Similar configurations for UI and performance environments
```

#### 1.3 Test Data Management

For consistent and reliable testing, we'll implement a comprehensive test data management system:

1. **Test Data Generation**
   - Python factory library (factory_boy) for generating test objects
   - Configurable data generation parameters
   - Support for edge cases and boundary values

2. **Test Fixtures Management**
   - Pytest fixtures for commonly used test data
   - Database fixtures for integration tests
   - File fixtures for file processing tests

3. **Test Data Reset**
   - Automatic cleanup after tests
   - Database transaction rollback
   - File system cleanup

```python
# tests/conftest.py
import pytest
import factory
from pathlib import Path
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Battle, Player, Alliance

class PlayerFactory(factory.Factory):
    class Meta:
        model = Player
    
    id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: f"Player{n}")
    power = factory.Faker('random_int', min=1000, max=100000)
    alliance_id = None

class BattleFactory(factory.Factory):
    class Meta:
        model = Battle
    
    id = factory.Sequence(lambda n: n)
    date = factory.Faker('date_time_this_year')
    attacker = factory.SubFactory(PlayerFactory)
    defender = factory.SubFactory(PlayerFactory)
    result = factory.Iterator(['win', 'loss', 'draw'])

@pytest.fixture
def sample_battles():
    """Generate a list of sample battles for testing."""
    return [BattleFactory() for _ in range(20)]

@pytest.fixture
def db_session():
    """Create a new database session for a test."""
    engine = create_engine('sqlite:///:memory:')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create tables
    Base.metadata.create_all(engine)
    
    yield session
    
    # Cleanup after test
    session.close()
    Base.metadata.drop_all(engine)

@pytest.fixture
def test_files_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        # Create test files in the directory
        (temp_path / "test_battle.csv").write_text("date,attacker,defender,result\n2023-01-01,Player1,Player2,win")
        yield temp_path
```

#### 1.4 Test Reporting Infrastructure

We'll implement a comprehensive test reporting infrastructure:

1. **JUnit XML Reports**
   - Standard format for CI/CD integration
   - Detailed test results and failure information
   - Historical tracking of test runs

2. **HTML Reports**
   - Visual representation of test results
   - Test execution trends and statistics
   - Detailed failure analysis

3. **Test Dashboard**
   - Aggregated view of all test results
   - Test coverage metrics
   - Performance trends

```yaml
# Test reporting workflow step
- name: Generate Test Reports
  run: |
    pytest tests/ --junitxml=junit-results.xml --html=report.html
    
- name: Upload Test Results
  uses: actions/upload-artifact@v3
  with:
    name: test-results
    path: |
      junit-results.xml
      report.html
    
- name: Publish Test Report
  uses: mikepenz/action-junit-report@v3
  if: always()  # Always run even if the previous step fails
  with:
    report_paths: 'junit-results.xml'
    check_name: 'Test Results'
    fail_on_failure: true
```

### 2. Unit Testing Automation

#### 2.1 Automated Unit Test Execution

Unit tests will be automatically executed on every code change:

```yaml
# Unit testing job in the testing pipeline
unit-tests:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        python -m pip install uv
        uv pip install -e .[dev,test]
        
    - name: Run unit tests
      run: |
        pytest tests/unit/ --junitxml=unit-results.xml --cov=src --cov-report=xml
        
    - name: Upload unit test results
      uses: actions/upload-artifact@v3
      with:
        name: unit-test-results
        path: unit-results.xml
        
    - name: Upload coverage report
      uses: actions/upload-artifact@v3
      with:
        name: coverage-report
        path: coverage.xml
```

#### 2.2 Test Parameterization for Edge Cases

We'll use pytest's parameterization to test edge cases systematically:

```python
# tests/unit/test_parser.py
import pytest
from app.parsers import CSVBattleParser

@pytest.mark.parametrize("input_data,expected_result", [
    # Normal case
    ("date,attacker,defender,result\n2023-01-01,Player1,Player2,win", 
     [{"date": "2023-01-01", "attacker": "Player1", "defender": "Player2", "result": "win"}]),
    
    # Empty file
    ("date,attacker,defender,result", []),
    
    # Missing fields
    ("date,attacker,defender\n2023-01-01,Player1,Player2", 
     ValueError),
    
    # Extra fields
    ("date,attacker,defender,result,extra\n2023-01-01,Player1,Player2,win,data", 
     [{"date": "2023-01-01", "attacker": "Player1", "defender": "Player2", "result": "win"}]),
    
    # Unicode characters (German umlauts)
    ("date,attacker,defender,result\n2023-01-01,Spieler_Ä,Spieler_Ü,win", 
     [{"date": "2023-01-01", "attacker": "Spieler_Ä", "defender": "Spieler_Ü", "result": "win"}]),
])
def test_csv_parser_edge_cases(input_data, expected_result):
    parser = CSVBattleParser()
    
    if expected_result is ValueError:
        with pytest.raises(ValueError):
            parser.parse(input_data)
    else:
        result = parser.parse(input_data)
        assert result == expected_result
```

#### 2.3 Mocking and Stubbing

We'll use unittest.mock and pytest-mock for mocking external dependencies:

```python
# tests/unit/test_data_service.py
import pytest
from unittest.mock import Mock, patch
from app.services import DataService
from app.models import Battle

def test_data_service_fetch_battles(mocker):
    # Mock the database session
    mock_session = Mock()
    mock_battle = Mock(spec=Battle)
    mock_session.query.return_value.filter.return_value.all.return_value = [mock_battle]
    
    # Mock the session factory
    mocker.patch('app.services.data_service.get_session', return_value=mock_session)
    
    # Create the service and test
    service = DataService()
    battles = service.fetch_battles(player_name="Player1")
    
    # Assertions
    assert len(battles) == 1
    assert battles[0] == mock_battle
    # Verify correct query was made
    mock_session.query.assert_called_once_with(Battle)
    mock_session.query.return_value.filter.assert_called_once()
```

#### 2.4 Code Coverage Reporting and Enforcement

We'll configure code coverage reporting and enforcements:

```yaml
# Code coverage step in unit tests job
- name: Check code coverage
  run: |
    python -m coverage report --fail-under=80
    python -m coverage xml
    python -m coverage html

# pyproject.toml configuration
[tool.coverage.run]
source = ["src"]
omit = ["*/__init__.py", "*/tests/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "pass",
    "raise ImportError",
]
```

#### 2.5 Unit Test Performance Optimization

To keep the test suite fast and efficient:

```python
# tests/conftest.py
import pytest

def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true", default=False, help="run slow tests")

def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")

def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
```

```yaml
# Performance optimized test runs
- name: Run fast unit tests (CI)
  run: |
    pytest tests/unit/ -v

- name: Run all unit tests (nightly)
  if: github.event_name == 'schedule'
  run: |
    pytest tests/unit/ --runslow -v
```

### 3. Integration Testing Automation

#### 3.1 Automated Integration Test Execution

Integration tests will verify interactions between components:

```yaml
# Integration testing job
integration-tests:
  needs: unit-tests
  runs-on: ubuntu-latest
  services:
    postgres:
      image: postgres:latest
      env:
        POSTGRES_USER: postgres
        POSTGRES_PASSWORD: postgres
        POSTGRES_DB: test_db
      ports:
        - 5432:5432
      options: >-
        --health-cmd pg_isready
        --health-interval 10s
        --health-timeout 5s
        --health-retries 5
  
  steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        python -m pip install uv
        uv pip install -e .[dev,test]
    
    - name: Initialize test database
      run: |
        python -m scripts.init_test_db
    
    - name: Run integration tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
      run: |
        pytest tests/integration/ --junitxml=integration-results.xml
    
    - name: Upload integration test results
      uses: actions/upload-artifact@v3
      with:
        name: integration-test-results
        path: integration-results.xml
```

#### 3.2 Database Fixtures and Test Data

We'll create reusable database fixtures for integration tests:

```python
# tests/integration/conftest.py
import pytest
import csv
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Battle, Player, Alliance

@pytest.fixture(scope="session")
def db_engine():
    # Get database URL from environment or use default
    db_url = os.environ.get("DATABASE_URL", "sqlite:///:memory:")
    engine = create_engine(db_url)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Drop all tables after tests
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(db_engine):
    """Create a new database session for tests."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    
    yield session
    
    # Rollback any changes
    session.rollback()
    session.close()

@pytest.fixture
def populated_db(db_session):
    """Populate the database with test data."""
    # Create test alliances
    alliances = [
        Alliance(id=1, name="TestAlliance1"),
        Alliance(id=2, name="TestAlliance2")
    ]
    db_session.add_all(alliances)
    
    # Create test players
    players = [
        Player(id=1, name="Player1", power=10000, alliance_id=1),
        Player(id=2, name="Player2", power=20000, alliance_id=1),
        Player(id=3, name="Player3", power=15000, alliance_id=2),
        Player(id=4, name="Player4", power=25000, alliance_id=2)
    ]
    db_session.add_all(players)
    
    # Create test battles
    battles = [
        Battle(id=1, date="2023-01-01", attacker_id=1, defender_id=3, result="win"),
        Battle(id=2, date="2023-01-02", attacker_id=2, defender_id=4, result="loss"),
        Battle(id=3, date="2023-01-03", attacker_id=3, defender_id=1, result="draw")
    ]
    db_session.add_all(battles)
    
    db_session.commit()
    
    return db_session
```

#### 3.3 API Testing Automation

We'll implement automated API tests for all endpoints:

```python
# tests/integration/test_api.py
import pytest
import json
from app import create_app

@pytest.fixture
def client(populated_db):
    app = create_app({'TESTING': True, 'DATABASE': populated_db})
    with app.test_client() as client:
        yield client

def test_get_battles_api(client):
    """Test the GET /api/battles endpoint."""
    response = client.get('/api/battles')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 3
    assert data[0]['attacker'] == "Player1"
    assert data[0]['defender'] == "Player3"

def test_get_battles_filtered_api(client):
    """Test filtering battles by player."""
    response = client.get('/api/battles?player=Player1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2  # Player1 participated in 2 battles
    
    # Check proper filtering
    player_names = []
    for battle in data:
        player_names.append(battle['attacker'])
        player_names.append(battle['defender'])
    assert "Player1" in player_names

def test_post_battle_api(client):
    """Test creating a new battle via API."""
    new_battle = {
        'date': '2023-01-04',
        'attacker_id': 1,
        'defender_id': 4,
        'result': 'win'
    }
    response = client.post('/api/battles', 
                         data=json.dumps(new_battle),
                         content_type='application/json')
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['id'] == 4  # Should be the 4th battle
    assert data['attacker'] == 'Player1'
    assert data['defender'] == 'Player4'
```

#### 3.4 Integration Test Environment Management

We'll use Docker containers for consistent integration test environments:

```yaml
# .github/workflows/integration-tests.yml
services:
  postgres:
    image: postgres:latest
    env:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: test_db
    ports:
      - 5432:5432
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
  
  redis:
    image: redis:latest
    ports:
      - 6379:6379
```

With a management script for local testing:

```python
# scripts/setup_test_env.py
import subprocess
import time
import os
from pathlib import Path

def setup_test_environment():
    """Set up the integration test environment using Docker."""
    # Start PostgreSQL container
    subprocess.run([
        "docker", "run", "-d",
        "--name", "tb-analyzer-test-db",
        "-e", "POSTGRES_USER=postgres",
        "-e", "POSTGRES_PASSWORD=postgres",
        "-e", "POSTGRES_DB=test_db",
        "-p", "5432:5432",
        "postgres:latest"
    ])
    
    # Wait for PostgreSQL to be ready
    print("Waiting for PostgreSQL to be ready...")
    for _ in range(30):
        result = subprocess.run([
            "docker", "exec", "tb-analyzer-test-db",
            "pg_isready", "-U", "postgres"
        ], capture_output=True)
        if result.returncode == 0:
            break
        time.sleep(1)
    else:
        print("PostgreSQL failed to start")
        cleanup_test_environment()
        exit(1)
    
    # Initialize the database
    print("Initializing test database...")
    os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/test_db"
    subprocess.run(["python", "-m", "scripts.init_test_db"])
    
    print("Test environment is ready")

def cleanup_test_environment():
    """Clean up the integration test environment."""
    print("Cleaning up test environment...")
    subprocess.run(["docker", "stop", "tb-analyzer-test-db"])
    subprocess.run(["docker", "rm", "tb-analyzer-test-db"])

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--cleanup", action="store_true", help="Clean up test environment")
    args = parser.parse_args()
    
    if args.cleanup:
        cleanup_test_environment()
    else:
        setup_test_environment()
```

### 4. UI and Acceptance Testing Automation

#### 4.1 Automated UI Test Execution

We'll implement automated UI testing using pytest-qt:

```yaml
# UI testing job
ui-tests:
  needs: integration-tests
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y xvfb libxkbcommon-x11-0 libxcb-icccm4 \
          libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 \
          libxcb-xinerama0 libxcb-xkb1 libxkbcommon-x11-0
    
    - name: Install Python dependencies
      run: |
        python -m pip install --upgrade pip
        python -m pip install uv
        uv pip install -e .[dev,test]
    
    - name: Run UI tests
      run: |
        xvfb-run --auto-servernum pytest tests/ui/ --junitxml=ui-results.xml
    
    - name: Upload UI test results
      uses: actions/upload-artifact@v3
      with:
        name: ui-test-results
        path: ui-results.xml
    
    - name: Upload UI test screenshots
      uses: actions/upload-artifact@v3
      with:
        name: ui-test-screenshots
        path: tests/screenshots/
```

#### 4.2 Visual Regression Testing

We'll implement visual regression testing to catch UI changes:

```python
# tests/ui/test_visual_regression.py
import pytest
import os
from pathlib import Path
from PIL import Image, ImageChops
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from app.widgets import DataTableWidget, FilterPanel, ChartWidget

SCREENSHOTS_DIR = Path("tests/screenshots")
BASELINE_DIR = SCREENSHOTS_DIR / "baseline"
CURRENT_DIR = SCREENSHOTS_DIR / "current"

def setup_module():
    """Set up directories for screenshots."""
    SCREENSHOTS_DIR.mkdir(exist_ok=True)
    BASELINE_DIR.mkdir(exist_ok=True)
    CURRENT_DIR.mkdir(exist_ok=True)

def take_screenshot(widget, name):
    """Take a screenshot of a widget."""
    pixmap = widget.grab()
    screenshot_path = CURRENT_DIR / f"{name}.png"
    pixmap.save(str(screenshot_path))
    return screenshot_path

def compare_with_baseline(current_path, name):
    """Compare a screenshot with its baseline version."""
    baseline_path = BASELINE_DIR / f"{name}.png"
    
    # If baseline doesn't exist, create it
    if not baseline_path.exists():
        import shutil
        shutil.copy(current_path, baseline_path)
        return True
    
    # Compare images
    current_img = Image.open(current_path)
    baseline_img = Image.open(baseline_path)
    
    # Check dimensions
    if current_img.size != baseline_img.size:
        return False
    
    # Compare pixel data
    diff = ImageChops.difference(current_img, baseline_img)
    return diff.getbbox() is None

@pytest.mark.visual
def test_data_table_visual(qtbot, sample_data):
    """Test the visual appearance of the data table widget."""
    widget = DataTableWidget()
    widget.resize(800, 600)
    qtbot.addWidget(widget)
    
    # Load sample data
    widget.load_data(sample_data)
    qtbot.wait(500)  # Allow widget to update
    
    # Take screenshot
    screenshot_path = take_screenshot(widget, "data_table")
    
    # Compare with baseline
    assert compare_with_baseline(screenshot_path, "data_table"), "Visual regression detected in data table"

@pytest.mark.visual
def test_filter_panel_visual(qtbot):
    """Test the visual appearance of the filter panel."""
    widget = FilterPanel()
    widget.resize(400, 300)
    qtbot.addWidget(widget)
    
    # Set up filter panel
    widget.set_available_columns(["Date", "Attacker", "Defender", "Result"])
    qtbot.wait(500)  # Allow widget to update
    
    # Take screenshot
    screenshot_path = take_screenshot(widget, "filter_panel")
    
    # Compare with baseline
    assert compare_with_baseline(screenshot_path, "filter_panel"), "Visual regression detected in filter panel"

@pytest.mark.visual
def test_chart_widget_visual(qtbot, sample_data):
    """Test the visual appearance of the chart widget."""
    widget = ChartWidget()
    widget.resize(800, 600)
    qtbot.addWidget(widget)
    
    # Create a chart
    widget.create_bar_chart("Results by Player", "Player", "Battles", sample_data)
    qtbot.wait(500)  # Allow widget to update
    
    # Take screenshot
    screenshot_path = take_screenshot(widget, "chart_widget")
    
    # Compare with baseline
    assert compare_with_baseline(screenshot_path, "chart_widget"), "Visual regression detected in chart widget"
```

#### 4.3 User Acceptance Test Automation

We'll automate user acceptance tests to validate complete user flows:

```python
# tests/acceptance/test_user_flows.py
import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QFileDialog

from app.main_window import MainWindow

@pytest.fixture
def main_window(qtbot, monkeypatch, tmp_path):
    """Set up a main window for acceptance testing."""
    # Create a sample CSV file
    sample_csv = tmp_path / "sample_battles.csv"
    sample_csv.write_text("date,attacker,defender,result\n"
                        "2023-01-01,Player1,Player2,win\n"
                        "2023-01-02,Player2,Player3,loss\n"
                        "2023-01-03,Player1,Player3,win")
    
    # Mock file dialog to return our sample file
    def mock_get_open_file_name(*args, **kwargs):
        return str(sample_csv), ""
    
    monkeypatch.setattr(QFileDialog, 'getOpenFileName', mock_get_open_file_name)
    
    # Create and show main window
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    
    return window

def test_complete_analysis_flow(qtbot, main_window):
    """Test a complete user flow from file import to analysis."""
    # Step 1: Import a CSV file
    qtbot.mouseClick(main_window.import_button, Qt.LeftButton)
    qtbot.wait(500)  # Wait for file to be processed
    
    # Verify data was loaded
    assert main_window.data_table.rowCount() > 0
    
    # Step 2: Apply a filter
    filter_panel = main_window.filter_panel
    qtbot.mouseClick(filter_panel.add_filter_button, Qt.LeftButton)
    
    # Select "Attacker" column
    column_combo = filter_panel.filters[0].column_combo
    qtbot.mouseClick(column_combo, Qt.LeftButton)
    qtbot.keyClicks(column_combo, "Attacker")
    qtbot.keyPress(column_combo, Qt.Key_Return)
    
    # Enter filter value
    value_field = filter_panel.filters[0].value_field
    qtbot.mouseClick(value_field, Qt.LeftButton)
    qtbot.keyClicks(value_field, "Player1")
    
    # Apply filter
    qtbot.mouseClick(filter_panel.apply_button, Qt.LeftButton)
    qtbot.wait(500)  # Wait for filter to be applied
    
    # Verify filter was applied
    assert main_window.data_table.rowCount() == 2  # Should show only Player1's battles
    
    # Step 3: Generate a chart
    qtbot.mouseClick(main_window.create_chart_button, Qt.LeftButton)
    qtbot.wait(500)  # Wait for chart to be generated
    
    # Verify chart was created
    assert main_window.chart_widget.has_chart()
    
    # Step 4: Export results
    export_path = tmp_path / "export_results.csv"
    
    # Mock save dialog
    def mock_get_save_file_name(*args, **kwargs):
        return str(export_path), ""
    
    with monkeypatch.context() as m:
        m.setattr(QFileDialog, 'getSaveFileName', mock_get_save_file_name)
        qtbot.mouseClick(main_window.export_button, Qt.LeftButton)
    
    qtbot.wait(500)  # Wait for export to complete
    
    # Verify export file was created
    assert export_path.exists()
    
    # Verify export content
    content = export_path.read_text()
    assert "Player1" in content
    assert "Player2" in content
    assert "win" in content
```

#### 4.4 Performance and Load Testing Automation

We'll automate performance testing to ensure responsiveness:

```python
# tests/performance/test_load_performance.py
import pytest
import time
import pandas as pd
import numpy as np
from app.services import DataProcessor

def generate_large_dataset(size=10000):
    """Generate a large dataset for performance testing."""
    players = [f"Player{i}" for i in range(1, 101)]
    
    # Create a DataFrame with random battle data
    data = {
        'date': pd.date_range(start='2022-01-01', periods=size),
        'attacker': np.random.choice(players, size=size),
        'defender': np.random.choice(players, size=size),
        'result': np.random.choice(['win', 'loss', 'draw'], size=size),
        'attacker_power': np.random.randint(1000, 100000, size=size),
        'defender_power': np.random.randint(1000, 100000, size=size)
    }
    
    return pd.DataFrame(data)

@pytest.mark.parametrize("dataset_size", [100, 1000, 10000, 100000])
def test_data_processing_performance(dataset_size):
    """Test the performance of data processing with different dataset sizes."""
    # Generate test data
    df = generate_large_dataset(dataset_size)
    
    # Initialize processor
    processor = DataProcessor()
    
    # Measure processing time
    start_time = time.time()
    results = processor.process_battles(df)
    end_time = time.time()
    
    processing_time = end_time - start_time
    
    # Log performance metrics
    print(f"Dataset size: {dataset_size}, Processing time: {processing_time:.4f} seconds")
    
    # Performance assertions - adjust thresholds as needed
    if dataset_size <= 1000:
        assert processing_time < 1.0, f"Processing {dataset_size} records took too long: {processing_time:.4f}s"
    elif dataset_size <= 10000:
        assert processing_time < 3.0, f"Processing {dataset_size} records took too long: {processing_time:.4f}s"
    elif dataset_size <= 100000:
        assert processing_time < 10.0, f"Processing {dataset_size} records took too long: {processing_time:.4f}s"

@pytest.mark.ui
@pytest.mark.performance
@pytest.mark.parametrize("dataset_size", [100, 1000, 5000])
def test_ui_performance_with_large_dataset(qtbot, dataset_size):
    """Test UI performance with different dataset sizes."""
    from app.widgets import DataTableWidget
    
    # Generate test data
    df = generate_large_dataset(dataset_size)
    
    # Create widget
    widget = DataTableWidget()
    widget.resize(800, 600)
    qtbot.addWidget(widget)
    
    # Measure time to load data
    start_time = time.time()
    widget.load_data(df)
    
    # Wait for UI to update and measure rendering time
    qtbot.wait(100)  # Wait for event processing
    end_time = time.time()
    
    loading_time = end_time - start_time
    
    # Log performance metrics
    print(f"UI Dataset size: {dataset_size}, Loading time: {loading_time:.4f} seconds")
    
    # Performance assertions for UI
    if dataset_size <= 1000:
        assert loading_time < 2.0, f"UI loading of {dataset_size} records took too long: {loading_time:.4f}s"
    elif dataset_size <= 5000:
        assert loading_time < 5.0, f"UI loading of {dataset_size} records took too long: {loading_time:.4f}s"
```

## Implementation Approach

The implementation of the Automated Testing Pipeline will follow this approach:

1. **Testing Pipeline Architecture** (Days 1-3)
   - Design and implement the overall testing workflow
   - Configure test environments
   - Set up test data management
   - Implement test reporting infrastructure

2. **Unit Testing Automation** (Days 4-5)
   - Configure automated unit test execution
   - Implement test parameterization
   - Set up mocking and coverage reporting
   - Optimize test performance

3. **Integration Testing Automation** (Days 6-7)
   - Configure integration test environment
   - Implement database fixtures
   - Set up API testing
   - Configure environment management scripts

4. **UI and Acceptance Testing** (Days 8-10)
   - Set up UI test automation
   - Implement visual regression testing
   - Configure user acceptance tests
   - Set up performance testing automation

## Dependencies

This part has dependencies on:
- Completed Phase 6 Part 1: CI/CD Strategy and Infrastructure
- Completed Phase 6 Part 2: Continuous Integration Implementation
- Completed Phase 5: Testing and Quality Assurance (particularly Parts 3 and 4 with test strategies)
- Access to GitHub repository with GitHub Actions capabilities

## Expected Outcomes

After completing Phase 6 Part 3, the project will have:
1. A comprehensive automated testing pipeline that runs on every code change
2. Detailed test reporting for all test types
3. Stable and reliable test environments for different test types
4. Visual regression testing to catch UI changes
5. Performance testing to ensure the application remains responsive
6. User acceptance testing to validate complete workflows 