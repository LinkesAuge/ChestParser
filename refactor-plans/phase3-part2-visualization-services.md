# Total Battle Analyzer Refactoring Plan: Phase 3 - Part 2
## Visualization Services

This document details the implementation of visualization services for the Total Battle Analyzer application as part of Phase 3 refactoring.

### 1. Setup and Preparation

- [ ] **Directory Structure Verification**
  - [ ] Ensure the `src/visualization/services` directory exists
  - [ ] Create it if missing:
    ```bash
    mkdir -p src/visualization/services
    ```
  - [ ] Create the `__init__.py` file in the services directory:
    ```bash
    touch src/visualization/services/__init__.py
    ```

- [ ] **Dependency Verification**
  - [ ] Ensure all required visualization libraries are installed:
    ```bash
    uv add matplotlib pandas numpy
    ```
  - [ ] Document any additional dependencies that may be needed

### 2. Chart Service Interface

- [ ] **Define Chart Service Interface**
  - [ ] Create `src/visualization/services/chart_service.py` with the following content:
    ```python
    # src/visualization/services/chart_service.py
    from abc import ABC, abstractmethod
    import pandas as pd
    import matplotlib.pyplot as plt
    from typing import Dict, Any, Optional, Tuple, List, Union
    from pathlib import Path

    class ChartService(ABC):
        """Interface for chart generation services."""
        
        @abstractmethod
        def create_bar_chart(
            self,
            data: pd.DataFrame,
            category_column: str,
            value_column: str,
            title: str = "",
            **kwargs
        ) -> Tuple[plt.Figure, plt.Axes]:
            """
            Create a bar chart.
            
            Args:
                data: DataFrame containing the data
                category_column: Column to use for categories
                value_column: Column to use for values
                title: Chart title
                **kwargs: Additional options
                
            Returns:
                Tuple of figure and axes
            """
            pass
        
        @abstractmethod
        def create_horizontal_bar_chart(
            self,
            data: pd.DataFrame,
            category_column: str,
            value_column: str,
            title: str = "",
            **kwargs
        ) -> Tuple[plt.Figure, plt.Axes]:
            """
            Create a horizontal bar chart.
            
            Args:
                data: DataFrame containing the data
                category_column: Column to use for categories
                value_column: Column to use for values
                title: Chart title
                **kwargs: Additional options
                
            Returns:
                Tuple of figure and axes
            """
            pass
        
        @abstractmethod
        def create_pie_chart(
            self,
            data: pd.DataFrame,
            category_column: str,
            value_column: str,
            title: str = "",
            **kwargs
        ) -> Tuple[plt.Figure, plt.Axes]:
            """
            Create a pie chart.
            
            Args:
                data: DataFrame containing the data
                category_column: Column to use for categories
                value_column: Column to use for values
                title: Chart title
                **kwargs: Additional options
                
            Returns:
                Tuple of figure and axes
            """
            pass
        
        @abstractmethod
        def create_line_chart(
            self,
            data: pd.DataFrame,
            category_column: str,
            value_column: str,
            title: str = "",
            **kwargs
        ) -> Tuple[plt.Figure, plt.Axes]:
            """
            Create a line chart.
            
            Args:
                data: DataFrame containing the data
                category_column: Column to use for categories
                value_column: Column to use for values
                title: Chart title
                **kwargs: Additional options
                
            Returns:
                Tuple of figure and axes
            """
            pass
        
        @abstractmethod
        def save_chart(
            self,
            fig: plt.Figure,
            file_path: Union[str, Path],
            **kwargs
        ) -> bool:
            """
            Save a chart to a file.
            
            Args:
                fig: Figure to save
                file_path: Path to save the chart to
                **kwargs: Additional options
                
            Returns:
                True if successful, False otherwise
            """
            pass
    ```

- [ ] **Test the Interface**
  - [ ] Create a simple test implementation to verify the interface
  - [ ] Ensure all methods are properly defined with correct signatures

### 3. Chart Configuration

