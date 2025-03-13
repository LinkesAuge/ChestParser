# Total Battle Analyzer Refactoring Plan: Phase 5 - Part 3
## Integration Testing Implementation

This document outlines the implementation of comprehensive integration tests for the Total Battle Analyzer application. While unit tests focus on testing individual components in isolation, integration tests focus on testing the interactions between components to ensure they work together correctly.

## Implementation Tasks

- [ ] **Data-to-Service Integration Tests**
  - [ ] Test DataProcessor to AnalysisService workflow
  - [ ] Test DataProcessor to ChartService workflow
  - [ ] Test DataProcessor to ReportService workflow
  - [ ] Test error handling between layers

- [ ] **Service-to-Service Integration Tests**
  - [ ] Test AnalysisService to ChartService interaction
  - [ ] Test AnalysisService to ReportService interaction
  - [ ] Test ChartService to ReportService interaction
  - [ ] Test configuration integration across services

- [ ] **UI-to-Service Integration Tests**
  - [ ] Test UI components with service layer interaction
  - [ ] Test screen interactions with services
  - [ ] Test data flow from UI to services and back
  - [ ] Test error propagation and handling

- [ ] **End-to-End Workflow Tests**
  - [ ] Test import-analyze-visualize-report workflow
  - [ ] Test filter-sort-export workflow
  - [ ] Test configuration save-load workflow
  - [ ] Test complete user journeys

## Implementation Approach

Integration testing for the Total Battle Analyzer will follow these principles:

1. **Component Boundaries**: Tests will focus on the boundaries between components, ensuring data flows correctly.
2. **Realistic Scenarios**: Tests will simulate real-world usage patterns and workflows.
3. **Minimal Mocking**: Only external dependencies will be mocked; internal components will be tested together.
4. **Test Independence**: Each test should be independent and not rely on the state from previous tests.
5. **Clear Error Reporting**: Tests should clearly identify which integration point failed when errors occur.

The implementation will use pytest fixtures to set up the necessary test environment and will follow a structured approach to ensure all integration points are tested thoroughly.

## Implementation Details

### 1. Data-to-Service Integration Tests

This section focuses on testing the interaction between the data layer (DataProcessor) and the various services.

#### DataProcessor to AnalysisService Integration

```python
# tests/integration/data_services/test_data_analysis_integration.py
import pytest
import pandas as pd
from pathlib import Path
from src.modules.dataprocessor import DataProcessor
from src.services.analysis_service import AnalysisService
from src.models.analysis_result import AnalysisResult

class TestDataAnalysisIntegration:
    """Integration tests between DataProcessor and AnalysisService."""
    
    @pytest.fixture
    def data_processor(self):
        """Create a DataProcessor instance for testing."""
        return DataProcessor(debug=False)
    
    @pytest.fixture
    def analysis_service(self):
        """Create an AnalysisService instance for testing."""
        return AnalysisService()
    
    def test_csv_to_analysis_workflow(self, data_processor, analysis_service, small_csv_path):
        """Test the workflow from CSV loading to data analysis."""
        # Load the CSV file
        df = data_processor.read_csv_with_encoding_fix(small_csv_path)
        
        # Verify data was loaded correctly
        assert not df.empty
        assert "PLAYER" in df.columns
        assert "SCORE" in df.columns
        
        # Process the loaded data
        processed_df = data_processor.fix_dataframe_text(df)
        
        # Perform analysis
        analysis_result = analysis_service.analyze(processed_df)
        
        # Verify analysis results
        assert isinstance(analysis_result, AnalysisResult)
        assert analysis_result.player_analysis is not None
        assert analysis_result.chest_analysis is not None
        assert analysis_result.source_analysis is not None
        assert "PLAYER" in analysis_result.player_analysis.columns
        assert "TOTAL_SCORE" in analysis_result.player_analysis.columns
    
    def test_data_filtering_to_analysis(self, data_processor, analysis_service, sample_dataframe):
        """Test data filtering followed by analysis."""
        # Filter data by player
        players = ["Player1", "Player2"]
        filtered_df = data_processor.filter_by_values(
            sample_dataframe, "PLAYER", players
        )
        
        # Verify filtering
        assert set(filtered_df["PLAYER"].unique()) == set(players)
        
        # Analyze filtered data
        analysis_result = analysis_service.analyze(filtered_df)
        
        # Verify analysis of filtered data
        assert len(analysis_result.player_analysis) == len(players)
        assert all(player in analysis_result.player_analysis["PLAYER"].values for player in players)
    
    def test_date_filtering_to_analysis(self, data_processor, analysis_service, sample_dataframe):
        """Test date filtering followed by analysis."""
        # Add a datetime column
        sample_dataframe["DATE_DT"] = pd.to_datetime(sample_dataframe["DATE"])
        
        # Filter for a specific date range
        start_date = pd.to_datetime("2023-01-02")
        end_date = pd.to_datetime("2023-01-04")
        filtered_df = data_processor.filter_by_date_range(
            sample_dataframe, start_date, end_date, "DATE_DT"
        )
        
        # Verify date filtering
        dates = pd.to_datetime(filtered_df["DATE"])
        assert all(start_date <= date <= end_date for date in dates)
        
        # Analyze filtered data
        analysis_result = analysis_service.analyze(filtered_df)
        
        # Verify analysis results reflect date filtering
        assert len(analysis_result.date_analysis) <= 3  # At most 3 dates in the range
    
    def test_error_handling_invalid_data(self, data_processor, analysis_service):
        """Test error handling when invalid data is passed between components."""
        # Create invalid data (missing required columns)
        invalid_df = pd.DataFrame({
            "InvalidColumn": [1, 2, 3],
            "AnotherInvalid": ["a", "b", "c"]
        })
        
        # Attempt to analyze invalid data and expect an appropriate error
        with pytest.raises(Exception) as excinfo:
            analysis_service.analyze(invalid_df)
        
        # Verify error message mentions missing columns
        error_msg = str(excinfo.value).lower()
        assert "column" in error_msg or "missing" in error_msg
```

#### DataProcessor to ChartService Integration

