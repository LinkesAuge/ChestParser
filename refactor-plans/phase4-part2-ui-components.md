# Total Battle Analyzer Refactoring Plan: Phase 4 - Part 2
## UI Components

This document details the implementation of UI components for the Total Battle Analyzer application as part of Phase 4 refactoring.

### 1. Setup and Preparation

- [ ] **Verify Foundation Components**
  - [ ] Ensure the UI foundation from Part 1 is complete
  - [ ] Test that the main window, navigation system, and theme manager are working correctly

- [ ] **Component Library Verification**
  - [ ] Ensure all required component libraries are installed:
    ```bash
    uv add matplotlib pandas numpy
    ```
  - [ ] Create a components test harness for rapid development and testing

### 2. Data Table Components

- [ ] **Create Base Data Table**
  - [ ] Create `src/ui/widgets/data_table.py` with the following content:
    ```python
    # src/ui/widgets/data_table.py
    from typing import Dict, Any, Optional, List, Union
    import pandas as pd
    import numpy as np
    from PySide6.QtWidgets import (
        QTableView, QAbstractItemView, QHeaderView, 
        QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QPushButton, QComboBox, QLineEdit, QSpinBox
    )
    from PySide6.QtCore import Qt, Signal, Slot, QAbstractTableModel, QModelIndex, QSortFilterProxyModel
    from PySide6.QtGui import QColor, QBrush, QFont

    class DataFrameModel(QAbstractTableModel):
        """Table model for pandas DataFrame."""
        
        def __init__(self, df: Optional[pd.DataFrame] = None):
            """
            Initialize the model.
            
            Args:
                df: Optional DataFrame to display
            """
            super().__init__()
            self._df = df if df is not None else pd.DataFrame()
            self._column_formats = {}
            self._column_colors = {}
            
        def rowCount(self, parent=None) -> int:
            """Get the number of rows."""
            return len(self._df)
            
        def columnCount(self, parent=None) -> int:
            """Get the number of columns."""
            return len(self._df.columns)
            
        def data(self, index: QModelIndex, role=Qt.DisplayRole) -> Any:
            """Get data at index for role."""
            if not index.isValid():
                return None
                
            if role == Qt.DisplayRole:
                value = self._df.iloc[index.row(), index.column()]
                
                # Apply column format if available
                column_name = self._df.columns[index.column()]
                if column_name in self._column_formats:
                    try:
                        return self._column_formats[column_name](value)
                    except:
                        return str(value)
                        
                # Default formatting
                if isinstance(value, float):
                    return f"{value:.2f}"
                return str(value)
                
            elif role == Qt.TextAlignmentRole:
                value = self._df.iloc[index.row(), index.column()]
                if isinstance(value, (int, float)):
                    return Qt.AlignRight | Qt.AlignVCenter
                return Qt.AlignLeft | Qt.AlignVCenter
                
            elif role == Qt.BackgroundRole:
                column_name = self._df.columns[index.column()]
                if column_name in self._column_colors:
                    color_func = self._column_colors[column_name]
                    value = self._df.iloc[index.row(), index.column()]
                    color = color_func(value)
                    if color:
                        return QBrush(QColor(color))
                        
            return None
            
        def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole) -> Any:
            """Get header data."""
            if role == Qt.DisplayRole:
                if orientation == Qt.Horizontal:
                    return str(self._df.columns[section])
                else:
                    return str(section + 1)
            return None
            
        def set_dataframe(self, df: pd.DataFrame) -> None:
            """
            Set the DataFrame for the model.
            
            Args:
                df: DataFrame to display
            """
            self.beginResetModel()
            self._df = df.copy()
            self.endResetModel()
            
        def get_dataframe(self) -> pd.DataFrame:
            """
            Get the DataFrame from the model.
            
            Returns:
                The DataFrame
            """
            return self._df.copy()
            
        def set_column_format(self, column: str, format_func: callable) -> None:
            """
            Set a formatting function for a column.
            
            Args:
                column: Column name
                format_func: Function to format values
            """
            self._column_formats[column] = format_func
            
        def set_column_color(self, column: str, color_func: callable) -> None:
            """
            Set a coloring function for a column.
            
            Args:
                column: Column name
                color_func: Function to return color for values
            """
            self._column_colors[column] = color_func
            
        def sort(self, column: int, order: Qt.SortOrder) -> None:
            """
            Sort the model by column.
            
            Args:
                column: Column index
                order: Sort order
            """
            self.beginResetModel()
            col_name = self._df.columns[column]
            ascending = order == Qt.AscendingOrder
            self._df = self._df.sort_values(col_name, ascending=ascending)
            self.endResetModel()

    class DataTableWidget(QWidget):
        """Widget for displaying tabular data."""
        
        selection_changed = Signal(pd.DataFrame)
        double_clicked = Signal(pd.DataFrame, int, int)
        
        def __init__(self, parent=None):
            """
            Initialize the widget.
            
            Args:
                parent: Optional parent widget
            """
            super().__init__(parent)
            
            # Create layout
            self.layout = QVBoxLayout()
            self.setLayout(self.layout)
            
            # Create table view
            self.table_view = QTableView()
            self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.table_view.setAlternatingRowColors(True)
            self.table_view.setSortingEnabled(True)
            self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
            self.table_view.horizontalHeader().setStretchLastSection(True)
            
            # Create model and proxy model
            self.model = DataFrameModel()
            self.proxy_model = QSortFilterProxyModel()
            self.proxy_model.setSourceModel(self.model)
            
            # Set model for table view
            self.table_view.setModel(self.proxy_model)
            
            # Create controls
            self.controls_layout = QHBoxLayout()
            
            # Add search field
            self.search_label = QLabel("Search:")
            self.search_field = QLineEdit()
            self.search_field.setPlaceholderText("Enter search text...")
            self.controls_layout.addWidget(self.search_label)
            self.controls_layout.addWidget(self.search_field)
            
            # Add column selector
            self.column_label = QLabel("Column:")
            self.column_selector = QComboBox()
            self.controls_layout.addWidget(self.column_label)
            self.controls_layout.addWidget(self.column_selector)
            
            # Add page size selector
            self.page_size_label = QLabel("Page Size:")
            self.page_size_selector = QSpinBox()
            self.page_size_selector.setMinimum(10)
            self.page_size_selector.setMaximum(1000)
            self.page_size_selector.setValue(100)
            self.page_size_selector.setSingleStep(10)
            self.controls_layout.addWidget(self.page_size_label)
            self.controls_layout.addWidget(self.page_size_selector)
            
            # Add export button
            self.export_button = QPushButton("Export")
            self.controls_layout.addWidget(self.export_button)
            
            # Add layouts to main layout
            self.layout.addLayout(self.controls_layout)
            self.layout.addWidget(self.table_view)
            
            # Connect signals
            self.search_field.textChanged.connect(self._on_search_changed)
            self.column_selector.currentIndexChanged.connect(self._on_column_changed)
            self.table_view.selectionModel().selectionChanged.connect(self._on_selection_changed)
            self.table_view.doubleClicked.connect(self._on_double_clicked)
            
        def set_data(self, df: pd.DataFrame) -> None:
            """
            Set the data for the table.
            
            Args:
                df: DataFrame to display
            """
            # Update model
            self.model.set_dataframe(df)
            
            # Update column selector
            self.column_selector.clear()
            self.column_selector.addItem("All Columns")
            for column in df.columns:
                self.column_selector.addItem(str(column))
                
            # Reset filter
            self.proxy_model.setFilterFixedString("")
            
            # Resize columns to content
            self.table_view.resizeColumnsToContents()
            
        def get_data(self) -> pd.DataFrame:
            """
            Get the data from the table.
            
            Returns:
                The DataFrame
            """
            return self.model.get_dataframe()
            
        def get_selected_data(self) -> pd.DataFrame:
            """
            Get the selected data from the table.
            
            Returns:
                DataFrame with selected rows
            """
            selection = self.table_view.selectionModel().selectedRows()
            if not selection:
                return pd.DataFrame()
                
            # Get source model indices
            source_indices = [self.proxy_model.mapToSource(index).row() for index in selection]
            
            # Get rows from source model
            df = self.model.get_dataframe()
            return df.iloc[source_indices].copy()
            
        def _on_search_changed(self, text: str) -> None:
            """Handle search text changes."""
            # Get filter column
            column_index = self.column_selector.currentIndex() - 1
            if column_index >= 0:
                self.proxy_model.setFilterKeyColumn(column_index)
            else:
                self.proxy_model.setFilterKeyColumn(-1)  # All columns
                
            # Set filter string
            self.proxy_model.setFilterFixedString(text)
            
        def _on_column_changed(self, index: int) -> None:
            """Handle column selection changes."""
            # Apply current search to selected column
            self._on_search_changed(self.search_field.text())
            
        def _on_selection_changed(self) -> None:
            """Handle selection changes."""
            selected_data = self.get_selected_data()
            self.selection_changed.emit(selected_data)
            
        def _on_double_clicked(self, index: QModelIndex) -> None:
            """Handle double click on item."""
            # Get source model index
            source_index = self.proxy_model.mapToSource(index)
            row = source_index.row()
            column = source_index.column()
            
            # Get selected data
            df = self.model.get_dataframe()
            row_data = df.iloc[[row]]
            
            self.double_clicked.emit(row_data, row, column)
    ```

