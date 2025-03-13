# Total Battle Analyzer Refactoring Plan: Phase 3 - Part 3
## Reporting Services

This document details the implementation of reporting services for the Total Battle Analyzer application as part of Phase 3 refactoring.

### 1. Setup and Preparation

- [ ] **Directory Structure Verification**
  - [ ] Ensure the `src/visualization/reports` directory exists
  - [ ] Create it if missing:
    ```bash
    mkdir -p src/visualization/reports
    ```
  - [ ] Create the `__init__.py` file in the reports directory:
    ```bash
    touch src/visualization/reports/__init__.py
    ```

- [ ] **Dependency Verification**
  - [ ] Ensure all required reporting libraries are installed:
    ```bash
    uv add jinja2 markdown
    ```
  - [ ] Document any additional dependencies that may be needed

### 2. Report Service Interface

- [ ] **Define Report Service Interface**
  - [ ] Create `src/visualization/reports/report_service.py` with the following content:
    ```python
    # src/visualization/reports/report_service.py
    from abc import ABC, abstractmethod
    from typing import Dict, Any, Optional, List, Union
    from pathlib import Path

    class ReportService(ABC):
        """Interface for report generation services."""
        
        @abstractmethod
        def create_report(
            self,
            data: Dict[str, Any],
            template: Optional[str] = None,
            output_file: Optional[Union[str, Path]] = None,
            **kwargs
        ) -> str:
            """
            Create a report from data.
            
            Args:
                data: Data to include in the report
                template: Optional template to use
                output_file: Optional file to write the report to
                **kwargs: Additional options
                
            Returns:
                Report content as string
            """
            pass
        
        @abstractmethod
        def create_section(
            self,
            title: str,
            content: str,
            **kwargs
        ) -> Dict[str, Any]:
            """
            Create a report section.
            
            Args:
                title: Section title
                content: Section content
                **kwargs: Additional options
                
            Returns:
                Dictionary representing the section
            """
            pass
        
        @abstractmethod
        def create_table_section(
            self,
            title: str,
            data: Any,
            description: Optional[str] = None,
            **kwargs
        ) -> Dict[str, Any]:
            """
            Create a report section with a table.
            
            Args:
                title: Section title
                data: Table data (DataFrame or similar)
                description: Optional description
                **kwargs: Additional options
                
            Returns:
                Dictionary representing the section
            """
            pass
        
        @abstractmethod
        def create_chart_section(
            self,
            title: str,
            chart: Any,
            description: Optional[str] = None,
            **kwargs
        ) -> Dict[str, Any]:
            """
            Create a report section with a chart.
            
            Args:
                title: Section title
                chart: Chart data (matplotlib figure, path to image, etc.)
                description: Optional description
                **kwargs: Additional options
                
            Returns:
                Dictionary representing the section
            """
            pass
        
        @abstractmethod
        def create_stats_section(
            self,
            title: str,
            stats: Dict[str, Any],
            description: Optional[str] = None,
            **kwargs
        ) -> Dict[str, Any]:
            """
            Create a report section with statistics.
            
            Args:
                title: Section title
                stats: Statistics dictionary
                description: Optional description
                **kwargs: Additional options
                
            Returns:
                Dictionary representing the section
            """
            pass
        
        @abstractmethod
        def save_report(
            self,
            report: str,
            output_file: Union[str, Path],
            **kwargs
        ) -> bool:
            """
            Save a report to a file.
            
            Args:
                report: Report content
                output_file: File to save to
                **kwargs: Additional options
                
            Returns:
                True if successful, False otherwise
            """
            pass
    ```

- [ ] **Test the Interface**
  - [ ] Create a simple test implementation to verify the interface
  - [ ] Ensure all methods are properly defined with correct signatures

### 3. HTML Report Service Implementation