```python
# tests/integration/data_services/test_data_chart_integration.py
import pytest
import pandas as pd
import matplotlib.pyplot as plt
from src.modules.dataprocessor import DataProcessor
from src.visualization.charts.chart_service import ChartService
from src.visualization.charts.chart_configuration import ChartConfiguration

class TestDataChartIntegration:
    """Integration tests between DataProcessor and ChartService."""
    
    @pytest.fixture
    def data_processor(self):
        """Create a DataProcessor instance for testing."""
        return DataProcessor(debug=False)
    
    @pytest.fixture
    def chart_service(self):
        """Create a ChartService instance for testing."""
        return ChartService()
    
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
    
    def test_processed_data_to_chart(self, data_processor, chart_service, 
                                     chart_config, small_csv_path):
        """Test creating a chart from processed CSV data."""
        # Load and process the CSV file
        df = data_processor.read_csv_with_encoding_fix(small_csv_path)
        processed_df = data_processor.fix_dataframe_text(df)
        
        # Verify data was loaded correctly
        assert not processed_df.empty
        assert "PLAYER" in processed_df.columns
        assert "SCORE" in processed_df.columns
        
        # Create a bar chart from the processed data
        fig, ax = chart_service.create_bar_chart(
            processed_df, "PLAYER", "SCORE", chart_config
        )
        
        # Verify chart was created successfully
        assert fig is not None
        assert ax is not None
        assert ax.get_title() == "Test Chart"
        
        # Clean up
        plt.close(fig)
    
    def test_analyzed_data_to_chart(self, data_processor, chart_service, 
                                   chart_config, sample_dataframe):
        """Test creating a chart from analyzed data."""
        # Analyze the data
        analysis_results = data_processor.analyze_data(sample_dataframe)
        
        # Verify analysis results exist
        assert "player_totals" in analysis_results
        player_totals = analysis_results["player_totals"]
        
        # Create a chart from the analysis results
        fig, ax = chart_service.create_bar_chart(
            player_totals, "PLAYER", "TOTAL_SCORE", chart_config
        )
        
        # Verify chart was created successfully
        assert fig is not None
        assert ax is not None
        assert ax.get_title() == "Test Chart"
        
        # Clean up
        plt.close(fig)
    
    def test_filtered_analyzed_data_to_chart(self, data_processor, chart_service, 
                                            chart_config, sample_dataframe):
        """Test creating a chart from filtered and analyzed data."""
        # Filter data by player
        players = ["Player1", "Player2"]
        filtered_df = data_processor.filter_by_values(
            sample_dataframe, "PLAYER", players
        )
        
        # Analyze filtered data
        analysis_results = data_processor.analyze_data(filtered_df)
        player_totals = analysis_results["player_totals"]
        
        # Verify filtering and analysis
        assert all(player in player_totals["PLAYER"].values for player in players)
        
        # Create a chart from the filtered analysis results
        fig, ax = chart_service.create_bar_chart(
            player_totals, "PLAYER", "TOTAL_SCORE", chart_config
        )
        
        # Verify chart was created successfully and reflects filtering
        assert fig is not None
        assert ax is not None
        assert len(ax.patches) == len(players)  # Only filtered players should be in the chart
        
        # Clean up
        plt.close(fig)
```

#### DataProcessor to ReportService Integration

```python
# tests/integration/data_services/test_data_report_integration.py
import pytest
import pandas as pd
from pathlib import Path
import tempfile
from src.modules.dataprocessor import DataProcessor
from src.visualization.reports.html_report_service import HTMLReportService

class TestDataReportIntegration:
    """Integration tests between DataProcessor and ReportService."""
    
    @pytest.fixture
    def data_processor(self):
        """Create a DataProcessor instance for testing."""
        return DataProcessor(debug=False)
    
    @pytest.fixture
    def report_service(self):
        """Create a ReportService instance for testing."""
        return HTMLReportService()
    
    def test_processed_data_to_report(self, data_processor, report_service, 
                                     small_csv_path, temp_test_dir):
        """Test creating a report from processed CSV data."""
        # Load and process the CSV file
        df = data_processor.read_csv_with_encoding_fix(small_csv_path)
        processed_df = data_processor.fix_dataframe_text(df)
        
        # Verify data was loaded correctly
        assert not processed_df.empty
        
        # Create a simple report from the processed data
        report_title = "Data Report"
        table_content = report_service.create_table(
            processed_df, title="Processed Data"
        )
        
        report_content = report_service.create_report(
            title=report_title,
            sections=[table_content],
            header_content="Test Header",
            footer_content="Test Footer"
        )
        
        # Verify report content
        assert report_title in report_content
        assert "Processed Data" in report_content
        assert "PLAYER" in report_content
        assert "SCORE" in report_content
        
        # Export the report
        report_path = temp_test_dir / "test_report.html"
        report_service.export_report(report_content, report_path)
        
        # Verify report was exported successfully
        assert report_path.exists()
        assert report_path.stat().st_size > 0
    
    def test_analyzed_data_to_report(self, data_processor, report_service, 
                                    sample_dataframe, temp_test_dir):
        """Test creating a report from analyzed data."""
        # Analyze the data
        analysis_results = data_processor.analyze_data(sample_dataframe)
        
        # Verify analysis results exist
        assert "player_totals" in analysis_results
        player_totals = analysis_results["player_totals"]
        
        # Create a report section from analysis results
        player_section = report_service.create_section(
            title="Player Analysis",
            content=report_service.create_table(
                player_totals, title="Player Performance"
            )
        )
        
        # Create the full report
        report_content = report_service.create_report(
            title="Analysis Report",
            sections=[player_section]
        )
        
        # Verify report content
        assert "Analysis Report" in report_content
        assert "Player Analysis" in report_content
        assert "Player Performance" in report_content
        assert "TOTAL_SCORE" in report_content
        
        # Export the report
        report_path = temp_test_dir / "analysis_report.html"
        report_service.export_report(report_content, report_path)
        
        # Verify report was exported successfully
        assert report_path.exists()
        assert report_path.stat().st_size > 0
    
    def test_error_handling_invalid_export(self, data_processor, report_service,
                                          sample_dataframe):
        """Test error handling when exporting to an invalid location."""
        # Analyze the data
        analysis_results = data_processor.analyze_data(sample_dataframe)
        player_totals = analysis_results["player_totals"]
        
        # Create a simple report
        report_content = report_service.create_report(
            title="Test Report",
            sections=[report_service.create_table(player_totals)]
        )
        
        # Try to export to an invalid location
        invalid_path = Path("/nonexistent_directory/report.html")
        
        # Verify appropriate error is raised
        with pytest.raises(Exception) as excinfo:
            report_service.export_report(report_content, invalid_path)
        
        # Check error message
        error_msg = str(excinfo.value).lower()
        assert "export" in error_msg or "save" in error_msg or "write" in error_msg or "permission" in error_msg 
```

### 2. Service-to-Service Integration Tests

This section focuses on testing how the different services interact with each other to ensure they work together seamlessly.

#### AnalysisService to ChartService Integration

