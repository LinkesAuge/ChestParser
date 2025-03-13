# Phase 5 Part 5: Performance, Security, and Deployment Testing

## Overview

This document outlines the approach for testing the performance, security, and deployment aspects of the Total Battle Analyzer application. These tests ensure that the application not only functions correctly but also performs efficiently, maintains data security, and can be reliably deployed across different environments.

## Implementation Tasks

### 1. Performance Testing

- [ ] Develop load testing approach for various data sizes
- [ ] Create stress testing methodology to identify breaking points
- [ ] Implement memory usage monitoring and optimization tests
- [ ] Develop CPU usage profiling and optimization techniques
- [ ] Create response time benchmarks for critical operations

### 2. Security Testing

- [ ] Implement data validation testing
- [ ] Develop error handling security tests
- [ ] Create dependency security scanning process
- [ ] Implement file path traversal security tests
- [ ] Develop tests for secure data export

### 3. Deployment Testing

- [ ] Create installation testing process
- [ ] Develop multi-platform compatibility testing
- [ ] Implement update/upgrade testing methodology
- [ ] Create environment configuration validation tests
- [ ] Develop distribution package verification tests

## Implementation Approach

The implementation of these tests will follow a methodical approach focusing on:

1. Automated testing where possible
2. Consistent measurement methodologies
3. Clear pass/fail criteria
4. Comprehensive reporting of results
5. Actionable recommendations for issues found

The timeframe for implementation is estimated at 2-3 weeks, with each major section (Performance, Security, Deployment) taking approximately one week.

## Dependencies

This phase depends on the completion of:
- Phase 5 Part 1: Test Strategy and Framework
- Phase 5 Part 2: Unit Testing
- Phase 5 Part 3: Integration Testing
- Phase 5 Part 4: UI Testing and User Acceptance

## Expected Outcomes

1. Comprehensive test suite for performance, security, and deployment aspects
2. Baseline performance metrics for key application operations
3. Security validation report
4. Deployment verification across target platforms
5. Recommendations for optimization and hardening

## Detailed Implementation Plans

### 1. Performance Testing

Performance testing ensures that the Total Battle Analyzer application performs efficiently under various conditions, particularly with different data sizes and during resource-intensive operations.

#### 1.1. Load Testing with Variable Data Sizes