- [ ] **Create HTML Report Service**
  - [ ] Create `src/visualization/reports/html_report_service.py` with the following content:
    ```python
    # src/visualization/reports/html_report_service.py
    import pandas as pd
    from typing import Dict, Any, Optional, List, Union
    from pathlib import Path
    import base64
    import io
    from datetime import datetime
    import matplotlib.pyplot as plt
    from .report_service import ReportService

    class HTMLReportService(ReportService):
        """Service for generating HTML reports."""
        
        def __init__(self, debug: bool = False):
            self.debug = debug
            
        def create_report(
            self,
            data: Dict[str, Any],
            template: Optional[str] = None,
            output_file: Optional[Union[str, Path]] = None,
            **kwargs
        ) -> str:
            """Create an HTML report."""
            try:
                title = kwargs.get('title', 'Total Battle Analyzer Report')
                css = kwargs.get('css', self._get_default_styles())
                
                # Initialize report sections
                sections = []
                
                # Process sections if provided
                if 'sections' in data:
                    sections = data['sections']
                    
                # Generate HTML
                html = self._generate_html_header(title, css)
                
                # Add sections
                for section in sections:
                    html += self._generate_section_html(section)
                    
                # Add footer
                html += self._generate_html_footer()
                
                # Save to file if output_file provided
                if output_file:
                    self.save_report(html, output_file)
                    
                return html
                
            except Exception as e:
                if self.debug:
                    print(f"Error creating HTML report: {str(e)}")
                    import traceback
                    traceback.print_exc()
                return f"<html><body><h1>Error creating report</h1><p>{str(e)}</p></body></html>"
        
        def create_section(
            self,
            title: str,
            content: str,
            **kwargs
        ) -> Dict[str, Any]:
            """Create a generic report section."""
            return {
                'title': title,
                'content': content,
                'type': 'generic'
            }
        
        def create_table_section(
            self,
            title: str,
            data: Any,
            description: Optional[str] = None,
            **kwargs
        ) -> Dict[str, Any]:
            """Create a table section."""
            try:
                # Convert to DataFrame if not already
                if not isinstance(data, pd.DataFrame):
                    data = pd.DataFrame(data)
                    
                # Convert DataFrame to HTML table
                table_html = data.to_html(
                    index=kwargs.get('include_index', False),
                    classes=kwargs.get('table_classes', 'data-table'),
                    border=kwargs.get('border', 0),
                    na_rep=kwargs.get('na_rep', '-')
                )
                
                # Create content with optional description
                content = ""
                if description:
                    content += f"<p>{description}</p>"
                content += table_html
                
                return {
                    'title': title,
                    'content': content,
                    'type': 'table',
                    'data': data
                }
                
            except Exception as e:
                if self.debug:
                    print(f"Error creating table section: {str(e)}")
                    import traceback
                    traceback.print_exc()
                return self.create_section(
                    title,
                    f"<p>Error creating table: {str(e)}</p>"
                )
        
        def create_chart_section(
            self,
            title: str,
            chart: Any,
            description: Optional[str] = None,
            **kwargs
        ) -> Dict[str, Any]:
            """Create a chart section."""
            try:
                content = ""
                if description:
                    content += f"<p>{description}</p>"
                    
                # If chart is a matplotlib figure
                if isinstance(chart, plt.Figure):
                    # Convert to base64 image
                    buf = io.BytesIO()
                    chart.savefig(
                        buf,
                        format='png',
                        dpi=kwargs.get('dpi', 100),
                        bbox_inches='tight'
                    )
                    buf.seek(0)
                    img_str = base64.b64encode(buf.read()).decode('ascii')
                    
                    # Add to content
                    content += f'<div class="chart-container"><img src="data:image/png;base64,{img_str}" alt="{title}" /></div>'
                    
                # If chart is a path to an image
                elif isinstance(chart, (str, Path)) and str(chart).endswith(('.png', '.jpg', '.jpeg', '.svg')):
                    # Check if it's a local file or URL
                    if str(chart).startswith(('http://', 'https://')):
                        # It's a URL
                        content += f'<div class="chart-container"><img src="{chart}" alt="{title}" /></div>'
                    else:
                        # It's a local file - convert to base64 to include inline
                        with open(chart, 'rb') as img_file:
                            img_str = base64.b64encode(img_file.read()).decode('ascii')
                        
                        # Get file extension
                        ext = str(chart).split('.')[-1].lower()
                        mime_type = {
                            'png': 'image/png',
                            'jpg': 'image/jpeg',
                            'jpeg': 'image/jpeg',
                            'svg': 'image/svg+xml'
                        }.get(ext, 'image/png')
                        
                        # Add to content
                        content += f'<div class="chart-container"><img src="data:{mime_type};base64,{img_str}" alt="{title}" /></div>'
                else:
                    # Just add as text
                    content += f"<div class='chart-container'>{str(chart)}</div>"
                    
                return {
                    'title': title,
                    'content': content,
                    'type': 'chart'
                }
                
            except Exception as e:
                if self.debug:
                    print(f"Error creating chart section: {str(e)}")
                    import traceback
                    traceback.print_exc()
                return self.create_section(
                    title,
                    f"<p>Error creating chart: {str(e)}</p>"
                )
        
        def create_stats_section(
            self,
            title: str,
            stats: Dict[str, Any],
            description: Optional[str] = None,
            **kwargs
        ) -> Dict[str, Any]:
            """Create a statistics section."""
            try:
                content = ""
                if description:
                    content += f"<p>{description}</p>"
                    
                # Create stats boxes
                content += '<div class="stats-container">'
                
                for key, value in stats.items():
                    # Format key for display
                    display_key = key.replace('_', ' ').title()
                    
                    # Format value
                    if isinstance(value, (int, float)):
                        display_value = f"{value:,}"
                        if key.endswith('_percent'):
                            display_value = f"{value:.1f}%"
                    else:
                        display_value = str(value)
                        
                    # Create a stat box
                    content += f'''
                    <div class="stat-box">
                        <p class="stat-label">{display_key}</p>
                        <p class="stat-value">{display_value}</p>
                    </div>
                    '''
                    
                content += '</div>'
                
                return {
                    'title': title,
                    'content': content,
                    'type': 'stats'
                }
                
            except Exception as e:
                if self.debug:
                    print(f"Error creating stats section: {str(e)}")
                    import traceback
                    traceback.print_exc()
                return self.create_section(
                    title,
                    f"<p>Error creating stats: {str(e)}</p>"
                )
        
        def save_report(
            self,
            report: str,
            output_file: Union[str, Path],
            **kwargs
        ) -> bool:
            """Save the report to a file."""
            try:
                # Ensure output_file is a Path object
                if isinstance(output_file, str):
                    output_file = Path(output_file)
                    
                # Ensure the directory exists
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Write the report
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report)
                    
                return True
                
            except Exception as e:
                if self.debug:
                    print(f"Error saving report: {str(e)}")
                    import traceback
                    traceback.print_exc()
                return False
        
        def _generate_html_header(self, title: str, css: str) -> str:
            """Generate HTML header."""
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{title}</title>
                <style>
                {css}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>{title}</h1>
                    <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            """
        
        def _generate_html_footer(self) -> str:
            """Generate HTML footer."""
            return f"""
                <div class="footer">
                    <p>Total Battle Analyzer - Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </body>
            </html>
            """
        
        def _generate_section_html(self, section: Dict[str, Any]) -> str:
            """Generate HTML for a section."""
            title = section.get('title', '')
            content = section.get('content', '')
            
            return f"""
            <div class="section">
                <h2>{title}</h2>
                {content}
            </div>
            """
        
        def _get_default_styles(self) -> str:
            """Get default CSS styles for reports."""
            return """
            body {
                font-family: Arial, sans-serif;
                background-color: #0E1629;
                color: #FFFFFF;
                margin: 20px;
                line-height: 1.6;
            }
            h1, h2, h3, h4 {
                color: #D4AF37;
                margin-top: 20px;
                margin-bottom: 10px;
            }
            h1 {
                font-size: 24px;
            }
            h2 {
                font-size: 20px;
                border-bottom: 1px solid #2A3F5F;
                padding-bottom: 5px;
            }
            h3 {
                font-size: 18px;
            }
            p {
                margin: 10px 0;
            }
            .header {
                border-bottom: 2px solid #D4AF37;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }
            .section {
                margin-bottom: 30px;
                background-color: #1A2742;
                padding: 15px;
                border-radius: 5px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
                font-size: 14px;
            }
            th, td {
                border: 1px solid #2A3F5F;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #0E1629;
                color: #D4AF37;
                font-weight: bold;
            }
            tr:nth-child(even) {
                background-color: #1E2D4A;
            }
            tr:hover {
                background-color: #2A3F5F;
            }
            .chart-container {
                margin: 20px 0;
                text-align: center;
            }
            .chart-container img {
                max-width: 100%;
                height: auto;
                border: 1px solid #2A3F5F;
                border-radius: 5px;
                background-color: #1A2742;
                padding: 10px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            }
            .footer {
                margin-top: 30px;
                text-align: center;
                font-size: 0.8em;
                color: #8899AA;
                border-top: 1px solid #2A3F5F;
                padding-top: 10px;
            }
            .stats-container {
                display: flex;
                flex-wrap: wrap;
                justify-content: space-between;
                margin: 20px 0;
            }
            .stat-box {
                background-color: #1A2742;
                border: 1px solid #2A3F5F;
                border-radius: 5px;
                padding: 15px;
                margin-bottom: 15px;
                width: calc(33% - 20px);
                box-sizing: border-box;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            }
            .stat-box p {
                margin: 5px 0;
            }
            .stat-value {
                font-size: 24px;
                font-weight: bold;
                color: #D4AF37;
            }
            
            /* Responsive adjustments */
            @media (max-width: 768px) {
                .stat-box {
                    width: calc(50% - 15px);
                }
            }
            
            @media (max-width: 480px) {
                .stat-box {
                    width: 100%;
                }
                
                body {
                    margin: 10px;
                }
                
                .section {
                    padding: 10px;
                }
            }
            """
    ```