```python
# tests/integration/services/test_analysis_chart_integration.py
import pytest
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from src.services.analysis_service import AnalysisService
from src.services.config_service import ConfigService
from src.visualization.charts.chart_service import ChartService
from src.visualization.charts.chart_configuration import ChartConfiguration

class TestAnalysisChartIntegration:
    """Integration tests between AnalysisService and ChartService."""
    
    @pytest.fixture
    def analysis_service(self):
        """Create an AnalysisService instance for testing."""
        return AnalysisService()
    
    @pytest.fixture
    def chart_service(self):
        """Create a ChartService instance for testing."""
        return ChartService()
    
    @pytest.fixture
    def config_service(self):
        """Create a ConfigService instance for testing."""
        return ConfigService()
    
    def test_player_analysis_to_chart(self, analysis_service, chart_service, sample_dataframe):
        """Test creating a chart from player analysis results."""
        # Perform analysis
        analysis_result = analysis_service.analyze(sample_dataframe)
        
        # Verify analysis was successful
        assert analysis_result.player_analysis is not None
        assert "PLAYER" in analysis_result.player_analysis.columns
        assert "TOTAL_SCORE" in analysis_result.player_analysis.columns
        
        # Create a chart configuration
        chart_config = ChartConfiguration(
            chart_type="bar",
            title="Player Score Analysis",
            x_label="Player",
            y_label="Total Score",
            show_values=True
        )
        
        # Create a chart from the analysis results
        fig, ax = chart_service.create_bar_chart(
            analysis_result.player_analysis, 
            x_column="PLAYER", 
            y_column="TOTAL_SCORE",
            config=chart_config
        )
        
        # Verify chart was created successfully
        assert fig is not None
        assert ax is not None
        assert ax.get_title() == "Player Score Analysis"
        assert ax.get_xlabel() == "Player"
        assert ax.get_ylabel() == "Total Score"
        
        # Clean up
        plt.close(fig)
    
    def test_chest_analysis_to_pie_chart(self, analysis_service, chart_service, sample_dataframe):
        """Test creating a pie chart from chest analysis results."""
        # Perform analysis
        analysis_result = analysis_service.analyze(sample_dataframe)
        
        # Verify analysis was successful
        assert analysis_result.chest_analysis is not None
        assert "CHEST_TYPE" in analysis_result.chest_analysis.columns
        assert "COUNT" in analysis_result.chest_analysis.columns
        
        # Create a chart configuration
        chart_config = ChartConfiguration(
            chart_type="pie",
            title="Chest Distribution",
            show_values=True,
            show_legend=True
        )
        
        # Create a pie chart from the analysis results
        fig, ax = chart_service.create_pie_chart(
            analysis_result.chest_analysis,
            label_column="CHEST_TYPE",
            value_column="COUNT",
            config=chart_config
        )
        
        # Verify chart was created successfully
        assert fig is not None
        assert ax is not None
        assert ax.get_title() == "Chest Distribution"
        
        # Clean up
        plt.close(fig)
    
    def test_time_trend_analysis_to_line_chart(self, analysis_service, chart_service, sample_dataframe):
        """Test creating a line chart from time trend analysis results."""
        # Add date column for time analysis
        sample_dataframe["DATE_DT"] = pd.to_datetime(sample_dataframe["DATE"])
        
        # Perform analysis
        analysis_result = analysis_service.analyze(sample_dataframe)
        
        # Verify time analysis was successful
        assert analysis_result.date_analysis is not None
        assert "DATE" in analysis_result.date_analysis.columns
        assert "TOTAL_SCORE" in analysis_result.date_analysis.columns
        
        # Create a chart configuration
        chart_config = ChartConfiguration(
            chart_type="line",
            title="Score Trend Over Time",
            x_label="Date",
            y_label="Total Score",
            show_grid=True,
            show_markers=True
        )
        
        # Create a line chart from the analysis results
        fig, ax = chart_service.create_line_chart(
            analysis_result.date_analysis,
            x_column="DATE",
            y_column="TOTAL_SCORE",
            config=chart_config
        )
        
        # Verify chart was created successfully
        assert fig is not None
        assert ax is not None
        assert ax.get_title() == "Score Trend Over Time"
        assert ax.get_xlabel() == "Date"
        assert ax.get_ylabel() == "Total Score"
        
        # Clean up
        plt.close(fig)
    
    def test_analysis_with_configured_chart_styles(self, analysis_service, chart_service, 
                                                 config_service, sample_dataframe):
        """Test creating charts with styles loaded from configuration."""
        # Create and save a custom chart configuration
        config_service.save_setting(
            "chart_styles", 
            {
                "theme": "dark",
                "colors": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"],
                "dpi": 150,
                "figure_size": [10, 6]
            }
        )
        
        # Load the chart style settings
        chart_styles = config_service.get_setting("chart_styles")
        
        # Perform analysis
        analysis_result = analysis_service.analyze(sample_dataframe)
        
        # Create a chart configuration with the loaded styles
        chart_config = ChartConfiguration(
            chart_type="bar",
            title="Styled Player Analysis",
            x_label="Player",
            y_label="Score",
            theme=chart_styles.get("theme"),
            colors=chart_styles.get("colors"),
            dpi=chart_styles.get("dpi"),
            figure_size=chart_styles.get("figure_size")
        )
        
        # Create a chart from the analysis results with the loaded styles
        fig, ax = chart_service.create_bar_chart(
            analysis_result.player_analysis,
            x_column="PLAYER",
            y_column="TOTAL_SCORE",
            config=chart_config
        )
        
        # Verify chart was created successfully with the correct styles
        assert fig is not None
        assert ax is not None
        assert fig.get_dpi() == 150
        assert fig.get_size_inches().tolist() == [10, 6]
        
        # Clean up
        plt.close(fig)
```

#### AnalysisService to ReportService Integration

```python
# tests/integration/services/test_analysis_report_integration.py
import pytest
import pandas as pd
from pathlib import Path
from src.services.analysis_service import AnalysisService
from src.visualization.reports.html_report_service import HTMLReportService
from src.visualization.reports.markdown_report_service import MarkdownReportService

class TestAnalysisReportIntegration:
    """Integration tests between AnalysisService and ReportService."""
    
    @pytest.fixture
    def analysis_service(self):
        """Create an AnalysisService instance for testing."""
        return AnalysisService()
    
    @pytest.fixture
    def html_report_service(self):
        """Create an HTML ReportService instance for testing."""
        return HTMLReportService()
    
    @pytest.fixture
    def markdown_report_service(self):
        """Create a Markdown ReportService instance for testing."""
        return MarkdownReportService()
    
    def test_analysis_to_html_report(self, analysis_service, html_report_service, 
                                   sample_dataframe, temp_test_dir):
        """Test creating an HTML report from analysis results."""
        # Perform analysis
        analysis_result = analysis_service.analyze(sample_dataframe)
        
        # Create report sections for each analysis component
        player_section = html_report_service.create_section(
            title="Player Analysis",
            content=html_report_service.create_table(
                analysis_result.player_analysis, 
                title="Player Performance"
            )
        )
        
        chest_section = html_report_service.create_section(
            title="Chest Analysis",
            content=html_report_service.create_table(
                analysis_result.chest_analysis,
                title="Chest Distribution"
            )
        )
        
        source_section = html_report_service.create_section(
            title="Source Analysis",
            content=html_report_service.create_table(
                analysis_result.source_analysis,
                title="Source Performance"
            )
        )
        
        # Create full report
        report_content = html_report_service.create_report(
            title="Total Battle Analysis Report",
            sections=[player_section, chest_section, source_section],
            header_content="Analysis performed on sample data",
            footer_content="Generated by Total Battle Analyzer"
        )
        
        # Verify report content
        assert "Total Battle Analysis Report" in report_content
        assert "Player Analysis" in report_content
        assert "Chest Analysis" in report_content
        assert "Source Analysis" in report_content
        
        # Export the report
        report_path = temp_test_dir / "analysis_report.html"
        html_report_service.export_report(report_content, report_path)
        
        # Verify report was exported successfully
        assert report_path.exists()
        assert report_path.stat().st_size > 0
    
    def test_analysis_to_markdown_report(self, analysis_service, markdown_report_service,
                                       sample_dataframe, temp_test_dir):
        """Test creating a Markdown report from analysis results."""
        # Perform analysis
        analysis_result = analysis_service.analyze(sample_dataframe)
        
        # Create report sections for each analysis component
        player_section = markdown_report_service.create_section(
            title="Player Analysis",
            content=markdown_report_service.create_table(
                analysis_result.player_analysis.head(5),  # Limit to 5 rows for brevity
                title="Player Performance (Top 5)"
            )
        )
        
        chest_section = markdown_report_service.create_section(
            title="Chest Analysis",
            content=markdown_report_service.create_table(
                analysis_result.chest_analysis,
                title="Chest Distribution"
            )
        )
        
        # Create a statistics section
        player_stats = {
            "Total Players": len(analysis_result.player_analysis),
            "Average Score": analysis_result.player_analysis["TOTAL_SCORE"].mean(),
            "Max Score": analysis_result.player_analysis["TOTAL_SCORE"].max(),
            "Min Score": analysis_result.player_analysis["TOTAL_SCORE"].min()
        }
        
        stats_section = markdown_report_service.create_section(
            title="Summary Statistics",
            content=markdown_report_service.create_statistics(player_stats)
        )
        
        # Create full report
        report_content = markdown_report_service.create_report(
            title="Total Battle Analysis Summary",
            sections=[stats_section, player_section, chest_section],
            header_content="## Analysis Summary\n\nThis report summarizes the analysis results.",
            footer_content="*Generated by Total Battle Analyzer*"
        )
        
        # Verify report content
        assert "# Total Battle Analysis Summary" in report_content
        assert "## Summary Statistics" in report_content
        assert "## Player Analysis" in report_content
        assert "## Chest Analysis" in report_content
        assert "Total Players" in report_content
        assert "Average Score" in report_content
        
        # Export the report
        report_path = temp_test_dir / "analysis_summary.md"
        markdown_report_service.export_report(report_content, report_path)
        
        # Verify report was exported successfully
        assert report_path.exists()
        assert report_path.stat().st_size > 0
    
    def test_filtered_analysis_to_report(self, analysis_service, html_report_service,
                                       sample_dataframe, temp_test_dir):
        """Test creating a report from filtered analysis results."""
        # Filter the dataframe
        player_filter = "Player1"
        filtered_df = sample_dataframe[sample_dataframe["PLAYER"] == player_filter]
        
        # Perform analysis on filtered data
        analysis_result = analysis_service.analyze(filtered_df)
        
        # Create a single section report for the filtered player
        player_section = html_report_service.create_section(
            title=f"Analysis for {player_filter}",
            content=html_report_service.create_table(
                analysis_result.player_analysis,
                title=f"{player_filter} Performance"
            )
        )
        
        # Add a section for chest distribution
        chest_section = html_report_service.create_section(
            title=f"Chest Distribution for {player_filter}",
            content=html_report_service.create_table(
                analysis_result.chest_analysis,
                title="Chest Types Received"
            )
        )
        
        # Create full report
        report_content = html_report_service.create_report(
            title=f"Player Report: {player_filter}",
            sections=[player_section, chest_section]
        )
        
        # Verify report content is specific to the filtered player
        assert f"Player Report: {player_filter}" in report_content
        assert f"Analysis for {player_filter}" in report_content
        assert f"{player_filter} Performance" in report_content
        
        # Export the report
        report_path = temp_test_dir / f"player_{player_filter}_report.html"
        html_report_service.export_report(report_content, report_path)
        
        # Verify report was exported successfully
        assert report_path.exists()
        assert report_path.stat().st_size > 0
```

