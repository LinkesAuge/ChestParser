from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QCheckBox, QLineEdit, QGroupBox, QDateEdit,
    QListWidget, QListWidgetItem, QSplitter, QAbstractItemView
)
from PySide6.QtCore import Signal, Qt, QDate
from .stylemanager import DARK_THEME

class FilterArea(QWidget):
    """
    A widget for filtering data based on column values and date ranges.
    Supports multiple value selection and date filtering.
    """
    
    filterApplied = Signal()  # Signal emitted when filter is applied
    filterCleared = Signal()  # Signal emitted when filter is cleared
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the filter area UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Create filter controls group
        filter_group = QGroupBox("Filter Controls")
        filter_layout = QVBoxLayout()
        
        # Column selection
        column_layout = QHBoxLayout()
        column_layout.addWidget(QLabel("Filter Column:"))
        self.column_selector = QComboBox()
        self.column_selector.currentIndexChanged.connect(self.update_filter_options)
        column_layout.addWidget(self.column_selector)
        
        # Value selection toggle
        self.show_value_selection = QCheckBox("Select specific values")
        self.show_value_selection.setChecked(True)
        self.show_value_selection.stateChanged.connect(self.toggle_value_selection)
        column_layout.addWidget(self.show_value_selection)
        column_layout.addStretch()
        
        # Value selection area
        self.value_list_widget = QWidget()
        value_list_layout = QVBoxLayout(self.value_list_widget)
        
        # Value list with multiple selection
        self.value_list = QListWidget()
        self.value_list.setSelectionMode(QAbstractItemView.MultiSelection)
        value_list_layout.addWidget(self.value_list)
        
        # Value selection buttons
        button_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all_values)
        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self.deselect_all_values)
        button_layout.addWidget(select_all_btn)
        button_layout.addWidget(deselect_all_btn)
        value_list_layout.addLayout(button_layout)
        
        # Date filter section
        date_filter_layout = QHBoxLayout()
        self.date_filter_enabled = QCheckBox("Enable Date Filter")
        date_filter_layout.addWidget(self.date_filter_enabled)
        
        date_filter_layout.addWidget(QLabel("From:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        date_filter_layout.addWidget(self.start_date)
        
        date_filter_layout.addWidget(QLabel("To:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        date_filter_layout.addWidget(self.end_date)
        date_filter_layout.addStretch()
        
        # Action buttons
        action_layout = QHBoxLayout()
        apply_button = QPushButton("Apply Filter")
        apply_button.clicked.connect(self.apply_filter)
        clear_button = QPushButton("Clear Filter")
        clear_button.clicked.connect(self.clear_filter)
        action_layout.addWidget(apply_button)
        action_layout.addWidget(clear_button)
        action_layout.addStretch()
        
        # Add all layouts to the filter group
        filter_layout.addLayout(column_layout)
        filter_layout.addWidget(self.value_list_widget)
        filter_layout.addLayout(date_filter_layout)
        filter_layout.addLayout(action_layout)
        
        filter_group.setLayout(filter_layout)
        main_layout.addWidget(filter_group)
        
        # Initialize state
        self.toggle_value_selection(True)
    
    def update_columns(self, columns):
        """Update the available columns in the column selector."""
        self.column_selector.clear()
        self.column_selector.addItems(columns)
        self.update_filter_options()
    
    def update_filter_options(self):
        """Update the available filter options based on the selected column."""
        self.value_list.clear()
        
        # Get parent's data
        parent = self.parent()
        if not hasattr(parent, 'raw_data') or parent.raw_data is None:
            return
        
        column = self.column_selector.currentText()
        if not column:
            return
        
        # Get unique values from the selected column
        unique_values = parent.raw_data[column].astype(str).unique().tolist()
        unique_values.sort()
        
        # Add items to the list
        for value in unique_values:
            item = QListWidgetItem(value)
            self.value_list.addItem(item)
    
    def toggle_value_selection(self, state):
        """Toggle the visibility of the value selection panel."""
        if isinstance(state, bool):
            is_visible = state
        else:
            is_visible = state == Qt.Checked
        self.value_list_widget.setVisible(is_visible)
        self.update_filter_options()
    
    def select_all_values(self):
        """Select all values in the value list."""
        for i in range(self.value_list.count()):
            self.value_list.item(i).setSelected(True)
    
    def deselect_all_values(self):
        """Deselect all values in the value list."""
        for i in range(self.value_list.count()):
            self.value_list.item(i).setSelected(False)
    
    def get_filter_settings(self):
        """Get the current filter settings."""
        settings = {
            'column': self.column_selector.currentText(),
            'value_filter_enabled': self.show_value_selection.isChecked(),
            'selected_values': [],
            'date_filter_enabled': self.date_filter_enabled.isChecked(),
            'start_date': self.start_date.date().toString("yyyy-MM-dd"),
            'end_date': self.end_date.date().toString("yyyy-MM-dd")
        }
        
        # Get selected values if value selection is enabled
        if settings['value_filter_enabled']:
            settings['selected_values'] = [
                item.text() for item in self.value_list.selectedItems()
            ]
        
        return settings
    
    def apply_filter(self):
        """Apply the current filter settings."""
        self.filterApplied.emit()
    
    def clear_filter(self):
        """Clear all filter settings."""
        self.deselect_all_values()
        self.date_filter_enabled.setChecked(False)
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.end_date.setDate(QDate.currentDate())
        self.filterCleared.emit() 