- [ ] **Test the HTML Report Service**
  - [ ] Create a test script to verify the service
  - [ ] Test each section type with sample data

### 4. Markdown Report Service Implementation

- [ ] **Create Markdown Report Service**
  - [ ] Create `src/visualization/reports/markdown_report_service.py` with the following content:
    ```python
    # src/visualization/reports/markdown_report_service.py
    import pandas as pd
    from typing import Dict, Any, Optional, List, Union
    from pathlib import Path
    from datetime import datetime
    import matplotlib.pyplot as plt
    from .report_service import ReportService

    class MarkdownReportService(ReportService):
        """Service for generating Markdown reports."""
        
        def __init__(self, debug: bool = False):
            self.debug = debug
        
        def create_report(
            self,
            data: Dict[str, Any],
            template: Optional[str] = None,
            output_file: Optional[Union[str, Path]] = None,
            **kwargs
        ) -> str:
            """Create a Markdown report."""
            try:
                title = kwargs.get('title', 'Total Battle Analyzer Report')
                
                # Initialize report content
                md_content = f"# {title}\n\n"
                md_content += f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
                
                # Process sections if provided
                if 'sections' in data:
                    for section in data['sections']:
                        md_content += self._generate_section_markdown(section)
                        md_content += "\n\n---\n\n"  # Section separator
                        
                # Save to file if output_file provided
                if output_file:
                    self.save_report(md_content, output_file)
                    
                return md_content
                
            except Exception as e:
                if self.debug:
                    print(f"Error creating Markdown report: {str(e)}")
                    import traceback
                    traceback.print_exc()
                return f"# Error creating report\n\n{str(e)}"
        
        def create_section(
            self,
            title: str,
            content: str,
            **kwargs
        ) -> Dict[str, Any]:
            """Create a generic report section."""
            return {
                'title': title,
                'content': content,
                'type': 'generic'
            }
        
        def create_table_section(
            self,
            title: str,
            data: Any,
            description: Optional[str] = None,
            **kwargs
        ) -> Dict[str, Any]:
            """Create a table section."""
            try:
                # Convert to DataFrame if not already
                if not isinstance(data, pd.DataFrame):
                    data = pd.DataFrame(data)
                    
                # Convert DataFrame to Markdown table
                table_md = data.to_markdown(
                    index=kwargs.get('include_index', False),
                    tablefmt=kwargs.get('table_format', 'pipe')
                )
                
                # Create content with optional description
                content = ""
                if description:
                    content += f"{description}\n\n"
                content += table_md
                
                return {
                    'title': title,
                    'content': content,
                    'type': 'table',
                    'data': data
                }
                
            except Exception as e:
                if self.debug:
                    print(f"Error creating table section: {str(e)}")
                    import traceback
                    traceback.print_exc()
                return self.create_section(
                    title,
                    f"Error creating table: {str(e)}"
                )
        
        def create_chart_section(
            self,
            title: str,
            chart: Any,
            description: Optional[str] = None,
            **kwargs
        ) -> Dict[str, Any]:
            """Create a chart section."""
            try:
                content = ""
                if description:
                    content += f"{description}\n\n"
                    
                # For Markdown, we can only reference images, not embed them directly
                if isinstance(chart, (str, Path)) and str(chart).endswith(('.png', '.jpg', '.jpeg', '.svg')):
                    # It's a path to an image file
                    content += f"![{title}]({chart})"
                elif isinstance(chart, plt.Figure):
                    # For matplotlib figures, we need to save them first
                    content += f"*Chart: {title}*\n\n"
                    content += "(Chart image would be saved separately and linked here)"
                else:
                    # Just add as text
                    content += f"*Chart: {title}*\n\n{str(chart)}"
                    
                return {
                    'title': title,
                    'content': content,
                    'type': 'chart'
                }
                
            except Exception as e:
                if self.debug:
                    print(f"Error creating chart section: {str(e)}")
                    import traceback
                    traceback.print_exc()
                return self.create_section(
                    title,
                    f"Error creating chart: {str(e)}"
                )
        
        def create_stats_section(
            self,
            title: str,
            stats: Dict[str, Any],
            description: Optional[str] = None,
            **kwargs
        ) -> Dict[str, Any]:
            """Create a statistics section."""
            try:
                content = ""
                if description:
                    content += f"{description}\n\n"
                    
                # Create stats list
                for key, value in stats.items():
                    # Format key for display
                    display_key = key.replace('_', ' ').title()
                    
                    # Format value
                    if isinstance(value, (int, float)):
                        display_value = f"{value:,}"
                        if key.endswith('_percent'):
                            display_value = f"{value:.1f}%"
                    else:
                        display_value = str(value)
                        
                    # Add to content
                    content += f"- **{display_key}**: {display_value}\n"
                    
                return {
                    'title': title,
                    'content': content,
                    'type': 'stats'
                }
                
            except Exception as e:
                if self.debug:
                    print(f"Error creating stats section: {str(e)}")
                    import traceback
                    traceback.print_exc()
                return self.create_section(
                    title,
                    f"Error creating stats: {str(e)}"
                )
        
        def save_report(
            self,
            report: str,
            output_file: Union[str, Path],
            **kwargs
        ) -> bool:
            """Save the report to a file."""
            try:
                # Ensure output_file is a Path object
                if isinstance(output_file, str):
                    output_file = Path(output_file)
                    
                # Ensure the directory exists
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Write the report
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report)
                    
                return True
                
            except Exception as e:
                if self.debug:
                    print(f"Error saving report: {str(e)}")
                    import traceback
                    traceback.print_exc()
                return False
        
        def _generate_section_markdown(self, section: Dict[str, Any]) -> str:
            """Generate Markdown for a section."""
            title = section.get('title', '')
            content = section.get('content', '')
            
            return f"## {title}\n\n{content}"
    ```