```python
# tests/performance/test_data_loading.py
import pytest
import time
import pandas as pd
import numpy as np
from memory_profiler import profile
from pathlib import Path
from src.services.data_service import DataService

class TestDataLoadingPerformance:
    """Tests for performance of data loading operations."""
    
    @pytest.fixture(scope="class")
    def test_files(self, tmp_path_factory):
        """Create test CSV files of various sizes."""
        files = {}
        base_path = tmp_path_factory.getbasetemp() / "perf_test_data"
        base_path.mkdir(exist_ok=True)
        
        # Generate small test file (100 rows)
        small_path = base_path / "small_dataset.csv"
        self._generate_test_file(small_path, 100)
        files["small"] = small_path
        
        # Generate medium test file (10,000 rows)
        medium_path = base_path / "medium_dataset.csv"
        self._generate_test_file(medium_path, 10_000)
        files["medium"] = medium_path
        
        # Generate large test file (100,000 rows)
        large_path = base_path / "large_dataset.csv"
        self._generate_test_file(large_path, 100_000)
        files["large"] = large_path
        
        # Generate extra large test file (1,000,000 rows)
        xlarge_path = base_path / "xlarge_dataset.csv"
        self._generate_test_file(xlarge_path, 1_000_000)
        files["xlarge"] = xlarge_path
        
        return files
    
    def _generate_test_file(self, path, num_rows):
        """Generate a test CSV file with specified number of rows."""
        # Create random player names (with German umlauts for testing encoding)
        players = [f"Player{i}" for i in range(50)]
        german_players = ["Müller", "Jäger", "Schröder", "Größmann", "Köhler"]
        players.extend(german_players)
        
        # Create random chest types
        chest_types = ["Gold", "Silver", "Bronze", "Diamond", "Platinum"]
        
        # Create random sources
        sources = ["Battle", "Guild", "Event", "Quest", "Tournament"]
        
        # Generate random data
        dates = [f"2023-{np.random.randint(1, 13):02d}-{np.random.randint(1, 29):02d}" for _ in range(num_rows)]
        player_names = [np.random.choice(players) for _ in range(num_rows)]
        chest_type = [np.random.choice(chest_types) for _ in range(num_rows)]
        score = [np.random.randint(50, 500) for _ in range(num_rows)]
        source = [np.random.choice(sources) for _ in range(num_rows)]
        
        # Create DataFrame
        df = pd.DataFrame({
            "DATE": dates,
            "PLAYER": player_names,
            "CHEST_TYPE": chest_type,
            "SCORE": score,
            "SOURCE": source
        })
        
        # Write to CSV
        df.to_csv(path, index=False)
    
    @pytest.mark.parametrize("file_size", ["small", "medium", "large", "xlarge"])
    def test_load_csv_performance(self, file_size, test_files):
        """Test the performance of loading CSV files of different sizes."""
        data_service = DataService()
        
        # Warm-up to avoid first-run penalties
        _ = data_service.load_csv(test_files["small"])
        
        # Measure performance
        start_time = time.time()
        df = data_service.load_csv(test_files[file_size])
        load_time = time.time() - start_time
        
        # Assert data was loaded correctly
        assert df is not None
        assert not df.empty
        
        # Log performance information
        row_count = len(df)
        load_time_per_row = load_time / row_count if row_count > 0 else 0
        
        # Create metrics for reporting
        metrics = {
            "file_size": file_size,
            "row_count": row_count,
            "load_time_seconds": load_time,
            "load_time_per_row_ms": load_time_per_row * 1000
        }
        
        # Log metrics for reporting
        print(f"Performance metrics: {metrics}")
        
        # Performance assertions - these should be calibrated based on actual testing
        if file_size == "small":
            assert load_time < 0.5, f"Small file load too slow: {load_time:.2f}s"
        elif file_size == "medium":
            assert load_time < 2.0, f"Medium file load too slow: {load_time:.2f}s"
        elif file_size == "large":
            assert load_time < 10.0, f"Large file load too slow: {load_time:.2f}s"
        # No strict assertion for xlarge, just measuring it
        
        return metrics
    
    @profile
    def test_memory_usage_during_loading(self, test_files):
        """Test memory usage during loading of different file sizes."""
        data_service = DataService()
        
        # Test with progressively larger files
        for size in ["small", "medium", "large"]:
            print(f"\n--- Testing memory usage with {size} file ---")
            df = data_service.load_csv(test_files[size])
            
            # Force some processing to ensure memory usage is measured
            _ = data_service.analyze_data(df)
            
            # Memory usage will be tracked by the @profile decorator
            
            # Basic verification
            assert df is not None
```

#### 1.2. Stress Testing

