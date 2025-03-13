# Report Generation Screen Implementation

The Report Generation Screen is the final major component of the Total Battle Analyzer application, allowing users to compile and export comprehensive reports of their game data analysis. This screen will utilize the report services implemented in Phase 3 to create customized reports in various formats.

## Implementation Tasks

- [ ] **Create Report Screen Class**
  - [ ] Implement the main screen class in `src/ui/screens/report_screen.py`
  - [ ] Create the report configuration panel with options for:
    - Report type selection (comprehensive, summary, focused)
    - Data source selection
    - Content customization options
    - Format selection (HTML, PDF, Markdown)
  - [ ] Implement report generation functionality
  - [ ] Add report preview capabilities

- [ ] **Create Report Preview Widget**
  - [ ] Create a specialized widget in `src/ui/widgets/report_preview.py`
  - [ ] Support rendering of HTML and Markdown content
  - [ ] Implement zooming and navigation controls

- [ ] **Create Report Template Selector**
  - [ ] Implement a widget for selecting and customizing report templates
  - [ ] Support template preview and selection

- [ ] **Update Report Services Integration**
  - [ ] Ensure proper integration with Phase 3 reporting services
  - [ ] Implement data preparation for different report types
  - [ ] Support embedding charts and tables in reports

- [ ] **Integrate with Main Window**
  - [ ] Register the Report Screen in the screen factory
  - [ ] Add navigation from Analysis and Charts screens
  - [ ] Implement data passing between screens

## Implementation Details

### 1. Report Screen Class

The Report Screen will be implemented as follows:

```python
# src/ui/screens/report_screen.py
from typing import Dict, Any, Optional, List
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QSplitter, QTabWidget,
    QComboBox, QCheckBox, QGroupBox, QRadioButton,
    QScrollArea, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QIcon, QPixmap

from ..widgets.report_preview import ReportPreviewWidget
from ...services.report_service import ReportService
from ...visualization.report_generator import ReportGenerator
from ..base_screen import BaseScreen

class ReportScreen(BaseScreen):
    """Screen for creating and exporting reports."""
    
    # Custom signals
    report_generated = Signal(dict)
    
    def __init__(self, parent=None):
        """
        Initialize the report screen.
        
        Args:
            parent: Optional parent widget
        """
        # Initialize services
        self.report_service = ReportService()
        self.report_generator = ReportGenerator()
        
        # Initialize base class
        super().__init__(parent)
        
    def _setup_ui(self):
        """Set up the user interface."""
        # Create header
        self.header = QLabel("Report Generation")
        self.header.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #D4AF37; margin: 10px;"
        )
        
        # Create control panel
        self.control_panel = QFrame()
        self.control_panel.setFrameShape(QFrame.StyledPanel)
        self.control_panel.setStyleSheet(
            "background-color: #2A374F; border-radius: 5px; padding: 10px;"
        )
        self.control_panel.setMaximumWidth(300)
        
        self.control_layout = QVBoxLayout(self.control_panel)
        
        # Create report configuration sections
        self._setup_report_type_section()
        self._setup_content_section()
        self._setup_format_section()
        self._setup_action_buttons()
        
        # Create report preview area
        self.preview_area = QFrame()
        self.preview_area.setFrameShape(QFrame.StyledPanel)
        self.preview_area.setStyleSheet(
            "background-color: #1A2742; border-radius: 5px;"
        )
        
        self.preview_layout = QVBoxLayout(self.preview_area)
        
        self.preview_header = QLabel("Report Preview")
        self.preview_header.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #D4AF37; padding: 5px;"
        )
        
        self.report_preview = ReportPreviewWidget()
        
        self.preview_layout.addWidget(self.preview_header)
        self.preview_layout.addWidget(self.report_preview, 1)
        
        # Create main content area with splitter
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.control_panel)
        self.splitter.addWidget(self.preview_area)
        self.splitter.setSizes([300, 700])  # Initial sizes
        
        # Add components to main layout
        self.layout.addWidget(self.header)
        self.layout.addWidget(self.splitter, 1)  # Give splitter stretch priority
    
    def _setup_report_type_section(self):
        """Set up the report type selection section."""
        # Report type group
        self.type_group = QGroupBox("Report Type")
        self.type_group.setStyleSheet(
            "QGroupBox { color: #FFFFFF; border: 1px solid #D4AF37; border-radius: 3px; padding: 5px; }"
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; }"
        )
        self.type_layout = QVBoxLayout(self.type_group)
        
        # Report type radio buttons
        self.comprehensive_report = QRadioButton("Comprehensive Report")
        self.comprehensive_report.setStyleSheet("color: #FFFFFF;")
        self.comprehensive_report.setChecked(True)
        
        self.summary_report = QRadioButton("Summary Report")
        self.summary_report.setStyleSheet("color: #FFFFFF;")
        
        self.chest_report = QRadioButton("Chest Analysis Report")
        self.chest_report.setStyleSheet("color: #FFFFFF;")
        
        self.source_report = QRadioButton("Source Analysis Report")
        self.source_report.setStyleSheet("color: #FFFFFF;")
        
        self.player_report = QRadioButton("Player Analysis Report")
        self.player_report.setStyleSheet("color: #FFFFFF;")
        
        # Add buttons to layout
        self.type_layout.addWidget(self.comprehensive_report)
        self.type_layout.addWidget(self.summary_report)
        self.type_layout.addWidget(self.chest_report)
        self.type_layout.addWidget(self.source_report)
        self.type_layout.addWidget(self.player_report)
        
        # Add to control panel
        self.control_layout.addWidget(self.type_group)
    
    def _setup_content_section(self):
        """Set up the report content customization section."""
        # Content group
        self.content_group = QGroupBox("Report Content")
        self.content_group.setStyleSheet(
            "QGroupBox { color: #FFFFFF; border: 1px solid #D4AF37; border-radius: 3px; padding: 5px; }"
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; }"
        )
        self.content_layout = QVBoxLayout(self.content_group)
        
        # Content checkboxes
        self.include_summary = QCheckBox("Include Summary")
        self.include_summary.setStyleSheet("color: #FFFFFF;")
        self.include_summary.setChecked(True)
        
        self.include_tables = QCheckBox("Include Data Tables")
        self.include_tables.setStyleSheet("color: #FFFFFF;")
        self.include_tables.setChecked(True)
        
        self.include_charts = QCheckBox("Include Charts")
        self.include_charts.setStyleSheet("color: #FFFFFF;")
        self.include_charts.setChecked(True)
        
        self.include_statistics = QCheckBox("Include Statistics")
        self.include_statistics.setStyleSheet("color: #FFFFFF;")
        self.include_statistics.setChecked(True)
        
        # Add checkboxes to layout
        self.content_layout.addWidget(self.include_summary)
        self.content_layout.addWidget(self.include_tables)
        self.content_layout.addWidget(self.include_charts)
        self.content_layout.addWidget(self.include_statistics)
        
        # Add to control panel
        self.control_layout.addWidget(self.content_group)
    
    def _setup_format_section(self):
        """Set up the report format selection section."""
        # Format group
        self.format_group = QGroupBox("Report Format")
        self.format_group.setStyleSheet(
            "QGroupBox { color: #FFFFFF; border: 1px solid #D4AF37; border-radius: 3px; padding: 5px; }"
            "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; }"
        )
        self.format_layout = QVBoxLayout(self.format_group)
        
        # Format selection
        self.format_label = QLabel("Output Format:")
        self.format_label.setStyleSheet("color: #FFFFFF;")
        
        self.format_selector = QComboBox()
        self.format_selector.setStyleSheet(
            "background-color: #1A2742; color: #FFFFFF; padding: 5px;"
        )
        self.format_selector.addItems(["HTML", "PDF", "Markdown"])
        
        # Add to layout
        self.format_layout.addWidget(self.format_label)
        self.format_layout.addWidget(self.format_selector)
        
        # Add to control panel
        self.control_layout.addWidget(self.format_group)
    
    def _setup_action_buttons(self):
        """Set up action buttons for generating and exporting reports."""
        # Generate button
        self.generate_button = QPushButton("Generate Report")
        self.generate_button.setStyleSheet(
            "background-color: #D4AF37; color: #1A2742; font-weight: bold; "
            "padding: 10px; border-radius: 5px; margin-top: 20px;"
        )
        self.generate_button.clicked.connect(self._on_generate_clicked)
        
        # Export button
        self.export_button = QPushButton("Export Report")
        self.export_button.setStyleSheet(
            "background-color: #D4AF37; color: #1A2742; font-weight: bold; "
            "padding: 10px; border-radius: 5px; margin-top: 10px;"
        )
        self.export_button.clicked.connect(self._on_export_clicked)
        self.export_button.setEnabled(False)  # Initially disabled
        
        # Add to control panel
        self.control_layout.addWidget(self.generate_button)
        self.control_layout.addWidget(self.export_button)
        self.control_layout.addStretch()
    
    def load_data(self, data: Dict[str, Any]) -> None:
        """
        Load data into the screen.
        
        Args:
            data: Dictionary containing the data to load
        """
        super().load_data(data)
        
        # Check what data is available
        has_analysis = 'analysis_results' in self._data
        has_chest = has_analysis and 'chest' in self._data['analysis_results']
        has_source = has_analysis and 'source' in self._data['analysis_results']
        has_player = has_analysis and 'player' in self._data['analysis_results']
        
        # Enable/disable report types based on available data
        self.comprehensive_report.setEnabled(has_analysis)
        self.summary_report.setEnabled(has_analysis)
        self.chest_report.setEnabled(has_chest)
        self.source_report.setEnabled(has_source)
        self.player_report.setEnabled(has_player)
        
        # If no data is available, show message
        if not has_analysis:
            self.report_preview.show_message(
                "No analysis data available. Please run analysis first."
            )
            self.generate_button.setEnabled(False)
        else:
            self.report_preview.show_message(
                "Select report options and click 'Generate Report' to preview."
            )
            self.generate_button.setEnabled(True)
    
    def _on_generate_clicked(self):
        """Handle generate report button click."""
        if 'analysis_results' not in self._data:
            QMessageBox.warning(
                self,
                "Report Error",
                "No analysis results available for creating a report"
            )
            return
        
        # Get report configuration
        config = self._get_report_config()
        
        try:
            # Generate the report
            report_content = self.report_generator.generate_report(
                self._data['analysis_results'],
                config
            )
            
            # Store in data
            self._data['current_report'] = {
                'content': report_content,
                'config': config
            }
            
            # Show preview
            self.report_preview.set_content(
                report_content,
                format_type=config['format']
            )
            
            # Enable export button
            self.export_button.setEnabled(True)
            
            # Emit signal
            self.report_generated.emit(self._data['current_report'])
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Report Error",
                f"Error generating report: {str(e)}"
            )
    
    def _get_report_config(self) -> Dict[str, Any]:
        """
        Get the current report configuration from the UI.
        
        Returns:
            Dictionary containing report configuration
        """
        # Determine report type
        if self.comprehensive_report.isChecked():
            report_type = "comprehensive"
        elif self.summary_report.isChecked():
            report_type = "summary"
        elif self.chest_report.isChecked():
            report_type = "chest"
        elif self.source_report.isChecked():
            report_type = "source"
        elif self.player_report.isChecked():
            report_type = "player"
        else:
            report_type = "comprehensive"  # Default
        
        # Get output format
        output_format = self.format_selector.currentText().lower()
        
        # Create config
        config = {
            'type': report_type,
            'format': output_format,
            'include_summary': self.include_summary.isChecked(),
            'include_tables': self.include_tables.isChecked(),
            'include_charts': self.include_charts.isChecked(),
            'include_statistics': self.include_statistics.isChecked()
        }
        
        return config
    
    def _on_export_clicked(self):
        """Handle export report button click."""
        if 'current_report' not in self._data or 'content' not in self._data['current_report']:
            QMessageBox.warning(
                self,
                "Export Error",
                "No report to export"
            )
            return
        
        # Get report format
        output_format = self._data['current_report']['config']['format']
        
        # Define file extension based on format
        format_extensions = {
            'html': '.html',
            'pdf': '.pdf',
            'markdown': '.md'
        }
        extension = format_extensions.get(output_format, '.txt')
        
        # Get file path for saving
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Report",
            str(Path.home() / f"report{extension}"),
            f"{output_format.upper()} Files (*{extension})"
        )
        
        if not file_path:
            return
        
        try:
            # Export the report
            self.report_service.export_report(
                self._data['current_report']['content'],
                Path(file_path),
                output_format
            )
            
            QMessageBox.information(
                self,
                "Export Successful",
                f"Report exported to {file_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Error exporting report: {str(e)}"
            )
```