#### ChartService to ReportService Integration

```python
# tests/integration/services/test_chart_report_integration.py
import pytest
import pandas as pd
import tempfile
from pathlib import Path
import matplotlib.pyplot as plt
from src.visualization.charts.chart_service import ChartService
from src.visualization.charts.chart_configuration import ChartConfiguration
from src.visualization.reports.html_report_service import HTMLReportService

class TestChartReportIntegration:
    """Integration tests between ChartService and ReportService."""
    
    @pytest.fixture
    def chart_service(self):
        """Create a ChartService instance for testing."""
        return ChartService()
    
    @pytest.fixture
    def report_service(self):
        """Create a ReportService instance for testing."""
        return HTMLReportService()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for chart creation."""
        return pd.DataFrame({
            "Category": ["A", "B", "C", "D", "E"],
            "Value": [23, 45, 56, 78, 32],
            "Group": ["Group1", "Group2", "Group1", "Group2", "Group1"]
        })
    
    def test_embed_chart_in_report(self, chart_service, report_service, 
                                sample_data, temp_test_dir):
        """Test embedding a chart in an HTML report."""
        # Create a chart
        chart_config = ChartConfiguration(
            chart_type="bar",
            title="Sample Bar Chart",
            x_label="Category",
            y_label="Value",
            show_values=True
        )
        
        fig, ax = chart_service.create_bar_chart(
            sample_data, "Category", "Value", chart_config
        )
        
        # Save the chart to a file
        chart_path = temp_test_dir / "sample_chart.png"
        chart_service.save_chart(fig, chart_path)
        
        # Verify chart was saved
        assert chart_path.exists()
        
        # Create a report with the embedded chart
        chart_section = report_service.create_section(
            title="Chart Analysis",
            content=report_service.create_chart(chart_path, "Sample Chart")
        )
        
        # Add a data table section
        table_section = report_service.create_section(
            title="Data Table",
            content=report_service.create_table(sample_data, "Raw Data")
        )
        
        # Create the full report
        report_content = report_service.create_report(
            title="Chart and Data Report",
            sections=[chart_section, table_section]
        )
        
        # Verify chart reference is in the report
        assert "Chart Analysis" in report_content
        assert "Sample Chart" in report_content
        assert "sample_chart.png" in report_content or chart_path.name in report_content
        
        # Export the report
        report_path = temp_test_dir / "chart_report.html"
        report_service.export_report(report_content, report_path)
        
        # Verify report was created successfully
        assert report_path.exists()
        
        # Clean up
        plt.close(fig)
    
    def test_multiple_charts_in_report(self, chart_service, report_service, 
                                     sample_data, temp_test_dir):
        """Test including multiple charts in a single report."""
        # Create a bar chart
        bar_config = ChartConfiguration(
            chart_type="bar",
            title="Bar Chart",
            x_label="Category",
            y_label="Value"
        )
        
        bar_fig, bar_ax = chart_service.create_bar_chart(
            sample_data, "Category", "Value", bar_config
        )
        
        bar_path = temp_test_dir / "bar_chart.png"
        chart_service.save_chart(bar_fig, bar_path)
        
        # Create a pie chart
        pie_config = ChartConfiguration(
            chart_type="pie",
            title="Pie Chart",
            show_values=True
        )
        
        pie_fig, pie_ax = chart_service.create_pie_chart(
            sample_data, "Category", "Value", pie_config
        )
        
        pie_path = temp_test_dir / "pie_chart.png"
        chart_service.save_chart(pie_fig, pie_path)
        
        # Create a line chart
        line_config = ChartConfiguration(
            chart_type="line",
            title="Line Chart",
            x_label="Category",
            y_label="Value",
            show_markers=True
        )
        
        line_fig, line_ax = chart_service.create_line_chart(
            sample_data, "Category", "Value", line_config
        )
        
        line_path = temp_test_dir / "line_chart.png"
        chart_service.save_chart(line_fig, line_path)
        
        # Create a report with all three charts
        bar_section = report_service.create_section(
            title="Bar Chart Analysis",
            content=report_service.create_chart(bar_path, "Category Comparison")
        )
        
        pie_section = report_service.create_section(
            title="Pie Chart Analysis",
            content=report_service.create_chart(pie_path, "Category Distribution")
        )
        
        line_section = report_service.create_section(
            title="Line Chart Analysis",
            content=report_service.create_chart(line_path, "Value Trend")
        )
        
        # Create the full report
        report_content = report_service.create_report(
            title="Multi-Chart Visualization Report",
            sections=[bar_section, pie_section, line_section],
            header_content="<h2>Data Visualization Analysis</h2><p>This report contains multiple chart types.</p>"
        )
        
        # Verify all charts are referenced in the report
        assert "Bar Chart Analysis" in report_content
        assert "Pie Chart Analysis" in report_content
        assert "Line Chart Analysis" in report_content
        assert "bar_chart.png" in report_content or bar_path.name in report_content
        assert "pie_chart.png" in report_content or pie_path.name in report_content
        assert "line_chart.png" in report_content or line_path.name in report_content
        
        # Export the report
        report_path = temp_test_dir / "multi_chart_report.html"
        report_service.export_report(report_content, report_path)
        
        # Verify report was created successfully
        assert report_path.exists()
        
        # Clean up
        plt.close(bar_fig)
        plt.close(pie_fig)
        plt.close(line_fig)
```