```python
# tests/performance/test_stress.py
import pytest
import time
import threading
import queue
import pandas as pd
from pathlib import Path
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication
from src.services.data_service import DataService
from src.services.analysis_service import AnalysisService
from src.services.chart_service import ChartService

class TestStressPerformance:
    """Tests for application behavior under stress conditions."""
    
    @pytest.fixture
    def large_dataset(self, test_files):
        """Load a large dataset for testing."""
        data_service = DataService()
        return data_service.load_csv(test_files["large"])
    
    def test_concurrent_operations(self, large_dataset):
        """Test performance with multiple concurrent operations."""
        data_service = DataService()
        analysis_service = AnalysisService()
        chart_service = ChartService()
        
        # Create a queue for results
        results_queue = queue.Queue()
        
        # Define worker functions
        def filter_data_worker():
            """Worker to filter data multiple times."""
            start_time = time.time()
            for player in large_dataset["PLAYER"].unique()[:20]:  # First 20 players
                filtered = data_service.filter_by_values(large_dataset, "PLAYER", [player])
                assert not filtered.empty
            results_queue.put(("filter", time.time() - start_time))
        
        def analyze_data_worker():
            """Worker to run analysis."""
            start_time = time.time()
            results = analysis_service.analyze(large_dataset)
            assert results is not None
            results_queue.put(("analyze", time.time() - start_time))
        
        def create_charts_worker():
            """Worker to create multiple charts."""
            start_time = time.time()
            chart_types = ["bar", "pie", "line"]
            for chart_type in chart_types:
                chart = chart_service.create_chart(
                    large_dataset, 
                    "PLAYER", 
                    "SCORE", 
                    chart_type=chart_type, 
                    limit=10
                )
                assert chart is not None
            results_queue.put(("charts", time.time() - start_time))
        
        # Run workers in separate threads
        threads = [
            threading.Thread(target=filter_data_worker),
            threading.Thread(target=analyze_data_worker),
            threading.Thread(target=create_charts_worker)
        ]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=60)  # 1 minute timeout
        
        # Collect results
        results = {}
        while not results_queue.empty():
            operation, duration = results_queue.get()
            results[operation] = duration
        
        # Log performance metrics
        print(f"Concurrent operation durations: {results}")
        
        # Performance assertions
        assert results.get("filter", 60) < 30, "Filtering operations too slow under concurrent load"
        assert results.get("analyze", 60) < 30, "Analysis operations too slow under concurrent load"
        assert results.get("charts", 60) < 30, "Chart creation too slow under concurrent load"
    
    def test_ui_responsiveness_under_load(self, qtbot, monkeypatch, large_dataset):
        """Test UI responsiveness while processing large datasets."""
        from src.ui.main_window import MainWindow
        from src.services.data_service import DataService
        
        # Mock data service to use our large dataset
        monkeypatch.setattr(
            DataService,
            "get_data",
            lambda self: large_dataset
        )
        
        # Create application window
        window = MainWindow(
            DataService(),
            AnalysisService(),
            ChartService()
        )
        window.show()
        
        # Track UI event response times
        response_times = []
        
        # Create a timer to measure UI response time
        def measure_response():
            start_time = time.time()
            # Schedule function to run in the next event loop cycle
            QTimer.singleShot(0, lambda: response_times.append(time.time() - start_time))
        
        # Trigger intensive operation
        with qtbot.waitSignal(window.analysisCompleted, timeout=30000):
            # Start measuring UI responsiveness
            measure_timer = QTimer()
            measure_timer.timeout.connect(measure_response)
            measure_timer.start(100)  # Measure every 100ms
            
            # Trigger analysis operation
            window.analyze_data()
        
        measure_timer.stop()
        
        # Calculate statistics
        avg_response = sum(response_times) / len(response_times) if response_times else 0
        max_response = max(response_times) if response_times else 0
        
        print(f"UI responsiveness metrics - Avg: {avg_response*1000:.2f}ms, Max: {max_response*1000:.2f}ms")
        
        # Performance assertions
        assert avg_response < 0.1, f"Average UI response time too high: {avg_response*1000:.2f}ms"
        assert max_response < 0.5, f"Maximum UI response time too high: {max_response*1000:.2f}ms"
```

#### 1.3. Memory Usage Optimization