- [ ] **Create Enhanced Data Grid**
  - [ ] Create `src/ui/widgets/data_grid.py` with advanced data grid functionality
  - [ ] Implement features like row grouping, custom cell rendering, and in-line editing

- [ ] **Create Data Pagination Component**
  - [ ] Create `src/ui/widgets/data_pagination.py` with pagination controls for large datasets

### 3. Chart and Visualization Widgets

- [ ] **Create Base Chart Widget**
  - [ ] Create `src/ui/widgets/chart_widget.py` with the following content:
    ```python
    # src/ui/widgets/chart_widget.py
    from typing import Dict, Any, Optional, List, Union, Tuple
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QPushButton, QComboBox, QSizePolicy, QToolBar,
        QAction
    )
    from PySide6.QtCore import Qt, Signal, Slot, QSize
    from PySide6.QtGui import QIcon

    class MplCanvas(FigureCanvas):
        """Matplotlib canvas for chart rendering."""
        
        def __init__(self, width=5, height=4, dpi=100):
            """
            Initialize the canvas.
            
            Args:
                width: Figure width in inches
                height: Figure height in inches
                dpi: Dots per inch
            """
            self.fig = Figure(figsize=(width, height), dpi=dpi)
            self.axes = self.fig.add_subplot(111)
            super().__init__(self.fig)
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.fig.tight_layout()

    class ChartWidget(QWidget):
        """Widget for displaying charts."""
        
        chart_updated = Signal()
        
        def __init__(self, parent=None):
            """
            Initialize the widget.
            
            Args:
                parent: Optional parent widget
            """
            super().__init__(parent)
            
            # Create layout
            self.layout = QVBoxLayout()
            self.setLayout(self.layout)
            
            # Create toolbar
            self.toolbar_layout = QHBoxLayout()
            
            # Chart type selector
            self.chart_type_label = QLabel("Chart Type:")
            self.chart_type_selector = QComboBox()
            self.chart_type_selector.addItems(["Bar", "Horizontal Bar", "Pie", "Line", "Scatter"])
            self.toolbar_layout.addWidget(self.chart_type_label)
            self.toolbar_layout.addWidget(self.chart_type_selector)
            
            # Add spacer
            self.toolbar_layout.addStretch()
            
            # Export button
            self.export_button = QPushButton("Export")
            self.toolbar_layout.addWidget(self.export_button)
            
            # Add toolbar to main layout
            self.layout.addLayout(self.toolbar_layout)
            
            # Create canvas
            self.canvas = MplCanvas(width=5, height=4, dpi=100)
            self.layout.addWidget(self.canvas)
            
            # Connect signals
            self.chart_type_selector.currentIndexChanged.connect(self._on_chart_type_changed)
            self.export_button.clicked.connect(self._on_export_clicked)
            
            # Initialize data
            self._data = pd.DataFrame()
            self._category_column = ""
            self._value_column = ""
            self._chart_title = ""
            
        def plot_data(
            self,
            data: pd.DataFrame,
            category_column: str,
            value_column: str,
            title: str = "",
            chart_type: Optional[str] = None
        ) -> None:
            """
            Plot data on the chart.
            
            Args:
                data: DataFrame with data to plot
                category_column: Column name for categories
                value_column: Column name for values
                title: Chart title
                chart_type: Optional chart type override
            """
            if data.empty or category_column not in data.columns or value_column not in data.columns:
                return
                
            # Store data for later
            self._data = data.copy()
            self._category_column = category_column
            self._value_column = value_column
            self._chart_title = title
            
            # Set chart type if provided
            if chart_type:
                index = self.chart_type_selector.findText(chart_type, Qt.MatchFixedString)
                if index >= 0:
                    self.chart_type_selector.setCurrentIndex(index)
                    
            # Plot the data
            self._update_chart()
            
        def _update_chart(self) -> None:
            """Update the chart with current settings."""
            if self._data.empty:
                return
                
            # Clear the axes
            self.canvas.axes.clear()
            
            # Get chart type
            chart_type = self.chart_type_selector.currentText()
            
            # Sort data for better visualization
            df = self._data.sort_values(self._value_column, ascending=False)
            
            # Limit to top 20 items for better visualization
            if len(df) > 20:
                df = df.head(20)
                
            # Plot based on chart type
            if chart_type == "Bar":
                df.plot(
                    kind='bar',
                    x=self._category_column,
                    y=self._value_column,
                    ax=self.canvas.axes,
                    legend=False
                )
                
            elif chart_type == "Horizontal Bar":
                df.plot(
                    kind='barh',
                    x=self._category_column,
                    y=self._value_column,
                    ax=self.canvas.axes,
                    legend=False
                )
                
            elif chart_type == "Pie":
                df.plot(
                    kind='pie',
                    y=self._value_column,
                    labels=df[self._category_column],
                    ax=self.canvas.axes,
                    autopct='%1.1f%%',
                    legend=False
                )
                
            elif chart_type == "Line":
                df.plot(
                    kind='line',
                    x=self._category_column,
                    y=self._value_column,
                    ax=self.canvas.axes,
                    marker='o',
                    legend=False
                )
                
            elif chart_type == "Scatter":
                df.plot(
                    kind='scatter',
                    x=self._category_column,
                    y=self._value_column,
                    ax=self.canvas.axes,
                    legend=False
                )
                
            # Set title
            if self._chart_title:
                self.canvas.axes.set_title(self._chart_title)
                
            # Adjust layout
            self.canvas.fig.tight_layout()
            
            # Redraw canvas
            self.canvas.draw()
            
            # Emit signal
            self.chart_updated.emit()
            
        def _on_chart_type_changed(self) -> None:
            """Handle chart type changes."""
            self._update_chart()
            
        def _on_export_clicked(self) -> None:
            """Handle export button clicks."""
            # To be implemented
            pass
            
        def get_figure(self) -> Figure:
            """
            Get the current figure.
            
            Returns:
                The matplotlib Figure
            """
            return self.canvas.fig
    ```