- [ ] **Create Chart Configuration Class**
  - [ ] Create `src/visualization/services/chart_configuration.py` with the following content:
    ```python
    # src/visualization/services/chart_configuration.py
    from typing import Dict, List, Any, Optional, Tuple
    from dataclasses import dataclass, field

    @dataclass
    class ChartConfiguration:
        """Configuration for chart generation."""
        
        # Chart type and data
        chart_type: str = "bar"  # 'bar', 'line', 'pie', 'horizontal_bar', etc.
        
        # Data columns
        category_column: str = ""
        value_column: str = ""
        
        # Chart appearance
        title: str = ""
        x_label: str = ""
        y_label: str = ""
        figsize: Tuple[int, int] = (8, 6)
        
        # Chart options
        show_values: bool = True
        show_grid: bool = True
        limit_categories: bool = False
        category_limit: int = 10
        sort_data: bool = True
        sort_ascending: bool = False
        
        # Colors and styling
        colors: List[str] = field(default_factory=lambda: [
            "#D4AF37",  # Gold
            "#5991C4",  # Blue
            "#6EC1A7",  # Green
            "#D46A5F",  # Red
            "#8899AA",  # Gray
            "#F0C75A"   # Light gold
        ])
        
        style: Dict[str, Any] = field(default_factory=lambda: {
            'bg_color': '#1A2742',        # Dark blue background
            'text_color': '#FFFFFF',      # White text
            'grid_color': '#2A3F5F',      # Medium blue grid
            'tick_color': '#FFFFFF',      # White ticks
            'title_color': '#D4AF37',     # Gold title
            'title_size': 14,
            'label_size': 12,
            'line_color': '#5991C4',      # Blue line
            'line_width': 2.5,
            'marker_size': 8,
            'marker_color': '#D4AF37',    # Gold markers
            'edge_color': '#1A2742'       # Dark blue edges
        })
        
        # Export options
        dpi: int = 100
        
        def __post_init__(self):
            """Validate configuration after initialization."""
            valid_chart_types = ['bar', 'horizontal_bar', 'pie', 'line', 'scatter']
            if self.chart_type not in valid_chart_types:
                raise ValueError(f"Invalid chart type: {self.chart_type}. " +
                              f"Must be one of {valid_chart_types}")
                              
            if not self.category_column:
                raise ValueError("Category column must be specified")
                
            if not self.value_column:
                raise ValueError("Value column must be specified")
    ```

- [ ] **Test the Chart Configuration**
  - [ ] Create a simple test script to verify the configuration class
  - [ ] Ensure validation works correctly

### 4. Matplotlib Chart Service Implementation