```python
# tests/performance/test_memory_optimization.py
import pytest
import gc
import pandas as pd
import psutil
import os
from memory_profiler import profile
from src.services.data_service import DataService
from src.services.analysis_service import AnalysisService
from src.services.chart_service import ChartService

class TestMemoryOptimization:
    """Tests for memory usage optimization."""
    
    def get_memory_usage():
        """Get current memory usage in MB."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    
    @pytest.fixture(scope="function", autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        # Force garbage collection before each test
        gc.collect()
        
        # Record starting memory
        self.start_memory = self.get_memory_usage()
        
        yield
        
        # Force garbage collection after each test
        gc.collect()
    
    @profile
    def test_data_service_memory_usage(self, test_files):
        """Test memory usage optimization in DataService."""
        data_service = DataService()
        
        # Test with progressively larger files
        for size in ["small", "medium", "large"]:
            # Record memory before loading
            before_memory = self.get_memory_usage()
            
            # Load the file
            df = data_service.load_csv(test_files[size])
            
            # Record memory after loading
            after_load_memory = self.get_memory_usage()
            
            # Get row count for metric calculation
            row_count = len(df)
            
            # Calculate metrics
            memory_per_row = (after_load_memory - before_memory) / row_count if row_count > 0 else 0
            
            print(f"{size} file ({row_count} rows): {after_load_memory - before_memory:.2f}MB total, {memory_per_row*1000:.2f}KB per row")
            
            # Check for memory leaks
            del df
            gc.collect()
            
            # Record memory after cleanup
            after_cleanup_memory = self.get_memory_usage()
            
            # Verify cleanup
            cleanup_diff = after_cleanup_memory - before_memory
            print(f"Memory after cleanup: {cleanup_diff:.2f}MB compared to start")
            
            # Memory efficiency assertions - these should be calibrated based on actual testing
            if size == "small":
                assert memory_per_row < 0.001, f"Memory usage per row too high: {memory_per_row*1000:.2f}KB"
            elif size == "medium":
                assert memory_per_row < 0.0005, f"Memory usage per row too high for medium dataset: {memory_per_row*1000:.2f}KB"
            
            # Verify no significant memory leak
            assert cleanup_diff < 5, f"Possible memory leak: {cleanup_diff:.2f}MB retained after cleanup"
    
    @profile
    def test_analysis_service_memory_efficiency(self, large_dataset):
        """Test memory efficiency of analysis operations."""
        analysis_service = AnalysisService()
        
        # Record memory before analysis
        before_memory = self.get_memory_usage()
        
        # Perform analysis
        results = analysis_service.analyze(large_dataset)
        
        # Record memory after analysis
        after_analysis_memory = self.get_memory_usage()
        
        # Calculate metrics
        analysis_memory = after_analysis_memory - before_memory
        
        print(f"Analysis memory usage: {analysis_memory:.2f}MB")
        
        # Check for memory leaks
        del results
        gc.collect()
        
        # Record memory after cleanup
        after_cleanup_memory = self.get_memory_usage()
        
        # Verify cleanup
        cleanup_diff = after_cleanup_memory - before_memory
        print(f"Memory after cleanup: {cleanup_diff:.2f}MB compared to start")
        
        # Memory efficiency assertions
        assert analysis_memory < (large_dataset.memory_usage(deep=True).sum() / (1024*1024)), "Analysis uses more memory than the original dataset"
        assert cleanup_diff < 5, f"Possible memory leak: {cleanup_diff:.2f}MB retained after cleanup"
    
    @profile
    def test_chart_service_memory_efficiency(self, large_dataset):
        """Test memory efficiency of chart generation operations."""
        chart_service = ChartService()
        
        # Test with different chart types
        chart_types = ["bar", "pie", "line", "horizontal_bar"]
        
        for chart_type in chart_types:
            # Record memory before chart creation
            before_memory = self.get_memory_usage()
            
            # Create chart
            chart = chart_service.create_chart(
                large_dataset, 
                "PLAYER", 
                "SCORE", 
                chart_type=chart_type, 
                limit=20
            )
            
            # Record memory after chart creation
            after_chart_memory = self.get_memory_usage()
            
            # Calculate metrics
            chart_memory = after_chart_memory - before_memory
            
            print(f"{chart_type} chart memory usage: {chart_memory:.2f}MB")
            
            # Check for memory leaks
            del chart
            gc.collect()
            
            # Record memory after cleanup
            after_cleanup_memory = self.get_memory_usage()
            
            # Verify cleanup
            cleanup_diff = after_cleanup_memory - before_memory
            print(f"Memory after {chart_type} chart cleanup: {cleanup_diff:.2f}MB compared to start")
            
            # Memory efficiency assertions
            assert chart_memory < 50, f"{chart_type} chart uses too much memory: {chart_memory:.2f}MB"
            assert cleanup_diff < 5, f"Possible memory leak in {chart_type} chart: {cleanup_diff:.2f}MB retained after cleanup"
```

#### 1.4. CPU Usage Profiling