- [ ] **Create Multi-Chart Container**
  - [ ] Create `src/ui/widgets/chart_container.py` for organizing and layouting multiple charts 

- [ ] **Create Chart Configuration Widgets**
  - [ ] Create `src/ui/widgets/chart_config.py` with controls for chart configuration
  - [ ] Implement components for selecting axes, data points, chart types, etc.

- [ ] **Create Advanced Charts**
  - [ ] Create `src/ui/widgets/advanced_charts.py` with support for stacked bar charts, time series, and heatmaps

### 4. Input Forms and Controls

- [ ] **Create Form Base**
  - [ ] Create `src/ui/forms/form_base.py` with the following content:
    ```python
    # src/ui/forms/form_base.py
    from typing import Dict, Any, Optional, List, Union, Callable
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
        QLabel, QPushButton, QLineEdit, QComboBox,
        QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox,
        QMessageBox, QDateEdit, QFileDialog
    )
    from PySide6.QtCore import Qt, Signal, Slot, QDate

    class FormField:
        """Base class for form fields."""
        
        def __init__(
            self,
            name: str,
            label: str,
            required: bool = False,
            default_value: Any = None,
            validator: Optional[Callable[[Any], bool]] = None,
            error_message: str = "Invalid input"
        ):
            """
            Initialize a form field.
            
            Args:
                name: Internal field name
                label: Display label
                required: Whether the field is required
                default_value: Default value for the field
                validator: Optional validation function
                error_message: Message to display when validation fails
            """
            self.name = name
            self.label = label
            self.required = required
            self.default_value = default_value
            self.validator = validator
            self.error_message = error_message
            self.widget = None
            
        def create_widget(self) -> QWidget:
            """
            Create the widget for this field.
            
            Returns:
                A QWidget for the field
            """
            raise NotImplementedError("Subclasses must implement this method")
            
        def get_value(self) -> Any:
            """
            Get the current value of the field.
            
            Returns:
                The field value
            """
            raise NotImplementedError("Subclasses must implement this method")
            
        def set_value(self, value: Any) -> None:
            """
            Set the value of the field.
            
            Args:
                value: New value for the field
            """
            raise NotImplementedError("Subclasses must implement this method")
            
        def validate(self) -> bool:
            """
            Validate the current field value.
            
            Returns:
                True if valid, False otherwise
            """
            value = self.get_value()
            
            # Check required
            if self.required and (value is None or value == ""):
                return False
                
            # Check validator
            if self.validator and value is not None and value != "":
                return self.validator(value)
                
            return True

    class TextFormField(FormField):
        """Form field for text input."""
        
        def create_widget(self) -> QLineEdit:
            """Create a line edit widget."""
            self.widget = QLineEdit()
            if self.default_value:
                self.widget.setText(str(self.default_value))
            return self.widget
            
        def get_value(self) -> str:
            """Get the current text."""
            return self.widget.text() if self.widget else ""
            
        def set_value(self, value: str) -> None:
            """Set the text."""
            if self.widget:
                self.widget.setText(str(value))

    class ComboFormField(FormField):
        """Form field for dropdown selection."""
        
        def __init__(self, name: str, label: str, options: List[str], **kwargs):
            """
            Initialize a combo form field.
            
            Args:
                name: Internal field name
                label: Display label
                options: List of options for the dropdown
                **kwargs: Additional arguments for FormField
            """
            super().__init__(name, label, **kwargs)
            self.options = options
            
        def create_widget(self) -> QComboBox:
            """Create a combo box widget."""
            self.widget = QComboBox()
            self.widget.addItems(self.options)
            if self.default_value and self.default_value in self.options:
                self.widget.setCurrentText(str(self.default_value))
            return self.widget
            
        def get_value(self) -> str:
            """Get the current selection."""
            return self.widget.currentText() if self.widget else ""
            
        def set_value(self, value: str) -> None:
            """Set the selection."""
            if self.widget and value in self.options:
                self.widget.setCurrentText(str(value))

    class IntegerFormField(FormField):
        """Form field for integer input."""
        
        def __init__(
            self,
            name: str,
            label: str,
            min_value: int = 0,
            max_value: int = 100,
            **kwargs
        ):
            """
            Initialize an integer form field.
            
            Args:
                name: Internal field name
                label: Display label
                min_value: Minimum allowed value
                max_value: Maximum allowed value
                **kwargs: Additional arguments for FormField
            """
            super().__init__(name, label, **kwargs)
            self.min_value = min_value
            self.max_value = max_value
            
        def create_widget(self) -> QSpinBox:
            """Create a spin box widget."""
            self.widget = QSpinBox()
            self.widget.setMinimum(self.min_value)
            self.widget.setMaximum(self.max_value)
            if self.default_value is not None:
                self.widget.setValue(int(self.default_value))
            return self.widget
            
        def get_value(self) -> int:
            """Get the current value."""
            return self.widget.value() if self.widget else 0
            
        def set_value(self, value: int) -> None:
            """Set the value."""
            if self.widget:
                self.widget.setValue(int(value))

    class BooleanFormField(FormField):
        """Form field for boolean input."""
        
        def create_widget(self) -> QCheckBox:
            """Create a check box widget."""
            self.widget = QCheckBox(self.label)
            if self.default_value:
                self.widget.setChecked(bool(self.default_value))
            return self.widget
            
        def get_value(self) -> bool:
            """Get the current state."""
            return self.widget.isChecked() if self.widget else False
            
        def set_value(self, value: bool) -> None:
            """Set the state."""
            if self.widget:
                self.widget.setChecked(bool(value))

    class FormWidget(QWidget):
        """Widget for displaying and managing forms."""
        
        form_submitted = Signal(dict)
        form_cancelled = Signal()
        
        def __init__(self, parent=None):
            """
            Initialize the widget.
            
            Args:
                parent: Optional parent widget
            """
            super().__init__(parent)
            
            # Create layout
            self.layout = QVBoxLayout()
            self.setLayout(self.layout)
            
            # Create form layout
            self.form_layout = QFormLayout()
            
            # Create button layout
            self.button_layout = QHBoxLayout()
            
            # Add spacer to align buttons to the right
            self.button_layout.addStretch()
            
            # Add cancel button
            self.cancel_button = QPushButton("Cancel")
            self.cancel_button.clicked.connect(self._on_cancel)
            self.button_layout.addWidget(self.cancel_button)
            
            # Add submit button
            self.submit_button = QPushButton("Submit")
            self.submit_button.clicked.connect(self._on_submit)
            self.button_layout.addWidget(self.submit_button)
            
            # Add layouts to main layout
            self.layout.addLayout(self.form_layout)
            self.layout.addLayout(self.button_layout)
            
            # Initialize fields
            self.fields: Dict[str, FormField] = {}
            
        def add_field(self, field: FormField) -> None:
            """
            Add a field to the form.
            
            Args:
                field: FormField to add
            """
            # Create widget
            widget = field.create_widget()
            
            # Add to form layout
            if isinstance(field, BooleanFormField):
                # CheckBox contains its own label
                self.form_layout.addRow("", widget)
            else:
                self.form_layout.addRow(field.label, widget)
                
            # Store field
            self.fields[field.name] = field
            
        def get_values(self) -> Dict[str, Any]:
            """
            Get the current values of all fields.
            
            Returns:
                Dictionary of field values
            """
            return {name: field.get_value() for name, field in self.fields.items()}
            
        def set_values(self, values: Dict[str, Any]) -> None:
            """
            Set the values of fields.
            
            Args:
                values: Dictionary of field values
            """
            for name, value in values.items():
                if name in self.fields:
                    self.fields[name].set_value(value)
                    
        def validate(self) -> bool:
            """
            Validate all fields.
            
            Returns:
                True if all fields are valid, False otherwise
            """
            for name, field in self.fields.items():
                if not field.validate():
                    QMessageBox.warning(
                        self,
                        "Validation Error",
                        f"{field.label}: {field.error_message}"
                    )
                    return False
            return True
            
        def _on_submit(self) -> None:
            """Handle submit button clicks."""
            if self.validate():
                values = self.get_values()
                self.form_submitted.emit(values)
                
        def _on_cancel(self) -> None:
            """Handle cancel button clicks."""
            self.form_cancelled.emit()
    ```