- [ ] **Implement the Matplotlib Chart Service**
  - [ ] Create `src/visualization/services/mpl_chart_service.py` with the following content:
    ```python
    # src/visualization/services/mpl_chart_service.py
    import pandas as pd
    import matplotlib.pyplot as plt
    import numpy as np
    from typing import Dict, Any, Optional, Tuple, List, Union
    from pathlib import Path
    from .chart_service import ChartService
    from .chart_configuration import ChartConfiguration

    class MplChartService(ChartService):
        """Chart generation service using matplotlib."""
        
        def __init__(self, debug: bool = False):
            self.debug = debug
            
        def create_figure(self, config: ChartConfiguration) -> Tuple[plt.Figure, plt.Axes]:
            """
            Create a figure and axes with styling.
            
            Args:
                config: Chart configuration
                
            Returns:
                Tuple of figure and axes
            """
            # Set the figure size
            fig = plt.figure(figsize=config.figsize, facecolor=config.style['bg_color'])
            ax = fig.add_subplot(111)
            
            # Apply styling
            ax.set_facecolor(config.style['bg_color'])
            ax.xaxis.label.set_color(config.style['text_color'])
            ax.yaxis.label.set_color(config.style['text_color'])
            ax.title.set_color(config.style['title_color'])
            ax.title.set_fontsize(config.style['title_size'])
            
            # Style tick parameters
            ax.tick_params(
                axis='both',
                colors=config.style['tick_color'],
                labelcolor=config.style['text_color']
            )
            
            # Set grid
            ax.grid(config.show_grid, color=config.style['grid_color'], linestyle='--', alpha=0.3)
            
            # Style spines
            for spine in ax.spines.values():
                spine.set_color(config.style['grid_color'])
                
            return fig, ax
        
        def prepare_data(
            self,
            data: pd.DataFrame,
            config: ChartConfiguration
        ) -> pd.DataFrame:
            """
            Prepare data for plotting.
            
            Args:
                data: DataFrame to prepare
                config: Chart configuration
                
            Returns:
                Prepared DataFrame
            """
            if data is None or data.empty:
                return pd.DataFrame()
                
            # Check if required columns exist
            if config.category_column not in data.columns:
                if self.debug:
                    print(f"Category column {config.category_column} not found in data")
                return pd.DataFrame()
                
            if config.value_column not in data.columns:
                if self.debug:
                    print(f"Value column {config.value_column} not found in data")
                return pd.DataFrame()
                
            # Create a copy to avoid modifying the original
            df = data.copy()
            
            # Sort if requested
            if config.sort_data:
                df = df.sort_values(
                    config.value_column,
                    ascending=config.sort_ascending
                )
                
            # Limit categories if requested
            if config.limit_categories and config.category_limit > 0:
                if config.sort_data:
                    # Keep the top N categories
                    df = df.head(config.category_limit)
                else:
                    # Sample N categories randomly
                    df = df.sample(min(len(df), config.category_limit))
                    
            return df
        
        def create_bar_chart(
            self,
            data: pd.DataFrame,
            category_column: str,
            value_column: str,
            title: str = "",
            **kwargs
        ) -> Tuple[plt.Figure, plt.Axes]:
            """Create a bar chart."""
            # Create config with provided parameters
            config = ChartConfiguration(
                chart_type="bar",
                category_column=category_column,
                value_column=value_column,
                title=title,
                **kwargs
            )
            
            # Create figure with styling
            fig, ax = self.create_figure(config)
            
            # Prepare data
            df = self.prepare_data(data, config)
            if df.empty:
                ax.text(
                    0.5, 0.5,
                    "No data available for chart",
                    ha='center',
                    va='center',
                    color=config.style['text_color'],
                    fontsize=14
                )
                return fig, ax
                
            # Create colors for bars
            bar_colors = [config.colors[i % len(config.colors)] for i in range(len(df))]
            
            # Create the bar chart
            bars = ax.bar(
                df[config.category_column],
                df[config.value_column],
                color=bar_colors
            )
            
            # Set labels and title
            if config.x_label:
                ax.set_xlabel(config.x_label)
            else:
                ax.set_xlabel(config.category_column)
                
            if config.y_label:
                ax.set_ylabel(config.y_label)
            else:
                ax.set_ylabel(config.value_column)
                
            if config.title:
                ax.set_title(config.title)
                
            # Rotate x-tick labels if there are many categories
            if len(df) > 5:
                plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
                
            # Add values on bars if requested
            if config.show_values:
                for bar in bars:
                    height = bar.get_height()
                    ax.text(
                        bar.get_x() + bar.get_width()/2.,
                        height,
                        f'{height:,.0f}',
                        ha='center',
                        va='bottom',
                        color=config.style['text_color'],
                        fontweight='bold'
                    )
                    
            # Adjust layout
            fig.tight_layout()
            
            return fig, ax
        
        def create_horizontal_bar_chart(
            self,
            data: pd.DataFrame,
            category_column: str,
            value_column: str,
            title: str = "",
            **kwargs
        ) -> Tuple[plt.Figure, plt.Axes]:
            """Create a horizontal bar chart."""
            # Create config with provided parameters
            config = ChartConfiguration(
                chart_type="horizontal_bar",
                category_column=category_column,
                value_column=value_column,
                title=title,
                **kwargs
            )
            
            # Create figure with styling
            fig, ax = self.create_figure(config)
            
            # Prepare data
            df = self.prepare_data(data, config)
            if df.empty:
                ax.text(
                    0.5, 0.5,
                    "No data available for chart",
                    ha='center',
                    va='center',
                    color=config.style['text_color'],
                    fontsize=14
                )
                return fig, ax
                
            # Create colors for bars
            bar_colors = [config.colors[i % len(config.colors)] for i in range(len(df))]
            
            # Create the horizontal bar chart
            bars = ax.barh(
                df[config.category_column],
                df[config.value_column],
                color=bar_colors
            )
            
            # Set labels and title
            if config.x_label:
                ax.set_xlabel(config.x_label)
            else:
                ax.set_xlabel(config.value_column)
                
            if config.y_label:
                ax.set_ylabel(config.y_label)
            else:
                ax.set_ylabel(config.category_column)
                
            if config.title:
                ax.set_title(config.title)
                
            # Add values at the end of bars if requested
            if config.show_values:
                for bar in bars:
                    width = bar.get_width()
                    ax.text(
                        width,
                        bar.get_y() + bar.get_height()/2.,
                        f'{width:,.0f}',
                        ha='left',
                        va='center',
                        color=config.style['text_color'],
                        fontweight='bold'
                    )
                    
            # Adjust layout
            fig.tight_layout()
            
            return fig, ax
        
        def create_pie_chart(
            self,
            data: pd.DataFrame,
            category_column: str,
            value_column: str,
            title: str = "",
            **kwargs
        ) -> Tuple[plt.Figure, plt.Axes]:
            """Create a pie chart."""
            # Implementation of pie chart creation
            # (Similar structure to the bar chart implementation)
            # ...
            
        def create_line_chart(
            self,
            data: pd.DataFrame,
            category_column: str,
            value_column: str,
            title: str = "",
            **kwargs
        ) -> Tuple[plt.Figure, plt.Axes]:
            """Create a line chart."""
            # Implementation of line chart creation
            # ...
            
        def save_chart(
            self,
            fig: plt.Figure,
            file_path: Union[str, Path],
            **kwargs
        ) -> bool:
            """Save a chart to a file."""
            try:
                # Ensure the file_path is a Path object
                if isinstance(file_path, str):
                    file_path = Path(file_path)
                    
                # Ensure the directory exists
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Get DPI setting
                dpi = kwargs.get('dpi', 100)
                
                # Save the figure
                fig.savefig(
                    file_path,
                    dpi=dpi,
                    bbox_inches='tight',
                    facecolor=fig.get_facecolor()
                )
                
                return True
                
            except Exception as e:
                if self.debug:
                    print(f"Error saving chart: {str(e)}")
                    import traceback
                    traceback.print_exc()
                return False
    ```