### 3. UI-to-Service Integration Tests

This section focuses on testing the integration between UI components and the service layer, ensuring that user interactions properly translate to service calls and data updates.

#### Screen-to-Service Integration

```python
# tests/integration/ui_services/test_screen_service_integration.py
import pytest
from pytest_mock import MockerFixture
from PyQt6.QtWidgets import QApplication
import sys
from pathlib import Path
import pandas as pd
from src.ui.screens.import_screen import ImportScreen
from src.ui.screens.raw_data_screen import RawDataScreen
from src.ui.screens.analysis_screen import AnalysisScreen
from src.services.data_service import DataService
from src.services.analysis_service import AnalysisService
from src.services.config_service import ConfigService

# Create a QApplication instance for UI tests
@pytest.fixture(scope="session")
def app():
    """Create a QApplication instance for UI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # No need to call app.quit() as pytest will handle cleanup

class TestScreenServiceIntegration:
    """Tests for integration between UI screens and services."""
    
    @pytest.fixture
    def data_service(self):
        """Create a DataService instance for testing."""
        return DataService()
    
    @pytest.fixture
    def analysis_service(self):
        """Create an AnalysisService instance for testing."""
        return AnalysisService()
    
    @pytest.fixture
    def config_service(self):
        """Create a ConfigService instance for testing."""
        return ConfigService()
    
    @pytest.fixture
    def sample_csv_path(self, tmp_path):
        """Create a sample CSV file for testing."""
        # Create a temporary CSV file with test data
        csv_path = tmp_path / "test_data.csv"
        sample_data = pd.DataFrame({
            "PLAYER": ["Player1", "Player2", "Player3"],
            "CHEST": ["Gold", "Silver", "Bronze"],
            "SOURCE": ["A", "B", "C"],
            "SCORE": [100, 150, 75],
            "DATE": ["2023-01-01", "2023-01-02", "2023-01-03"]
        })
        sample_data.to_csv(csv_path, index=False)
        return csv_path
    
    def test_import_screen_file_loading(self, app, data_service, config_service, 
                                      sample_csv_path, mocker: MockerFixture):
        """Test that the Import Screen correctly loads a CSV file using DataService."""
        # Create an ImportScreen instance
        import_screen = ImportScreen(data_service, config_service)
        
        # Mock the file dialog to return our sample CSV path
        mocker.patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName', 
                    return_value=(str(sample_csv_path), "CSV files (*.csv)"))
        
        # Simulate button click to select file
        import_screen.file_selector.select_file_button.click()
        
        # Verify that the file path was correctly set
        assert import_screen.file_selector.file_path_edit.text() == str(sample_csv_path)
        
        # Verify that the preview data was loaded
        assert import_screen.preview_data is not None
        assert "PLAYER" in import_screen.preview_data.columns
        assert "SCORE" in import_screen.preview_data.columns
        
        # Mock the import method to capture calls
        import_method_mock = mocker.patch.object(data_service, 'import_data', return_value=True)
        
        # Simulate import button click
        import_screen.import_button.click()
        
        # Verify that the DataService's import_data method was called with the correct file path
        import_method_mock.assert_called_once_with(sample_csv_path)
    
    def test_raw_data_screen_data_loading(self, app, data_service, mocker: MockerFixture):
        """Test that the Raw Data Screen correctly loads and displays data."""
        # Create sample data that would be returned by the data service
        sample_data = pd.DataFrame({
            "PLAYER": ["Player1", "Player2", "Player3"],
            "CHEST": ["Gold", "Silver", "Bronze"],
            "SOURCE": ["A", "B", "C"],
            "SCORE": [100, 150, 75],
            "DATE": ["2023-01-01", "2023-01-02", "2023-01-03"]
        })
        
        # Mock the get_data method to return our sample data
        mocker.patch.object(data_service, 'get_data', return_value=sample_data)
        
        # Create a RawDataScreen instance
        raw_data_screen = RawDataScreen(data_service)
        
        # Load the data
        raw_data_screen.load_data()
        
        # Verify the data was loaded correctly
        assert raw_data_screen.data_table.rowCount() == 3  # 3 rows in our sample data
        assert raw_data_screen.data_table.columnCount() == 5  # 5 columns in our sample data
        
        # Test filter functionality
        # Mock the filter_by_values method to return filtered data
        filtered_data = sample_data[sample_data["PLAYER"] == "Player1"]
        mocker.patch.object(data_service, 'filter_by_values', return_value=filtered_data)
        
        # Set up filter criteria and apply
        raw_data_screen.filter_panel.add_filter("PLAYER", "Player1")
        raw_data_screen.apply_filters_button.click()
        
        # Verify that the DataService's filter_by_values method was called
        # and the filtered data is correctly displayed
        assert raw_data_screen.data_table.rowCount() == 1  # Only 1 row after filtering
    
    def test_analysis_screen_integration(self, app, data_service, analysis_service, 
                                       mocker: MockerFixture):
        """Test the integration between Analysis Screen and analysis services."""
        # Create sample data and analysis results
        sample_data = pd.DataFrame({
            "PLAYER": ["Player1", "Player2", "Player3", "Player1"],
            "CHEST": ["Gold", "Silver", "Bronze", "Gold"],
            "SOURCE": ["A", "B", "C", "A"],
            "SCORE": [100, 150, 75, 120],
            "DATE": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"]
        })
        
        # Player analysis result should include aggregated data
        player_analysis = pd.DataFrame({
            "PLAYER": ["Player1", "Player2", "Player3"],
            "TOTAL_SCORE": [220, 150, 75],
            "CHEST_COUNT": [2, 1, 1]
        })
        
        # Create analysis result mock
        class MockAnalysisResult:
            def __init__(self):
                self.player_analysis = player_analysis
                self.chest_analysis = pd.DataFrame({"CHEST_TYPE": ["Gold", "Silver", "Bronze"], 
                                                  "COUNT": [2, 1, 1]})
                self.source_analysis = pd.DataFrame({"SOURCE": ["A", "B", "C"], 
                                                   "TOTAL_SCORE": [220, 150, 75]})
                self.date_analysis = pd.DataFrame({"DATE": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"], 
                                                 "TOTAL_SCORE": [100, 150, 75, 120]})
        
        # Mock service methods
        mocker.patch.object(data_service, 'get_data', return_value=sample_data)
        mocker.patch.object(analysis_service, 'analyze', return_value=MockAnalysisResult())
        
        # Create an AnalysisScreen instance
        analysis_screen = AnalysisScreen(data_service, analysis_service)
        
        # Load the data and perform analysis
        analysis_screen.load_data()
        analysis_screen.analyze_button.click()
        
        # Verify that the analysis results are displayed correctly
        assert analysis_screen.player_table.rowCount() == 3  # 3 players in results
        assert analysis_screen.chest_table.rowCount() == 3  # 3 chest types
        assert analysis_screen.source_table.rowCount() == 3  # 3 sources
        
        # Verify player totals for specific player
        player1_row = 0  # Assuming Player1 is in the first row
        player1_total_col = 1  # Assuming TOTAL_SCORE is second column
        player1_total = analysis_screen.player_table.item(player1_row, player1_total_col).text()
        assert player1_total == "220"  # Total score for Player1
```

#### UI Components to Service Integration