- [ ] **Test the Markdown Report Service**
  - [ ] Create a test script to verify the service
  - [ ] Test each section type with sample data

### 5. Report Generator Implementation

- [ ] **Create Report Generator Class**
  - [ ] Create `src/visualization/reports/report_generator.py` with the following content:
    ```python
    # src/visualization/reports/report_generator.py
    from typing import Dict, Any, Optional, List, Union
    from pathlib import Path
    import os
    import tempfile
    from .html_report_service import HTMLReportService
    from .markdown_report_service import MarkdownReportService
    from visualization.services.chart_manager import ChartManager

    class ReportGenerator:
        """Generator for comprehensive reports."""
        
        def __init__(
            self,
            report_service=None,
            chart_manager=None,
            debug: bool = False
        ):
            self.debug = debug
            self.report_service = report_service or HTMLReportService(debug=debug)
            self.chart_manager = chart_manager or ChartManager(debug=debug)
            
        def generate_player_report(
            self,
            data: Dict[str, Any],
            output_file: Optional[Union[str, Path]] = None,
            include_charts: bool = True,
            include_tables: bool = True,
            include_stats: bool = True
        ) -> str:
            """
            Generate a player performance report.
            
            Args:
                data: Analysis data
                output_file: Optional file to write the report to
                include_charts: Whether to include charts
                include_tables: Whether to include tables
                include_stats: Whether to include statistics
                
            Returns:
                Report content as string
            """
            # Create report sections
            sections = []
            
            try:
                # Create temporary directory for charts if needed
                chart_dir = None
                if include_charts:
                    chart_dir = Path(tempfile.mkdtemp())
                
                # 1. Overview section
                if include_stats and 'player_overview' in data:
                    overview = data['player_overview']
                    sections.append(
                        self.report_service.create_stats_section(
                            "Player Overview",
                            overview,
                            "Summary statistics for player performance."
                        )
                    )
                    
                # 2. Top performers section
                if include_tables and 'player_analysis' in data and 'performance' in data['player_analysis']:
                    performance = data['player_analysis']['performance']
                    if 'top_performers' in performance:
                        sections.append(
                            self.report_service.create_table_section(
                                "Top Performers",
                                performance['top_performers'],
                                "Players with the highest total scores."
                            )
                        )
                        
                # 3. Performance charts
                if include_charts:
                    # Generate charts
                    player_charts = self.chart_manager.create_player_charts(data, chart_dir)
                    
                    # Add charts to report
                    for chart_name, chart in player_charts.items():
                        if chart_name == 'player_performance':
                            sections.append(
                                self.report_service.create_chart_section(
                                    "Player Performance",
                                    chart,
                                    "Total scores by player."
                                )
                            )
                        elif chart_name == 'player_efficiency':
                            sections.append(
                                self.report_service.create_chart_section(
                                    "Player Efficiency",
                                    chart,
                                    "Score per chest by player."
                                )
                            )
                            
                # 4. Player source effectiveness
                if include_tables and 'player_analysis' in data and 'source_effectiveness' in data['player_analysis']:
                    source_data = data['player_analysis']['source_effectiveness']
                    if 'most_effective_source' in source_data:
                        sections.append(
                            self.report_service.create_table_section(
                                "Most Effective Sources by Player",
                                source_data['most_effective_source'],
                                "The most effective source for each player based on average score."
                            )
                        )
                        
                # 5. Time trends
                if include_charts and 'player_analysis' in data and 'time_trends' in data['player_analysis']:
                    # Time trend charts could be added here
                    pass
                    
                # Create the report
                report_data = {
                    'title': 'Player Performance Report',
                    'sections': sections
                }
                
                return self.report_service.create_report(
                    report_data,
                    output_file=output_file,
                    title="Player Performance Report"
                )
                
            except Exception as e:
                if self.debug:
                    print(f"Error generating player report: {str(e)}")
                    import traceback
                    traceback.print_exc()
                return "Error generating report"
            
        def generate_chest_report(
            self,
            data: Dict[str, Any],
            output_file: Optional[Union[str, Path]] = None,
            include_charts: bool = True,
            include_tables: bool = True,
            include_stats: bool = True
        ) -> str:
            """Generate a chest analysis report."""
            # Implementation similar to player report
            # ...
            
        def generate_source_report(
            self,
            data: Dict[str, Any],
            output_file: Optional[Union[str, Path]] = None,
            include_charts: bool = True,
            include_tables: bool = True,
            include_stats: bool = True
        ) -> str:
            """Generate a source analysis report."""
            # Implementation similar to player report
            # ...
            
        def generate_comprehensive_report(
            self,
            data: Dict[str, Any],
            output_file: Optional[Union[str, Path]] = None,
            include_charts: bool = True,
            include_tables: bool = True,
            include_stats: bool = True
        ) -> str:
            """Generate a comprehensive analysis report."""
            # Implementation combining all report types
            # ...
    ```