```python
# tests/performance/test_cpu_profiling.py
import pytest
import cProfile
import pstats
import io
import pandas as pd
from pathlib import Path
from src.services.data_service import DataService
from src.services.analysis_service import AnalysisService
from src.services.chart_service import ChartService

class TestCPUProfiling:
    """Tests for CPU usage profiling and optimization."""
    
    @pytest.fixture
    def profiler(self):
        """Create a cProfile profiler for CPU usage measurement."""
        return cProfile.Profile()
    
    def print_profile_stats(self, profiler, top_n=20):
        """Print the top N most time-consuming operations."""
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(top_n)
        print(s.getvalue())
    
    def test_data_loading_cpu_profile(self, profiler, test_files):
        """Profile CPU usage during data loading."""
        data_service = DataService()
        
        # Start profiling
        profiler.enable()
        
        # Load a large file
        df = data_service.load_csv(test_files["large"])
        
        # Stop profiling
        profiler.disable()
        
        # Print profile results
        print("\nCPU Profile for Data Loading:")
        self.print_profile_stats(profiler)
        
        # Basic verification
        assert df is not None
        assert not df.empty
    
    def test_data_analysis_cpu_profile(self, profiler, large_dataset):
        """Profile CPU usage during data analysis."""
        analysis_service = AnalysisService()
        
        # Start profiling
        profiler.enable()
        
        # Perform analysis
        results = analysis_service.analyze(large_dataset)
        
        # Stop profiling
        profiler.disable()
        
        # Print profile results
        print("\nCPU Profile for Data Analysis:")
        self.print_profile_stats(profiler)
        
        # Basic verification
        assert results is not None
    
    def test_chart_generation_cpu_profile(self, profiler, large_dataset):
        """Profile CPU usage during chart generation."""
        chart_service = ChartService()
        
        # Test different chart types
        chart_types = ["bar", "pie", "line", "horizontal_bar"]
        
        for chart_type in chart_types:
            # Start profiling
            profiler.enable()
            
            # Create chart
            chart = chart_service.create_chart(
                large_dataset, 
                "PLAYER", 
                "SCORE", 
                chart_type=chart_type, 
                limit=20
            )
            
            # Stop profiling
            profiler.disable()
            
            # Print profile results
            print(f"\nCPU Profile for {chart_type} Chart Generation:")
            self.print_profile_stats(profiler)
            
            # Basic verification
            assert chart is not None
    
    def test_report_generation_cpu_profile(self, profiler, large_dataset):
        """Profile CPU usage during report generation."""
        from src.services.report_service import ReportService
        
        analysis_service = AnalysisService()
        chart_service = ChartService()
        report_service = ReportService(analysis_service, chart_service)
        
        # Analyze data first
        analysis_results = analysis_service.analyze(large_dataset)
        
        # Start profiling
        profiler.enable()
        
        # Generate a comprehensive report
        report = report_service.generate_report(
            large_dataset,
            analysis_results,
            report_type="full",
            include_charts=True,
            include_tables=True,
            include_stats=True
        )
        
        # Stop profiling
        profiler.disable()
        
        # Print profile results
        print("\nCPU Profile for Report Generation:")
        self.print_profile_stats(profiler)
        
        # Basic verification
        assert report is not None
```

#### 1.5. Response Time Benchmarking