```python
# tests/integration/ui_services/test_widgets_service_integration.py
import pytest
from pytest_mock import MockerFixture
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import Qt
import sys
import pandas as pd
from src.ui.widgets.data_table_widget import DataTableWidget
from src.ui.widgets.chart_widget import ChartWidget
from src.ui.widgets.filter_panel import FilterPanel
from src.services.data_service import DataService
from src.visualization.charts.chart_service import ChartService
from src.visualization.charts.chart_configuration import ChartConfiguration

@pytest.fixture(scope="session")
def app():
    """Create a QApplication instance for UI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # No need to call app.quit() as pytest will handle cleanup

@pytest.fixture
def main_window(app):
    """Create a QMainWindow for hosting widgets during tests."""
    window = QMainWindow()
    window.setGeometry(100, 100, 800, 600)
    yield window
    window.close()

class TestWidgetsServiceIntegration:
    """Tests for integration between UI widgets and services."""
    
    @pytest.fixture
    def data_service(self):
        """Create a DataService instance for testing."""
        return DataService()
    
    @pytest.fixture
    def chart_service(self):
        """Create a ChartService instance for testing."""
        return ChartService()
    
    @pytest.fixture
    def sample_data(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame({
            "PLAYER": ["Player1", "Player2", "Player3", "Player1"],
            "CHEST": ["Gold", "Silver", "Bronze", "Gold"],
            "SOURCE": ["A", "B", "C", "A"],
            "SCORE": [100, 150, 75, 120],
            "DATE": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"]
        })
    
    def test_data_table_widget_service_integration(self, main_window, data_service, 
                                                sample_data, mocker: MockerFixture):
        """Test DataTableWidget integration with DataService."""
        # Create the DataTableWidget
        data_table = DataTableWidget(main_window)
        main_window.setCentralWidget(data_table)
        
        # Mock the sort_by_column method to return sorted data
        sorted_data = sample_data.sort_values(by="SCORE", ascending=False)
        mocker.patch.object(data_service, 'sort_by_column', return_value=sorted_data)
        
        # Load data into the table
        data_table.load_data(sample_data)
        
        # Verify data was loaded correctly
        assert data_table.rowCount() == 4  # 4 rows in sample data
        assert data_table.columnCount() == 5  # 5 columns in sample data
        
        # Simulate a header click to sort by SCORE
        score_column_index = sample_data.columns.get_loc("SCORE")
        data_table.horizontalHeader().sectionClicked.emit(score_column_index)
        
        # Connect to the DataService to perform sorting
        data_table.sort_requested.connect(
            lambda col, order: data_table.load_data(
                data_service.sort_by_column(sample_data, col, order == Qt.SortOrder.AscendingOrder)
            )
        )
        
        # Trigger sorting
        data_table.horizontalHeader().sectionClicked.emit(score_column_index)
        
        # Verify that data is sorted in descending order
        first_row_value = data_table.item(0, score_column_index).text()
        assert first_row_value == "150"  # Highest SCORE value
    
    def test_chart_widget_service_integration(self, main_window, chart_service, 
                                           sample_data, mocker: MockerFixture):
        """Test ChartWidget integration with ChartService."""
        # Create the ChartWidget
        chart_widget = ChartWidget(main_window)
        main_window.setCentralWidget(chart_widget)
        
        # Mock the ChartService.create_bar_chart method
        # We'll simulate returning a Matplotlib figure and axes
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        mocker.patch.object(chart_service, 'create_bar_chart', return_value=(fig, ax))
        
        # Create a chart configuration
        chart_config = ChartConfiguration(
            chart_type="bar",
            title="Test Chart",
            x_label="Player",
            y_label="Score",
            show_values=True
        )
        
        # Update the chart using the service
        chart_widget.update_chart(
            chart_service.create_bar_chart(
                sample_data, "PLAYER", "SCORE", chart_config
            )
        )
        
        # Verify the chart service was called with correct parameters
        chart_service.create_bar_chart.assert_called_once()
        args, kwargs = chart_service.create_bar_chart.call_args
        assert args[0] is sample_data
        assert args[1] == "PLAYER"
        assert args[2] == "SCORE"
        
        # Cleanup
        plt.close(fig)
    
    def test_filter_panel_data_service_integration(self, main_window, data_service, 
                                                sample_data, mocker: MockerFixture):
        """Test FilterPanel integration with DataService."""
        # Create the FilterPanel
        filter_panel = FilterPanel(main_window)
        main_window.setCentralWidget(filter_panel)
        
        # Initialize the filter panel with available columns from the sample data
        filter_panel.set_available_columns(sample_data.columns.tolist())
        
        # Mock the filter_by_values method to return filtered data
        filtered_data = sample_data[sample_data["PLAYER"] == "Player1"]
        mocker.patch.object(data_service, 'filter_by_values', return_value=filtered_data)
        
        # Add filter criteria
        filter_panel.add_filter("PLAYER", "Player1")
        
        # Create a slot to handle filter requests
        def apply_filter():
            filters = filter_panel.get_filters()
            if filters:
                # Apply the first filter as an example
                filter_col, filter_val = filters[0]
                return data_service.filter_by_values(sample_data, filter_col, [filter_val])
            return sample_data
        
        # Connect the filter applied signal to our slot
        filter_panel.filter_changed.connect(apply_filter)
        
        # Simulate applying the filter
        filtered_result = apply_filter()
        
        # Verify the filtered data
        assert len(filtered_result) == 2  # There are 2 rows with Player1
        assert all(row["PLAYER"] == "Player1" for _, row in filtered_result.iterrows())
        
        # Verify the DataService was called with correct parameters
        data_service.filter_by_values.assert_called_once()
        args, kwargs = data_service.filter_by_values.call_args
        assert args[0] is sample_data
        assert args[1] == "PLAYER"
        assert args[2] == ["Player1"]
```

### 4. End-to-End Workflow Tests

This section focuses on testing complete user workflows that span multiple components, ensuring that the entire application functions correctly as an integrated system.

#### Import-Analyze-Visualize-Report Workflow