- [ ] **Test the Matplotlib Chart Service**
  - [ ] Create a simple test script to verify the service
  - [ ] Test each chart type with sample data

### 5. Chart Manager Implementation

- [ ] **Create Chart Manager Class**
  - [ ] Create `src/visualization/services/chart_manager.py` with the following content:
    ```python
    # src/visualization/services/chart_manager.py
    import pandas as pd
    import numpy as np
    from typing import Dict, Any, Optional, List, Union, Tuple
    import matplotlib.pyplot as plt
    from pathlib import Path
    import os
    from .mpl_chart_service import MplChartService
    from .chart_configuration import ChartConfiguration

    class ChartManager:
        """Manager for creating and managing charts."""
        
        def __init__(self, chart_service=None, debug: bool = False):
            self.debug = debug
            self.chart_service = chart_service or MplChartService(debug=debug)
            
        def create_player_charts(
            self,
            data: Dict[str, Any],
            export_dir: Optional[Union[str, Path]] = None
        ) -> Dict[str, str]:
            """
            Create player analysis charts.
            
            Args:
                data: Analysis data
                export_dir: Optional directory to export charts to
                
            Returns:
                Dictionary mapping chart names to file paths or figure objects
            """
            charts = {}
            
            try:
                # Check if player analysis data is available
                if not data or 'player_analysis' not in data:
                    if self.debug:
                        print("No player analysis data available")
                    return charts
                    
                player_analysis = data['player_analysis']
                
                # Create player performance chart
                if 'performance' in player_analysis and 'player_totals' in player_analysis['performance']:
                    player_totals = player_analysis['performance']['player_totals']
                    
                    if not player_totals.empty:
                        fig, ax = self.chart_service.create_horizontal_bar_chart(
                            player_totals,
                            'PLAYER',
                            'SCORE',
                            title="Player Performance",
                            sort_data=True,
                            sort_ascending=False,
                            limit_categories=True,
                            category_limit=10
                        )
                        
                        # Save chart if export directory provided
                        if export_dir:
                            export_path = self._get_export_path(export_dir, "player_performance.png")
                            if self.chart_service.save_chart(fig, export_path):
                                charts['player_performance'] = str(export_path)
                            plt.close(fig)
                        else:
                            charts['player_performance'] = fig
                
                # Create player efficiency chart
                if 'performance' in player_analysis and 'player_totals' in player_analysis['performance']:
                    player_totals = player_analysis['performance']['player_totals']
                    
                    if not player_totals.empty and 'EFFICIENCY' in player_totals.columns:
                        fig, ax = self.chart_service.create_horizontal_bar_chart(
                            player_totals,
                            'PLAYER',
                            'EFFICIENCY',
                            title="Player Efficiency (Score per Chest)",
                            sort_data=True,
                            sort_ascending=False,
                            limit_categories=True,
                            category_limit=10
                        )
                        
                        # Save chart if export directory provided
                        if export_dir:
                            export_path = self._get_export_path(export_dir, "player_efficiency.png")
                            if self.chart_service.save_chart(fig, export_path):
                                charts['player_efficiency'] = str(export_path)
                            plt.close(fig)
                        else:
                            charts['player_efficiency'] = fig
                            
                # Additional charts can be added here...
                
            except Exception as e:
                if self.debug:
                    print(f"Error creating player charts: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    
            return charts
            
        def create_chest_charts(
            self,
            data: Dict[str, Any],
            export_dir: Optional[Union[str, Path]] = None
        ) -> Dict[str, str]:
            """
            Create chest analysis charts.
            
            Args:
                data: Analysis data
                export_dir: Optional directory to export charts to
                
            Returns:
                Dictionary mapping chart names to file paths or figure objects
            """
            # Implementation for chest charts
            # ...
            
        def create_source_charts(
            self,
            data: Dict[str, Any],
            export_dir: Optional[Union[str, Path]] = None
        ) -> Dict[str, str]:
            """
            Create source analysis charts.
            
            Args:
                data: Analysis data
                export_dir: Optional directory to export charts to
                
            Returns:
                Dictionary mapping chart names to file paths or figure objects
            """
            # Implementation for source charts
            # ...
            
        def create_time_trend_charts(
            self,
            data: Dict[str, Any],
            export_dir: Optional[Union[str, Path]] = None
        ) -> Dict[str, str]:
            """
            Create time trend charts.
            
            Args:
                data: Analysis data
                export_dir: Optional directory to export charts to
                
            Returns:
                Dictionary mapping chart names to file paths or figure objects
            """
            # Implementation for time trend charts
            # ...
            
        def _get_export_path(
            self,
            export_dir: Union[str, Path],
            filename: str
        ) -> Path:
            """
            Get the export path for a chart.
            
            Args:
                export_dir: Directory to export to
                filename: Filename
                
            Returns:
                Path object for the export location
            """
            # Ensure export_dir is a Path object
            if isinstance(export_dir, str):
                export_dir = Path(export_dir)
                
            # Ensure the directory exists
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Return the full path
            return export_dir / filename
    ```