```python
# tests/performance/test_response_time.py
import pytest
import time
import pandas as pd
import numpy as np
from pathlib import Path
from src.services.data_service import DataService
from src.services.analysis_service import AnalysisService
from src.services.chart_service import ChartService
from src.ui.main_window import MainWindow

class TestResponseTime:
    """Tests for response time benchmarking."""
    
    @pytest.fixture
    def medium_dataset(self, test_files):
        """Load a medium-sized dataset for testing."""
        data_service = DataService()
        return data_service.load_csv(test_files["medium"])
    
    def test_filter_response_time(self, medium_dataset):
        """Benchmark response time for filtering operations."""
        data_service = DataService()
        
        # Get unique values for filter tests
        players = medium_dataset["PLAYER"].unique()
        sources = medium_dataset["SOURCE"].unique()
        chest_types = medium_dataset["CHEST_TYPE"].unique()
        
        filter_scenarios = [
            ("Single Player", "PLAYER", [players[0]]),
            ("Multiple Players", "PLAYER", players[:5]),
            ("Single Source", "SOURCE", [sources[0]]),
            ("All Sources", "SOURCE", sources),
            ("Single Chest Type", "CHEST_TYPE", [chest_types[0]]),
            ("Complex Filter", "PLAYER", players[:10])  # Will add date filter too
        ]
        
        results = {}
        
        for scenario_name, column, values in filter_scenarios:
            # Warm up
            _ = data_service.filter_by_values(medium_dataset, column, values)
            
            # Benchmark
            iterations = 5
            times = []
            
            for _ in range(iterations):
                start_time = time.time()
                
                if scenario_name == "Complex Filter":
                    # Apply multiple filters for complex scenario
                    df = data_service.filter_by_values(medium_dataset, column, values)
                    df = data_service.filter_by_values(df, "SOURCE", sources[:2])
                    df = data_service.filter_by_date_range(df, "2023-01-01", "2023-06-30")
                else:
                    df = data_service.filter_by_values(medium_dataset, column, values)
                
                end_time = time.time()
                times.append(end_time - start_time)
            
            # Calculate statistics
            avg_time = sum(times) / len(times)
            max_time = max(times)
            min_time = min(times)
            
            results[scenario_name] = {
                "avg_ms": avg_time * 1000,
                "min_ms": min_time * 1000,
                "max_ms": max_time * 1000
            }
            
            # Basic verification
            assert not df.empty, f"Filter resulted in empty DataFrame: {scenario_name}"
        
        # Print benchmark results
        print("\nFilter Response Time Benchmarks:")
        for scenario, metrics in results.items():
            print(f"{scenario}: Avg={metrics['avg_ms']:.2f}ms, Min={metrics['min_ms']:.2f}ms, Max={metrics['max_ms']:.2f}ms")
        
        # Performance assertions
        assert results["Single Player"]["avg_ms"] < 100, "Single player filter too slow"
        assert results["Multiple Players"]["avg_ms"] < 200, "Multiple players filter too slow"
        assert results["Complex Filter"]["avg_ms"] < 500, "Complex filter too slow"
    
    def test_analysis_response_time(self, medium_dataset):
        """Benchmark response time for analysis operations."""
        analysis_service = AnalysisService()
        
        # Warm up
        _ = analysis_service.analyze(medium_dataset)
        
        # Benchmark
        iterations = 3
        times = []
        
        for _ in range(iterations):
            start_time = time.time()
            results = analysis_service.analyze(medium_dataset)
            end_time = time.time()
            times.append(end_time - start_time)
        
        # Calculate statistics
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        print(f"\nAnalysis Response Time Benchmark:")
        print(f"Avg={avg_time*1000:.2f}ms, Min={min_time*1000:.2f}ms, Max={max_time*1000:.2f}ms")
        
        # Performance assertions
        assert avg_time < 2.0, f"Analysis too slow: {avg_time*1000:.2f}ms"
        
        # Basic verification
        assert results is not None
        assert "player_analysis" in results
        assert "chest_analysis" in results
        assert "source_analysis" in results
        assert "player_overview" in results
    
    def test_chart_generation_response_time(self, medium_dataset):
        """Benchmark response time for chart generation."""
        chart_service = ChartService()
        
        chart_scenarios = [
            ("Bar Chart - Default", "bar", "PLAYER", "SCORE", 10),
            ("Bar Chart - All Data", "bar", "PLAYER", "SCORE", None),
            ("Pie Chart", "pie", "CHEST_TYPE", "SCORE", None),
            ("Line Chart", "line", "DATE", "SCORE", None),
            ("Horizontal Bar", "horizontal_bar", "PLAYER", "SCORE", 20)
        ]
        
        results = {}
        
        for scenario_name, chart_type, category, measure, limit in chart_scenarios:
            # Warm up
            _ = chart_service.create_chart(
                medium_dataset, category, measure, 
                chart_type=chart_type, limit=limit
            )
            
            # Benchmark
            iterations = 3
            times = []
            
            for _ in range(iterations):
                start_time = time.time()
                chart = chart_service.create_chart(
                    medium_dataset, category, measure, 
                    chart_type=chart_type, limit=limit
                )
                end_time = time.time()
                times.append(end_time - start_time)
            
            # Calculate statistics
            avg_time = sum(times) / len(times)
            max_time = max(times)
            min_time = min(times)
            
            results[scenario_name] = {
                "avg_ms": avg_time * 1000,
                "min_ms": min_time * 1000,
                "max_ms": max_time * 1000
            }
            
            # Basic verification
            assert chart is not None
        
        # Print benchmark results
        print("\nChart Generation Response Time Benchmarks:")
        for scenario, metrics in results.items():
            print(f"{scenario}: Avg={metrics['avg_ms']:.2f}ms, Min={metrics['min_ms']:.2f}ms, Max={metrics['max_ms']:.2f}ms")
        
        # Performance assertions
        assert results["Bar Chart - Default"]["avg_ms"] < 500, "Bar chart generation too slow"
        assert results["Pie Chart"]["avg_ms"] < 500, "Pie chart generation too slow"
        assert results["Line Chart"]["avg_ms"] < 500, "Line chart generation too slow"
    
    def test_ui_operation_response_time(self, qtbot, monkeypatch, medium_dataset):
        """Benchmark response time for UI operations."""
        data_service = DataService()
        analysis_service = AnalysisService()
        chart_service = ChartService()
        
        # Mock data service to use our medium dataset
        monkeypatch.setattr(
            DataService,
            "get_data",
            lambda self: medium_dataset
        )
        
        # Create application window
        window = MainWindow(
            data_service,
            analysis_service,
            chart_service
        )
        window.show()
        
        ui_scenarios = [
            "Switch to Raw Data Tab",
            "Switch to Analysis Tab",
            "Switch to Charts Tab",
            "Apply Filter",
            "Reset Filter",
            "Change Chart Type",
            "Change Analysis View"
        ]
        
        results = {}
        
        # Benchmark UI operations
        for scenario in ui_scenarios:
            times = []
            iterations = 3
            
            for _ in range(iterations):
                if scenario == "Switch to Raw Data Tab":
                    start_time = time.time()
                    window.tab_widget.setCurrentIndex(1)  # Raw Data tab
                    qtbot.wait(100)  # Wait for UI to update
                    end_time = time.time()
                
                elif scenario == "Switch to Analysis Tab":
                    start_time = time.time()
                    window.tab_widget.setCurrentIndex(2)  # Analysis tab
                    qtbot.wait(100)  # Wait for UI to update
                    end_time = time.time()
                
                elif scenario == "Switch to Charts Tab":
                    start_time = time.time()
                    window.tab_widget.setCurrentIndex(3)  # Charts tab
                    qtbot.wait(100)  # Wait for UI to update
                    end_time = time.time()
                
                elif scenario == "Apply Filter":
                    # Switch to Raw Data tab first
                    window.tab_widget.setCurrentIndex(1)
                    qtbot.wait(100)
                    
                    # Select a filter
                    window.raw_data_filter_column.setCurrentText("PLAYER")
                    qtbot.wait(100)
                    
                    # Add a value to filter by
                    if hasattr(window, "raw_data_filter_values") and window.raw_data_filter_values.count() > 0:
                        window.raw_data_filter_values.item(0).setSelected(True)
                        
                        # Measure the filter application
                        start_time = time.time()
                        qtbot.mouseClick(window.raw_data_apply_filters_button, Qt.MouseButton.LeftButton)
                        qtbot.wait(500)  # Wait for filtering to complete
                        end_time = time.time()
                    else:
                        # Skip if filter values aren't available
                        continue
                
                elif scenario == "Reset Filter":
                    # Switch to Raw Data tab first
                    window.tab_widget.setCurrentIndex(1)
                    qtbot.wait(100)
                    
                    # Measure the filter reset
                    start_time = time.time()
                    qtbot.mouseClick(window.raw_data_reset_filters_button, Qt.MouseButton.LeftButton)
                    qtbot.wait(200)  # Wait for reset to complete
                    end_time = time.time()
                
                elif scenario == "Change Chart Type":
                    # Switch to Charts tab first
                    window.tab_widget.setCurrentIndex(3)
                    qtbot.wait(100)
                    
                    # Measure chart type change
                    start_time = time.time()
                    window.chart_type_selector.setCurrentText("Pie Chart")
                    qtbot.wait(500)  # Wait for chart update
                    end_time = time.time()
                
                elif scenario == "Change Analysis View":
                    # Switch to Analysis tab first
                    window.tab_widget.setCurrentIndex(2)
                    qtbot.wait(100)
                    
                    # Measure analysis view change
                    start_time = time.time()
                    if hasattr(window, "analysis_selector") and window.analysis_selector.count() > 1:
                        window.analysis_selector.setCurrentIndex(1)  # Switch to second view
                        qtbot.wait(500)  # Wait for view update
                        end_time = time.time()
                    else:
                        # Skip if analysis views aren't available
                        continue
                
                times.append(end_time - start_time)
            
            if times:
                # Calculate statistics
                avg_time = sum(times) / len(times)
                max_time = max(times)
                min_time = min(times)
                
                results[scenario] = {
                    "avg_ms": avg_time * 1000,
                    "min_ms": min_time * 1000,
                    "max_ms": max_time * 1000
                }
        
        # Print benchmark results
        print("\nUI Operation Response Time Benchmarks:")
        for scenario, metrics in results.items():
            print(f"{scenario}: Avg={metrics['avg_ms']:.2f}ms, Min={metrics['min_ms']:.2f}ms, Max={metrics['max_ms']:.2f}ms")
        
        # Performance assertions for tab switching should be very fast
        tab_scenarios = ["Switch to Raw Data Tab", "Switch to Analysis Tab", "Switch to Charts Tab"]
        for scenario in tab_scenarios:
            if scenario in results:
                assert results[scenario]["avg_ms"] < 100, f"{scenario} too slow: {results[scenario]['avg_ms']:.2f}ms"
```