- [ ] **Create File Selection Widgets**
  - [ ] Create `src/ui/forms/file_selector.py` with components for file and directory selection
  - [ ] Implement features for file type filtering, recent files, and file preview

- [ ] **Create Date/Time Selection Controls**
  - [ ] Create `src/ui/forms/datetime_selector.py` with components for date and time selection
  - [ ] Implement features like date range selection, presets, and calendar views

### 5. Custom Dialogs and Modal Windows

- [ ] **Create Dialog Base**
  - [ ] Create `src/ui/dialogs/dialog_base.py` with a base class for dialog windows

- [ ] **Create Confirmation Dialog**
  - [ ] Create `src/ui/dialogs/confirmation_dialog.py` for user confirmations

- [ ] **Create Settings Dialog**
  - [ ] Create `src/ui/dialogs/settings_dialog.py` for application settings
  - [ ] Implement tabs for different setting categories
  - [ ] Add save/load functionality for settings

- [ ] **Create Import/Export Dialog**
  - [ ] Create `src/ui/dialogs/import_export_dialog.py` for data import/export
  - [ ] Implement format selection, options, and progress feedback

### 6. Notification and Alert System

- [ ] **Create Toast Notification Component**
  - [ ] Create `src/ui/notifications/toast.py` with the following content:
    ```python
    # src/ui/notifications/toast.py
    from typing import Optional, List
    from PySide6.QtWidgets import (
        QWidget, QLabel, QHBoxLayout, QVBoxLayout,
        QPushButton, QGraphicsOpacityEffect, QFrame
    )
    from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Property, QSize
    from PySide6.QtGui import QColor, QPalette, QIcon

    class ToastNotification(QFrame):
        """A toast notification widget."""
        
        INFO = "info"
        SUCCESS = "success"
        WARNING = "warning"
        ERROR = "error"
        
        def __init__(
            self,
            parent=None,
            message: str = "",
            title: str = "",
            notification_type: str = INFO,
            duration: int = 3000,
            closable: bool = True
        ):
            """
            Initialize the notification.
            
            Args:
                parent: Optional parent widget
                message: Notification message
                title: Notification title
                notification_type: Type of notification
                duration: Display duration in milliseconds
                closable: Whether the notification can be closed
            """
            super().__init__(parent)
            
            # Set frame style
            self.setFrameShape(QFrame.StyledPanel)
            self.setFrameShadow(QFrame.Raised)
            
            # Set properties
            self.message = message
            self.title = title
            self.notification_type = notification_type
            self.duration = duration
            self.closable = closable
            
            # Create layout
            self.layout = QHBoxLayout()
            self.setLayout(self.layout)
            
            # Create icon label
            self.icon_label = QLabel()
            self.icon_label.setFixedSize(24, 24)
            
            # Create content layout
            self.content_layout = QVBoxLayout()
            
            # Create title label
            self.title_label = QLabel(title)
            self.title_label.setStyleSheet("font-weight: bold;")
            
            # Create message label
            self.message_label = QLabel(message)
            self.message_label.setWordWrap(True)
            
            # Add labels to content layout
            if title:
                self.content_layout.addWidget(self.title_label)
            self.content_layout.addWidget(self.message_label)
            
            # Create close button
            self.close_button = QPushButton()
            self.close_button.setFixedSize(16, 16)
            self.close_button.setFlat(True)
            self.close_button.clicked.connect(self.close)
            
            # Add widgets to layout
            self.layout.addWidget(self.icon_label)
            self.layout.addLayout(self.content_layout, 1)
            if closable:
                self.layout.addWidget(self.close_button)
                
            # Set up timer
            self.timer = QTimer(self)
            self.timer.setSingleShot(True)
            self.timer.timeout.connect(self.fade_out)
            
            # Set up animations
            self.opacity_effect = QGraphicsOpacityEffect(self)
            self.opacity_effect.setOpacity(0.0)
            self.setGraphicsEffect(self.opacity_effect)
            
            self.fade_in_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
            self.fade_in_animation.setDuration(250)
            self.fade_in_animation.setStartValue(0.0)
            self.fade_in_animation.setEndValue(1.0)
            self.fade_in_animation.setEasingCurve(QEasingCurve.OutCubic)
            
            self.fade_out_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
            self.fade_out_animation.setDuration(250)
            self.fade_out_animation.setStartValue(1.0)
            self.fade_out_animation.setEndValue(0.0)
            self.fade_out_animation.setEasingCurve(QEasingCurve.InCubic)
            self.fade_out_animation.finished.connect(self.hide)
            
            # Apply style based on type
            self._apply_style()
            
        def _apply_style(self) -> None:
            """Apply style based on notification type."""
            base_style = """
                QFrame {
                    border-radius: 4px;
                    padding: 8px;
                }
            """
            
            if self.notification_type == self.INFO:
                self.setStyleSheet(base_style + """
                    QFrame {
                        background-color: #E3F2FD;
                        border: 1px solid #90CAF9;
                    }
                """)
                # Set icon
                # self.icon_label.setPixmap(QIcon.fromTheme("dialog-information").pixmap(24, 24))
                
            elif self.notification_type == self.SUCCESS:
                self.setStyleSheet(base_style + """
                    QFrame {
                        background-color: #E8F5E9;
                        border: 1px solid #A5D6A7;
                    }
                """)
                # Set icon
                # self.icon_label.setPixmap(QIcon.fromTheme("dialog-ok").pixmap(24, 24))
                
            elif self.notification_type == self.WARNING:
                self.setStyleSheet(base_style + """
                    QFrame {
                        background-color: #FFF8E1;
                        border: 1px solid #FFCC80;
                    }
                """)
                # Set icon
                # self.icon_label.setPixmap(QIcon.fromTheme("dialog-warning").pixmap(24, 24))
                
            elif self.notification_type == self.ERROR:
                self.setStyleSheet(base_style + """
                    QFrame {
                        background-color: #FFEBEE;
                        border: 1px solid #EF9A9A;
                    }
                """)
                # Set icon
                # self.icon_label.setPixmap(QIcon.fromTheme("dialog-error").pixmap(24, 24))
            
            # Set close button icon
            # self.close_button.setIcon(QIcon.fromTheme("window-close"))
            
        def show(self) -> None:
            """Show the notification with fade-in animation."""
            super().show()
            self.fade_in_animation.start()
            if self.duration > 0:
                self.timer.start(self.duration)
                
        def fade_out(self) -> None:
            """Start the fade-out animation."""
            self.timer.stop()
            self.fade_out_animation.start()
            
        def close(self) -> None:
            """Close the notification."""
            self.fade_out()

    class ToastManager(QWidget):
        """Manager for toast notifications."""
        
        def __init__(self, parent=None):
            """
            Initialize the manager.
            
            Args:
                parent: Optional parent widget
            """
            super().__init__(parent)
            
            # Set properties
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setAttribute(Qt.WA_ShowWithoutActivating)
            
            # Create layout
            self.layout = QVBoxLayout()
            self.layout.setContentsMargins(10, 10, 10, 10)
            self.layout.setSpacing(10)
            self.setLayout(self.layout)
            
            # Initialize notifications
            self.notifications: List[ToastNotification] = []
            
            # Set position
            self._position_widget()
            
        def _position_widget(self) -> None:
            """Position the widget in the bottom-right corner."""
            if self.parentWidget():
                parent_rect = self.parentWidget().rect()
                width = 300
                height = 0
                x = parent_rect.width() - width - 20
                y = parent_rect.height() - height - 20
                self.setGeometry(x, y, width, height)
                
        def add_notification(
            self,
            message: str,
            title: str = "",
            notification_type: str = ToastNotification.INFO,
            duration: int = 3000,
            closable: bool = True
        ) -> ToastNotification:
            """
            Add a notification.
            
            Args:
                message: Notification message
                title: Notification title
                notification_type: Type of notification
                duration: Display duration in milliseconds
                closable: Whether the notification can be closed
                
            Returns:
                The created notification
            """
            # Create notification
            notification = ToastNotification(
                self,
                message=message,
                title=title,
                notification_type=notification_type,
                duration=duration,
                closable=closable
            )
            
            # Add to layout
            self.layout.addWidget(notification)
            
            # Store notification
            self.notifications.append(notification)
            
            # Show notification
            notification.show()
            
            # Resize manager
            self._position_widget()
            
            return notification
            
        def info(self, message: str, title: str = "", **kwargs) -> ToastNotification:
            """Show an info notification."""
            return self.add_notification(
                message,
                title,
                ToastNotification.INFO,
                **kwargs
            )
            
        def success(self, message: str, title: str = "", **kwargs) -> ToastNotification:
            """Show a success notification."""
            return self.add_notification(
                message,
                title,
                ToastNotification.SUCCESS,
                **kwargs
            )
            
        def warning(self, message: str, title: str = "", **kwargs) -> ToastNotification:
            """Show a warning notification."""
            return self.add_notification(
                message,
                title,
                ToastNotification.WARNING,
                **kwargs
            )
            
        def error(self, message: str, title: str = "", **kwargs) -> ToastNotification:
            """Show an error notification."""
            return self.add_notification(
                message,
                title,
                ToastNotification.ERROR,
                **kwargs
            )
    ```