- [ ] **Test the Chart Manager**
  - [ ] Create a test script to verify the chart manager
  - [ ] Test with sample analysis data

### 6. Integration with Analysis Services

- [ ] **Create Integration Tests**
  - [ ] Create tests that use analysis services to generate data
  - [ ] Pass the analysis data to chart services
  - [ ] Verify that the integration works correctly

- [ ] **Optimize Chart Generation**
  - [ ] Profile chart generation performance
  - [ ] Implement optimizations for slow operations
  - [ ] Test optimizations to ensure they improve performance

### 7. Style Customization

- [ ] **Create Theme Manager**
  - [ ] Create `src/visualization/services/theme_manager.py`
  - [ ] Implement theme management for chart styles
  - [ ] Add predefined themes for different use cases

- [ ] **Add Theme Support to Chart Service**
  - [ ] Update the chart service to use the theme manager
  - [ ] Allow switching between themes

### 8. Documentation

- [ ] **Update Visualization Service Documentation**
  - [ ] Add detailed docstrings to all classes and methods
  - [ ] Create examples for common chart generation tasks
  - [ ] Document error handling and debugging procedures

- [ ] **Create Visualization Service Guide**
  - [ ] Create a guide for using the visualization services
  - [ ] Include examples of common chart generation scenarios
  - [ ] Add troubleshooting section for common issues

### 9. Part 2 Validation

- [ ] **Review Implementation**
  - [ ] Verify all required services are implemented
  - [ ] Check for proper error handling and robustness
  - [ ] Ensure code quality meets project standards

- [ ] **Test Coverage Verification**
  - [ ] Verify test coverage of all services
  - [ ] Add tests for any missing functionality
  - [ ] Ensure edge cases are handled correctly

- [ ] **Documentation Verification**
  - [ ] Verify all services are properly documented
  - [ ] Update any outdated documentation
  - [ ] Ensure examples are clear and helpful

### Feedback Request

After completing Part 2 of Phase 3, please provide feedback on the following aspects:

1. Are the visualization services comprehensive enough for your needs?
2. Are there any additional chart types or visualizations that should be included?
3. Is the styling approach flexible enough for customization?
4. Does the implementation align with the overall refactoring goals?
5. Any suggestions for improvements before proceeding to Part 3? 