# Analysis Screen Implementation

The Analysis Screen is a core component of the Total Battle Analyzer application that provides users with insights into their game data. This screen will leverage the analysis services implemented in Phase 3 to process data and visualize results in various formats.

## Implementation Tasks

- [ ] **Create Analysis Screen Class**
  - [ ] Create `src/ui/screens/analysis_screen.py` with the following content:
    ```python
    # src/ui/screens/analysis_screen.py
    from typing import Dict, Any, Optional, List
    from pathlib import Path
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
        QPushButton, QFrame, QSplitter, QTabWidget,
        QComboBox, QSpinBox, QCheckBox, QGroupBox,
        QScrollArea, QMessageBox, QStackedWidget,
        QFileDialog
    )
    from PySide6.QtCore import Qt, Signal, Slot, QSize
    from PySide6.QtGui import QIcon, QPixmap

    from ..widgets.data_table import DataTableWidget
    from ..widgets.summary_widget import SummaryWidget
    from ...services.analysis_service import AnalysisService
    from ...services.chest_analysis_service import ChestAnalysisService
    from ...services.source_analysis_service import SourceAnalysisService
    from ..base_screen import BaseScreen

    class AnalysisScreen(BaseScreen):
        """Screen for analyzing data and displaying results."""
        
        # Custom signals
        analysis_complete = Signal(dict)
        
        def __init__(self, parent=None):
            """
            Initialize the analysis screen.
            
            Args:
                parent: Optional parent widget
            """
            # Initialize services
            self.analysis_service = AnalysisService()
            self.chest_analysis_service = ChestAnalysisService()
            self.source_analysis_service = SourceAnalysisService()
            
            # Initialize base class
            super().__init__(parent)
            
        def _setup_ui(self):
            """Set up the user interface."""
            # Create header
            self.header = QLabel("Data Analysis")
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
            
            # Create control components
            self.control_header = QLabel("Analysis Controls")
            self.control_header.setStyleSheet(
                "font-size: 16px; font-weight: bold; color: #D4AF37; padding: 5px;"
            )
            
            # Analysis type selection
            self.type_group = QGroupBox("Analysis Type")
            self.type_group.setStyleSheet(
                "QGroupBox { color: #FFFFFF; border: 1px solid #D4AF37; border-radius: 3px; padding: 5px; }"
                "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; }"
            )
            self.type_layout = QVBoxLayout(self.type_group)
            
            self.analysis_type = QComboBox()
            self.analysis_type.setStyleSheet(
                "background-color: #1A2742; color: #FFFFFF; padding: 5px;"
            )
            self.analysis_type.addItems([
                "All Analysis", 
                "Chest Analysis", 
                "Source Analysis",
                "Player Analysis"
            ])
            
            self.type_layout.addWidget(self.analysis_type)
            
            # Date range options
            self.date_group = QGroupBox("Date Range")
            self.date_group.setStyleSheet(
                "QGroupBox { color: #FFFFFF; border: 1px solid #D4AF37; border-radius: 3px; padding: 5px; }"
                "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; }"
            )
            self.date_layout = QVBoxLayout(self.date_group)
            
            self.use_all_dates = QCheckBox("Use All Available Dates")
            self.use_all_dates.setStyleSheet("color: #FFFFFF;")
            self.use_all_dates.setChecked(True)
            
            self.date_range_selector = QComboBox()
            self.date_range_selector.setStyleSheet(
                "background-color: #1A2742; color: #FFFFFF; padding: 5px;"
            )
            self.date_range_selector.addItems([
                "Last 7 Days",
                "Last 30 Days",
                "Last 90 Days",
                "Last 365 Days",
                "Custom Range"
            ])
            self.date_range_selector.setEnabled(False)
            
            self.date_layout.addWidget(self.use_all_dates)
            self.date_layout.addWidget(self.date_range_selector)
            
            # Analysis options
            self.options_group = QGroupBox("Analysis Options")
            self.options_group.setStyleSheet(
                "QGroupBox { color: #FFFFFF; border: 1px solid #D4AF37; border-radius: 3px; padding: 5px; }"
                "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; }"
            )
            self.options_layout = QVBoxLayout(self.options_group)
            
            self.include_summary = QCheckBox("Generate Summary")
            self.include_summary.setStyleSheet("color: #FFFFFF;")
            self.include_summary.setChecked(True)
            
            self.include_detailed_tables = QCheckBox("Generate Detailed Tables")
            self.include_detailed_tables.setStyleSheet("color: #FFFFFF;")
            self.include_detailed_tables.setChecked(True)
            
            self.include_top_items = QCheckBox("Include Top Items")
            self.include_top_items.setStyleSheet("color: #FFFFFF;")
            self.include_top_items.setChecked(True)
            
            self.top_items_count_layout = QHBoxLayout()
            self.top_items_count_label = QLabel("Number of items:")
            self.top_items_count_label.setStyleSheet("color: #FFFFFF;")
            self.top_items_count = QSpinBox()
            self.top_items_count.setMinimum(1)
            self.top_items_count.setMaximum(100)
            self.top_items_count.setValue(10)
            self.top_items_count.setStyleSheet(
                "background-color: #1A2742; color: #FFFFFF; padding: 5px;"
            )
            
            self.top_items_count_layout.addWidget(self.top_items_count_label)
            self.top_items_count_layout.addWidget(self.top_items_count)
            
            self.options_layout.addWidget(self.include_summary)
            self.options_layout.addWidget(self.include_detailed_tables)
            self.options_layout.addWidget(self.include_top_items)
            self.options_layout.addLayout(self.top_items_count_layout)
            
            # Action buttons
            self.run_analysis_button = QPushButton("Run Analysis")
            self.run_analysis_button.setStyleSheet(
                "background-color: #D4AF37; color: #1A2742; font-weight: bold; "
                "padding: 10px; border-radius: 5px; margin-top: 20px;"
            )
            
            self.export_results_button = QPushButton("Export Results")
            self.export_results_button.setStyleSheet(
                "background-color: #D4AF37; color: #1A2742; font-weight: bold; "
                "padding: 10px; border-radius: 5px; margin-top: 10px;"
            )
            self.export_results_button.setEnabled(False)  # Disabled until analysis is run
            
            # Add components to control layout
            self.control_layout.addWidget(self.control_header)
            self.control_layout.addWidget(self.type_group)
            self.control_layout.addWidget(self.date_group)
            self.control_layout.addWidget(self.options_group)
            self.control_layout.addWidget(self.run_analysis_button)
            self.control_layout.addWidget(self.export_results_button)
            self.control_layout.addStretch()
            
            # Create results area
            self.results_area = QStackedWidget()
            self.results_area.setFrameShape(QFrame.StyledPanel)
            self.results_area.setStyleSheet(
                "background-color: #1A2742; border-radius: 5px;"
            )
            
            # Create welcome/placeholder page
            self.welcome_widget = QWidget()
            self.welcome_layout = QVBoxLayout(self.welcome_widget)
            
            self.welcome_label = QLabel(
                "Select analysis options and click 'Run Analysis' to get started",
                alignment=Qt.AlignCenter
            )
            self.welcome_label.setStyleSheet(
                "font-size: 16px; color: #FFFFFF; margin: 20px;"
            )
            
            self.welcome_layout.addStretch()
            self.welcome_layout.addWidget(self.welcome_label)
            self.welcome_layout.addStretch()
            
            # Create results tab widget
            self.results_tabs = QTabWidget()
            self.results_tabs.setStyleSheet(
                "QTabWidget::pane { border: 1px solid #D4AF37; background-color: #1A2742; }"
                "QTabBar::tab { background-color: #2A374F; color: #FFFFFF; padding: 8px 16px; margin-right: 2px; }"
                "QTabBar::tab:selected { background-color: #D4AF37; color: #1A2742; font-weight: bold; }"
            )
            
            # Create summary tab
            self.summary_tab = QWidget()
            self.summary_layout = QVBoxLayout(self.summary_tab)
            self.summary_widget = SummaryWidget()
            self.summary_layout.addWidget(self.summary_widget)
            
            # Create chest analysis tab
            self.chest_tab = QWidget()
            self.chest_layout = QVBoxLayout(self.chest_tab)
            self.chest_table = DataTableWidget()
            self.chest_layout.addWidget(self.chest_table)
            
            # Create source analysis tab
            self.source_tab = QWidget()
            self.source_layout = QVBoxLayout(self.source_tab)
            self.source_table = DataTableWidget()
            self.source_layout.addWidget(self.source_table)
            
            # Create player analysis tab
            self.player_tab = QWidget()
            self.player_layout = QVBoxLayout(self.player_tab)
            self.player_table = DataTableWidget()
            self.player_layout.addWidget(self.player_table)
            
            # Add tabs to tab widget
            self.results_tabs.addTab(self.summary_tab, "Summary")
            self.results_tabs.addTab(self.chest_tab, "Chest Analysis")
            self.results_tabs.addTab(self.source_tab, "Source Analysis")
            self.results_tabs.addTab(self.player_tab, "Player Analysis")
            
            # Add widgets to stacked widget
            self.results_area.addWidget(self.welcome_widget)
            self.results_area.addWidget(self.results_tabs)
            
            # Show welcome widget initially
            self.results_area.setCurrentWidget(self.welcome_widget)
            
            # Create main content area with splitter
            self.splitter = QSplitter(Qt.Horizontal)
            self.splitter.addWidget(self.control_panel)
            self.splitter.addWidget(self.results_area)
            self.splitter.setSizes([300, 700])  # Initial sizes
            
            # Add components to main layout
            self.layout.addWidget(self.header)
            self.layout.addWidget(self.splitter, 1)  # Give splitter stretch priority
            
            # Connect signals
            self.use_all_dates.toggled.connect(self._on_use_all_dates_toggled)
            self.include_top_items.toggled.connect(self._on_include_top_items_toggled)
            self.run_analysis_button.clicked.connect(self._on_run_analysis_clicked)
            self.export_results_button.clicked.connect(self._on_export_results_clicked)
            self.analysis_type.currentIndexChanged.connect(self._on_analysis_type_changed)
            
        def _on_use_all_dates_toggled(self, checked: bool) -> None:
            """
            Handle use all dates checkbox toggled.
            
            Args:
                checked: Whether the checkbox is checked
            """
            self.date_range_selector.setEnabled(not checked)
            
        def _on_include_top_items_toggled(self, checked: bool) -> None:
            """
            Handle include top items checkbox toggled.
            
            Args:
                checked: Whether the checkbox is checked
            """
            self.top_items_count.setEnabled(checked)
            self.top_items_count_label.setEnabled(checked)
            
        def _on_analysis_type_changed(self, index: int) -> None:
            """
            Handle analysis type selection change.
            
            Args:
                index: Index of the selected analysis type
            """
            # Enable/disable options based on selected analysis type
            analysis_type = self.analysis_type.currentText()
            
            # Adjust UI based on selected type
            # This could be expanded later for type-specific options
            pass
            
        def _on_run_analysis_clicked(self) -> None:
            """Handle run analysis button click."""
            if 'raw_data' not in self._data or self._data['raw_data'].empty:
                QMessageBox.warning(
                    self,
                    "Analysis Error",
                    "No data available for analysis"
                )
                return
                
            # Get analysis options
            options = self._get_analysis_options()
            
            # Show loading indicator or progress
            self.run_analysis_button.setEnabled(False)
            self.run_analysis_button.setText("Running...")
            
            try:
                # Run the analysis based on type
                analysis_type = self.analysis_type.currentText()
                results = {}
                
                # Run selected analyses
                if analysis_type == "All Analysis" or analysis_type == "Chest Analysis":
                    chest_results = self.chest_analysis_service.analyze(
                        self._data['raw_data'], 
                        options
                    )
                    results['chest'] = chest_results
                    
                if analysis_type == "All Analysis" or analysis_type == "Source Analysis":
                    source_results = self.source_analysis_service.analyze(
                        self._data['raw_data'], 
                        options
                    )
                    results['source'] = source_results
                    
                if analysis_type == "All Analysis" or analysis_type == "Player Analysis":
                    player_results = self.analysis_service.analyze_players(
                        self._data['raw_data'], 
                        options
                    )
                    results['player'] = player_results
                
                # Generate summary if requested
                if options.get('include_summary', True):
                    summary = self.analysis_service.generate_summary(results)
                    results['summary'] = summary
                
                # Update UI with results
                self._update_results_ui(results)
                
                # Store results in data
                self._data['analysis_results'] = results
                
                # Emit signals
                self.analysis_complete.emit(results)
                self.data_changed.emit()
                
                # Enable export button
                self.export_results_button.setEnabled(True)
                
                # Show results tab
                self.results_area.setCurrentWidget(self.results_tabs)
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Analysis Error",
                    f"Error running analysis: {str(e)}"
                )
            finally:
                # Reset button
                self.run_analysis_button.setEnabled(True)
                self.run_analysis_button.setText("Run Analysis")
                
        def _get_analysis_options(self) -> Dict[str, Any]:
            """
            Get the current analysis options from the UI.
            
            Returns:
                Dictionary containing analysis options
            """
            options = {
                'analysis_type': self.analysis_type.currentText(),
                'include_summary': self.include_summary.isChecked(),
                'include_detailed_tables': self.include_detailed_tables.isChecked(),
                'include_top_items': self.include_top_items.isChecked(),
                'top_items_count': self.top_items_count.value() if self.include_top_items.isChecked() else 0,
                'use_all_dates': self.use_all_dates.isChecked(),
                'date_range': self.date_range_selector.currentText() if not self.use_all_dates.isChecked() else None
            }
            return options
            
        def _update_results_ui(self, results: Dict[str, Any]) -> None:
            """
            Update the UI with analysis results.
            
            Args:
                results: Dictionary containing analysis results
            """
            # Update summary widget if summary is available
            if 'summary' in results:
                self.summary_widget.set_data(results['summary'])
                
            # Update chest table if chest results are available
            if 'chest' in results and 'data' in results['chest']:
                self.chest_table.set_data(results['chest']['data'])
                
            # Update source table if source results are available
            if 'source' in results and 'data' in results['source']:
                self.source_table.set_data(results['source']['data'])
                
            # Update player table if player results are available
            if 'player' in results and 'data' in results['player']:
                self.player_table.set_data(results['player']['data'])
                
            # Show appropriate tabs based on which analyses were run
            analysis_type = self.analysis_type.currentText()
            
            if analysis_type == "All Analysis":
                # Show all tabs
                for i in range(self.results_tabs.count()):
                    self.results_tabs.setTabVisible(i, True)
                # Set summary tab as active
                self.results_tabs.setCurrentIndex(0)
            else:
                # Show only relevant tabs
                self.results_tabs.setTabVisible(0, 'summary' in results)  # Summary tab
                self.results_tabs.setTabVisible(1, analysis_type == "Chest Analysis" or analysis_type == "All Analysis")
                self.results_tabs.setTabVisible(2, analysis_type == "Source Analysis" or analysis_type == "All Analysis")
                self.results_tabs.setTabVisible(3, analysis_type == "Player Analysis" or analysis_type == "All Analysis")
                
                # Set appropriate tab as active
                if analysis_type == "Chest Analysis":
                    self.results_tabs.setCurrentIndex(1)
                elif analysis_type == "Source Analysis":
                    self.results_tabs.setCurrentIndex(2)
                elif analysis_type == "Player Analysis":
                    self.results_tabs.setCurrentIndex(3)
                else:
                    self.results_tabs.setCurrentIndex(0)
            
        def _on_export_results_clicked(self) -> None:
            """Handle export results button click."""
            if 'analysis_results' not in self._data:
                QMessageBox.warning(
                    self,
                    "Export Error",
                    "No analysis results to export"
                )
                return
                
            # Get directory path for saving
            dir_path = QFileDialog.getExistingDirectory(
                self,
                "Select Export Directory",
                str(Path.home())
            )
            
            if not dir_path:
                return
                
            try:
                # Convert to Path
                export_dir = Path(dir_path)
                
                # Ensure directory exists
                export_dir.mkdir(parents=True, exist_ok=True)
                
                # Export results
                options = self._get_analysis_options()
                self.analysis_service.export_results(
                    self._data['analysis_results'],
                    export_dir,
                    options
                )
                
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Analysis results exported to {dir_path}"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"Error exporting results: {str(e)}"
                )
    ```