- [ ] **Create Status Bar Integration**
  - [ ] Create `src/ui/notifications/status_bar.py` for status bar messages
  - [ ] Implement status message display, progress indicators, and status icons

- [ ] **Create Modal Alerts**
  - [ ] Create `src/ui/notifications/alerts.py` for modal alert windows
  - [ ] Implement standard alert types like info, warning, error, confirmation

### 7. Documentation and Validation

- [ ] **Update Documentation**
  - [ ] Update application documentation with UI components overview
  - [ ] Create detailed guides for using each UI component
  - [ ] Add screenshots and examples

- [ ] **Implement Testing**
  - [ ] Create unit tests for UI components in `tests/ui`
  - [ ] Develop testing utilities for UI tests
  - [ ] Implement integration tests for component interactions

- [ ] **Validate Component Behavior**
  - [ ] Verify component behavior across various screen sizes
  - [ ] Test keyboard navigation and accessibility
  - [ ] Validate error handling and edge cases

---

## Feedback Request

Please provide feedback on the following aspects of this UI components plan:

1. Completeness of component coverage for the application's needs
2. Component architecture and organization
3. Alignment with modern UI/UX practices
4. Integration with the existing application architecture
5. Suggestions for additional components or features
6. Any recommendations for improvements before proceeding to Part 3