- [ ] **Test the Report Generator**
  - [ ] Create a test script to verify the report generator
  - [ ] Test with sample analysis data and chart data

### 6. Integration with Analysis and Visualization Services

- [ ] **Create Integration Tests**
  - [ ] Create tests that use analysis services to generate data
  - [ ] Use chart services to create visualizations
  - [ ] Use report services to generate reports with the analysis and charts
  - [ ] Verify that the integration works correctly

- [ ] **Optimize Report Generation**
  - [ ] Profile report generation performance
  - [ ] Implement optimizations for slow operations
  - [ ] Test optimizations to ensure they improve performance

### 7. Report Templates

- [ ] **Create Report Template System**
  - [ ] Create `src/visualization/reports/templates` directory
  - [ ] Implement a template loading mechanism
  - [ ] Create standard templates for different report types

- [ ] **Add Template Support to Report Services**
  - [ ] Update report services to use templates
  - [ ] Allow customization of templates

### 8. Documentation

- [ ] **Update Report Service Documentation**
  - [ ] Add detailed docstrings to all classes and methods
  - [ ] Create examples for common report generation tasks
  - [ ] Document error handling and debugging procedures

- [ ] **Create Report Service Guide**
  - [ ] Create a guide for using the report services
  - [ ] Include examples of common report generation scenarios
  - [ ] Add troubleshooting section for common issues

### 9. Part 3 Validation

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

After completing Part 3 of Phase 3, please provide feedback on the following aspects:

1. Are the reporting services comprehensive enough for your needs?
2. Are there any additional report types or formats that should be included?
3. Is the report content and styling appropriate for the application?
4. Does the implementation align with the overall refactoring goals?
5. Any suggestions for improvements before proceeding to Part 4? 