The performance testing implementation provides a comprehensive approach to measuring and optimizing the application's performance. Key aspects include:

1. **Load Testing**: Evaluates how the application handles datasets of various sizes, from small (100 rows) to extremely large (1,000,000 rows). This helps identify scaling issues and optimize data loading processes.

2. **Stress Testing**: Tests application behavior under concurrent operations and high load, ensuring stability during intensive use.

3. **Memory Usage Optimization**: Monitors memory consumption during various operations to identify potential memory leaks and optimize resource usage.

4. **CPU Usage Profiling**: Identifies the most CPU-intensive operations to target optimization efforts where they'll have the most impact.

5. **Response Time Benchmarking**: Measures and sets performance standards for critical operations such as filtering, analysis, chart generation, and UI operations.

The implementation includes clear pass/fail criteria with assertions that verify the application meets performance requirements. It also provides detailed metrics for ongoing monitoring and comparison as the application evolves.

### 2. Security Testing

Security testing ensures that the Total Battle Analyzer application maintains data integrity, handles errors gracefully, and protects against potential vulnerabilities. The implementation focuses on five critical areas:

#### 2.1. Data Validation Testing

Data validation tests verify that the application properly handles various types of input data, including:
- Malformed CSV files with broken structure
- Files with encoding issues (particularly with German umlauts)
- Missing required columns
- Invalid data types (e.g., text in numeric fields)
- Empty files