- [ ] **Create Summary Widget**
  - [ ] Create `src/ui/widgets/summary_widget.py` to display analysis summaries:
    ```python
    # src/ui/widgets/summary_widget.py
    from typing import Dict, Any, Optional, List
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
        QFrame, QScrollArea, QSizePolicy, QGridLayout
    )
    from PySide6.QtCore import Qt, Signal, Slot
    from PySide6.QtGui import QFont, QColor

    class SummaryCard(QFrame):
        """A card widget for displaying a summary statistic."""
        
        def __init__(
            self, 
            title: str = "", 
            value: str = "", 
            description: str = "",
            parent=None
        ):
            """
            Initialize the summary card.
            
            Args:
                title: Title of the card
                value: Main value to display
                description: Additional description or context
                parent: Optional parent widget
            """
            super().__init__(parent)
            
            # Setup card appearance
            self.setFrameShape(QFrame.StyledPanel)
            self.setStyleSheet(
                "background-color: #2A374F; border-radius: 5px; padding: 10px;"
            )
            self.setMinimumSize(200, 120)
            
            # Create layout
            self.layout = QVBoxLayout(self)
            
            # Create title label
            self.title_label = QLabel(title)
            self.title_label.setStyleSheet(
                "font-size: 14px; color: #FFFFFF;"
            )
            
            # Create value label
            self.value_label = QLabel(value)
            self.value_label.setStyleSheet(
                "font-size: 24px; font-weight: bold; color: #D4AF37; margin: 5px 0;"
            )
            self.value_label.setAlignment(Qt.AlignCenter)
            
            # Create description label
            self.description_label = QLabel(description)
            self.description_label.setStyleSheet(
                "font-size: 12px; color: #AAAAAA; font-style: italic;"
            )
            self.description_label.setAlignment(Qt.AlignCenter)
            self.description_label.setWordWrap(True)
            
            # Add widgets to layout
            self.layout.addWidget(self.title_label)
            self.layout.addWidget(self.value_label, 1)
            self.layout.addWidget(self.description_label)
            
        def set_data(self, title: str, value: str, description: str = "") -> None:
            """
            Update the card with new data.
            
            Args:
                title: New title
                value: New value
                description: New description
            """
            self.title_label.setText(title)
            self.value_label.setText(value)
            self.description_label.setText(description)

    class SummaryWidget(QWidget):
        """Widget for displaying analysis summary information."""
        
        def __init__(self, parent=None):
            """
            Initialize the summary widget.
            
            Args:
                parent: Optional parent widget
            """
            super().__init__(parent)
            
            # Setup widget
            self.layout = QVBoxLayout(self)
            
            # Create scroll area for cards
            self.scroll_area = QScrollArea()
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setFrameShape(QFrame.NoFrame)
            
            # Create container for cards
            self.cards_container = QWidget()
            self.cards_layout = QGridLayout(self.cards_container)
            self.cards_layout.setContentsMargins(10, 10, 10, 10)
            self.cards_layout.setSpacing(15)
            
            # Set scroll area widget
            self.scroll_area.setWidget(self.cards_container)
            
            # Add to main layout
            self.layout.addWidget(self.scroll_area)
            
            # Initialize card collection
            self.cards = []
            
            # Create some default cards
            self._create_default_cards()
            
        def _create_default_cards(self) -> None:
            """Create default summary cards."""
            # Clear existing cards
            for card in self.cards:
                card.setParent(None)
            self.cards = []
            
            # Create new cards (4x2 grid)
            for i in range(8):
                card = SummaryCard(
                    title=f"Statistic {i+1}",
                    value="--",
                    description="No data available"
                )
                self.cards.append(card)
                row, col = divmod(i, 4)  # 4 columns
                self.cards_layout.addWidget(card, row, col)
            
        def set_data(self, data: Dict[str, Any]) -> None:
            """
            Update the summary widget with new data.
            
            Args:
                data: Dictionary containing summary data
            """
            # Clear existing cards
            for card in self.cards:
                card.setParent(None)
            self.cards = []
            
            # Check if data is valid
            if not data or not isinstance(data, dict):
                self._create_default_cards()
                return
            
            # Extract summary items
            summary_items = []
            
            # Process different sections
            if 'general' in data:
                for key, value in data['general'].items():
                    if isinstance(value, dict) and 'value' in value:
                        item = {
                            'title': key.replace('_', ' ').title(),
                            'value': str(value.get('value', '')),
                            'description': value.get('description', '')
                        }
                        summary_items.append(item)
            
            if 'chest' in data:
                for key, value in data['chest'].items():
                    if isinstance(value, dict) and 'value' in value:
                        item = {
                            'title': f"Chest: {key.replace('_', ' ').title()}",
                            'value': str(value.get('value', '')),
                            'description': value.get('description', '')
                        }
                        summary_items.append(item)
            
            if 'source' in data:
                for key, value in data['source'].items():
                    if isinstance(value, dict) and 'value' in value:
                        item = {
                            'title': f"Source: {key.replace('_', ' ').title()}",
                            'value': str(value.get('value', '')),
                            'description': value.get('description', '')
                        }
                        summary_items.append(item)
            
            if 'player' in data:
                for key, value in data['player'].items():
                    if isinstance(value, dict) and 'value' in value:
                        item = {
                            'title': f"Player: {key.replace('_', ' ').title()}",
                            'value': str(value.get('value', '')),
                            'description': value.get('description', '')
                        }
                        summary_items.append(item)
            
            # If no items found, create default cards
            if not summary_items:
                self._create_default_cards()
                return
            
            # Create cards for each item
            for i, item in enumerate(summary_items):
                card = SummaryCard(
                    title=item['title'],
                    value=item['value'],
                    description=item['description']
                )
                self.cards.append(card)
                row, col = divmod(i, 4)  # 4 columns
                self.cards_layout.addWidget(card, row, col)
    ```

- [ ] **Update Analysis Services for Analysis Screen**
  - [ ] Ensure the services used by the Analysis Screen are implemented in Phase 3:
    - [ ] AnalysisService with player analysis methods
    - [ ] ChestAnalysisService
    - [ ] SourceAnalysisService
    - [ ] Result export functionality

- [ ] **Integrate Analysis Screen with Main Window**
  - [ ] Update the screen factory to register the Analysis Screen
  - [ ] Add navigation buttons in the Raw Data Screen to proceed to analysis
  - [ ] Implement data passing between screens 