```python
# tests/integration/workflows/test_import_analyze_report_workflow.py
import pytest
from pytest_mock import MockerFixture
from PyQt6.QtWidgets import QApplication
import sys
import pandas as pd
from pathlib import Path
import tempfile
import shutil
from src.ui.main_window import MainWindow
from src.ui.screens.screen_manager import ScreenManager
from src.services.data_service import DataService
from src.services.analysis_service import AnalysisService
from src.services.config_service import ConfigService
from src.visualization.charts.chart_service import ChartService
from src.visualization.reports.html_report_service import HTMLReportService

@pytest.fixture(scope="session")
def app():
    """Create a QApplication instance for UI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app

class TestImportAnalyzeReportWorkflow:
    """Test the complete workflow from data import to report generation."""
    
    @pytest.fixture
    def test_data_dir(self, tmp_path):
        """Create a temporary directory with test data files."""
        # Create a test CSV file
        csv_path = tmp_path / "test_data.csv"
        sample_data = pd.DataFrame({
            "PLAYER": ["Player1", "Player2", "Player3", "Player1"],
            "CHEST": ["Gold", "Silver", "Bronze", "Gold"],
            "SOURCE": ["A", "B", "C", "A"],
            "SCORE": [100, 150, 75, 120],
            "DATE": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"]
        })
        sample_data.to_csv(csv_path, index=False)
        
        # Create an output directory for reports
        output_dir = tmp_path / "output"
        output_dir.mkdir(exist_ok=True)
        
        return tmp_path
    
    def test_end_to_end_workflow(self, app, test_data_dir, mocker: MockerFixture):
        """Test the complete workflow from data import to report generation."""
        # Initialize services
        data_service = DataService()
        analysis_service = AnalysisService()
        config_service = ConfigService()
        chart_service = ChartService()
        report_service = HTMLReportService()
        
        # Mock file operations to use our test data
        csv_path = test_data_dir / "test_data.csv"
        output_path = test_data_dir / "output" / "analysis_report.html"
        
        # Mock the QFileDialog to return our test CSV path
        mocker.patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName', 
                    return_value=(str(csv_path), "CSV files (*.csv)"))
        
        # Mock the QFileDialog for saving to return our output path
        mocker.patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName', 
                    return_value=(str(output_path), "HTML files (*.html)"))
        
        # Create screen manager and main window
        screen_manager = ScreenManager()
        main_window = MainWindow(
            screen_manager, data_service, analysis_service, 
            config_service, chart_service, report_service
        )
        
        # 1. STEP 1: Navigate to Import Screen and import data
        main_window.show_screen("import")
        import_screen = main_window.current_screen
        
        # Select file and load preview
        import_screen.file_selector.select_file_button.click()
        
        # Mock file loading and import operations
        mock_df = pd.read_csv(csv_path)
        mocker.patch.object(data_service, 'load_csv_preview', return_value=mock_df)
        mocker.patch.object(data_service, 'import_data', return_value=True)
        
        # Import the file
        import_screen.import_button.click()
        
        # Verify data was imported
        assert data_service.import_data.called
        
        # 2. STEP 2: Navigate to Raw Data Screen and view data
        main_window.show_screen("raw_data")
        raw_data_screen = main_window.current_screen
        
        # Mock get_data to return our test data
        mocker.patch.object(data_service, 'get_data', return_value=mock_df)
        
        # Load the data
        raw_data_screen.load_data()
        
        # Verify the data was loaded correctly
        assert raw_data_screen.data_table.rowCount() == len(mock_df)
        assert raw_data_screen.data_table.columnCount() == len(mock_df.columns)
        
        # 3. STEP 3: Navigate to Analysis Screen and perform analysis
        main_window.show_screen("analysis")
        analysis_screen = main_window.current_screen
        
        # Create mock analysis results
        player_analysis = pd.DataFrame({
            "PLAYER": ["Player1", "Player2", "Player3"],
            "TOTAL_SCORE": [220, 150, 75],
            "CHEST_COUNT": [2, 1, 1]
        })
        
        chest_analysis = pd.DataFrame({
            "CHEST_TYPE": ["Gold", "Silver", "Bronze"], 
            "COUNT": [2, 1, 1]
        })
        
        source_analysis = pd.DataFrame({
            "SOURCE": ["A", "B", "C"], 
            "TOTAL_SCORE": [220, 150, 75]
        })
        
        date_analysis = pd.DataFrame({
            "DATE": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"], 
            "TOTAL_SCORE": [100, 150, 75, 120]
        })
        
        # Create a mock AnalysisResult
        class MockAnalysisResult:
            def __init__(self):
                self.player_analysis = player_analysis
                self.chest_analysis = chest_analysis
                self.source_analysis = source_analysis
                self.date_analysis = date_analysis
        
        # Mock analyze method to return our mock results
        mocker.patch.object(analysis_service, 'analyze', return_value=MockAnalysisResult())
        
        # Load data and perform analysis
        analysis_screen.load_data()
        analysis_screen.analyze_button.click()
        
        # Verify analysis was performed and results displayed
        assert analysis_service.analyze.called
        assert analysis_screen.player_table.rowCount() == len(player_analysis)
        
        # 4. STEP 4: Navigate to Chart Screen and create charts
        main_window.show_screen("charts")
        chart_screen = main_window.current_screen
        
        # Mock chart creation
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        mocker.patch.object(chart_service, 'create_bar_chart', return_value=(fig, ax))
        mocker.patch.object(chart_service, 'create_pie_chart', return_value=(fig, ax))
        mocker.patch.object(chart_service, 'create_line_chart', return_value=(fig, ax))
        mocker.patch.object(chart_service, 'save_chart', return_value=None)
        
        # Load data and generate charts
        chart_screen.load_data()
        chart_screen.generate_player_chart()
        chart_screen.generate_chest_chart()
        chart_screen.generate_time_trend_chart()
        
        # Verify charts were created
        assert chart_service.create_bar_chart.called
        assert chart_service.create_pie_chart.called
        assert chart_service.create_line_chart.called
        
        # 5. STEP 5: Navigate to Report Screen and generate report
        main_window.show_screen("report")
        report_screen = main_window.current_screen
        
        # Mock report generation
        sample_html = "<html><body><h1>Test Report</h1></body></html>"
        mocker.patch.object(report_service, 'create_report', return_value=sample_html)
        mocker.patch.object(report_service, 'export_report', return_value=None)
        
        # Load data and generate report
        report_screen.load_data()
        report_screen.generate_report_button.click()
        
        # Export the report
        report_screen.export_report_button.click()
        
        # Verify report was generated and exported
        assert report_service.create_report.called
        assert report_service.export_report.called
        
        # Clean up
        plt.close(fig)
```

#### Filter-Sort-Export Workflow

```python
# tests/integration/workflows/test_filter_sort_export_workflow.py
import pytest
from pytest_mock import MockerFixture
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
import sys
import pandas as pd
from pathlib import Path
from src.ui.main_window import MainWindow
from src.ui.screens.screen_manager import ScreenManager
from src.services.data_service import DataService
from src.services.config_service import ConfigService

@pytest.fixture(scope="session")
def app():
    """Create a QApplication instance for UI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app

class TestFilterSortExportWorkflow:
    """Test the workflow for filtering, sorting and exporting data."""
    
    @pytest.fixture
    def sample_data(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame({
            "PLAYER": ["Player1", "Player2", "Player3", "Player4", "Player5"],
            "CHEST": ["Gold", "Silver", "Bronze", "Gold", "Silver"],
            "SOURCE": ["A", "B", "C", "A", "B"],
            "SCORE": [100, 150, 75, 200, 125],
            "DATE": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05"]
        })
    
    def test_filter_sort_export_workflow(self, app, sample_data, mocker: MockerFixture):
        """Test the workflow for filtering, sorting, and exporting data."""
        # Initialize services
        data_service = DataService()
        config_service = ConfigService()
        
        # Mock data service to return our sample data
        mocker.patch.object(data_service, 'get_data', return_value=sample_data)
        
        # Create screen manager and main window
        screen_manager = ScreenManager()
        main_window = MainWindow(screen_manager, data_service, config_service=config_service)
        
        # Navigate to Raw Data Screen
        main_window.show_screen("raw_data")
        raw_data_screen = main_window.current_screen
        
        # Load the data
        raw_data_screen.load_data()
        
        # 1. STEP 1: Filter data
        # Mock filter_by_values to return filtered data
        gold_filter = sample_data[sample_data["CHEST"] == "Gold"]
        mocker.patch.object(data_service, 'filter_by_values', return_value=gold_filter)
        
        # Add a filter for gold chests
        raw_data_screen.filter_panel.add_filter("CHEST", "Gold")
        
        # Apply the filter
        raw_data_screen.apply_filters_button.click()
        
        # Verify filtered data is displayed
        assert raw_data_screen.data_table.rowCount() == 2  # 2 rows with Gold chests
        assert data_service.filter_by_values.called
        
        # 2. STEP 2: Sort data
        # Mock sort_by_column to return sorted data
        sorted_data = gold_filter.sort_values(by="SCORE", ascending=False)
        mocker.patch.object(data_service, 'sort_by_column', return_value=sorted_data)
        
        # Get the SCORE column index
        score_column_index = raw_data_screen.data_table.get_column_index("SCORE")
        
        # Trigger a sort by clicking the column header
        raw_data_screen.data_table.horizontalHeader().sectionClicked.emit(score_column_index)
        
        # Verify the data service was called for sorting
        assert data_service.sort_by_column.called
        
        # Ensure the data is sorted correctly
        first_row_score = raw_data_screen.data_table.item(0, score_column_index).text()
        assert first_row_score == "200"  # Highest score should be first
        
        # 3. STEP 3: Export data
        # Mock export_csv and file dialog
        export_path = Path("filtered_gold_data.csv")
        mocker.patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName', 
                    return_value=(str(export_path), "CSV files (*.csv)"))
        mocker.patch.object(data_service, 'export_csv', return_value=True)
        
        # Click the export button
        raw_data_screen.export_button.click()
        
        # Verify export was triggered with filtered and sorted data
        assert data_service.export_csv.called
        export_args = data_service.export_csv.call_args[0]
        assert export_args[0] is sorted_data  # Filtered and sorted data
        assert export_args[1] == export_path  # Export path
```