### 2. Report Preview Widget

The Report Preview Widget will support rendering reports in different formats:

```python
# src/ui/widgets/report_preview.py
from typing import Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextBrowser, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal, Slot, QUrl, QSize
from PySide6.QtGui import QFont

class ReportPreviewWidget(QWidget):
    """Widget for displaying report previews."""
    
    def __init__(self, parent=None):
        """
        Initialize the report preview widget.
        
        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)
        
        # Set up the layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Create the preview browser
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setStyleSheet(
            "background-color: #FFFFFF; color: #000000; padding: 10px;"
        )
        
        # Add to layout
        self.layout.addWidget(self.browser)
        
    def set_content(self, content: str, format_type: str = 'html') -> None:
        """
        Set content to display in the preview.
        
        Args:
            content: The content to display
            format_type: The format of the content ('html', 'markdown', 'text')
        """
        if format_type.lower() == 'html':
            self.browser.setHtml(content)
        elif format_type.lower() == 'markdown':
            # Use Qt's Markdown support if available
            if hasattr(self.browser, 'setMarkdown'):
                self.browser.setMarkdown(content)
            else:
                # Basic fallback: display as plain text
                self.browser.setPlainText(content)
        else:
            # Default to plain text
            self.browser.setPlainText(content)
            
    def show_message(self, message: str) -> None:
        """
        Show a message in the preview area.
        
        Args:
            message: The message to display
        """
        html = f"""
        <div style="text-align: center; margin-top: 50px; color: #888888; font-size: 16px;">
            <p>{message}</p>
        </div>
        """
        self.browser.setHtml(html)
```

### 3. Integration with Other Screens

- The Report Screen should be accessible from the Analysis and Charts screens
- Add navigation buttons to enable easy movement between screens
- Implement proper data sharing to ensure analysis results are available for report generation
- Support saving and loading of report configurations for reuse 