The tests ensure that the application:
- Rejects invalid data with appropriate error messages
- Handles encoding issues gracefully when configured to do so
- Enforces data requirements when in strict mode
- Provides helpful validation information for invalid data

#### 2.2. Error Handling Security Tests

Error handling tests verify that the application's error messages:
- Do not expose sensitive system information (paths, usernames, etc.)
- Do not reveal implementation details that could aid attackers
- Provide useful information for legitimate users without oversharing
- Handle permission issues, file access problems, and other errors securely

#### 2.3. Dependency Security Scanning

Dependency security tests:
- Check for known vulnerabilities in project dependencies using the "safety" package
- Verify that all dependencies are pinned to specific versions
- Ensure the application isn't susceptible to supply chain attacks
- Document any allowed low-severity vulnerabilities with justification

#### 2.4. File Path Traversal Security Tests

Path traversal tests verify that the application:
- Prevents access to files outside the intended directories
- Sanitizes file paths to remove potentially malicious components
- Rejects paths with directory traversal sequences (e.g., "../")
- Handles URL-encoded traversal attempts

#### 2.5. Secure Data Export Tests

Data export security tests ensure:
- PDF exports are properly formatted and don't contain unexpected content
- CSV exports properly escape data to prevent formula injection
- Excel exports are created securely without macros or external links
- Temporary files are created with appropriate permissions and deleted after use

This comprehensive security testing approach helps identify and address potential vulnerabilities before they can be exploited. The implementation includes specific test cases for each security concern, with clear assertions to verify that the application meets security requirements.

### 3. Deployment Testing

Deployment testing ensures that the Total Battle Analyzer application can be reliably installed, configured, and run across different environments. The implementation focuses on five critical areas:

#### 3.1. Installation Testing
Installation tests verify that the application and its dependencies can be cleanly installed in various environments. These tests:
- Validate requirements installation in a fresh virtual environment
- Ensure the package itself can be installed in development mode
- Verify the application can initialize without errors
- Check that all required components are properly installed and accessible

#### 3.2. Multi-Platform Compatibility Testing
Multi-platform compatibility tests ensure consistent behavior across operating systems. These tests:
- Verify file path handling works correctly on Windows and Unix systems
- Test CSV file processing with different encodings and line endings
- Ensure German umlauts are handled properly across platforms
- Validate chart rendering and saving on different systems

#### 3.3. Update and Upgrade Testing
Update and upgrade tests verify that the application can be safely updated. These tests:
- Ensure user configurations are preserved during updates
- Validate database schema migrations maintain data integrity
- Test the application's ability to handle different versions of dependencies
- Verify graceful handling of configuration format changes

#### 3.4. Environment Configuration Testing
Environment configuration tests validate the application's adaptability to different deployments. These tests:
- Verify configuration loading from files with appropriate overrides
- Test environment variable integration for deployment-specific settings
- Ensure path normalization works correctly for various configuration scenarios
- Validate fallback behavior when configuration files are missing

#### 3.5. Distribution Package Testing
Distribution package tests ensure the application can be properly packaged for distribution. These tests:
- Verify creation of source distributions (sdist)
- Validate wheel package building and integrity
- Test executable creation with PyInstaller (where applicable)
- Ensure archive creation includes all necessary files and resources

The deployment testing implementation helps ensure that the Total Battle Analyzer application can be reliably deployed, configured, and updated across different environments, providing a smooth experience for users regardless of their operating system or configuration preferences. 