#### Configuration Save-Load Workflow

```python
# tests/integration/workflows/test_config_workflow.py
import pytest
from pytest_mock import MockerFixture
from PyQt6.QtWidgets import QApplication
import sys
import pandas as pd
import json
from pathlib import Path
from src.ui.main_window import MainWindow
from src.ui.screens.screen_manager import ScreenManager
from src.services.config_service import ConfigService
from src.visualization.charts.chart_configuration import ChartConfiguration

@pytest.fixture(scope="session")
def app():
    """Create a QApplication instance for UI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app

class TestConfigWorkflow:
    """Test the configuration save and load workflow."""
    
    @pytest.fixture
    def config_file(self, tmp_path):
        """Create a temporary config file."""
        config_path = tmp_path / "test_config.json"
        return config_path
    
    def test_save_load_config_workflow(self, app, config_file, mocker: MockerFixture):
        """Test saving and loading configuration settings."""
        # Initialize config service
        config_service = ConfigService()
        
        # Mock config file operations
        mocker.patch.object(config_service, 'get_config_file_path', return_value=config_file)
        
        # Create screen manager and main window
        screen_manager = ScreenManager()
        main_window = MainWindow(screen_manager, config_service=config_service)
        
        # 1. STEP 1: Configure chart settings
        main_window.show_screen("settings")
        settings_screen = main_window.current_screen
        
        # Set chart configuration options
        settings_screen.chart_theme_combo.setCurrentText("dark")
        settings_screen.chart_dpi_spinbox.setValue(150)
        settings_screen.chart_width_spinbox.setValue(10)
        settings_screen.chart_height_spinbox.setValue(6)
        
        # Set player chart settings
        settings_screen.player_chart_type_combo.setCurrentText("horizontal_bar")
        settings_screen.player_chart_limit_spinbox.setValue(10)
        
        # Mock the save_settings method to capture calls
        mocker.patch.object(config_service, 'save_setting')
        
        # Click the save button
        settings_screen.save_button.click()
        
        # Verify settings were saved
        assert config_service.save_setting.called
        # Check that chart settings were saved
        chart_settings_call = [call for call in config_service.save_setting.call_args_list 
                             if call[0][0] == "chart_settings"]
        assert len(chart_settings_call) > 0
        
        # 2. STEP 2: Verify settings are loaded properly on restart
        # Mock the load_setting method to return our saved settings
        chart_settings = {
            "theme": "dark",
            "dpi": 150,
            "figure_size": [10, 6],
            "player_chart_type": "horizontal_bar",
            "player_limit": 10
        }
        mocker.patch.object(config_service, 'get_setting', return_value=chart_settings)
        
        # Create a new main window to simulate application restart
        new_main_window = MainWindow(screen_manager, config_service=config_service)
        new_main_window.show_screen("settings")
        new_settings_screen = new_main_window.current_screen
        
        # Verify settings were loaded from config
        assert new_settings_screen.chart_theme_combo.currentText() == "dark"
        assert new_settings_screen.chart_dpi_spinbox.value() == 150
        assert new_settings_screen.chart_width_spinbox.value() == 10
        assert new_settings_screen.chart_height_spinbox.value() == 6
        assert new_settings_screen.player_chart_type_combo.currentText() == "horizontal_bar"
        assert new_settings_screen.player_chart_limit_spinbox.value() == 10
        
        # 3. STEP 3: Verify settings are applied to charts
        new_main_window.show_screen("charts")
        chart_screen = new_main_window.current_screen
        
        # Mock chart service to capture chart configuration
        chart_service_mock = mocker.MagicMock()
        chart_screen.chart_service = chart_service_mock
        
        # Generate a chart to test configuration application
        chart_screen.generate_player_chart()
        
        # Verify the chart service was called with correct configuration
        assert chart_service_mock.create_horizontal_bar_chart.called
        
        # Extract the chart configuration object used
        config_arg = None
        for call in chart_service_mock.create_horizontal_bar_chart.call_args_list:
            for arg in call[0]:
                if isinstance(arg, ChartConfiguration):
                    config_arg = arg
                    break
        
        # Verify configuration was applied
        assert config_arg is not None
        assert config_arg.theme == "dark"
        assert config_arg.dpi == 150
        assert config_arg.figure_size == [10, 6]
```

## Validation Criteria

This section outlines the criteria for validating the integration testing implementation.

### Requirements for Integration Test Validation

1. **Test Coverage**:
   - [ ] All integration points between components are tested
   - [ ] All major workflows are covered by end-to-end tests
   - [ ] Error handling and edge cases are tested

2. **Test Quality**:
   - [ ] Tests are independent and do not rely on each other's state
   - [ ] Tests use appropriate fixtures and setup/teardown procedures
   - [ ] Tests clearly identify which integration point is failing when errors occur

3. **Test Performance**:
   - [ ] Integration tests run within reasonable time limits
   - [ ] Tests use appropriate mocking to avoid external dependencies
   - [ ] Tests are designed to be efficient and avoid redundant operations

4. **Documentation**:
   - [ ] Tests include clear docstrings explaining their purpose
   - [ ] Test failures provide actionable information
   - [ ] Integration test strategy is documented and maintained

### Validation Process

1. **Code Review**:
   - [ ] Review integration test implementation against this plan
   - [ ] Ensure all required integration tests are implemented
   - [ ] Verify test quality and independence

2. **Test Execution**:
   - [ ] Run the full integration test suite and verify all tests pass
   - [ ] Measure test coverage for integration points
   - [ ] Verify error cases are properly tested

3. **Workflow Validation**:
   - [ ] Manually validate core workflows to complement automated tests
   - [ ] Verify that automated tests accurately reflect real user workflows
   - [ ] Ensure workflow tests properly exercise the full application stack

4. **Report Generation**:
   - [ ] Generate test coverage reports for integration tests
   - [ ] Document any gaps or limitations in test coverage
   - [ ] Provide recommendations for future test improvements

## Conclusion

The integration testing approach outlined in this document provides a comprehensive strategy for ensuring that all components of the Total Battle Analyzer application work together correctly. By testing the interactions between data processing, analysis services, visualization components, and the UI layer, we can ensure that the application functions as a cohesive whole.

Implementation of these integration tests will help identify issues that might not be caught by unit tests alone, particularly those related to the integration of different services and the end-to-end user experience. The validation criteria provide clear guidelines for ensuring that our integration testing approach is thorough and effective.

Once these integration tests are implemented and passing, we can proceed with confidence to the next phase of testing, focusing on user acceptance and performance testing.