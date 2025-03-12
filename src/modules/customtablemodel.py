# customtablemodel.py - CustomTableModel class implementation
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PySide6.QtGui import QColor
import pandas as pd
import numpy as np
from .stylemanager import DARK_THEME

class CustomTableModel(QAbstractTableModel):
    """Custom table model for displaying pandas DataFrame data."""
    
    def __init__(self, data):
        """Initialize the model with data."""
        super().__init__()
        self._data = data
        
    def data(self, index, role=Qt.DisplayRole):
        """Return data for the given index and role."""
        if not index.isValid():
            return None
            
        if role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            if pd.isna(value):
                return ""
            elif isinstance(value, (float, np.floating)):
                return f"{value:,.2f}"  # Format numbers with commas and 2 decimal places
            elif isinstance(value, (int, np.integer)):
                return f"{value:,}"  # Format integers with commas
            return str(value)
            
        elif role == Qt.TextAlignmentRole:
            value = self._data.iloc[index.row(), index.column()]
            if isinstance(value, (int, float, np.number)):
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter
            
        elif role == Qt.BackgroundRole:
            if index.row() % 2 == 0:
                return QColor(DARK_THEME['background_light'])
            else:
                return QColor(DARK_THEME['card_bg'])
                
        elif role == Qt.ForegroundRole:
            return QColor(DARK_THEME['foreground'])
            
        return None
        
    def rowCount(self, parent=None):
        """Return the number of rows."""
        return len(self._data)
        
    def columnCount(self, parent=None):
        """Return the number of columns."""
        return len(self._data.columns)
        
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Return header data for the given section, orientation and role."""
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])
            else:
                return str(section + 1)
                
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
            
        elif role == Qt.BackgroundRole:
            return QColor(DARK_THEME['header_bg'])
            
        elif role == Qt.ForegroundRole:
            return QColor(DARK_THEME['foreground'])
            
        return None

    def sort(self, column, order):
        """
        Sort the model by the given column and order.
        
        Args:
            column (int): The column to sort by.
            order (Qt.SortOrder): The sort order.
        """
        self.layoutAboutToBeChanged.emit()
        col_name = self._data.columns[column]
        ascending = order == Qt.AscendingOrder
        self._data = self._data.sort_values(col_name, ascending=ascending)
        self.layoutChanged.emit()


