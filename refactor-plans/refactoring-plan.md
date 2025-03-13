# Total Battle Analyzer Refactoring Plan

This document provides a detailed, step-by-step plan for refactoring the Total Battle Analyzer application. Each section outlines specific improvements with clear implementation instructions.

## Table of Contents

1. [UI Improvements](#1-ui-improvements)
2. [Better Data Handling](#2-better-data-handling)
3. [Improved Code Modularity](#3-improved-code-modularity)
4. [Simplified Code Structure](#4-simplified-code-structure)
5. [Better Separation of Concerns](#5-better-separation-of-concerns)
6. [Fixing Potential Issues and Bugs](#6-fixing-potential-issues-and-bugs)
7. [Codebase Refactoring Strategy](#7-codebase-refactoring-strategy)

## 1. UI Improvements

### 1.1. Standardize Component Sizes and Spacing

- [ ] **Create a StyleConstants class:**
  ```python
  # src/ui/styles/constants.py
  class StyleConstants:
      # Base spacing
      MARGIN_SMALL = 5
      MARGIN_MEDIUM = 10
      MARGIN_LARGE = 20
      
      # Component sizes
      BUTTON_HEIGHT = 30
      WIDGET_HEIGHT_SMALL = 25
      WIDGET_HEIGHT_MEDIUM = 30
      WIDGET_HEIGHT_LARGE = 40
      
      # Font sizes
      FONT_SIZE_SMALL = 10
      FONT_SIZE_MEDIUM = 12
      FONT_SIZE_LARGE = 14
      FONT_SIZE_HEADER = 16
  ```

- [ ] **Create a StyleUtils class with methods for applying consistent styling:**
  ```python
  # src/ui/styles/utils.py
  from PySide6.QtWidgets import QWidget, QPushButton, QLabel
  from .constants import StyleConstants
  
  class StyleUtils:
      @staticmethod
      def apply_button_style(button: QPushButton, is_primary=False):
          button.setFixedHeight(StyleConstants.BUTTON_HEIGHT)
          # Apply other styling...
          
      @staticmethod
      def apply_standard_layout_margins(layout):
          layout.setContentsMargins(
              StyleConstants.MARGIN_MEDIUM,
              StyleConstants.MARGIN_MEDIUM,
              StyleConstants.MARGIN_MEDIUM,
              StyleConstants.MARGIN_MEDIUM
          )
          layout.setSpacing(StyleConstants.MARGIN_SMALL)
  ```

- [ ] **Apply consistent styling throughout the application:**
  - Update `setup_ui_components`, `setup_import_tab`, etc., to use StyleUtils
  - Replace hardcoded margins and sizes with constants from StyleConstants

### 1.2. Implement Dynamic Layouts

- [ ] **Replace fixed widget sizes with size policies:**
  ```python
  # Example in setup_charts_tab
  self.chart_canvas.setSizePolicy(
      QSizePolicy.Expanding, 
      QSizePolicy.Expanding
  )
  ```

- [ ] **Use stretches in layouts appropriately:**
  ```python
  # Example in filter panel layout
  left_layout = QVBoxLayout(left_panel)
  left_layout.addWidget(filter_group)
  left_layout.addStretch(1)  # This pushes controls to the top
  ```

- [ ] **Update SplitterHandles to be more responsive:**
  ```python
  # In MainWindow.__init__
  self.setStyleSheet("""
      QSplitter::handle {
          background-color: #2A3F5F;
          width: 2px;
          height: 2px;
      }
      QSplitter::handle:hover {
          background-color: #D4AF37;
      }
  """)
  ```

### 1.3. Implement Progressive Disclosure Pattern

- [ ] **Create a CollapsibleSection widget:**
  ```python
  # src/ui/widgets/collapsible_section.py
  from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFrame
  from PySide6.QtCore import Qt
  
  class CollapsibleSection(QWidget):
      def __init__(self, title, parent=None):
          super().__init__(parent)
          self.title = title
          self.content = QFrame()
          self.content_layout = QVBoxLayout(self.content)
          
          self.toggle_button = QPushButton(f"▶ {title}")
          self.toggle_button.setCheckable(True)
          self.toggle_button.clicked.connect(self.toggle_content)
          
          layout = QVBoxLayout(self)
          layout.addWidget(self.toggle_button)
          layout.addWidget(self.content)
          self.content.setVisible(False)
          
      def toggle_content(self, checked):
          self.content.setVisible(checked)
          self.toggle_button.setText(f"▼ {self.title}" if checked else f"▶ {self.title}")
          
      def add_widget(self, widget):
          self.content_layout.addWidget(widget)
  ```

- [ ] **Reorganize Charts tab to use collapsible sections:**
  - Move advanced options like limits and sorting into a "Advanced Options" collapsible section
  - Organize display options under a collapsible "Display Settings" section
  - Keep primary data selection options visible by default

### 1.4. Enhance Data Table Interactions

- [ ] **Create an EnhancedTableView class extending QTableView:**
  ```python
  # src/ui/widgets/enhanced_table_view.py
  from PySide6.QtWidgets import QTableView, QMenu, QHeaderView
  from PySide6.QtCore import Qt, Signal
  
  class EnhancedTableView(QTableView):
      exportRequested = Signal(str)  # Emitted when export is requested
      
      def __init__(self, parent=None):
          super().__init__(parent)
          self.setContextMenuPolicy(Qt.CustomContextMenu)
          self.customContextMenuRequested.connect(self.show_context_menu)
          
          # Enable sorting
          self.setSortingEnabled(True)
          
          # Enable selection
          self.setSelectionBehavior(QTableView.SelectRows)
          
          # Setup headers
          self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
          self.horizontalHeader().setStretchLastSection(True)
          self.horizontalHeader().setSectionsMovable(True)
          
          # Double click to resize columns to content
          self.horizontalHeader().setDefaultSectionSize(120)
          self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
          self.horizontalHeader().sectionDoubleClicked.connect(
              lambda index: self.horizontalHeader().resizeSection(
                  index, QHeaderView.ResizeToContents
              )
          )
      
      def show_context_menu(self, position):
          menu = QMenu(self)
          export_action = menu.addAction("Export to CSV")
          export_action.triggered.connect(lambda: self.exportRequested.emit("csv"))
          
          copy_action = menu.addAction("Copy Selection")
          copy_action.triggered.connect(self.copy_selection)
          
          menu.exec_(self.viewport().mapToGlobal(position))
          
      def copy_selection(self):
          # Implementation for copying selected cells to clipboard
          selected = self.selectionModel().selectedIndexes()
          if not selected:
              return
              
          # ... rest of implementation
  ```

- [ ] **Replace existing QTableView instances with EnhancedTableView:**
  - Update references in MainWindow.setup_raw_data_tab
  - Update references in MainWindow.setup_analysis_tab
  - Connect the exportRequested signal to appropriate export methods

### 1.5. Improve Visual Hierarchy

- [ ] **Create and apply text style classes:**
  ```python
  # In StyleUtils class
  @staticmethod
  def apply_header_style(label):
      label.setStyleSheet(f"""
          color: {DARK_THEME['accent']};
          font-size: {StyleConstants.FONT_SIZE_HEADER}px;
          font-weight: bold;
      """)
      
  @staticmethod
  def apply_subtitle_style(label):
      label.setStyleSheet(f"""
          color: {DARK_THEME['text_secondary']};
          font-size: {StyleConstants.FONT_SIZE_MEDIUM}px;
          font-style: italic;
      """)
  ```

- [ ] **Use font weights instead of colors for hierarchy where appropriate:**
  - Update headers to use bold text rather than color changes
  - Use italic styling for supplementary information
  - Apply font size variations to establish hierarchy

- [ ] **Reduce border usage and rely more on spacing:**
  - Replace heavy borders with subtle padding to create visual separation
  - Use alternating row colors instead of borders in tables

### 1.6. Add Real-time Filter Feedback

- [ ] **Create a FilterStatusLabel widget:**
  ```python
  # src/ui/widgets/filter_status_label.py
  from PySide6.QtWidgets import QLabel
  from PySide6.QtCore import Qt
  
  class FilterStatusLabel(QLabel):
      def __init__(self, parent=None):
          super().__init__(parent)
          self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
          self.update_count(0, 0)
          
      def update_count(self, filtered_count, total_count):
          self.setText(f"Showing {filtered_count} of {total_count} records")
          
          # Visual indication if filtering is active
          if filtered_count < total_count:
              self.setStyleSheet(f"color: {DARK_THEME['accent']};")
          else:
              self.setStyleSheet(f"color: {DARK_THEME['text_secondary']};")
  ```

- [ ] **Add filter status labels to filter panels:**
  - Add to Raw Data tab filter panel
  - Add to Analysis tab filter panel
  - Update label when filter options change

- [ ] **Implement real-time preview filtering:**
  ```python
  # In update_filter_options method
  def update_filter_options(self):
      # ... existing code ...
      
      # Update filter status with preview count
      selected_values = [self.value_list.item(i).text() 
                          for i in range(self.value_list.count())
                          if self.value_list.item(i).isSelected()]
      
      if selected_values and self.show_value_selection.isChecked():
          preview_count = len(self.raw_data[self.raw_data[column].isin(selected_values)])
          self.filter_status_label.update_count(preview_count, len(self.raw_data))
      else:
          self.filter_status_label.update_count(len(self.raw_data), len(self.raw_data))
  ```

### 1.7. Modernize Components

- [ ] **Create IconButton class:**
  ```python
  # src/ui/widgets/icon_button.py
  from PySide6.QtWidgets import QPushButton
  from PySide6.QtGui import QIcon
  from PySide6.QtCore import QSize
  
  class IconButton(QPushButton):
      def __init__(self, icon_path, text="", tooltip="", parent=None):
          super().__init__(text, parent)
          self.setIcon(QIcon(icon_path))
          self.setIconSize(QSize(16, 16))
          if tooltip:
              self.setToolTip(tooltip)
  ```

- [ ] **Replace standard buttons with icon buttons:**
  - Update import buttons to use file icons
  - Add filter icons to filter buttons
  - Use chart icons in the chart controls
  - Add export icons to export buttons

- [ ] **Add tooltips to all complex controls:**
  ```python
  # Example in setup_charts_tab
  self.chart_type_selector.setToolTip(
      "Select the type of chart to display your data."
  )
  ```

## 2. Better Data Handling

### 2.1. Create a Centralized DataManager

- [ ] **Create a DataManager class:**
  ```python
  # src/core/data/data_manager.py
  import pandas as pd
  from pathlib import Path
  from typing import Dict, List, Optional, Tuple, Any
  
  class DataManager:
      def __init__(self, debug=False):
          self.debug = debug
          self.raw_data = None
          self.processed_data = None
          self.analysis_data = None
          self.analysis_results = {}
          self.current_file_path = None
          
      def load_file(self, file_path: Path) -> Tuple[bool, str]:
          """Load a file and return success flag and message"""
          # Implementation moved from MainWindow.load_csv_file
          # Return tuple of (success, message)
          
      def get_raw_data(self) -> Optional[pd.DataFrame]:
          """Get the raw data"""
          return self.raw_data.copy() if self.raw_data is not None else None
          
      def get_processed_data(self) -> Optional[pd.DataFrame]:
          """Get the processed data"""
          return self.processed_data.copy() if self.processed_data is not None else None
          
      def filter_data(self, column: str, values: List[str]) -> pd.DataFrame:
          """Filter data based on column and values"""
          # Implementation
          
      def analyze_data(self) -> Dict[str, Any]:
          """Run analysis on the data"""
          # Implementation moved from DataProcessor.analyze_data
          
      # Other methods for data operations
  ```

- [ ] **Update MainWindow to use DataManager:**
  ```python
  # In MainWindow.__init__
  from core.data.data_manager import DataManager
  
  self.data_manager = DataManager(debug=self.debug)
  
  # Replace direct data access with DataManager methods:
  # Before:
  # self.raw_data = ...
  # After:
  # data = self.data_manager.get_raw_data()
  ```

### 2.2. Implement Proper Data Models

- [ ] **Create data model classes:**
  ```python
  # src/core/data/models.py
  from dataclasses import dataclass
  from datetime import date
  from typing import List, Dict, Any, Optional
  
  @dataclass
  class ChestRecord:
      date: date
      player: str
      source: str
      chest: str
      score: float
      
      @classmethod
      def from_dict(cls, data: Dict[str, Any]) -> 'ChestRecord':
          """Create a ChestRecord from a dictionary."""
          return cls(
              date=data['DATE'],
              player=data['PLAYER'],
              source=data['SOURCE'],
              chest=data['CHEST'],
              score=float(data['SCORE'])
          )
          
  @dataclass
  class PlayerSummary:
      player: str
      total_score: float
      chest_count: int
      sources: Dict[str, float]
      
      @property
      def efficiency(self) -> float:
          """Calculate points per chest."""
          return self.total_score / self.chest_count if self.chest_count > 0 else 0
  ```

- [ ] **Create a DatasetModel to manage collections of records:**
  ```python
  # src/core/data/dataset_model.py
  import pandas as pd
  from typing import List, Dict, Optional, Any
  from .models import ChestRecord, PlayerSummary
  
  class DatasetModel:
      def __init__(self, records: Optional[List[ChestRecord]] = None):
          self.records = records or []
          
      @classmethod
      def from_dataframe(cls, df: pd.DataFrame) -> 'DatasetModel':
          """Create a DatasetModel from a pandas DataFrame."""
          records = [ChestRecord.from_dict(row) for _, row in df.iterrows()]
          return cls(records)
          
      def to_dataframe(self) -> pd.DataFrame:
          """Convert the records to a pandas DataFrame."""
          return pd.DataFrame([vars(r) for r in self.records])
          
      def filter_by_player(self, player: str) -> 'DatasetModel':
          """Filter records by player name."""
          filtered = [r for r in self.records if r.player == player]
          return DatasetModel(filtered)
          
      # Additional filter and analysis methods
  ```

- [ ] **Update DataManager to use the new data models:**
  ```python
  # Updated DataManager.load_file method
  def load_file(self, file_path: Path) -> Tuple[bool, str]:
      # ... existing file loading code ...
      
      if success:
          try:
              # Convert DataFrame to our data model
              self.dataset = DatasetModel.from_dataframe(df)
              self.raw_data = df  # Keep for backward compatibility
              return True, "File loaded successfully"
          except Exception as e:
              return False, f"Error converting data: {str(e)}"
      else:
          return False, error_message
  ```

### 2.3. Implement Incremental Processing

- [ ] **Add progress reporting to DataManager:**
  ```python
  # Add to DataManager class
  from PySide6.QtCore import Signal, QObject
  
  class DataManager(QObject):
      progressChanged = Signal(int, str)  # Progress percentage, status message
      
      # ... existing code ...
      
      def load_file(self, file_path: Path) -> Tuple[bool, str]:
          self.progressChanged.emit(0, "Starting file load...")
          
          # ... file loading code with progress updates ...
          
          self.progressChanged.emit(50, "Processing data...")
          
          # ... data processing code ...
          
          self.progressChanged.emit(100, "File loaded successfully")
          return True, "File loaded successfully"
  ```

- [ ] **Create a ProgressDialog to show during operations:**
  ```python
  # src/ui/dialogs/progress_dialog.py
  from PySide6.QtWidgets import QDialog, QProgressBar, QLabel, QVBoxLayout
  from PySide6.QtCore import Qt
  
  class ProgressDialog(QDialog):
      def __init__(self, title, parent=None):
          super().__init__(parent)
          self.setWindowTitle(title)
          self.setModal(True)
          
          layout = QVBoxLayout(self)
          
          self.status_label = QLabel("Starting...")
          layout.addWidget(self.status_label)
          
          self.progress_bar = QProgressBar()
          self.progress_bar.setRange(0, 100)
          layout.addWidget(self.progress_bar)
          
          self.setFixedSize(400, 100)
          
      def update_progress(self, percentage, message):
          self.progress_bar.setValue(percentage)
          self.status_label.setText(message)
  ```

- [ ] **Implement chunked data processing for large files:**
  ```python
  # In DataManager.load_file
  def load_file(self, file_path: Path) -> Tuple[bool, str]:
      # ... file existence check ...
      
      try:
          # For large files, process in chunks
          if file_path.stat().st_size > 10_000_000:  # 10MB
              chunks = []
              total_chunks = 0
              
              # Count total chunks first
              for _ in pd.read_csv(file_path, chunksize=10000):
                  total_chunks += 1
                  
              # Now process chunks
              chunk_count = 0
              for chunk in pd.read_csv(file_path, chunksize=10000):
                  # Process chunk
                  chunk = self._preprocess_chunk(chunk)
                  chunks.append(chunk)
                  
                  # Update progress
                  chunk_count += 1
                  progress = int(chunk_count / total_chunks * 100)
                  self.progressChanged.emit(
                      progress, 
                      f"Processing chunk {chunk_count}/{total_chunks}..."
                  )
                  
              # Combine all chunks
              df = pd.concat(chunks, ignore_index=True)
          else:
              # Process small file normally
              df = pd.read_csv(file_path)
              df = self._preprocess_dataframe(df)
              
          # ... continue with processing ...
      except Exception as e:
          return False, f"Error loading file: {str(e)}"
  ```

### 2.4. Improve Memory Management

- [ ] **Implement data sampling for large datasets:**
  ```python
  # Add to DataManager
  def get_visualization_sample(self, max_records=1000):
      """Get a sample suitable for visualization."""
      if self.processed_data is None:
          return None
          
      if len(self.processed_data) <= max_records:
          return self.processed_data.copy()
          
      # For large datasets, return a representative sample
      return self.processed_data.sample(max_records)
  ```

- [ ] **Add cleanup methods for unused data:**
  ```python
  # Add to DataManager
  def cleanup_memory(self, keep_raw=True, keep_processed=True, keep_analysis=True):
      """Clean up memory by releasing data not currently needed."""
      import gc
      
      if not keep_raw:
          self.raw_data = None
          
      if not keep_processed:
          self.processed_data = None
          
      if not keep_analysis:
          self.analysis_data = None
          self.analysis_results = {}
          
      # Force garbage collection
      gc.collect()
  ```

- [ ] **Implement tab-specific data loading:**
  ```python
  # In MainWindow.on_tab_changed method
  def on_tab_changed(self, index):
      """Handle tab change events to manage memory."""
      tab_name = self.tab_widget.tabText(index)
      
      # Only keep relevant data based on active tab
      if tab_name == "Import":
          self.data_manager.cleanup_memory(keep_raw=True, keep_processed=False, keep_analysis=False)
      elif tab_name == "Raw Data":
          self.data_manager.cleanup_memory(keep_raw=True, keep_processed=True, keep_analysis=False)
      elif tab_name == "Analysis":
          self.data_manager.cleanup_memory(keep_raw=True, keep_processed=True, keep_analysis=True)
      elif tab_name == "Charts":
          self.data_manager.cleanup_memory(keep_raw=False, keep_processed=True, keep_analysis=True)
      elif tab_name == "Report":
          self.data_manager.cleanup_memory(keep_raw=False, keep_processed=False, keep_analysis=True)
  ```

### 2.5. Standardize Data Transformations

- [ ] **Create a DataTransformer class with a pipeline of transformations:**
  ```python
  # src/core/data/transformers.py
  import pandas as pd
  from typing import List, Callable, Dict, Any
  
  class DataTransformer:
      """
      A class to apply a sequence of transformations to data.
      """
      def __init__(self):
          self.transformations = []
          
      def add_transformation(self, name: str, transform_func: Callable[[pd.DataFrame], pd.DataFrame]):
          """Add a transformation to the pipeline."""
          self.transformations.append((name, transform_func))
          
      def apply(self, df: pd.DataFrame, progress_callback=None) -> pd.DataFrame:
          """Apply all transformations in sequence."""
          result = df.copy()
          total_steps = len(self.transformations)
          
          for i, (name, transform_func) in enumerate(self.transformations):
              if progress_callback:
                  progress = int((i / total_steps) * 100)
                  progress_callback(progress, f"Applying transformation: {name}")
                  
              result = transform_func(result)
              
          if progress_callback:
              progress_callback(100, "Transformations complete")
              
          return result
  ```

- [ ] **Create standard transformations:**
  ```python
  # src/core/data/standard_transformations.py
  import pandas as pd
  
  def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
      """Standardize column names to uppercase."""
      return df.rename(columns={col: col.upper() for col in df.columns})
      
  def convert_date_column(df: pd.DataFrame) -> pd.DataFrame:
      """Convert DATE column to datetime."""
      if 'DATE' in df.columns:
          df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
      return df
      
  def convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
      """Convert numeric columns to appropriate types."""
      if 'SCORE' in df.columns:
          df['SCORE'] = pd.to_numeric(df['SCORE'], errors='coerce')
      return df
      
  # ... more transformations ...
  ```

- [ ] **Use standard transformations in DataManager:**
  ```python
  # In DataManager.__init__
  from core.data.transformers import DataTransformer
  from core.data.standard_transformations import (
      clean_column_names, convert_date_column, convert_numeric_columns
  )
  
  self.transformer = DataTransformer()
  self.transformer.add_transformation("Clean Column Names", clean_column_names)
  self.transformer.add_transformation("Convert Dates", convert_date_column)
  self.transformer.add_transformation("Convert Numerics", convert_numeric_columns)
  
  # In DataManager.load_file
  # Replace manual transformations with:
  df = self.transformer.apply(df, progress_callback=self.progressChanged.emit)
  ```

### 2.6. Add Data Caching Layer

- [ ] **Implement a DataCache class:**
  ```python
  # src/core/data/cache.py
  import pandas as pd
  from typing import Dict, Any, Optional
  import hashlib
  import pickle
  from pathlib import Path
  
  class DataCache:
      def __init__(self, cache_dir: Path):
          self.cache_dir = cache_dir
          self.cache_dir.mkdir(parents=True, exist_ok=True)
          self.memory_cache = {}
          
      def get_cache_key(self, data_id: str, params: Dict[str, Any]) -> str:
          """Generate a unique cache key based on data ID and parameters."""
          param_str = str(sorted(params.items()))
          combined = f"{data_id}:{param_str}".encode('utf-8')
          return hashlib.md5(combined).hexdigest()
          
      def get(self, data_id: str, params: Dict[str, Any]) -> Optional[Any]:
          """Get cached data if available."""
          cache_key = self.get_cache_key(data_id, params)
          
          # Check memory cache first
          if cache_key in self.memory_cache:
              return self.memory_cache[cache_key]
              
          # Check disk cache
          cache_file = self.cache_dir / f"{cache_key}.pkl"
          if cache_file.exists():
              try:
                  with open(cache_file, 'rb') as f:
                      result = pickle.load(f)
                      # Store in memory cache for faster access next time
                      self.memory_cache[cache_key] = result
                      return result
              except Exception:
                  # If loading fails, return None
                  return None
                  
          return None
          
      def set(self, data_id: str, params: Dict[str, Any], data: Any, 
              save_to_disk: bool = True) -> None:
          """Save data to cache."""
          cache_key = self.get_cache_key(data_id, params)
          
          # Store in memory cache
          self.memory_cache[cache_key] = data
          
          # Optionally store on disk
          if save_to_disk:
              cache_file = self.cache_dir / f"{cache_key}.pkl"
              with open(cache_file, 'wb') as f:
                  pickle.dump(data, f)
                  
      def clear(self, data_id: Optional[str] = None) -> None:
          """Clear cache for specific data ID or all cache."""
          if data_id is None:
              # Clear all cache
              self.memory_cache = {}
              for cache_file in self.cache_dir.glob("*.pkl"):
                  cache_file.unlink()
          else:
              # Clear cache for specific data ID
              keys_to_remove = [k for k in self.memory_cache if k.startswith(data_id)]
              for key in keys_to_remove:
                  del self.memory_cache[key]
                  
              for cache_file in self.cache_dir.glob(f"{data_id}_*.pkl"):
                  cache_file.unlink()
  ```

- [ ] **Use DataCache in DataManager:**
  ```python
  # In DataManager.__init__
  from core.data.cache import DataCache
  
  self.cache = DataCache(Path("cache"))
  
  # In DataManager.analyze_data
  def analyze_data(self) -> Dict[str, Any]:
      """Run analysis on the data with caching."""
      if self.processed_data is None:
          return {}
          
      # Create cache parameters based on current state
      cache_params = {
          "data_hash": hash(str(self.processed_data.values.tobytes())),
          "columns": ','.join(self.processed_data.columns)
      }
      
      # Try to get cached results
      cached_results = self.cache.get("analysis", cache_params)
      if cached_results is not None:
          return cached_results
          
      # Run analysis if not cached
      results = self._run_analysis()
      
      # Cache the results
      self.cache.set("analysis", cache_params, results)
      
      return results
  ```

### 2.7. Strengthen Type Safety

- [ ] **Add comprehensive type hints throughout the code:**
  ```python
  # Example for a method in DataManager
  def filter_data(
      self, 
      column: str, 
      values: List[str], 
      date_range: Optional[Tuple[date, date]] = None
  ) -> pd.DataFrame:
      """
      Filter data based on column values and optional date range.
      
      Args:
          column: Column name to filter on
          values: List of values to include
          date_range: Optional tuple of (start_date, end_date)
          
      Returns:
          Filtered DataFrame
      """
      if self.processed_data is None:
          return pd.DataFrame()
          
      # ... implementation ...
  ```

- [ ] **Add input validation to all data methods:**
  ```python
  # Example for DataManager.filter_data
  def filter_data(self, column: str, values: List[str]) -> pd.DataFrame:
      """Filter data based on column and values."""
      # Validate inputs
      if not isinstance(column, str):
          raise TypeError(f"Column must be a string, got {type(column)}")
          
      if not isinstance(values, list):
          raise TypeError(f"Values must be a list, got {type(values)}")
          
      if self.processed_data is None:
          return pd.DataFrame()
          
      if column not in self.processed_data.columns:
          raise ValueError(f"Column '{column}' not found in data")
          
      # ... actual filtering logic ...
  ```

- [ ] **Create custom Exceptions for data operations:**
  ```python
  # src/core/data/exceptions.py
  class DataError(Exception):
      """Base class for all data-related errors."""
      pass
      
  class DataLoadError(DataError):
      """Error raised when data cannot be loaded."""
      pass
      
  class DataValidationError(DataError):
      """Error raised when data fails validation."""
      pass
      
  class DataProcessingError(DataError):
      """Error raised during data processing."""
      pass
  ```

## 3. Improved Code Modularity

### 3.1. Extract Chart Generation Logic

- [ ] **Create a ChartGenerator base class:**
  ```python
  # src/visualization/charts/chart_generator.py
  import matplotlib.pyplot as plt
  import pandas as pd
  from typing import Dict, Any, Optional, Tuple
  from pathlib import Path
  
  class ChartGenerator:
      """Base class for chart generation."""
      
      def __init__(self, style_config: Dict[str, Any] = None):
          self.style_config = style_config or {
              'bg_color': '#1A2742',
              'text_color': '#FFFFFF',
              'accent_color': '#D4AF37',
              'grid_color': '#2A3F5F'
          }
          
      def create_figure(self, figsize: Tuple[int, int] = (8, 6)) -> Tuple[plt.Figure, plt.Axes]:
          """Create a figure and axes with proper styling."""
          fig = plt.figure(figsize=figsize, facecolor=self.style_config['bg_color'])
          ax = fig.add_subplot(111)
          
          # Apply styling
          ax.set_facecolor(self.style_config['bg_color'])
          
          # Set text colors
          ax.xaxis.label.set_color(self.style_config['text_color'])
          ax.yaxis.label.set_color(self.style_config['text_color'])
          ax.title.set_color(self.style_config['accent_color'])
          
          # Set tick colors
          ax.tick_params(
              axis='both', 
              colors=self.style_config['text_color'],
              labelcolor=self.style_config['text_color']
          )
          
          # Set spine colors
          for spine in ax.spines.values():
              spine.set_color(self.style_config['grid_color'])
              
          return fig, ax
          
      def generate(self, data: pd.DataFrame, **kwargs) -> Tuple[plt.Figure, plt.Axes]:
          """
          Generate a chart from data.
          
          This is an abstract method that should be implemented by subclasses.
          """
          raise NotImplementedError("Subclasses must implement generate method")
          
      def save_chart(self, fig: plt.Figure, filepath: Path, dpi: int = 300) -> None:
          """Save the chart to a file."""
          fig.savefig(
              filepath,
              dpi=dpi,
              bbox_inches='tight',
              facecolor=self.style_config['bg_color'],
              edgecolor='none'
          )
          
      def close_figure(self, fig: plt.Figure) -> None:
          """Close the figure to free memory."""
          plt.close(fig)
  ```

- [ ] **Create specific chart generator implementations:**
  ```python
  # src/visualization/charts/bar_chart_generator.py
  from .chart_generator import ChartGenerator
  import pandas as pd
  import matplotlib.pyplot as plt
  from typing import Dict, Any, List, Tuple, Optional
  
  class BarChartGenerator(ChartGenerator):
      """Generator for bar charts."""
      
      def __init__(self, style_config: Dict[str, Any] = None):
          super().__init__(style_config)
          self.colors = style_config.get('bar_colors', [
              '#D4AF37', '#5991C4', '#6EC1A7', '#D46A5F'
          ])
          
      def generate(
          self, 
          data: pd.DataFrame,
          category_column: str,
          value_column: str,
          title: str = "",
          xlabel: str = "",
          ylabel: str = "",
          show_values: bool = True,
          **kwargs
      ) -> Tuple[plt.Figure, plt.Axes]:
          """Generate a bar chart."""
          fig, ax = self.create_figure()
          
          # Create list of colors by cycling through the palette
          bar_colors = [self.colors[i % len(self.colors)] for i in range(len(data))]
          
          # Create the bar chart
          bars = ax.bar(
              data[category_column].values, 
              data[value_column].values, 
              color=bar_colors
          )
          
          # Set labels and title
          if xlabel:
              ax.set_xlabel(xlabel)
          if ylabel:
              ax.set_ylabel(ylabel)
          if title:
              ax.set_title(title)
              
          # Rotate x-tick labels if there are many categories
          if len(data) > 5:
              plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
              
          # Add values on top of bars if requested
          if show_values:
              for bar in bars:
                  height = bar.get_height()
                  ax.text(
                      bar.get_x() + bar.get_width()/2.,
                      height,
                      f'{height:,.0f}',
                      ha='center',
                      va='bottom',
                      color=self.style_config['text_color'],
                      fontweight='bold'
                  )
                  
          fig.tight_layout()
          return fig, ax
  ```

- [ ] **Create more chart generators for other chart types:**
  - Implement PieChartGenerator
  - Implement LineChartGenerator
  - Implement HorizontalBarChartGenerator
  - Implement ScatterChartGenerator

- [ ] **Create a ChartFactory to instantiate appropriate chart generators:**
  ```python
  # src/visualization/charts/chart_factory.py
  from typing import Dict, Any, Optional
  from .chart_generator import ChartGenerator
  from .bar_chart_generator import BarChartGenerator
  from .pie_chart_generator import PieChartGenerator
  from .line_chart_generator import LineChartGenerator
  from .horizontal_bar_chart_generator import HorizontalBarChartGenerator
  
  class ChartFactory:
      """Factory for creating chart generators."""
      
      @staticmethod
      def create_chart_generator(
          chart_type: str, 
          style_config: Optional[Dict[str, Any]] = None
      ) -> ChartGenerator:
          """
          Create a chart generator based on the chart type.
          
          Args:
              chart_type: Type of chart to create
              style_config: Optional style configuration
              
          Returns:
              A ChartGenerator instance
              
          Raises:
              ValueError: If chart_type is not supported
          """
          chart_type = chart_type.lower().replace(" ", "_")
          
          if chart_type == "bar_chart":
              return BarChartGenerator(style_config)
          elif chart_type == "pie_chart":
              return PieChartGenerator(style_config)
          elif chart_type == "line_chart":
              return LineChartGenerator(style_config)
          elif chart_type == "horizontal_bar":
              return HorizontalBarChartGenerator(style_config)
          else:
              raise ValueError(f"Unsupported chart type: {chart_type}")
  ```

- [ ] **Update MainWindow.update_chart to use the chart generators:**
  ```python
  # In MainWindow.update_chart
  from visualization.charts.chart_factory import ChartFactory
  
  def update_chart(self):
      # ... existing code to get data ...
      
      # Get chart type and style config
      chart_type = self.chart_type_selector.currentText()
      style_config = self.chart_canvas.style_presets['default']
      
      try:
          # Create chart generator
          chart_generator = ChartFactory.create_chart_generator(chart_type, style_config)
          
          # Generate chart
          fig, ax = chart_generator.generate(
              data=data,
              category_column=category_column,
              value_column=measure,
              title=chart_title,
              xlabel=category_column,
              ylabel=measure,
              show_values=self.chart_show_values.isChecked()
          )
          
          # Replace existing chart
          self.chart_canvas.fig.clear()
          self.chart_canvas.fig = fig
          self.chart_canvas.axes = ax
          self.chart_canvas.draw()
          
      except Exception as e:
          if self.debug:
              print(f"Error updating chart: {str(e)}")
              import traceback
              traceback.print_exc()
  ```

### 3.2. Create UI Component Library

- [ ] **Create a BaseFilterPanel component:**
  ```python
  # src/ui/widgets/base_filter_panel.py
  from PySide6.QtWidgets import (
      QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
      QPushButton, QCheckBox, QListWidget, QGroupBox, QAbstractItemView
  )
  from PySide6.QtCore import Signal, Qt
  
  class BaseFilterPanel(QWidget):
      """Base class for filter panels."""
      
      filterApplied = Signal(dict)  # Emitted with filter settings
      filterCleared = Signal()
      
      def __init__(self, parent=None, title="Filter Options"):
          super().__init__(parent)
          self.title = title
          self.setup_ui()
          
      def setup_ui(self):
          """Set up the UI components."""
          main_layout = QVBoxLayout(self)
          
          # Create filter group
          self.filter_group = QGroupBox(self.title)
          filter_layout = QVBoxLayout()
          
          # Column selection
          column_layout = QHBoxLayout()
          column_layout.addWidget(QLabel("Filter Column:"))
          self.column_selector = QComboBox()
          self.column_selector.currentIndexChanged.connect(self.on_column_changed)
          column_layout.addWidget(self.column_selector)
          filter_layout.addLayout(column_layout)
          
          # Value selection toggle
          self.show_value_selection = QCheckBox("Select specific values")
          self.show_value_selection.setChecked(True)
          self.show_value_selection.stateChanged.connect(self.toggle_value_selection)
          filter_layout.addWidget(self.show_value_selection)
          
          # Value selection area
          self.value_panel = QWidget()
          value_layout = QVBoxLayout(self.value_panel)
          
          # Value list
          self.value_list = QListWidget()
          self.value_list.setSelectionMode(QAbstractItemView.MultiSelection)
          value_layout.addWidget(self.value_list)
          
          # Value selection buttons
          button_layout = QHBoxLayout()
          self.select_all_button = QPushButton("Select All")
          self.select_all_button.clicked.connect(self.select_all_values)
          self.deselect_all_button = QPushButton("Deselect All")
          self.deselect_all_button.clicked.connect(self.deselect_all_values)
          button_layout.addWidget(self.select_all_button)
          button_layout.addWidget(self.deselect_all_button)
          value_layout.addLayout(button_layout)
          
          filter_layout.addWidget(self.value_panel)
          
          # Action buttons
          action_layout = QHBoxLayout()
          self.apply_button = QPushButton("Apply Filter")
          self.apply_button.clicked.connect(self.apply_filter)
          self.clear_button = QPushButton("Clear Filter")
          self.clear_button.clicked.connect(self.clear_filter)
          action_layout.addWidget(self.apply_button)
          action_layout.addWidget(self.clear_button)
          filter_layout.addLayout(action_layout)
          
          self.filter_group.setLayout(filter_layout)
          main_layout.addWidget(self.filter_group)
          main_layout.addStretch(1)
          
      def on_column_changed(self, index):
          """Handle column selection change."""
          self.update_value_list()
          
      def toggle_value_selection(self, state):
          """Toggle value selection panel visibility."""
          self.value_panel.setVisible(state == Qt.Checked)
          
      def update_value_list(self):
          """
          Update the value list based on the selected column.
          
          This method should be implemented by subclasses.
          """
          pass
          
      def select_all_values(self):
          """Select all values in the list."""
          for i in range(self.value_list.count()):
              self.value_list.item(i).setSelected(True)
              
      def deselect_all_values(self):
          """Deselect all values in the list."""
          for i in range(self.value_list.count()):
              self.value_list.item(i).setSelected(False)
              
      def get_filter_settings(self):
          """
          Get the current filter settings.
          
          Returns:
              A dictionary with filter settings
          """
          settings = {
              'column': self.column_selector.currentText(),
              'value_filter_enabled': self.show_value_selection.isChecked(),
              'selected_values': []
          }
          
          if settings['value_filter_enabled']:
              settings['selected_values'] = [
                  item.text() for item in self.value_list.selectedItems()
              ]
              
          return settings
          
      def apply_filter(self):
          """Apply the filter."""
          self.filterApplied.emit(self.get_filter_settings())
          
      def clear_filter(self):
          """Clear the filter."""
          self.deselect_all_values()
          self.filterCleared.emit()
  ```

- [ ] **Create a DataFilterPanel that extends BaseFilterPanel:**
  ```python
  # src/ui/widgets/data_filter_panel.py
  from PySide6.QtWidgets import QMessageBox
  import pandas as pd
  from .base_filter_panel import BaseFilterPanel
  
  class DataFilterPanel(BaseFilterPanel):
      """Filter panel specifically for DataFrame filtering."""
      
      def __init__(self, parent=None, title="Data Filter"):
          super().__init__(parent, title)
          self.dataframe = None
          
      def set_dataframe(self, df):
          """Set the DataFrame to filter."""
          self.dataframe = df
          self.update_columns()
          
      def update_columns(self):
          """Update column selector with DataFrame columns."""
          if self.dataframe is None:
              return
              
          self.column_selector.clear()
          self.column_selector.addItems(self.dataframe.columns.tolist())
          
      def update_value_list(self):
          """Update value list based on selected column."""
          if self.dataframe is None:
              return
              
          column = self.column_selector.currentText()
          if not column:
              return
              
          self.value_list.clear()
          
          try:
              # Get unique values from the selected column
              unique_values = self.dataframe[column].astype(str).unique().tolist()
              unique_values.sort()
              
              # Add items to the list
              for value in unique_values:
                  self.value_list.addItem(value)
                  
              # Select all by default
              self.select_all_values()
          except Exception as e:
              QMessageBox.warning(
                  self,
                  "Error",
                  f"Error updating value list: {str(e)}"
              )
  ```

- [ ] **Create more reusable UI components:**
  - Create a SearchableListWidget (list with search bar)
  - Create a DateRangeSelector (start/end date with calendar popups)
  - Create a ColorPicker for chart customization
  - Create a SortableTableView with enhanced sorting

- [ ] **Update MainWindow to use the new components:**
  ```python
  # In MainWindow.setup_raw_data_tab
  from ui.widgets.data_filter_panel import DataFilterPanel
  
  # Create filter panel
  self.raw_data_filter_panel = DataFilterPanel(title="Raw Data Filter")
  self.raw_data_filter_panel.filterApplied.connect(self.apply_raw_data_filter)
  self.raw_data_filter_panel.filterCleared.connect(self.clear_raw_data_filter)
  
  # Add filter panel to layout
  raw_data_splitter.addWidget(self.raw_data_filter_panel)
  
  # Similarly in setup_analysis_tab
  self.analysis_filter_panel = DataFilterPanel(title="Analysis Filter")
  self.analysis_filter_panel.filterApplied.connect(self.apply_analysis_filter)
  self.analysis_filter_panel.filterCleared.connect(self.clear_analysis_filter)
  ```

### 3.3. Implement Clear Interfaces

- [ ] **Create an interface for data loaders:**
  ```python
  # src/core/data/interfaces.py
  from abc import ABC, abstractmethod
  import pandas as pd
  from typing import Tuple, Optional
  from pathlib import Path
  
  class DataLoader(ABC):
      """Interface for data loading."""
      
      @abstractmethod
      def load(self, file_path: Path) -> Tuple[Optional[pd.DataFrame], bool, str]:
          """
          Load data from a file.
          
          Args:
              file_path: Path to the file
              
          Returns:
              Tuple of (DataFrame, success, message)
          """
          pass
  ```

- [ ] **Create a CSV data loader implementation:**
  ```python
  # src/core/data/csv_loader.py
  import pandas as pd
  from typing import Tuple, Optional, List
  from pathlib import Path
  from .interfaces import DataLoader
  
  class CSVLoader(DataLoader):
      """CSV data loader."""
      
      def __init__(self, encodings: List[str] = None, debug: bool = False):
          self.encodings = encodings or ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
          self.debug = debug
          
      def load(self, file_path: Path) -> Tuple[Optional[pd.DataFrame], bool, str]:
          """Load a CSV file."""
          if not file_path.exists():
              return None, False, f"File not found: {file_path}"
              
          for encoding in self.encodings:
              try:
                  if self.debug:
                      print(f"Trying to read with {encoding}...")
                  df = pd.read_csv(file_path, encoding=encoding)
                  return df, True, f"File loaded with {encoding} encoding"
              except Exception as e:
                  if self.debug:
                      print(f"Failed with {encoding}: {str(e)}")
                  continue
                  
          return None, False, "Failed to load CSV with any encoding"
  ```

- [ ] **Create interfaces for other components:**
  - Create DataProcessor interface
  - Create DataExporter interface
  - Create ChartRenderer interface
  - Create ReportGenerator interface

- [ ] **Update DataManager to use the interfaces:**
  ```python
  # In DataManager.__init__
  from core.data.interfaces import DataLoader
  from core.data.csv_loader import CSVLoader
  
  # Use dependency injection for components
  def __init__(self, data_loader: DataLoader = None, debug: bool = False):
      self.debug = debug
      self.data_loader = data_loader or CSVLoader(debug=debug)
      
  # In DataManager.load_file
  def load_file(self, file_path: Path) -> Tuple[bool, str]:
      """Load a file using the configured data loader."""
      try:
          df, success, message = self.data_loader.load(file_path)
          
          if success:
              self.raw_data = df
              # ... process data ...
              return True, "File loaded successfully"
          else:
              return False, message
      except Exception as e:
          return False, f"Error loading file: {str(e)}"
  ```

### 3.4. Decouple Configuration

- [ ] **Create a proper AppConfig class:**
  ```python
  # src/core/config/app_config.py
  from pathlib import Path
  import json
  from typing import Dict, Any, Optional
  
  class AppConfig:
      """Application configuration manager."""
      
      def __init__(self, config_file: Path = None):
          self.config_file = config_file or Path.home() / ".config" / "total-battle-analyzer" / "config.json"
          self.config = self._load_config()
          
      def _load_config(self) -> Dict[str, Any]:
          """Load configuration from file."""
          if self.config_file.exists():
              try:
                  with open(self.config_file, 'r') as f:
                      return json.load(f)
              except Exception:
                  return self._get_default_config()
          else:
              # Create default config
              config = self._get_default_config()
              self.save_config()
              return config
              
      def _get_default_config(self) -> Dict[str, Any]:
          """Get default configuration."""
          return {
              "general": {
                  "theme": "dark",
                  "language": "en",
                  "debug": False
              },
              "paths": {
                  "import_dir": str(Path.cwd() / "data" / "imports"),
                  "export_dir": str(Path.cwd() / "data" / "exports"),
                  "cache_dir": str(Path.cwd() / "cache")
              },
              "ui": {
                  "window_width": 1200,
                  "window_height": 800,
                  "splitter_positions": {}
              },
              "files": {
                  "recent_files": [],
                  "max_recent_files": 10
              },
              "charts": {
                  "default_chart_type": "Bar Chart",
                  "show_values": True,
                  "show_grid": True,
                  "colors": ["#D4AF37", "#5991C4", "#6EC1A7", "#D46A5F"]
              }
          }
          
      def save_config(self) -> None:
          """Save configuration to file."""
          self.config_file.parent.mkdir(parents=True, exist_ok=True)
          
          with open(self.config_file, 'w') as f:
              json.dump(self.config, f, indent=4)
              
      def get(self, section: str, key: str, default: Any = None) -> Any:
          """Get a configuration value."""
          if section in self.config and key in self.config[section]:
              return self.config[section][key]
          return default
          
      def set(self, section: str, key: str, value: Any) -> None:
          """Set a configuration value."""
          if section not in self.config:
              self.config[section] = {}
              
          self.config[section][key] = value
          self.save_config()
          
      def get_path(self, key: str, default: Optional[Path] = None) -> Path:
          """Get a path from configuration."""
          path_str = self.get("paths", key, default)
          if path_str is None:
              return Path.cwd()
              
          return Path(path_str)
          
      def set_path(self, key: str, path: Path) -> None:
          """Set a path in configuration."""
          self.set("paths", key, str(path))
          
      def add_recent_file(self, file_path: Path) -> None:
          """Add a file to recent files list."""
          recent_files = self.get("files", "recent_files", [])
          max_recent = self.get("files", "max_recent_files", 10)
          
          # Convert to string for JSON serialization
          file_path_str = str(file_path)
          
          # Remove if already exists
          if file_path_str in recent_files:
              recent_files.remove(file_path_str)
              
          # Add to start of list
          recent_files.insert(0, file_path_str)
          
          # Limit to max recent files
          if len(recent_files) > max_recent:
              recent_files = recent_files[:max_recent]
              
          self.set("files", "recent_files", recent_files)
  ```

- [ ] **Update MainWindow to use AppConfig:**
  ```python
  # In MainWindow.__init__
  from core.config.app_config import AppConfig
  
  self.config = AppConfig()
  
  # Initialize window size from config
  window_width = self.config.get("ui", "window_width", 1200)
  window_height = self.config.get("ui", "window_height", 800)
  self.resize(window_width, window_height)
  
  # Later, save window size on close event
  def closeEvent(self, event):
      # Save window size
      self.config.set("ui", "window_width", self.width())
      self.config.set("ui", "window_height", self.height())
      
      # Save splitter positions
      if hasattr(self, 'raw_data_splitter'):
          self.config.set("ui", "splitter_positions", {
              "raw_data": self.raw_data_splitter.sizes(),
              "analysis": self.analysis_splitter.sizes(),
              "charts": self.chart_splitter.sizes()
          })
          
      event.accept()
  ```

### 3.5. Use Composition Over Inheritance

- [ ] **Refactor MainWindow to use composition:**
  ```python
  # src/ui/main/tab_manager.py
  from PySide6.QtWidgets import QTabWidget
  
  class TabManager:
      """Manager for application tabs."""
      
      def __init__(self, tab_widget: QTabWidget):
          self.tab_widget = tab_widget
          self.tabs = {}
          
      def add_tab(self, tab, name):
          """Add a tab to the manager."""
          self.tabs[name] = tab
          self.tab_widget.addTab(tab, name)
          
      def get_tab(self, name):
          """Get a tab by name."""
          return self.tabs.get(name)
          
      def get_current_tab(self):
          """Get the currently active tab."""
          index = self.tab_widget.currentIndex()
          return self.tab_widget.widget(index)
          
      def set_current_tab(self, name):
          """Set the current tab by name."""
          if name in self.tabs:
              index = self.tab_widget.indexOf(self.tabs[name])
              self.tab_widget.setCurrentIndex(index)
              
      def disable_tabs_except(self, name):
          """Disable all tabs except the named one."""
          for tab_name, tab in self.tabs.items():
              index = self.tab_widget.indexOf(tab)
              self.tab_widget.setTabEnabled(index, tab_name == name)
              
      def enable_all_tabs(self):
          """Enable all tabs."""
          for tab in self.tabs.values():
              index = self.tab_widget.indexOf(tab)
              self.tab_widget.setTabEnabled(index, True)
  ```

- [ ] **Create tab controller classes:**
  ```python
  # src/ui/tabs/import_tab_controller.py
  from PySide6.QtWidgets import QWidget
  from PySide6.QtCore import Signal
  from core.data.interfaces import DataLoader
  
  class ImportTabController:
      """Controller for the Import tab."""
      
      file_loaded = Signal(str)  # Emitted when a file is loaded
      
      def __init__(self, tab_widget: QWidget, data_loader: DataLoader):
          self.tab_widget = tab_widget
          self.data_loader = data_loader
          self.setup_connections()
          
      def setup_connections(self):
          """Set up signal connections."""
          # Connect import area signals
          if hasattr(self.tab_widget, 'import_area'):
              self.tab_widget.import_area.fileSelected.connect(self.load_file)
              
      def load_file(self, file_path: str):
          """Load a file and emit signal if successful."""
          # Use data_loader to load file
          # If successful, emit file_loaded signal
          pass
  ```

- [ ] **Update MainWindow to use the controllers:**
  ```python
  # In MainWindow.setup_ui_components
  from ui.main.tab_manager import TabManager
  from ui.tabs.import_tab_controller import ImportTabController
  from ui.tabs.raw_data_tab_controller import RawDataTabController
  from ui.tabs.analysis_tab_controller import AnalysisTabController
  from ui.tabs.charts_tab_controller import ChartsTabController
  from ui.tabs.report_tab_controller import ReportTabController
  
  # Create tab widget
  self.tab_widget = QTabWidget()
  self.tab_manager = TabManager(self.tab_widget)
  
  # Create tabs
  self.import_tab = QWidget()
  self.raw_data_tab = QWidget()
  self.analysis_tab = QWidget()
  self.charts_tab = QWidget()
  self.report_tab = QWidget()
  
  # Setup tabs
  self.setup_import_tab()
  self.setup_raw_data_tab()
  self.setup_analysis_tab()
  self.setup_charts_tab()
  self.setup_report_tab()
  
  # Add tabs to manager
  self.tab_manager.add_tab(self.import_tab, "Import")
  self.tab_manager.add_tab(self.raw_data_tab, "Raw Data")
  self.tab_manager.add_tab(self.analysis_tab, "Analysis")
  self.tab_manager.add_tab(self.charts_tab, "Charts")
  self.tab_manager.add_tab(self.report_tab, "Report")
  
  # Create controllers
  self.import_controller = ImportTabController(self.import_tab, self.data_manager)
  self.raw_data_controller = RawDataTabController(self.raw_data_tab, self.data_manager)
  self.analysis_controller = AnalysisTabController(self.analysis_tab, self.data_manager)
  self.charts_controller = ChartsTabController(self.charts_tab, self.data_manager)
  self.report_controller = ReportTabController(self.report_tab, self.data_manager)
  
  # Connect controllers
  self.import_controller.file_loaded.connect(self.on_file_loaded)
  ```

### 3.6. Standardize Event Handling

- [ ] **Create an EventBus for communication between components:**
  ```python
  # src/core/events/event_bus.py
  from typing import Dict, List, Callable, Any
  
  class EventBus:
      """
      A simple event bus for communication between components.
      """
      
      def __init__(self):
          self.subscribers = {}
          
      def subscribe(self, event_type: str, callback: Callable) -> None:
          """
          Subscribe to an event.
          
          Args:
              event_type: The type of event to subscribe to
              callback: The function to call when the event occurs
          """
          if event_type not in self.subscribers:
              self.subscribers[event_type] = []
              
          self.subscribers[event_type].append(callback)
          
      def unsubscribe(self, event_type: str, callback: Callable) -> None:
          """
          Unsubscribe from an event.
          
          Args:
              event_type: The type of event to unsubscribe from
              callback: The function to unsubscribe
          """
          if event_type in self.subscribers:
              if callback in self.subscribers[event_type]:
                  self.subscribers[event_type].remove(callback)
                  
      def publish(self, event_type: str, data: Any = None) -> None:
          """
          Publish an event.
          
          Args:
              event_type: The type of event to publish
              data: Optional data to pass to subscribers
          """
          if event_type in self.subscribers:
              for callback in self.subscribers[event_type]:
                  callback(data)
  ```

- [ ] **Create standard event types:**
  ```python
  # src/core/events/event_types.py
  class EventTypes:
      """Standard event types for the application."""
      
      # Data events
      DATA_LOADED = "data_loaded"
      DATA_FILTERED = "data_filtered"
      DATA_ANALYZED = "data_analyzed"
      DATA_EXPORTED = "data_exported"
      
      # UI events
      TAB_CHANGED = "tab_changed"
      FILTER_APPLIED = "filter_applied"
      FILTER_CLEARED = "filter_cleared"
      
      # Chart events
      CHART_TYPE_CHANGED = "chart_type_changed"
      CHART_DATA_CHANGED = "chart_data_changed"
      CHART_GENERATED = "chart_generated"
      
      # Report events
      REPORT_GENERATED = "report_generated"
      REPORT_EXPORTED = "report_exported"
  ```

- [ ] **Use EventBus in the application:**
  ```python
  # In MainWindow.__init__
  from core.events.event_bus import EventBus
  from core.events.event_types import EventTypes
  
  self.event_bus = EventBus()
  
  # Subscribe to events
  self.event_bus.subscribe(EventTypes.DATA_LOADED, self.on_data_loaded)
  self.event_bus.subscribe(EventTypes.FILTER_APPLIED, self.on_filter_applied)
  
  # In MainWindow.load_csv_file
  def load_csv_file(self, file_path: str):
      # ... existing code ...
      
      if success:
          # Publish event
          self.event_bus.publish(EventTypes.DATA_LOADED, {
              'file_path': file_path,
              'row_count': len(self.raw_data)
          })
  ```

## 4. Simplified Code Structure

### 4.1. Reduce Method Sizes

- [ ] **Break down large methods like update_chart:**
  ```python
  # Original update_chart method
  def update_chart(self):
      # ... 100+ lines of code ...
      
  # Refactored into smaller methods
  def update_chart(self):
      """Update the chart based on the selected options."""
      # Get chart configuration
      config = self._get_chart_config()
      
      # Get data for the chart
      data = self._get_chart_data(config)
      if data is None or len(data) == 0:
          return
          
      # Apply data transformations
      data = self._transform_chart_data(data, config)
      
      # Generate the chart
      self._generate_chart(data, config)
      
  def _get_chart_config(self):
      """Get the current chart configuration from UI components."""
      return {
          'chart_type': self.chart_type_selector.currentText(),
          'data_category': self.chart_data_category.currentText(),
          'measure': self.chart_data_column.currentText(),
          'sort_column': self.chart_sort_column.currentText(),
          'sort_ascending': self.chart_sort_order.currentText() == "Ascending",
          'limit_enabled': self.chart_limit_enabled.isChecked(),
          'limit_value': self.chart_limit_value.value(),
          'show_values': self.chart_show_values.isChecked(),
          'show_grid': self.chart_show_grid.isChecked(),
      }
      
  def _get_chart_data(self, config):
      """Get data for the chart based on configuration."""
      # ... 25 lines of code ...
      
  def _transform_chart_data(self, data, config):
      """Apply transformations to the chart data."""
      # ... 25 lines of code ...
      
  def _generate_chart(self, data, config):
      """Generate the chart based on data and configuration."""
      # ... 30 lines of code ...
  ```

- [ ] **Break down load_csv_file into smaller methods:**
  ```python
  # Break down load_csv_file into:
  def load_csv_file(self, file_path: str):
      """Load a CSV file and process the data."""
      # File validation
      if not self._validate_file(file_path):
          return False
          
      # Check for redundant load
      if self._is_already_loaded(file_path):
          return True
          
      # Load and parse file
      success, message = self._load_and_parse_file(file_path)
      if not success:
          self.show_error_dialog("Error Loading File", message)
          return False
          
      # Process data
      self._process_loaded_data()
      
      # Update UI
      self._update_ui_after_load(file_path)
      
      return True
  ```

- [ ] **Apply the same pattern to other large methods:**
  - Break down setup_ui_components
  - Break down process_data
  - Break down analyze_data
  - Break down create_full_report_html

### 4.2. Minimize Conditional Logic

- [ ] **Replace chart type if-else chain with a dictionary:**
  ```python
  # Instead of:
  if chart_type == "Bar Chart":
      self._create_bar_chart(ax, data, category_column, measure, colors, show_values, chart_title)
  elif chart_type == "Horizontal Bar":
      self._create_horizontal_bar_chart(ax, data, category_column, measure, colors, show_values, chart_title)
  elif chart_type == "Pie Chart":
      self._create_pie_chart(ax, data, category_column, measure, colors, show_values, chart_title)
  # ...
  
  # Use a dictionary of functions:
  chart_creators = {
      "Bar Chart": self._create_bar_chart,
      "Horizontal Bar": self._create_horizontal_bar_chart,
      "Pie Chart": self._create_pie_chart,
      "Line Chart": self._create_line_chart,
      "Scatter Chart": self._create_scatter_chart
  }
  
  chart_creator = chart_creators.get(chart_type)
  if chart_creator:
      chart_creator(ax, data, category_column, measure, colors, show_values, chart_title)
  else:
      print(f"Unknown chart type: {chart_type}")
  ```

- [ ] **Use strategy pattern for different data processing approaches:**
  ```python
  # Create DataProcessingStrategy base class
  class DataProcessingStrategy:
      """Base class for data processing strategies."""
      
      def process(self, data):
          """Process the data."""
          raise NotImplementedError("Subclasses must implement process method")
          
  # Create specific strategies
  class StandardDataProcessingStrategy(DataProcessingStrategy):
      """Standard data processing strategy."""
      
      def process(self, data):
          """Process the data using standard approach."""
          # ... implementation ...
          
  class LargeDataProcessingStrategy(DataProcessingStrategy):
      """Strategy for processing large datasets."""
      
      def process(self, data):
          """Process the data using approach optimized for large datasets."""
          # ... implementation ...
          
  # In DataManager
  def process_data(self, data):
      """Process data using appropriate strategy."""
      # Choose strategy based on data size
      if len(data) > 10000:
          strategy = LargeDataProcessingStrategy()
      else:
          strategy = StandardDataProcessingStrategy()
          
      return strategy.process(data)
  ```

### 4.3. Standardize Error Handling

- [ ] **Create a standard error handling utility:**
  ```python
  # src/utils/error_handler.py
  import traceback
  import logging
  from PySide6.QtWidgets import QMessageBox
  from typing import Optional, Callable
  
  logger = logging.getLogger(__name__)
  
  class ErrorHandler:
      """Centralized error handling utility."""
      
      @staticmethod
      def log_error(error_msg, exception=None, show_traceback=True):
          """
          Log an error to the console and log file.
          
          Args:
              error_msg: Error message to log
              exception: Exception object, if available
              show_traceback: Whether to print the traceback
          """
          if exception:
              logger.error(f"{error_msg}: {str(exception)}")
          else:
              logger.error(error_msg)
              
          if show_traceback and exception:
              logger.error(traceback.format_exc())
              
      @staticmethod
      def show_error_dialog(parent, title, message, detailed_text=None):
          """
          Show an error dialog to the user.
          
          Args:
              parent: Parent widget
              title: Dialog title
              message: Error message
              detailed_text: Detailed error information
          """
          error_dialog = QMessageBox(parent)
          error_dialog.setIcon(QMessageBox.Critical)
          error_dialog.setWindowTitle(title)
          error_dialog.setText(message)
          
          if detailed_text:
              error_dialog.setDetailedText(detailed_text)
              
          error_dialog.setStandardButtons(QMessageBox.Ok)
          error_dialog.exec_()
          
      @staticmethod
      def handle_exception(func: Callable) -> Callable:
          """
          Decorator for handling exceptions in methods.
          
          Args:
              func: Function to decorate
              
          Returns:
              Wrapped function with exception handling
          """
          def wrapper(*args, **kwargs):
              try:
                  return func(*args, **kwargs)
              except Exception as e:
                  # First argument should be self
                  self = args[0] if args else None
                  
                  # Log the error
                  ErrorHandler.log_error(
                      f"Error in {func.__name__}",
                      exception=e,
                      show_traceback=True
                  )
                  
                  # Show error dialog if self has show_error_dialog method
                  if hasattr(self, 'show_error_dialog'):
                      self.show_error_dialog(
                          f"Error in {func.__name__.replace('_', ' ').title()}",
                          f"An error occurred: {str(e)}"
                      )
                  
                  # Re-raise or return default value
                  return None
                  
          return wrapper
  ```

- [ ] **Use the ErrorHandler throughout the codebase:**
  ```python
  # In a method that could raise exceptions
  from utils.error_handler import ErrorHandler
  
  @ErrorHandler.handle_exception
  def load_csv_file(self, file_path):
      """Load a CSV file with error handling."""
      # Implementation that might raise exceptions
  ```

- [ ] **Create custom exceptions for different error categories:**
  ```python
  # src/utils/exceptions.py
  class AppError(Exception):
      """Base class for application errors."""
      pass
      
  class DataError(AppError):
      """Error related to data operations."""
      pass
      
  class FileError(AppError):
      """Error related to file operations."""
      pass
      
  class ConfigError(AppError):
      """Error related to configuration."""
      pass
      
  class UIError(AppError):
      """Error related to UI operations."""
      pass
      
  class ChartError(AppError):
      """Error related to chart generation."""
      pass
  ```

### 4.4. Adopt Type Hints

- [ ] **Add type hints to all functions and methods:**
  ```python
  # Example with type hints
  from typing import List, Dict, Optional, Tuple, Any
  import pandas as pd
  from pathlib import Path
  
  def filter_data(
      self,
      dataframe: pd.DataFrame,
      column: str,
      values: List[str],
      date_range: Optional[Tuple[str, str]] = None
  ) -> pd.DataFrame:
      """
      Filter a DataFrame based on column values and date range.
      
      Args:
          dataframe: The DataFrame to filter
          column: Column name to filter on
          values: List of values to include
          date_range: Optional tuple of (start_date, end_date)
          
      Returns:
          Filtered DataFrame
      """
      # Implementation
  ```

- [ ] **Create type aliases for common types:**
  ```python
  # src/utils/types.py
  from typing import Dict, List, Union, Any, TypeVar, Optional
  import pandas as pd
  
  # Type aliases
  DataDict = Dict[str, Any]
  StrList = List[str]
  DataFrameOrNone = Optional[pd.DataFrame]
  
  # Generic types
  T = TypeVar('T')
  
  # Function types
  FilterFunc = Callable[[pd.DataFrame], pd.DataFrame]
  ```

- [ ] **Use type hints throughout the codebase:**
  - Add return type hints to all methods
  - Add parameter type hints to all methods
  - Use Optional for parameters that can be None
  - Use Union for parameters that can be multiple types
  - Include typing imports at the top of each file

### 4.5. Implement Builder Patterns

- [ ] **Create a ChartBuilder class:**
  ```python
  # src/visualization/charts/chart_builder.py
  import matplotlib.pyplot as plt
  import pandas as pd
  from typing import Dict, List, Any, Optional, Tuple
  
  class ChartBuilder:
      """
      Builder for creating charts with a fluent interface.
      """
      
      def __init__(self):
          self.reset()
          
      def reset(self):
          """Reset the builder to default state."""
          self.fig = None
          self.ax = None
          self.data = None
          self.chart_type = "bar"
          self.category_column = ""
          self.value_column = ""
          self.title = ""
          self.xlabel = ""
          self.ylabel = ""
          self.show_values = True
          self.show_grid = True
          self.colors = ["#D4AF37", "#5991C4", "#6EC1A7", "#D46A5F"]
          self.figsize = (8, 6)
          self.style = {
              'bg_color': '#1A2742',
              'text_color': '#FFFFFF',
              'accent_color': '#D4AF37',
              'grid_color': '#2A3F5F'
          }
          return self
          
      def with_data(self, data: pd.DataFrame) -> 'ChartBuilder':
          """Set the data for the chart."""
          self.data = data
          return self
          
      def with_type(self, chart_type: str) -> 'ChartBuilder':
          """Set the chart type."""
          self.chart_type = chart_type.lower()
          return self
          
      def with_columns(self, category: str, value: str) -> 'ChartBuilder':
          """Set the category and value columns."""
          self.category_column = category
          self.value_column = value
          return self
          
      def with_title(self, title: str) -> 'ChartBuilder':
          """Set the chart title."""
          self.title = title
          return self
          
      def with_labels(self, xlabel: str, ylabel: str) -> 'ChartBuilder':
          """Set the axis labels."""
          self.xlabel = xlabel
          self.ylabel = ylabel
          return self
          
      def with_values(self, show: bool) -> 'ChartBuilder':
          """Set whether to show values on the chart."""
          self.show_values = show
          return self
          
      def with_grid(self, show: bool) -> 'ChartBuilder':
          """Set whether to show the grid."""
          self.show_grid = show
          return self
          
      def with_colors(self, colors: List[str]) -> 'ChartBuilder':
          """Set the colors for the chart."""
          self.colors = colors
          return self
          
      def with_size(self, width: int, height: int) -> 'ChartBuilder':
          """Set the figure size."""
          self.figsize = (width, height)
          return self
          
      def with_style(self, style: Dict[str, Any]) -> 'ChartBuilder':
          """Set the chart style."""
          self.style = style
          return self
          
      def build(self) -> Tuple[plt.Figure, plt.Axes]:
          """Build and return the chart."""
          if self.data is None:
              raise ValueError("Data must be set before building a chart")
              
          if not self.category_column or not self.value_column:
              raise ValueError("Category and value columns must be set")
              
          # Create figure and axes
          self.fig = plt.figure(figsize=self.figsize, facecolor=self.style['bg_color'])
          self.ax = self.fig.add_subplot(111)
          
          # Apply styling
          self.ax.set_facecolor(self.style['bg_color'])
          self.ax.xaxis.label.set_color(self.style['text_color'])
          self.ax.yaxis.label.set_color(self.style['text_color'])
          self.ax.title.set_color(self.style['accent_color'])
          self.ax.tick_params(axis='both', colors=self.style['text_color'], labelcolor=self.style['text_color'])
          
          for spine in self.ax.spines.values():
              spine.set_color(self.style['grid_color'])
              
          # Set grid
          self.ax.grid(self.show_grid, color=self.style['grid_color'], linestyle='--', alpha=0.3)
          
          # Set labels and title
          if self.xlabel:
              self.ax.set_xlabel(self.xlabel)
          if self.ylabel:
              self.ax.set_ylabel(self.ylabel)
          if self.title:
              self.ax.set_title(self.title)
              
          # Create the chart based on type
          if self.chart_type == "bar":
              self._create_bar_chart()
          elif self.chart_type == "line":
              self._create_line_chart()
          elif self.chart_type == "pie":
              self._create_pie_chart()
          elif self.chart_type == "horizontal_bar":
              self._create_horizontal_bar_chart()
          else:
              raise ValueError(f"Unsupported chart type: {self.chart_type}")
              
          self.fig.tight_layout()
          return self.fig, self.ax
          
      def _create_bar_chart(self):
          """Create a bar chart."""
          # Implementation
          
      def _create_line_chart(self):
          """Create a line chart."""
          # Implementation
          
      def _create_pie_chart(self):
          """Create a pie chart."""
          # Implementation
          
      def _create_horizontal_bar_chart(self):
          """Create a horizontal bar chart."""
          # Implementation
  ```

- [ ] **Use ChartBuilder in the application:**
  ```python
  # In MainWindow.update_chart
  from visualization.charts.chart_builder import ChartBuilder
  
  def update_chart(self):
      """Update the chart based on the selected options."""
      # Get data and configuration
      # ...
      
      try:
          # Create chart using builder
          builder = ChartBuilder()
          fig, ax = (builder
              .with_data(data)
              .with_type(chart_type)
              .with_columns(category_column, measure)
              .with_title(chart_title)
              .with_labels(category_column, measure)
              .with_values(self.chart_show_values.isChecked())
              .with_grid(self.chart_show_grid.isChecked())
              .with_colors(self.chart_canvas.get_colors())
              .with_style(self.chart_canvas.style_presets['default'])
              .build())
          
          # Update chart canvas
          self.chart_canvas.fig.clear()
          self.chart_canvas.fig = fig
          self.chart_canvas.axes = ax
          self.chart_canvas.draw()
          
      except Exception as e:
          if self.debug:
              print(f"Error updating chart: {str(e)}")
              import traceback
              traceback.print_exc()
  ```

- [ ] **Create a ReportBuilder for report generation:**
  ```python
  # src/visualization/reports/report_builder.py
  from typing import List, Dict, Any, Optional
  import pandas as pd
  from pathlib import Path
  
  class ReportBuilder:
      """
      Builder for creating HTML reports with a fluent interface.
      """
      
      def __init__(self):
          self.reset()
          
      def reset(self):
          """Reset the builder to default state."""
          self.title = "Total Battle Analyzer Report"
          self.subtitle = ""
          self.include_charts = True
          self.include_tables = True
          self.include_stats = True
          self.sections = []
          self.css_styles = self._get_default_styles()
          return self
          
      def with_title(self, title: str) -> 'ReportBuilder':
          """Set the report title."""
          self.title = title
          return self
          
      def with_subtitle(self, subtitle: str) -> 'ReportBuilder':
          """Set the report subtitle."""
          self.subtitle = subtitle
          return self
          
      def with_features(self, charts: bool, tables: bool, stats: bool) -> 'ReportBuilder':
          """Set which features to include in the report."""
          self.include_charts = charts
          self.include_tables = tables
          self.include_stats = stats
          return self
          
      def add_section(self, title: str, content: str) -> 'ReportBuilder':
          """Add a section to the report."""
          self.sections.append({
              'title': title,
              'content': content
          })
          return self
          
      def add_chart_section(self, title: str, chart_path: str, description: str = "") -> 'ReportBuilder':
          """Add a chart section to the report."""
          if not self.include_charts:
              return self
              
          content = f"""
          <div class="chart-container">
              <img src="file:///{chart_path}" alt="{title}" style="max-width:100%; height:auto;">
              {f"<p>{description}</p>" if description else ""}
          </div>
          """
          
          self.sections.append({
              'title': title,
              'content': content
          })
          
          return self
          
      def add_table_section(self, title: str, df: pd.DataFrame, description: str = "") -> 'ReportBuilder':
          """Add a table section to the report."""
          if not self.include_tables:
              return self
              
          # Convert DataFrame to HTML table
          table_html = df.to_html(classes="data-table", index=False)
          
          content = f"""
          {f"<p>{description}</p>" if description else ""}
          {table_html}
          """
          
          self.sections.append({
              'title': title,
              'content': content
          })
          
          return self
          
      def add_stats_section(self, title: str, stats: Dict[str, Any], description: str = "") -> 'ReportBuilder':
          """Add a statistics section to the report."""
          if not self.include_stats:
              return self
              
          # Convert stats to HTML
          stats_html = """
          <div class="stats-container">
          """
          
          for key, value in stats.items():
              formatted_key = key.replace('_', ' ').title()
              formatted_value = f"{value:,.2f}" if isinstance(value, (int, float)) else str(value)
              
              stats_html += f"""
              <div class="stat-box">
                  <p>{formatted_key}</p>
                  <p class="stat-value">{formatted_value}</p>
              </div>
              """
              
          stats_html += """
          </div>
          """
          
          content = f"""
          {f"<p>{description}</p>" if description else ""}
          {stats_html}
          """
          
          self.sections.append({
              'title': title,
              'content': content
          })
          
          return self
          
      def build(self) -> str:
          """Build and return the HTML report."""
          # Generate HTML header
          html = f"""
          <!DOCTYPE html>
          <html>
          <head>
              <meta charset="UTF-8">
              <title>{self.title}</title>
              <style>
              {self.css_styles}
              </style>
          </head>
          <body>
              <div class="header">
                  <h1>{self.title}</h1>
                  {f"<h2>{self.subtitle}</h2>" if self.subtitle else ""}
                  <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
              </div>
          """
          
          # Add sections
          for section in self.sections:
              html += f"""
              <div class="section">
                  <h2>{section['title']}</h2>
                  {section['content']}
              </div>
              """
              
          # Add footer
          html += f"""
          <div class="footer">
              <p>Total Battle Analyzer - Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
          </div>
          </body>
          </html>
          """
          
          return html
          
      def _get_default_styles(self) -> str:
          """Get default CSS styles for the report."""
          return """
          body {
              font-family: Arial, sans-serif;
              background-color: #0E1629;
              color: #FFFFFF;
              margin: 20px;
          }
          h1, h2, h3, h4 {
              color: #D4AF37;
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
          }
          table {
              width: 100%;
              border-collapse: collapse;
              margin: 15px 0;
          }
          th, td {
              border: 1px solid #2A3F5F;
              padding: 8px;
              text-align: left;
          }
          th {
              background-color: #0E1629;
              color: #D4AF37;
          }
          .chart-container {
              margin: 20px 0;
              text-align: center;
          }
          .footer {
              margin-top: 30px;
              text-align: center;
              font-size: 0.8em;
              color: #FFFFFF;
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
          }
          .stat-value {
              font-size: 24px;
              font-weight: bold;
              color: #D4AF37;
          }
          """
  ```

### 4.6. Simplify UI Updates

- [ ] **Create a UI update manager:**
  ```python
  # src/ui/utils/ui_updater.py
  from PySide6.QtWidgets import QWidget, QComboBox, QTableView
  from PySide6.QtCore import QObject, Signal, Qt
  import pandas as pd
  
  class UIUpdater(QObject):
      """
      A utility class for managing UI updates.
      """
      
      # Signals for different UI update events
      dataTableUpdated = Signal(str)  # Table name
      comboBoxUpdated = Signal(str)   # ComboBox name
      
      def __init__(self):
          super().__init__()
          self.table_models = {}
          
      def update_table_model(self, table_view: QTableView, model, table_name: str = ""):
          """
          Update a table view with a new model.
          
          Args:
              table_view: The QTableView to update
              model: The model to set
              table_name: Optional table name for tracking
          """
          table_view.setModel(model)
          
          # Store reference to the model
          if table_name:
              self.table_models[table_name] = model
              
          # Resize columns to content
          for i in range(model.columnCount()):
              table_view.resizeColumnToContents(i)
              
          # Emit signal
          if table_name:
              self.dataTableUpdated.emit(table_name)
              
      def update_combo_box(self, combo_box: QComboBox, items, current_item=None, combo_name: str = ""):
          """
          Update a combo box with new items.
          
          Args:
              combo_box: The QComboBox to update
              items: List of items to add
              current_item: Optional item to set as current
              combo_name: Optional combo box name for tracking
          """
          # Block signals to prevent recursive updates
          combo_box.blockSignals(True)
          
          # Remember current text if needed
          old_text = combo_box.currentText()
          
          # Clear and add new items
          combo_box.clear()
          combo_box.addItems(items)
          
          # Set current item
          if current_item is not None:
              index = combo_box.findText(current_item)
              if index >= 0:
                  combo_box.setCurrentIndex(index)
          elif old_text:
              # Try to restore previous selection
              index = combo_box.findText(old_text)
              if index >= 0:
                  combo_box.setCurrentIndex(index)
                  
          # Unblock signals
          combo_box.blockSignals(False)
          
          # Emit signal
          if combo_name:
              self.comboBoxUpdated.emit(combo_name)
              
      def refresh_all_tables(self):
          """Refresh all tracked table views."""
          for table_name, model in self.table_models.items():
              self.dataTableUpdated.emit(table_name)
  ```

- [ ] **Use UIUpdater in MainWindow:**
  ```python
  # In MainWindow.__init__
  from ui.utils.ui_updater import UIUpdater
  
  self.ui_updater = UIUpdater()
  
  # In MainWindow.load_csv_file (after loading data)
  # Update the column selectors
  columns = self.raw_data.columns.tolist()
  self.ui_updater.update_combo_box(self.column_selector, columns, None, "raw_data_column_selector")
  self.ui_updater.update_combo_box(self.analysis_column_selector, columns, None, "analysis_column_selector")
  
  # Update the data table
  self.ui_updater.update_table_model(self.raw_data_table, model, "raw_data_table")
  ```

- [ ] **Create UI update constants:**
  ```python
  # src/ui/utils/ui_constants.py
  class UIUpdateEvents:
      """Constants for UI update events."""
      
      # Table update events
      RAW_DATA_TABLE_UPDATED = "raw_data_table_updated"
      ANALYSIS_TABLE_UPDATED = "analysis_table_updated"
      
      # Combo box update events
      COLUMN_SELECTOR_UPDATED = "column_selector_updated"
      CHART_TYPE_SELECTOR_UPDATED = "chart_type_selector_updated"
      
      # Filter events
      RAW_DATA_FILTER_APPLIED = "raw_data_filter_applied"
      ANALYSIS_FILTER_APPLIED = "analysis_filter_applied"
      
      # Chart events
      CHART_UPDATED = "chart_updated"
      CHART_CONFIG_CHANGED = "chart_config_changed"
  ```

- [ ] **Create a UI State Manager for tracking UI state:**
  ```python
  # src/ui/utils/ui_state_manager.py
  from typing import Dict, Any, Optional
  
  class UIStateManager:
      """
      Manages the state of UI components across the application.
      """
      
      def __init__(self):
          self.states = {}
          
      def set_state(self, component_id: str, state: Any) -> None:
          """
          Set the state of a component.
          
          Args:
              component_id: Unique identifier for the component
              state: State to store
          """
          self.states[component_id] = state
          
      def get_state(self, component_id: str, default: Any = None) -> Any:
          """
          Get the state of a component.
          
          Args:
              component_id: Unique identifier for the component
              default: Default value if state is not found
              
          Returns:
              The stored state or default value
          """
          return self.states.get(component_id, default)
          
      def remove_state(self, component_id: str) -> None:
          """
          Remove the state of a component.
          
          Args:
              component_id: Unique identifier for the component
          """
          if component_id in self.states:
              del self.states[component_id]
              
      def clear_all_states(self) -> None:
          """Clear all stored states."""
          self.states = {}
          
      def get_all_states(self) -> Dict[str, Any]:
          """
          Get all stored states.
          
          Returns:
              Dictionary of all component states
          """
          return self.states.copy()
  ```

## 5. Better Separation of Concerns

### 5.1. Implement Model-View-Presenter Pattern

- [ ] **Create a DataModel class:**
  ```python
  # src/core/data/data_model.py
  import pandas as pd
  from typing import Dict, List, Optional, Any
  from datetime import datetime
  
  class DataModel:
      """
      Model representing the application's data state.
      """
      
      def __init__(self):
          self.raw_data = None  # Original data
          self.processed_data = None  # Processed data
          self.analysis_results = {}  # Analysis results
          self.current_file_path = None  # Current file path
          self.last_updated = None  # Last update timestamp
          
      def set_raw_data(self, df: pd.DataFrame) -> None:
          """Set the raw data."""
          self.raw_data = df
          self.last_updated = datetime.now()
          
      def set_processed_data(self, df: pd.DataFrame) -> None:
          """Set the processed data."""
          self.processed_data = df
          self.last_updated = datetime.now()
          
      def set_analysis_results(self, results: Dict[str, Any]) -> None:
          """Set the analysis results."""
          self.analysis_results = results
          self.last_updated = datetime.now()
          
      def set_current_file_path(self, file_path: str) -> None:
          """Set the current file path."""
          self.current_file_path = file_path
          
      def get_raw_data(self) -> Optional[pd.DataFrame]:
          """Get the raw data."""
          return self.raw_data.copy() if self.raw_data is not None else None
          
      def get_processed_data(self) -> Optional[pd.DataFrame]:
          """Get the processed data."""
          return self.processed_data.copy() if self.processed_data is not None else None
          
      def get_analysis_results(self) -> Dict[str, Any]:
          """Get the analysis results."""
          return self.analysis_results.copy()
          
      def get_current_file_path(self) -> Optional[str]:
          """Get the current file path."""
          return self.current_file_path
          
      def get_last_updated(self) -> Optional[datetime]:
          """Get the last update timestamp."""
          return self.last_updated
          
      def clear(self) -> None:
          """Clear all data."""
          self.raw_data = None
          self.processed_data = None
          self.analysis_results = {}
          self.current_file_path = None
          self.last_updated = datetime.now()
  ```

- [ ] **Create a Presenter base class:**
  ```python
  # src/ui/presenters/presenter.py
  from typing import Optional
  
  class Presenter:
      """
      Base class for presenters in the MVP pattern.
      """
      
      def __init__(self, model, view):
          self.model = model
          self.view = view
          self.initialize()
          
      def initialize(self) -> None:
          """
          Initialize the presenter.
          
          This method should be implemented by subclasses to set up
          initial UI state and connect signals.
          """
          pass
          
      def cleanup(self) -> None:
          """
          Clean up the presenter.
          
          This method should be implemented by subclasses to
          clean up any resources used by the presenter.
          """
          pass
  ```

- [ ] **Create specific presenters for each tab:**
  ```python
  # src/ui/presenters/raw_data_presenter.py
  from .presenter import Presenter
  from core.data.data_model import DataModel
  from ui.widgets.data_filter_panel import DataFilterPanel
  from PySide6.QtWidgets import QTableView
  
  class RawDataPresenter(Presenter):
      """
      Presenter for the Raw Data tab.
      """
      
      def __init__(self, model: DataModel, filter_panel: DataFilterPanel, table_view: QTableView):
          self.filter_panel = filter_panel
          self.table_view = table_view
          super().__init__(model, None)  # No single view
          
      def initialize(self) -> None:
          """Initialize the presenter."""
          # Connect signals
          self.filter_panel.filterApplied.connect(self.on_filter_applied)
          self.filter_panel.filterCleared.connect(self.on_filter_cleared)
          
          # Update UI if model has data
          self.update_ui()
          
      def update_ui(self) -> None:
          """Update the UI based on the model state."""
          processed_data = self.model.get_processed_data()
          if processed_data is not None:
              # Update filter panel
              self.filter_panel.set_dataframe(processed_data)
              
              # Update table view
              from ui.models.custom_table_model import CustomTableModel
              model = CustomTableModel(processed_data)
              self.table_view.setModel(model)
              
              # Resize columns to content
              for i in range(model.columnCount()):
                  self.table_view.resizeColumnToContents(i)
                  
      def on_filter_applied(self, filter_settings: dict) -> None:
          """Handle filter applied event."""
          raw_data = self.model.get_raw_data()
          if raw_data is None:
              return
              
          # Apply filter
          filtered_data = self._apply_filter(raw_data, filter_settings)
          
          # Update model
          self.model.set_processed_data(filtered_data)
          
          # Update table view
          from ui.models.custom_table_model import CustomTableModel
          self.table_view.setModel(CustomTableModel(filtered_data))
          
      def on_filter_cleared(self) -> None:
          """Handle filter cleared event."""
          raw_data = self.model.get_raw_data()
          if raw_data is None:
              return
              
          # Reset processed data to raw data
          self.model.set_processed_data(raw_data.copy())
          
          # Update UI
          self.update_ui()
          
      def _apply_filter(self, df, filter_settings: dict):
          """Apply filter to DataFrame."""
          # Implementation
  ```

- [ ] **Update MainWindow to use the MVP pattern:**
  ```python
  # In MainWindow.setup_ui_components
  from core.data.data_model import DataModel
  from ui.presenters.raw_data_presenter import RawDataPresenter
  from ui.presenters.analysis_presenter import AnalysisPresenter
  from ui.presenters.chart_presenter import ChartPresenter
  from ui.presenters.report_presenter import ReportPresenter
  
  # Create data model
  self.data_model = DataModel()
  
  # Create presenters
  self.raw_data_presenter = RawDataPresenter(
      self.data_model,
      self.raw_data_filter_panel,
      self.raw_data_table
  )
  
  self.analysis_presenter = AnalysisPresenter(
      self.data_model,
      self.analysis_filter_panel,
      self.analysis_view
  )
  
  self.chart_presenter = ChartPresenter(
      self.data_model,
      self.chart_canvas,
      self.chart_controls_widget
  )
  
  self.report_presenter = ReportPresenter(
      self.data_model,
      self.report_view
  )
  ```

### 5.2. Create Data Access Layer

- [ ] **Create a DataAccess interface:**
  ```python
  # src/core/data/access/data_access.py
  from abc import ABC, abstractmethod
  import pandas as pd
  from typing import Tuple, Optional
  from pathlib import Path
  
  class DataAccess(ABC):
      """
      Interface for data access operations.
      """
      
      @abstractmethod
      def load_data(self, file_path: Path) -> Tuple[Optional[pd.DataFrame], bool, str]:
          """
          Load data from a file.
          
          Args:
              file_path: Path to the file
              
          Returns:
              Tuple of (DataFrame, success, message)
          """
          pass
          
      @abstractmethod
      def save_data(self, df: pd.DataFrame, file_path: Path) -> Tuple[bool, str]:
          """
          Save data to a file.
          
          Args:
              df: DataFrame to save
              file_path: Path to save to
              
          Returns:
              Tuple of (success, message)
          """
          pass
  ```

- [ ] **Create a CSVDataAccess implementation:**
  ```python
  # src/core/data/access/csv_data_access.py
  import pandas as pd
  from typing import Tuple, Optional, List
  from pathlib import Path
  from .data_access import DataAccess
  
  class CSVDataAccess(DataAccess):
      """
      CSV implementation of the DataAccess interface.
      """
      
      def __init__(self, encodings: List[str] = None, debug: bool = False):
          self.encodings = encodings or ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
          self.debug = debug
          
      def load_data(self, file_path: Path) -> Tuple[Optional[pd.DataFrame], bool, str]:
          """
          Load data from a CSV file.
          
          Args:
              file_path: Path to the CSV file
              
          Returns:
              Tuple of (DataFrame, success, message)
          """
          if not file_path.exists():
              return None, False, f"File not found: {file_path}"
              
          if self.debug:
              print(f"Attempting to load: {file_path}")
              
          for encoding in self.encodings:
              try:
                  if self.debug:
                      print(f"Trying encoding: {encoding}")
                      
                  # Try comma separator
                  df = pd.read_csv(file_path, encoding=encoding)
                  if self.debug:
                      print(f"Successfully loaded with encoding: {encoding} and comma separator")
                  return df, True, f"File loaded with {encoding} encoding"
              except Exception as e:
                  if self.debug:
                      print(f"Failed with encoding {encoding} and comma separator: {str(e)}")
                      
                  # Try semicolon separator
                  try:
                      df = pd.read_csv(file_path, encoding=encoding, sep=';')
                      if self.debug:
                          print(f"Successfully loaded with encoding: {encoding} and semicolon separator")
                      return df, True, f"File loaded with {encoding} encoding and semicolon separator"
                  except Exception as e:
                      if self.debug:
                          print(f"Failed with encoding {encoding} and semicolon separator: {str(e)}")
                      continue
                      
          return None, False, "Failed to load CSV with any encoding"
          
      def save_data(self, df: pd.DataFrame, file_path: Path) -> Tuple[bool, str]:
          """
          Save data to a CSV file.
          
          Args:
              df: DataFrame to save
              file_path: Path to save to
              
          Returns:
              Tuple of (success, message)
          """
          try:
              df.to_csv(file_path, index=False, encoding='utf-8')
              return True, f"Data saved to {file_path}"
          except Exception as e:
              return False, f"Error saving data: {str(e)}"
  ```

- [ ] **Use the DataAccess layer in DataManager:**
  ```python
  # Updated DataManager.__init__
  from core.data.access.data_access import DataAccess
  from core.data.access.csv_data_access import CSVDataAccess
  
  def __init__(self, data_access: DataAccess = None, debug: bool = False):
      self.debug = debug
      self.data_access = data_access or CSVDataAccess(debug=debug)
      
  # Updated DataManager.load_file
  def load_file(self, file_path: Path) -> Tuple[bool, str]:
      """Load a file using the data access layer."""
      if self.debug:
          print(f"Loading file: {file_path}")
          
      try:
          df, success, message = self.data_access.load_data(file_path)
          
          if success:
              self.raw_data = df
              # ... process data ...
              self.current_file_path = file_path
              return True, "File loaded successfully"
          else:
              return False, message
      except Exception as e:
          return False, f"Error loading file: {str(e)}"
  ```

### 5.3. Separate Business Logic

- [ ] **Create a DataAnalysisService class:**
  ```python
  # src/core/services/data_analysis_service.py
  import pandas as pd
  from typing import Dict, List, Any, Optional
  
  class DataAnalysisService:
      """
      Service for data analysis operations.
      """
      
      def __init__(self, debug: bool = False):
          self.debug = debug
          
      def analyze_data(self, df: pd.DataFrame) -> Dict[str, Any]:
          """
          Analyze data and return analysis results.
          
          Args:
              df: DataFrame to analyze
              
          Returns:
              Dictionary of analysis results
          """
          if df is None or df.empty:
              return {}
              
          results = {}
          
          # Check for required columns
          required_columns = {'PLAYER', 'SCORE', 'CHEST', 'SOURCE'}
          if not all(col in df.columns for col in required_columns):
              if self.debug:
                  print(f"Missing required columns for analysis")
              return {}
              
          try:
              # Calculate player totals
              player_totals = df.groupby('PLAYER')['SCORE'].sum().reset_index()
              player_totals = player_totals.sort_values('SCORE', ascending=False)
              
              # Add chest counts
              player_counts = df.groupby('PLAYER').size().reset_index(name='CHEST_COUNT')
              player_totals = player_totals.merge(player_counts, on='PLAYER', how='left')
              
              results['player_totals'] = player_totals
              
              # Calculate chest totals
              chest_totals = df.groupby('CHEST')['SCORE'].sum().reset_index()
              chest_totals = chest_totals.sort_values('SCORE', ascending=False)
              
              # Add chest counts
              chest_counts = df.groupby('CHEST').size().reset_index(name='CHEST_COUNT')
              chest_totals = chest_totals.merge(chest_counts, on='CHEST', how='left')
              
              results['chest_totals'] = chest_totals
              
              # Calculate source totals
              source_totals = df.groupby('SOURCE')['SCORE'].sum().reset_index()
              source_totals = source_totals.sort_values('SCORE', ascending=False)
              
              # Add source counts
              source_counts = df.groupby('SOURCE').size().reset_index(name='CHEST_COUNT')
              source_totals = source_totals.merge(source_counts, on='SOURCE', how='left')
              
              results['source_totals'] = source_totals
              
              # Create player overview
              player_overview = player_totals.copy()
              player_overview = player_overview.rename(columns={'SCORE': 'TOTAL_SCORE'})
              
              # Get scores by source for each player
              source_scores = df.pivot_table(
                  index='PLAYER',
                  columns='SOURCE',
                  values='SCORE',
                  aggfunc='sum',
                  fill_value=0
              ).reset_index()
              
              # Merge with player overview
              player_overview = player_overview.merge(source_scores, on='PLAYER', how='left')
              
              results['player_overview'] = player_overview
              
              return results
              
          except Exception as e:
              if self.debug:
                  print(f"Error in data analysis: {str(e)}")
              return {}
              
      def filter_data(
          self, 
          df: pd.DataFrame, 
          column: str, 
          values: List[str],
          date_range: Optional[Tuple[str, str]] = None
      ) -> pd.DataFrame:
          """
          Filter data based on column values and date range.
          
          Args:
              df: DataFrame to filter
              column: Column to filter on
              values: Values to include
              date_range: Optional tuple of (start_date, end_date)
              
          Returns:
              Filtered DataFrame
          """
          if df is None or df.empty:
              return pd.DataFrame()
              
          if column not in df.columns:
              return df.copy()
              
          # Filter by column values
          if values:
              filtered_df = df[df[column].astype(str).isin(values)]
          else:
              filtered_df = df.copy()
              
          # Filter by date range if provided
          if date_range and 'DATE' in filtered_df.columns:
              start_date, end_date = date_range
              try:
                  filtered_df = filtered_df[
                      (filtered_df['DATE'] >= start_date) &
                      (filtered_df['DATE'] <= end_date)
                  ]
              except Exception as e:
                  if self.debug:
                      print(f"Error filtering by date range: {str(e)}")
                      
          return filtered_df
  ```

- [ ] **Create a ReportGenerationService:**
  ```python
  # src/core/services/report_generation_service.py
  import pandas as pd
  from typing import Dict, List, Any, Optional
  from datetime import datetime
  
  class ReportGenerationService:
      """
      Service for report generation operations.
      """
      
      def __init__(self, debug: bool = False):
          self.debug = debug
          
      def generate_player_report(
          self, 
          player_data: pd.DataFrame,
          include_charts: bool = True,
          include_tables: bool = True,
          include_stats: bool = True
      ) -> str:
          """
          Generate a player performance report.
          
          Args:
              player_data: Player data
              include_charts: Whether to include charts
              include_tables: Whether to include tables
              include_stats: Whether to include statistics
              
          Returns:
              HTML string containing the report
          """
          # Implementation
          
      def generate_chest_report(
          self, 
          chest_data: pd.DataFrame,
          include_charts: bool = True,
          include_tables: bool = True,
          include_stats: bool = True
      ) -> str:
          """
          Generate a chest analysis report.
          
          Args:
              chest_data: Chest data
              include_charts: Whether to include charts
              include_tables: Whether to include tables
              include_stats: Whether to include statistics
              
          Returns:
              HTML string containing the report
          """
          # Implementation
          
      def generate_full_report(
          self, 
          analysis_results: Dict[str, Any],
          include_charts: bool = True,
          include_tables: bool = True,
          include_stats: bool = True
      ) -> str:
          """
          Generate a comprehensive report.
          
          Args:
              analysis_results: Analysis results
              include_charts: Whether to include charts
              include_tables: Whether to include tables
              include_stats: Whether to include statistics
              
          Returns:
              HTML string containing the report
          """
          # Implementation
  ```

- [ ] **Use the services in DataManager:**
  ```python
  # Updated DataManager.__init__
  from core.services.data_analysis_service import DataAnalysisService
  from core.services.report_generation_service import ReportGenerationService
  
  def __init__(
      self, 
      data_access=None, 
      analysis_service=None,
      report_service=None,
      debug=False
  ):
      self.debug = debug
      self.data_access = data_access or CSVDataAccess(debug=debug)
      self.analysis_service = analysis_service or DataAnalysisService(debug=debug)
      self.report_service = report_service or ReportGenerationService(debug=debug)
      
  # Updated DataManager.analyze_data
  def analyze_data(self):
      """Analyze data using the analysis service."""
      if self.processed_data is None:
          return {}
          
      return self.analysis_service.analyze_data(self.processed_data)
      
  # Updated DataManager.filter_data
  def filter_data(self, column, values, date_range=None):
      """Filter data using the analysis service."""
      if self.raw_data is None:
          return pd.DataFrame()
          
      return self.analysis_service.filter_data(
          self.raw_data,
          column,
          values,
          date_range
      )
  ```

### 5.4. Decouple Chart Logic from UI

- [ ] **Create a ChartConfiguration class:**
  ```python
  # src/visualization/charts/chart_configuration.py
  from typing import Dict, List, Any, Optional
  
  class ChartConfiguration:
      """
      Configuration for chart generation.
      """
      
      def __init__(
          self,
          chart_type: str = "bar",
          data_category: str = "PLAYER",
          measure: str = "SCORE",
          title: str = "",
          x_label: str = "",
          y_label: str = "",
          show_values: bool = True,
          show_grid: bool = True,
          limit_results: bool = False,
          limit_value: int = 10,
          sort_column: str = "",
          sort_ascending: bool = False,
          colors: Optional[List[str]] = None,
          style: Optional[Dict[str, Any]] = None
      ):
          self.chart_type = chart_type
          self.data_category = data_category
          self.measure = measure
          self.title = title
          self.x_label = x_label
          self.y_label = y_label
          self.show_values = show_values
          self.show_grid = show_grid
          self.limit_results = limit_results
          self.limit_value = limit_value
          self.sort_column = sort_column
          self.sort_ascending = sort_ascending
          self.colors = colors or ["#D4AF37", "#5991C4", "#6EC1A7", "#D46A5F"]
          self.style = style or {
              'bg_color': '#1A2742',
              'text_color': '#FFFFFF',
              'accent_color': '#D4AF37',
              'grid_color': '#2A3F5F'
          }
          
      def to_dict(self) -> Dict[str, Any]:
          """Convert to dictionary."""
          return {
              'chart_type': self.chart_type,
              'data_category': self.data_category,
              'measure': self.measure,
              'title': self.title,
              'x_label': self.x_label,
              'y_label': self.y_label,
              'show_values': self.show_values,
              'show_grid': self.show_grid,
              'limit_results': self.limit_results,
              'limit_value': self.limit_value,
              'sort_column': self.sort_column,
              'sort_ascending': self.sort_ascending,
              'colors': self.colors,
              'style': self.style
          }
          
      @classmethod
      def from_dict(cls, config_dict: Dict[str, Any]) -> 'ChartConfiguration':
          """Create from dictionary."""
          return cls(**config_dict)
          
      def get_title(self) -> str:
          """Get the chart title."""
          if self.title:
              return self.title
              
          # Generate a default title based on configuration
          return f"{self.data_category} by {self.measure}"
  ```

- [ ] **Create a ChartService class:**
  ```python
  # src/visualization/charts/chart_service.py
  import pandas as pd
  import matplotlib.pyplot as plt
  from typing import Dict, List, Any, Optional, Tuple
  from pathlib import Path
  from .chart_configuration import ChartConfiguration
  
  class ChartService:
      """
      Service for chart generation operations.
      """
      
      def __init__(self, debug: bool = False):
          self.debug = debug
          
      def prepare_data(
          self, 
          df: pd.DataFrame, 
          config: ChartConfiguration
      ) -> pd.DataFrame:
          """
          Prepare data for chart generation.
          
          Args:
              df: DataFrame to prepare
              config: Chart configuration
              
          Returns:
              Prepared DataFrame
          """
          if df is None or df.empty:
              return pd.DataFrame()
              
          # Ensure required columns exist
          if config.data_category not in df.columns or config.measure not in df.columns:
              if self.debug:
                  print(f"Missing required columns: {config.data_category} or {config.measure}")
              return pd.DataFrame()
              
          # Select required columns
          data = df[[config.data_category, config.measure]].copy()
          
          # Sort data
          sort_column = config.sort_column or config.measure
          if sort_column in data.columns:
              data = data.sort_values(
                  sort_column,
                  ascending=config.sort_ascending
              )
          
          # Limit results if requested
          if config.limit_results and config.limit_value > 0:
              data = data.head(config.limit_value)
              
          return data
          
      def generate_chart(
          self, 
          data: pd.DataFrame, 
          config: ChartConfiguration
      ) -> Tuple[plt.Figure, plt.Axes]:
          """
          Generate a chart.
          
          Args:
              data: DataFrame to chart
              config: Chart configuration
              
          Returns:
              Tuple of (Figure, Axes)
          """
          if data.empty:
              # Create an empty figure with error message
              fig = plt.figure(figsize=(8, 6), facecolor=config.style['bg_color'])
              ax = fig.add_subplot(111)
              ax.text(
                  0.5, 0.5,
                  "No data available for chart",
                  ha='center',
                  va='center',
                  color=config.style['text_color'],
                  fontsize=14
              )
              return fig, ax
              
          # Create figure and axes
          fig = plt.figure(figsize=(8, 6), facecolor=config.style['bg_color'])
          ax = fig.add_subplot(111)
          
          # Apply styling
          ax.set_facecolor(config.style['bg_color'])
          ax.xaxis.label.set_color(config.style['text_color'])
          ax.yaxis.label.set_color(config.style['text_color'])
          ax.title.set_color(config.style['accent_color'])
          ax.tick_params(
              axis='both', 
              colors=config.style['text_color'],
              labelcolor=config.style['text_color']
          )
          
          # Set grid
          ax.grid(config.show_grid, color=config.style['grid_color'], linestyle='--', alpha=0.3)
          
          # Set spine colors
          for spine in ax.spines.values():
              spine.set_color(config.style['grid_color'])
              
          # Set title and labels
          title = config.get_title()
          ax.set_title(title)
          
          if config.x_label:
              ax.set_xlabel(config.x_label)
          else:
              ax.set_xlabel(config.data_category)
              
          if config.y_label:
              ax.set_ylabel(config.y_label)
          else:
              ax.set_ylabel(config.measure)
              
          # Create chart based on type
          chart_type = config.chart_type.lower()
          
          if chart_type == "bar":
              self._create_bar_chart(ax, data, config)
          elif chart_type == "horizontal_bar":
              self._create_horizontal_bar_chart(ax, data, config)
          elif chart_type == "pie":
              self._create_pie_chart(ax, data, config)
          elif chart_type == "line":
              self._create_line_chart(ax, data, config)
          else:
              ax.text(
                  0.5, 0.5,
                  f"Unsupported chart type: {config.chart_type}",
                  ha='center',
                  va='center',
                  color=config.style['text_color'],
                  fontsize=14
              )
              
          fig.tight_layout()
          return fig, ax
          
      def save_chart(
          self, 
          fig: plt.Figure, 
          file_path: Path, 
          dpi: int = 300
      ) -> bool:
          """
          Save a chart to file.
          
          Args:
              fig: Figure to save
              file_path: Path to save to
              dpi: Resolution in dots per inch
              
          Returns:
              True if successful, False otherwise
          """
          try:
              fig.savefig(
                  file_path,
                  dpi=dpi,
                  bbox_inches='tight',
                  facecolor=fig.get_facecolor(),
                  edgecolor='none'
              )
              return True
          except Exception as e:
              if self.debug:
                  print(f"Error saving chart: {str(e)}")
              return False
              
      def _create_bar_chart(self, ax, data, config):
          """Create a bar chart."""
          # Implementation
          
      def _create_horizontal_bar_chart(self, ax, data, config):
          """Create a horizontal bar chart."""
          # Implementation
          
      def _create_pie_chart(self, ax, data, config):
          """Create a pie chart."""
          # Implementation
          
      def _create_line_chart(self, ax, data, config):
          """Create a line chart."""
          # Implementation
  ```

- [ ] **Use ChartService and ChartConfiguration in ChartPresenter:**
  ```python
  # src/ui/presenters/chart_presenter.py
  from .presenter import Presenter
  from core.data.data_model import DataModel
  from visualization.charts.chart_service import ChartService
  from visualization.charts.chart_configuration import ChartConfiguration
  from PySide6.QtWidgets import QWidget
  
  class ChartPresenter(Presenter):
      """
      Presenter for the Chart tab.
      """
      
      def __init__(
          self, 
          model: DataModel, 
          chart_canvas, 
          controls_widget: QWidget,
          chart_service=None
      ):
          self.chart_canvas = chart_canvas
          self.controls_widget = controls_widget
          self.chart_service = chart_service or ChartService()
          super().__init__(model, None)  # No single view
          
      def initialize(self) -> None:
          """Initialize the presenter."""
          # Connect signals from controls
          self._connect_signals()
          
          # Initial update
          self.update_chart()
          
      def _connect_signals(self) -> None:
          """Connect signals from controls."""
          # Connect chart type selector
          if hasattr(self.controls_widget, 'chart_type_selector'):
              self.controls_widget.chart_type_selector.currentIndexChanged.connect(
                  self.update_chart
              )
              
          # Connect data category selector
          if hasattr(self.controls_widget, 'chart_data_category'):
              self.controls_widget.chart_data_category.currentIndexChanged.connect(
                  self._on_data_category_changed
              )
              
          # Connect other controls...
          
      def _on_data_category_changed(self, index) -> None:
          """Handle data category change."""
          # Update available measures
          self._update_available_measures()
          
          # Update sort options
          self._update_sort_options()
          
          # Update chart with new settings
          self.update_chart()
          
      def _update_available_measures(self) -> None:
          """Update available measures based on data category."""
          # Implementation
          
      def _update_sort_options(self) -> None:
          """Update sort options based on data category."""
          # Implementation
          
      def get_chart_configuration(self) -> ChartConfiguration:
          """Get chart configuration from UI controls."""
          return ChartConfiguration(
              chart_type=self.controls_widget.chart_type_selector.currentText().lower().replace(" ", "_"),
              data_category=self.controls_widget.chart_data_category.currentText(),
              measure=self.controls_widget.chart_data_column.currentText(),
              show_values=self.controls_widget.chart_show_values.isChecked(),
              show_grid=self.controls_widget.chart_show_grid.isChecked(),
              limit_results=self.controls_widget.chart_limit_enabled.isChecked(),
              limit_value=self.controls_widget.chart_limit_value.value(),
              sort_column=self.controls_widget.chart_sort_column.currentText(),
              sort_ascending=self.controls_widget.chart_sort_order.currentText() == "Ascending",
              colors=self.chart_canvas.get_colors(),
              style=self.chart_canvas.style_presets['default']
          )
          
      def update_chart(self) -> None:
          """Update the chart based on current configuration."""
          # Get analysis results
          analysis_results = self.model.get_analysis_results()
          if not analysis_results:
              return
              
          # Get chart configuration
          config = self.get_chart_configuration()
          
          try:
              # Get the appropriate dataset
              data = self._get_chart_data(config.data_category, analysis_results)
              if data is None or data.empty:
                  return
                  
              # Prepare data for chart
              prepared_data = self.chart_service.prepare_data(data, config)
              
              # Generate chart
              fig, ax = self.chart_service.generate_chart(prepared_data, config)
              
              # Update chart canvas
              self.chart_canvas.fig.clear()
              self.chart_canvas.fig = fig
              self.chart_canvas.axes = ax
              self.chart_canvas.draw()
              
          except Exception as e:
              print(f"Error updating chart: {str(e)}")
              import traceback
              traceback.print_exc()
              
      def _get_chart_data(self, data_category, analysis_results):
          """Get appropriate data for the chart based on data category."""
          # Implementation
  ```

### 5.5. Extract Report Generation Engine

- [ ] **Create a ReportEngine class:**
  ```python
  # src/visualization/reports/report_engine.py
  from typing import Dict, List, Any, Optional
  import pandas as pd
  from datetime import datetime
  from pathlib import Path
  
  class ReportEngine:
      """
      Engine for generating reports.
      """
      
      def __init__(self, debug: bool = False):
          self.debug = debug
          self.style_settings = self._get_default_styles()
          
      def generate_report(
          self,
          title: str,
          sections: List[Dict[str, Any]],
          include_charts: bool = True,
          include_tables: bool = True,
          include_stats: bool = True
      ) -> str:
          """
          Generate an HTML report.
          
          Args:
              title: Report title
              sections: List of report sections
              include_charts: Whether to include charts
              include_tables: Whether to include tables
              include_stats: Whether to include statistics
              
          Returns:
              HTML string containing the report
          """
          # Start with HTML header and styling
          html = self._generate_html_header(title)
          
          # Add report sections
          for section in sections:
              if not self._should_include_section(section, include_charts, include_tables, include_stats):
                  continue
                  
              html += self._generate_section_html(section)
              
          # Add footer
          html += self._generate_html_footer()
          
          return html
          
      def export_report_to_html(self, html_content: str, file_path: Path) -> bool:
          """
          Export an HTML report to a file.
          
          Args:
              html_content: HTML content
              file_path: Path to save to
              
          Returns:
              True if successful, False otherwise
          """
          try:
              with open(file_path, 'w', encoding='utf-8') as f:
                  f.write(html_content)
              return True
          except Exception as e:
              if self.debug:
                  print(f"Error exporting HTML report: {str(e)}")
              return False
              
      def export_report_to_pdf(self, html_content: str, file_path: Path) -> bool:
          """
          Export an HTML report to a PDF file.
          
          Args:
              html_content: HTML content
              file_path: Path to save to
              
          Returns:
              True if successful, False otherwise
          """
          try:
              from weasyprint import HTML
              HTML(string=html_content).write_pdf(file_path)
              return True
          except ImportError:
              if self.debug:
                  print("WeasyPrint not installed, fallback to alternative method")
              
              try:
                  # Alternative method using QWebEngineView
                  from PySide6.QtWebEngineWidgets import QWebEngineView
                  from PySide6.QtCore import QUrl, QBuffer, QIODevice
                  from PySide6.QtWidgets import QApplication
                  from PySide6.QtGui import QPageLayout, QPageSize
                  from PySide6.QtPrintSupport import QPrinter
                  
                  app = QApplication.instance() or QApplication([])
                  
                  web = QWebEngineView()
                  web.setHtml(html_content)
                  
                  printer = QPrinter(QPrinter.HighResolution)
                  printer.setOutputFormat(QPrinter.PdfFormat)
                  printer.setOutputFileName(str(file_path))
                  
                  # Set page size to A4
                  layout = QPageLayout()
                  layout.setPageSize(QPageSize(QPageSize.A4))
                  printer.setPageLayout(layout)
                  
                  # Wait for the page to load
                  web.loadFinished.connect(lambda _: web.page().print(printer))
                  
                  # Ensure the event loop is running
                  if not app.instance():
                      app.processEvents()
                      
                  return True
              except Exception as e:
                  if self.debug:
                      print(f"Error exporting PDF report with alternative method: {str(e)}")
                  return False
          except Exception as e:
              if self.debug:
                  print(f"Error exporting PDF report: {str(e)}")
              return False
              
      def _should_include_section(
          self, 
          section: Dict[str, Any],
          include_charts: bool,
          include_tables: bool,
          include_stats: bool
      ) -> bool:
          """Determine if a section should be included based on settings."""
          section_type = section.get('type')
          
          if section_type == 'chart' and not include_charts:
              return False
          elif section_type == 'table' and not include_tables:
              return False
          elif section_type == 'stats' and not include_stats:
              return False
              
          return True
          
      def _generate_html_header(self, title: str) -> str:
          """Generate HTML header and styling."""
          return f"""
          <!DOCTYPE html>
          <html>
          <head>
              <meta charset="UTF-8">
              <title>{title}</title>
              <style>
              {self.style_settings}
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
          """Generate HTML for a report section."""
          title = section.get('title', '')
          content = section.get('content', '')
          
          return f"""
          <div class="section">
              <h2>{title}</h2>
              {content}
          </div>
          """
          
      def _get_default_styles(self) -> str:
          """Get default CSS styles for the report."""
          return """
          body {
              font-family: Arial, sans-serif;
              background-color: #0E1629;
              color: #FFFFFF;
              margin: 20px;
          }
          h1, h2, h3, h4 {
              color: #D4AF37;
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
          }
          table {
              width: 100%;
              border-collapse: collapse;
              margin: 15px 0;
          }
          th, td {
              border: 1px solid #2A3F5F;
              padding: 8px;
              text-align: left;
          }
          th {
              background-color: #0E1629;
              color: #D4AF37;
          }
          .chart-container {
              margin: 20px 0;
              text-align: center;
          }
          .footer {
              margin-top: 30px;
              text-align: center;
              font-size: 0.8em;
              color: #FFFFFF;
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
          }
          .stat-value {
              font-size: 24px;
              font-weight: bold;
              color: #D4AF37;
          }
          """
  ```

- [ ] **Create a ReportGenerator interface and implementations:**
  ```python
  # src/visualization/reports/report_generator.py
  from abc import ABC, abstractmethod
  import pandas as pd
  from typing import Dict, List, Any, Optional
  
  class ReportGenerator(ABC):
      """
      Interface for report generators.
      """
      
      @abstractmethod
      def generate_report_sections(
          self,
          data: Dict[str, Any],
          include_charts: bool,
          include_tables: bool,
          include_stats: bool
      ) -> List[Dict[str, Any]]:
          """
          Generate report sections.
          
          Args:
              data: The data to generate report sections from
              include_charts: Whether to include charts
              include_tables: Whether to include tables
              include_stats: Whether to include statistics
              
          Returns:
              List of report sections
          """
          pass
          
      @abstractmethod
      def get_report_title(self) -> str:
          """
          Get the report title.
          
          Returns:
              Report title
          """
          pass
  ```

- [ ] **Create specific report generators:**
  ```python
  # src/visualization/reports/player_report_generator.py
  from .report_generator import ReportGenerator
  import pandas as pd
  from typing import Dict, List, Any, Optional
  from visualization.charts.chart_service import ChartService
  from visualization.charts.chart_configuration import ChartConfiguration
  import matplotlib.pyplot as plt
  import tempfile
  
  class PlayerReportGenerator(ReportGenerator):
      """
      Generator for player performance reports.
      """
      
      def __init__(self, chart_service=None):
          self.chart_service = chart_service or ChartService()
          
      def get_report_title(self) -> str:
          """Get the report title."""
          return "Player Performance Report"
          
      def generate_report_sections(
          self,
          data: Dict[str, Any],
          include_charts: bool = True,
          include_tables: bool = True,
          include_stats: bool = True
      ) -> List[Dict[str, Any]]:
          """Generate report sections."""
          sections = []
          
          # Add player overview section
          sections.append({
              'title': 'Player Overview',
              'type': 'stats',
              'content': self._generate_player_overview_content(data, include_stats)
          })
          
          # Add player performance details section
          sections.append({
              'title': 'Player Performance Details',
              'type': 'chart',
              'content': self._generate_player_performance_content(data, include_charts, include_tables)
          })
          
          # Add player efficiency section
          sections.append({
              'title': 'Player Efficiency Analysis',
              'type': 'stats',
              'content': self._generate_player_efficiency_content(data, include_stats, include_tables)
          })
          
          return sections
          
      def _generate_player_overview_content(self, data, include_stats):
          """Generate content for player overview section."""
          if not include_stats or 'player_totals' not in data:
              return ""
              
          player_df = data['player_totals']
          if player_df.empty:
              return "<p>No player data available for statistics</p>"
              
          # Calculate statistics
          top_player = player_df.sort_values('SCORE', ascending=False).iloc[0]
          total_players = len(player_df)
          avg_score = player_df['SCORE'].mean()
          
          return f"""
          <p>Total Players: {total_players}</p>
          <p>Average Score per Player: {avg_score:.2f}</p>
          <p>Top Player: {top_player['PLAYER']} with {top_player['SCORE']:.2f} points</p>
          """
          
      def _generate_player_performance_content(self, data, include_charts, include_tables):
          """Generate content for player performance details section."""
          content = ""
          
          if include_charts and 'player_totals' in data:
              # Generate bar chart for player performance
              chart_file = self._generate_player_chart(data)
              if chart_file:
                  content += f"""
                  <div class="chart-container">
                      <img src="file:///{chart_file}" alt="Player Performance Chart" style="max-width:100%; height:auto;">
                      <p>Player Total Scores</p>
                  </div>
                  """
          
          if include_tables and 'player_totals' in data:
              # Add player performance table
              player_df = data['player_totals']
              if not player_df.empty:
                  # Convert DataFrame to HTML table
                  player_table = player_df.to_html(index=False, classes="table")
                  content += f"""
                  <h3>Player Performance Data</h3>
                  {player_table}
                  """
              else:
                  content += "<p>No player performance data available</p>"
          
          return content
          
      def _generate_player_efficiency_content(self, data, include_stats, include_tables):
          """Generate content for player efficiency section."""
          content = ""
          
          if include_stats and 'player_totals' in data:
              # Add player efficiency statistics
              player_df = data['player_totals'].copy()
              if not player_df.empty and 'CHEST_COUNT' in player_df.columns and 'SCORE' in player_df.columns:
                  # Calculate points per chest for each player
                  player_df['POINTS_PER_CHEST'] = player_df['SCORE'] / player_df['CHEST_COUNT'].replace(0, 1)
                  most_efficient_player = player_df.sort_values('POINTS_PER_CHEST', ascending=False).iloc[0]
                  
                  content += f"""
                  <p>Most Efficient Player: {most_efficient_player['PLAYER']} with {most_efficient_player['POINTS_PER_CHEST']:.2f} points per chest</p>
                  """
          
          if include_tables and 'player_totals' in data:
              player_df = data['player_totals'].copy()
              if not player_df.empty and 'CHEST_COUNT' in player_df.columns and 'SCORE' in player_df.columns:
                  # Calculate and show top 5 most efficient players
                  player_df['POINTS_PER_CHEST'] = player_df['SCORE'] / player_df['CHEST_COUNT'].replace(0, 1)
                  top_5_efficient = player_df.sort_values('POINTS_PER_CHEST', ascending=False).head(5)
                  efficient_table = top_5_efficient[['PLAYER', 'POINTS_PER_CHEST', 'SCORE', 'CHEST_COUNT']].to_html(index=False, classes="table")
                  
                  content += f"""
                  <h3>Top 5 Most Efficient Players</h3>
                  {efficient_table}
                  """
              else:
                  content += "<p>No player efficiency data available</p>"
          
          return content
          
      def _generate_player_chart(self, data):
          """Generate a chart for player performance."""
          if 'player_totals' not in data or data['player_totals'].empty:
              return None
              
          try:
              # Create a temporary file for the chart
              temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
              temp_file.close()
              
              # Prepare chart configuration
              config = ChartConfiguration(
                  chart_type="bar",
                  data_category="PLAYER",
                  measure="SCORE",
                  title="Player Total Scores",
                  show_values=True,
                  limit_results=True,
                  limit_value=10,
                  sort_column="SCORE",
                  sort_ascending=False
              )
              
              # Prepare data
              data_df = data['player_totals'].copy()
              prepared_data = self.chart_service.prepare_data(data_df, config)
              
              # Generate chart
              fig, ax = self.chart_service.generate_chart(prepared_data, config)
              
              # Save chart
              self.chart_service.save_chart(fig, temp_file.name)
              
              # Close figure to free memory
              plt.close(fig)
              
              return temp_file.name
          except Exception as e:
              print(f"Error generating player chart: {str(e)}")
              return None
  ```

- [ ] **Use the report engine in the ReportPresenter:**
  ```python
  # src/ui/presenters/report_presenter.py
  from .presenter import Presenter
  from core.data.data_model import DataModel
  from PySide6.QtWidgets import QTextBrowser
  from visualization.reports.report_engine import ReportEngine
  from visualization.reports.player_report_generator import PlayerReportGenerator
  from visualization.reports.chest_report_generator import ChestReportGenerator
  from visualization.reports.source_report_generator import SourceReportGenerator
  from visualization.reports.full_report_generator import FullReportGenerator
  
  class ReportPresenter(Presenter):
      """
      Presenter for the Report tab.
      """
      
      def __init__(self, model: DataModel, report_view: QTextBrowser):
          self.report_view = report_view
          self.report_engine = ReportEngine()
          self.report_generators = {
              "Player Performance": PlayerReportGenerator(),
              "Chest Type Analysis": ChestReportGenerator(),
              "Source Analysis": SourceReportGenerator(),
              "Full Report": FullReportGenerator()
          }
          super().__init__(model, report_view)
          
      def initialize(self) -> None:
          """Initialize the presenter."""
          # Display welcome message
          self.show_welcome_message()
          
      def show_welcome_message(self) -> None:
          """Show a welcome message in the report view."""
          welcome_html = """
          <html>
          <head>
              <style>
                  body { font-family: Arial, sans-serif; margin: 20px; color: #fff; }
                  h1, h2 { color: #D4AF37; }
                  .container { text-align: center; margin-top: 50px; }
              </style>
          </head>
          <body>
              <div class="container">
                  <h1>Total Battle Analyzer - Report Generator</h1>
                  <h2>Select report options and click "Generate Report" to create a report</h2>
                  <p>You can include charts, tables, and statistics in your report.</p>
                  <p>Once generated, you can export the report as HTML or PDF.</p>
              </div>
          </body>
          </html>
          """
          self.report_view.setHtml(welcome_html)
          
      def generate_report(self, report_type: str, include_charts: bool, include_tables: bool, include_stats: bool) -> None:
          """
          Generate a report based on the selected options.
          
          Args:
              report_type: Type of report to generate
              include_charts: Whether to include charts
              include_tables: Whether to include tables
              include_stats: Whether to include statistics
          """
          # Get analysis results
          analysis_results = self.model.get_analysis_results()
          if not analysis_results:
              self.report_view.setHtml("<h1>No data available for report generation</h1>")
              return
              
          try:
              # Get appropriate report generator
              if report_type not in self.report_generators:
                  self.report_view.setHtml(f"<h1>Unknown report type: {report_type}</h1>")
                  return
                  
              generator = self.report_generators[report_type]
              
              # Generate report sections
              sections = generator.generate_report_sections(
                  analysis_results,
                  include_charts,
                  include_tables,
                  include_stats
              )
              
              # Generate report HTML
              html = self.report_engine.generate_report(
                  generator.get_report_title(),
                  sections,
                  include_charts,
                  include_tables,
                  include_stats
              )
              
              # Show the report
              self.report_view.setHtml(html)
              
          except Exception as e:
              error_html = f"""
              <html>
              <body>
                  <h1>Error Generating Report</h1>
                  <p>An error occurred while generating the report:</p>
                  <p>{str(e)}</p>
              </body>
              </html>
              """
              self.report_view.setHtml(error_html)
              
      def export_report(self, file_path: str, format_type: str) -> bool:
          """
          Export the current report.
          
          Args:
              file_path: Path to save the report to
              format_type: Format type ('html' or 'pdf')
              
          Returns:
              True if successful, False otherwise
          """
          # Get the current HTML content
          html_content = self.report_view.toHtml()
          
          if format_type.lower() == 'html':
              return self.report_engine.export_report_to_html(html_content, file_path)
          elif format_type.lower() == 'pdf':
              return self.report_engine.export_report_to_pdf(html_content, file_path)
          else:
              return False
  ```

### 5.6. Isolate Theme Management

- [ ] **Create a ThemeManager class:**
  ```python
  # src/ui/styles/theme_manager.py
  from PySide6.QtWidgets import QApplication
  from PySide6.QtGui import QPalette, QColor
  from typing import Dict, Any, Optional
  
  class ThemeManager:
      """
      Manages application theming.
      """
      
      def __init__(self, config_file=None):
          self.themes = {
              'dark': self._get_dark_theme()
              # Add more themes in the future
          }
          self.active_theme = 'dark'  # Always use dark theme
          
      def _get_dark_theme(self) -> Dict[str, Any]:
          """Get dark theme colors and settings."""
          return {
              'background': '#0E1629',          # Darker blue background
              'foreground': '#FFFFFF',          # White text
              'accent': '#D4AF37',              # Gold accent
              'accent_hover': '#F0C75A',        # Lighter gold for hover
              'background_light': '#1A2742',    # Lighter background
              'background_secondary': '#162038', # Secondary background
              'card_bg': '#0D1A33',             # Card background
              'border': '#2A3F5F',              # Border color
              'text': '#FFFFFF',                # Primary text
              'text_secondary': '#A0B0C0',      # Secondary text
              'text_disabled': '#8899AA',       # Disabled text
              'header_bg': '#0A1220',           # Header background
              'button_gradient_start': '#1A3863', # Button gradient start
              'button_gradient_end': '#0B1A36',   # Button gradient end
              'button_hover_gradient_start': '#D4AF37', # Button hover start
              'button_hover_gradient_end': '#B28E1C',   # Button hover end
              'button_pressed': '#A37F18',      # Button pressed
              'button_disabled': '#5A6A7A',     # Button disabled
              'selection_bg': '#2C427A',        # Selection background
              'selection_text': '#FFFFFF',      # Selection text
              'warning': '#f28e2c',             # Warning color
              'info': '#76b7b2',                # Info color
              'success': '#56A64B',             # Success color
              'error': '#A6564B',               # Error color
              'checkbox_bg': '#0E1629',         # Checkbox background
              'checkbox_border': '#2A3F5F',     # Checkbox border
              'checkbox_checked_bg': '#1A2742', # Checkbox checked bg
              'checkbox_check_mark': '#D4AF37'  # Checkbox check mark
          }
          
      def get_active_theme(self) -> str:
          """Get the name of the active theme."""
          return self.active_theme
          
      def get_theme_colors(self, theme_name: Optional[str] = None) -> Dict[str, str]:
          """
          Get the colors for a theme.
          
          Args:
              theme_name: Name of the theme to get colors for, or None for active theme
              
          Returns:
              Dictionary of color names and values
          """
          theme = theme_name or self.active_theme
          return self.themes.get(theme, self.themes['dark'])
          
      def apply_theme(self, app: QApplication, theme_name: Optional[str] = None) -> None:
          """
          Apply a theme to the application.
          
          Args:
              app: The QApplication instance
              theme_name: Name of the theme to apply, or None for active theme
          """
          theme = theme_name or self.active_theme
          if theme not in self.themes:
              theme = 'dark'
              
          self.active_theme = theme
          colors = self.themes[theme]
          
          # Apply stylesheet
          app.setStyleSheet(self._generate_stylesheet(colors))
          
      def _generate_stylesheet(self, colors: Dict[str, str]) -> str:
          """
          Generate a stylesheet from the theme colors.
          
          Args:
              colors: Dictionary of color names and values
              
          Returns:
              CSS stylesheet as a string
          """
          return f"""
          QMainWindow, QDialog {{
              background-color: {colors['background']};
              color: {colors['foreground']};
          }}
          
          QWidget {{
              background-color: {colors['background']};
              color: {colors['foreground']};
          }}
          
          QLabel {{
              color: {colors['foreground']};
              background: transparent;
          }}
          
          QPushButton {{
              background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                  stop:0 {colors['button_gradient_start']},
                  stop:1 {colors['button_gradient_end']});
              border: 1px solid {colors['border']};
              border-radius: 3px;
              color: {colors['foreground']};
              padding: 5px 15px;
              min-height: 25px;
          }}
          
          QPushButton:hover {{
              background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                  stop:0 {colors['button_hover_gradient_start']},
                  stop:1 {colors['button_hover_gradient_end']});
              border-color: {colors['accent']};
          }}
          
          QPushButton:pressed {{
              background: {colors['button_pressed']};
          }}
          
          QPushButton:disabled {{
              background: {colors['button_disabled']};
              color: {colors['text_disabled']};
              border-color: {colors['border']};
          }}
          
          QLineEdit, QComboBox, QSpinBox, QDateEdit {{
              background-color: {colors['background_light']};
              border: 1px solid {colors['border']};
              border-radius: 3px;
              color: {colors['foreground']};
              padding: 5px;
          }}
          
          QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus {{
              border-color: {colors['accent']};
          }}
          
          QTableView {{
              background-color: {colors['background_light']};
              alternate-background-color: {colors['card_bg']};
              border: 1px solid {colors['border']};
              gridline-color: {colors['border']};
              selection-background-color: {colors['selection_bg']};
              selection-color: {colors['selection_text']};
          }}
          
          QHeaderView::section {{
              background-color: {colors['header_bg']};
              color: {colors['foreground']};
              padding: 5px;
              border: 1px solid {colors['border']};
          }}
          
          QTabWidget::pane {{
              border: 1px solid {colors['border']};
              background-color: {colors['background']};
          }}
          
          QTabBar::tab {{
              background-color: {colors['background_light']};
              color: {colors['foreground']};
              padding: 8px 20px;
              border: 1px solid {colors['border']};
              border-bottom: none;
              border-top-left-radius: 4px;
              border-top-right-radius: 4px;
          }}
          
          QTabBar::tab:selected {{
              background-color: {colors['background']};
              border-bottom: 2px solid {colors['accent']};
          }}
          
          QTabBar::tab:!selected {{
              margin-top: 2px;
          }}
          
          QGroupBox {{
              border: 2px solid {colors['accent']};
              border-radius: 5px;
              margin-top: 1em;
              padding: 10px;
          }}
          
          QGroupBox::title {{
              subcontrol-origin: margin;
              left: 10px;
              padding: 0 3px 0 3px;
              color: {colors['accent']};
              font-weight: bold;
          }}
          """
  ```

- [ ] **Use ThemeManager in MainWindow:**
  ```python
  # In MainWindow.__init__
  from ui.styles.theme_manager import ThemeManager
  
  # Create theme manager
  self.theme_manager = ThemeManager()
  
  # Apply theme
  self.theme_manager.apply_theme(QApplication.instance())
  
  # Use colors
  theme_colors = self.theme_manager.get_theme_colors()
  # Now you can use theme_colors['accent'] etc.
  ```

- [ ] **Create style presets for chart components:**
  ```python
  # src/visualization/styles/chart_styles.py
  from typing import Dict, Any
  
  class ChartStyles:
      """
      Styles for chart components.
      """
      
      @staticmethod
      def get_default_style() -> Dict[str, Any]:
          """Get the default chart style."""
          return {
              'bg_color': '#1A2742',  # Dark blue background
              'text_color': '#FFFFFF',  # White text
              'grid_color': '#2A3F5F',  # Medium blue grid
              'tick_color': '#FFFFFF',  # White ticks
              'title_color': '#D4AF37',  # Gold title
              'title_size': 14,
              'label_size': 12,
              'bar_colors': ['#D4AF37', '#5991C4', '#6EC1A7', '#D46A5F'],  # Gold, Blue, Green, Red
              'pie_colors': ['#D4AF37', '#5991C4', '#6EC1A7', '#D46A5F', '#8899AA', '#F0C75A'],
              'line_color': '#5991C4',  # Blue
              'line_width': 2.5,
              'marker_size': 8,
              'marker_color': '#D4AF37',  # Gold markers
              'edge_color': '#1A2742'  # Dark blue edges
          }
          
      @staticmethod
      def get_dark_theme_style() -> Dict[str, Any]:
          """Get dark theme chart style."""
          return ChartStyles.get_default_style()  # Same as default for now
          
      @staticmethod
      def get_style_for_chart_type(chart_type: str) -> Dict[str, Any]:
          """
          Get a style specific to a chart type.
          
          Args:
              chart_type: Type of chart
              
          Returns:
              Dictionary of style settings
          """
          base_style = ChartStyles.get_default_style()
          
          if chart_type.lower() == 'pie':
              # Use more distinct colors for pie chart segments
              base_style['colors'] = base_style['pie_colors']
          elif chart_type.lower() == 'line':
              # Use a different color scheme for line charts
              base_style['line_color'] = '#5991C4'
              base_style['marker_color'] = '#D4AF37'
          
          return base_style
  ```

## 6. Fixing Potential Issues and Bugs

### 6.1. Signal Connection Management

- [ ] **Create a SignalManager class:**
  ```python
  # src/ui/utils/signal_manager.py
  from PySide6.QtCore import QObject, Signal
  from typing import Dict, List, Callable, Any
  
  class SignalManager:
      """
      Manages signal connections in the application.
      """
      
      def __init__(self):
          self.connections = {}
          
      def connect(self, sender: QObject, signal_name: str, slot: Callable, connection_id: str = None) -> str:
          """
          Connect a signal to a slot.
          
          Args:
              sender: The sender object
              signal_name: The name of the signal
              slot: The slot to connect to
              connection_id: Optional ID for the connection
              
          Returns:
              Connection ID
          """
          if not hasattr(sender, signal_name):
              print(f"Warning: Sender {sender} has no signal named {signal_name}")
              return None
              
          # Get the signal
          signal = getattr(sender, signal_name)
          
          # Generate a connection ID if not provided
          if connection_id is None:
              connection_id = f"{id(sender)}_{signal_name}_{id(slot)}"
              
          # Disconnect existing connection with the same ID
          if connection_id in self.connections:
              self.disconnect(connection_id)
              
          # Make the connection
          try:
              signal.connect(slot)
              self.connections[connection_id] = (sender, signal_name, slot)
              return connection_id
          except Exception as e:
              print(f"Error connecting signal {signal_name}: {str(e)}")
              return None
              
      def disconnect(self, connection_id: str) -> bool:
          """
          Disconnect a signal connection.
          
          Args:
              connection_id: Connection ID
              
          Returns:
              True if successful, False otherwise
          """
          if connection_id not in self.connections:
              return False
              
          sender, signal_name, slot = self.connections[connection_id]
          
          # Get the signal
          if not hasattr(sender, signal_name):
              del self.connections[connection_id]
              return False
              
          signal = getattr(sender, signal_name)
          
          # Disconnect
          try:
              signal.disconnect(slot)
              del self.connections[connection_id]
              return True
          except Exception as e:
              print(f"Error disconnecting signal {signal_name}: {str(e)}")
              del self.connections[connection_id]
              return False
              
      def disconnect_all(self) -> None:
          """Disconnect all signal connections."""
          for connection_id in list(self.connections.keys()):
              self.disconnect(connection_id)
              
      def disconnect_sender(self, sender: QObject) -> None:
          """
          Disconnect all connections for a sender.
          
          Args:
              sender: The sender object
          """
          for connection_id in list(self.connections.keys()):
              if self.connections[connection_id][0] == sender:
                  self.disconnect(connection_id)
  ```

- [ ] **Use SignalManager in MainWindow:**
  ```python
  # In MainWindow.__init__
  from ui.utils.signal_manager import SignalManager
  
  self.signal_manager = SignalManager()
  
  # In connect_signals
  def connect_signals(self):
      """Connect signals to slots."""
      # Connect import area signals
      if hasattr(self, 'import_area'):
          self.signal_manager.connect(
              self.import_area,
              'fileSelected',
              self.load_csv_file,
              'import_area_file_selected'
          )
          
      # Connect menu actions
      if hasattr(self, 'action_import_csv'):
          self.signal_manager.connect(
              self.action_import_csv,
              'triggered',
              self.import_area.open_file_dialog,
              'action_import_csv_triggered'
          )
          
      # ... other signal connections ...
      
  # In closeEvent
  def closeEvent(self, event):
      """Handle window close event."""
      # Disconnect all signals
      self.signal_manager.disconnect_all()
      
      # ... other cleanup ...
      
      event.accept()
  ```

### 6.2. Path Handling Inconsistencies

- [ ] **Create a PathUtils class:**
  ```python
  # src/utils/path_utils.py
  from pathlib import Path
  from typing import Union, List, Optional
  import os
  
  class PathUtils:
      """
      Utilities for path handling.
      """
      
      @staticmethod
      def ensure_path(path: Union[str, Path]) -> Path:
          """
          Ensure the input is a Path object.
          
          Args:
              path: String or Path object
              
          Returns:
              Path object
          """
          return Path(path) if not isinstance(path, Path) else path
          
      @staticmethod
      def ensure_directory(path: Union[str, Path]) -> Path:
          """
          Ensure a directory exists.
          
          Args:
              path: Directory path
              
          Returns:
              Path object
          """
          path = PathUtils.ensure_path(path)
          path.mkdir(parents=True, exist_ok=True)
          return path
          
      @staticmethod
      def get_home_directory() -> Path:
          """
          Get the user's home directory.
          
          Returns:
              Path to home directory
          """
          return Path.home()
          
      @staticmethod
      def get_app_data_directory(app_name: str) -> Path:
          """
          Get the application data directory.
          
          Args:
              app_name: Application name
              
          Returns:
              Path to application data directory
          """
          if os.name == 'nt':  # Windows
              return Path(os.environ['APPDATA']) / app_name
          else:  # Linux/Mac
              return Path.home() / f".{app_name.lower()}"
              
      @staticmethod
      def get_app_config_directory(app_name: str) -> Path:
          """
          Get the application configuration directory.
          
          Args:
              app_name: Application name
              
          Returns:
              Path to application configuration directory
          """
          if os.name == 'nt':  # Windows
              return Path(os.environ['APPDATA']) / app_name
          else:  # Linux/Mac
              return Path.home() / ".config" / app_name.lower()
              
      @staticmethod
      def get_app_cache_directory(app_name: str) -> Path:
          """
          Get the application cache directory.
          
          Args:
              app_name: Application name
              
          Returns:
              Path to application cache directory
          """
          if os.name == 'nt':  # Windows
              return Path(os.environ['LOCALAPPDATA']) / app_name / "Cache"
          else:  # Linux/Mac
              return Path.home() / ".cache" / app_name.lower()
              
      @staticmethod
      def get_relative_path(path: Union[str, Path], base_path: Union[str, Path]) -> Path:
          """
          Get a path relative to a base path.
          
          Args:
              path: Path to make relative
              base_path: Base path
              
          Returns:
              Relative path
          """
          path = PathUtils.ensure_path(path)
          base_path = PathUtils.ensure_path(base_path)
          return path.relative_to(base_path)
          
      @staticmethod
      def change_extension(path: Union[str, Path], new_extension: str) -> Path:
          """
          Change the extension of a file path.
          
          Args:
              path: File path
              new_extension: New extension (with or without dot)
              
          Returns:
              Path with new extension
          """
          path = PathUtils.ensure_path(path)
          new_extension = new_extension if new_extension.startswith('.') else f".{new_extension}"
          return path.with_suffix(new_extension)
  ```

- [ ] **Use PathUtils throughout the codebase:**
  ```python
  # In DataManager.load_file
  from utils.path_utils import PathUtils
  
  def load_file(self, file_path: Union[str, Path]) -> Tuple[bool, str]:
      """Load a file using the data access layer."""
      # Ensure file_path is a Path object
      file_path = PathUtils.ensure_path(file_path)
      
      if not file_path.exists():
          return False, f"File not found: {file_path}"
          
      # ... rest of the method ...
  ```

### 6.3. Memory Management with Charts

- [ ] **Create a ChartMemoryManager class:**
  ```python
  # src/visualization/charts/chart_memory_manager.py
  import matplotlib.pyplot as plt
  from typing import Dict, Any, List
  import gc
  
  class ChartMemoryManager:
      """
      Manages memory for chart figures.
      """
      
      def __init__(self, max_figures: int = 5):
          self.max_figures = max_figures
          self.figures = []
          
      def register_figure(self, fig):
          """
          Register a figure to be managed.
          
          Args:
              fig: Matplotlib figure
          """
          # Add to the list
          self.figures.append(fig)
          
          # Close oldest figures if we exceed the maximum
          self._cleanup_old_figures()
          
      def clear_all_figures(self):
          """Close all registered figures."""
          for fig in self.figures:
              try:
                  plt.close(fig)
              except Exception:
                  pass
                  
          self.figures = []
          
          # Force garbage collection
          gc.collect()
          
      def _cleanup_old_figures(self):
          """Close oldest figures if we exceed the maximum."""
          while len(self.figures) > self.max_figures:
              old_fig = self.figures.pop(0)
              try:
                  plt.close(old_fig)
              except Exception:
                  pass
                  
      def __del__(self):
          """Destructor - clean up figures."""
          self.clear_all_figures()
  ```

- [ ] **Use ChartMemoryManager in ChartService:**
  ```python
  # Updated ChartService.__init__
  from visualization.charts.chart_memory_manager import ChartMemoryManager
  
  def __init__(self, debug: bool = False):
      self.debug = debug
      self.memory_manager = ChartMemoryManager()
      
  # Updated ChartService.generate_chart
  def generate_chart(self, data: pd.DataFrame, config: ChartConfiguration) -> Tuple[plt.Figure, plt.Axes]:
      """Generate a chart."""
      # ... existing implementation ...
      
      # Register the figure with the memory manager
      self.memory_manager.register_figure(fig)
      
      return fig, ax
  ```

### 6.4. Error Handling in File Operations

- [ ] **Create a FileOperationError class:**
  ```python
  # src/utils/exceptions.py
  class FileOperationError(Exception):
      """Base class for file operation errors."""
      pass
      
  class FileNotFoundError(FileOperationError):
      """Error raised when a file is not found."""
      pass
      
  class FilePermissionError(FileOperationError):
      """Error raised when file permissions prevent an operation."""
      pass
      
  class FileCorruptError(FileOperationError):
      """Error raised when a file is corrupt or cannot be parsed."""
      pass
      
  class FileEncodingError(FileOperationError):
      """Error raised when a file's encoding cannot be determined or is unsupported."""
      pass
  ```

- [ ] **Create a FileOperationsUtils class:**
  ```python
  # src/utils/file_operations_utils.py
  from pathlib import Path
  from typing import Union, List, Optional, Any, Tuple, BinaryIO
  import os
  import tempfile
  import shutil
  from .exceptions import FileOperationError, FileNotFoundError, FilePermissionError
  from .path_utils import PathUtils
  
  class FileOperationsUtils:
      """
      Utilities for file operations with robust error handling.
      """
      
      @staticmethod
      def read_file(
          file_path: Union[str, Path], 
          mode: str = 'r', 
          encoding: Optional[str] = None
      ) -> str:
          """
          Read a file with robust error handling.
          
          Args:
              file_path: Path to the file
              mode: File open mode
              encoding: File encoding
              
          Returns:
              File contents as string
              
          Raises:
              FileNotFoundError: If the file does not exist
              FilePermissionError: If the file cannot be read due to permissions
              FileOperationError: For other errors
          """
          file_path = PathUtils.ensure_path(file_path)
          
          if not file_path.exists():
              raise FileNotFoundError(f"File not found: {file_path}")
              
          try:
              if encoding:
                  with open(file_path, mode, encoding=encoding) as f:
                      return f.read()
              else:
                  with open(file_path, mode) as f:
                      return f.read()
          except PermissionError:
              raise FilePermissionError(f"Permission denied: {file_path}")
          except Exception as e:
              raise FileOperationError(f"Error reading file: {str(e)}")
              
      @staticmethod
      def write_file(
          file_path: Union[str, Path], 
          content: Union[str, bytes],
          mode: str = 'w', 
          encoding: Optional[str] = None
      ) -> None:
          """
          Write to a file with robust error handling.
          
          Args:
              file_path: Path to the file
              content: Content to write
              mode: File open mode
              encoding: File encoding
              
          Raises:
              FilePermissionError: If the file cannot be written due to permissions
              FileOperationError: For other errors
          """
          file_path = PathUtils.ensure_path(file_path)
          
          # Create parent directories if they don't exist
          file_path.parent.mkdir(parents=True, exist_ok=True)
          
          # Use atomic write to prevent corruption if the operation fails
          try:
              # Create a temporary file in the same directory
              with tempfile.NamedTemporaryFile(
                  mode='w' if 'b' not in mode else 'wb',
                  encoding=encoding,
                  dir=file_path.parent,
                  delete=False
              ) as temp_file:
                  # Write content to the temporary file
                  temp_file.write(content)
                  temp_file_path = temp_file.name
                  
              # Replace the target file with the temporary file
              shutil.move(temp_file_path, file_path)
              
          except PermissionError:
              raise FilePermissionError(f"Permission denied: {file_path}")
          except Exception as e:
              raise FileOperationError(f"Error writing file: {str(e)}")
              
      @staticmethod
      def copy_file(
          source_path: Union[str, Path],
          dest_path: Union[str, Path],
          overwrite: bool = True
      ) -> None:
          """
          Copy a file with robust error handling.
          
          Args:
              source_path: Source file path
              dest_path: Destination file path
              overwrite: Whether to overwrite existing files
              
          Raises:
              FileNotFoundError: If the source file does not exist
              FilePermissionError: If the file cannot be copied due to permissions
              FileOperationError: For other errors
          """
          source_path = PathUtils.ensure_path(source_path)
          dest_path = PathUtils.ensure_path(dest_path)
          
          if not source_path.exists():
              raise FileNotFoundError(f"Source file not found: {source_path}")
              
          if dest_path.exists() and not overwrite:
              raise FileOperationError(f"Destination file already exists: {dest_path}")
              
          try:
              # Create parent directories if they don't exist
              dest_path.parent.mkdir(parents=True, exist_ok=True)
              
              # Copy the file
              shutil.copy2(source_path, dest_path)
              
          except PermissionError:
              raise FilePermissionError(f"Permission denied copying {source_path} to {dest_path}")
          except Exception as e:
              raise FileOperationError(f"Error copying file: {str(e)}")
              
      @staticmethod
      def delete_file(file_path: Union[str, Path]) -> None:
          """
          Delete a file with robust error handling.
          
          Args:
              file_path: Path to the file
              
          Raises:
              FileNotFoundError: If the file does not exist
              FilePermissionError: If the file cannot be deleted due to permissions
              FileOperationError: For other errors
          """
          file_path = PathUtils.ensure_path(file_path)
          
          if not file_path.exists():
              raise FileNotFoundError(f"File not found: {file_path}")
              
          try:
              file_path.unlink()
          except PermissionError:
              raise FilePermissionError(f"Permission denied: {file_path}")
          except Exception as e:
              raise FileOperationError(f"Error deleting file: {str(e)}")
  ```

- [ ] **Use the file operation utilities throughout the codebase:**
  ```python
  # In CSVLoader.load
  from utils.file_operations_utils import FileOperationsUtils
  
  def load(self, file_path: Path) -> Tuple[Optional[pd.DataFrame], bool, str]:
      """Load a CSV file."""
      try:
          # Read file content
          content = FileOperationsUtils.read_file(file_path, mode='rb')
          
          # ... process content ...
          
      except FileNotFoundError as e:
          return None, False, str(e)
      except FilePermissionError as e:
          return None, False, str(e)
      except FileOperationError as e:
          return None, False, str(e)
      except Exception as e:
          return None, False, f"Unexpected error: {str(e)}"
  ```

### 6.5. Thread Safety Concerns

- [ ] **Create a BackgroundTask class:**
  ```python
  # src/utils/background_task.py
  from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool, Slot
  from typing import Callable, Any, Dict
  
  class TaskSignals(QObject):
      """Signals for background task communication."""
      
      started = Signal()
      progress = Signal(int, str)  # Progress percentage, message
      error = Signal(str, str)  # Error message, traceback
      result = Signal(object)  # Task result
      finished = Signal()
      
  class BackgroundTask(QRunnable):
      """
      Task to run in a background thread.
      """
      
      def __init__(self, task_func: Callable, *args, **kwargs):
          super().__init__()
          self.task_func = task_func
          self.args = args
          self.kwargs = kwargs
          self.signals = TaskSignals()
          
      @Slot()
      def run(self):
          """Run the task."""
          # Emit started signal
          self.signals.started.emit()
          
          try:
              # Run the task
              result = self.task_func(
                  *self.args,
                  progress_callback=self.signals.progress.emit,
                  **self.kwargs
              )
              
              # Emit result signal
              self.signals.result.emit(result)
              
          except Exception as e:
              import traceback
              # Emit error signal
              self.signals.error.emit(str(e), traceback.format_exc())
              
          finally:
              # Emit finished signal
              self.signals.finished.emit()
              
  class BackgroundTaskManager:
      """
      Manager for background tasks.
      """
      
      def __init__(self, max_threads: int = 4):
          self.thread_pool = QThreadPool()
          self.thread_pool.setMaxThreadCount(max_threads)
          self.tasks = {}
          
      def start_task(
          self,
          task_id: str,
          task_func: Callable,
          *args,
          on_started: Callable = None,
          on_progress: Callable = None,
          on_error: Callable = None,
          on_result: Callable = None,
          on_finished: Callable = None,
          **kwargs
      ) -> bool:
          """
          Start a task in the background.
          
          Args:
              task_id: Unique ID for the task
              task_func: Function to run
              *args: Arguments for the function
              on_started: Callback when task starts
              on_progress: Callback for progress updates
              on_error: Callback for errors
              on_result: Callback for task result
              on_finished: Callback when task finishes
              **kwargs: Keyword arguments for the function
              
          Returns:
              True if task started, False otherwise
          """
          # Cancel existing task with the same ID
          if task_id in self.tasks:
              self.cancel_task(task_id)
              
          # Create the task
          task = BackgroundTask(task_func, *args, **kwargs)
          
          # Connect signals
          if on_started:
              task.signals.started.connect(on_started)
          if on_progress:
              task.signals.progress.connect(on_progress)
          if on_error:
              task.signals.error.connect(on_error)
          if on_result:
              task.signals.result.connect(on_result)
          if on_finished:
              task.signals.finished.connect(on_finished)
              
          # Store the task
          self.tasks[task_id] = task
          
          # Start the task
          self.thread_pool.start(task)
          
          return True
          
      def cancel_task(self, task_id: str) -> bool:
          """
          Cancel a task.
          
          Args:
              task_id: ID of the task to cancel
              
          Returns:
              True if task was cancelled, False otherwise
          """
          if task_id not in self.tasks:
              return False
              
          # Remove the task from the list
          # Note: QThreadPool doesn't support cancellation, so the task will continue
          # to run, but we can disconnect its signals
          task = self.tasks.pop(task_id)
          
          # Disconnect all signals
          try:
              task.signals.started.disconnect()
              task.signals.progress.disconnect()
              task.signals.error.disconnect()
              task.signals.result.disconnect()
              task.signals.finished.disconnect()
          except Exception:
              pass
              
          return True
          
      def cancel_all_tasks(self) -> None:
          """Cancel all tasks."""
          for task_id in list(self.tasks.keys()):
              self.cancel_task(task_id)
              
      def task_count(self) -> int:
          """Get the number of active tasks."""
          return len(self.tasks)
  ```

- [ ] **Use BackgroundTaskManager for data loading:**
  ```python
  # In MainWindow.__init__
  from utils.background_task import BackgroundTaskManager
  
  self.task_manager = BackgroundTaskManager()
  
  # In MainWindow.load_csv_file
  def load_csv_file(self, file_path: str):
      """Load a CSV file in the background."""
      # Show loading indicator
      self.statusBar().showMessage("Loading file...")
      
      # Disable the import button while loading
      if hasattr(self, 'import_area'):
          self.import_area.select_button.setEnabled(False)
          
      # Start the task
      self.task_manager.start_task(
          "load_csv",
          self._load_csv_file_task,
          file_path,
          on_progress=self._update_load_progress,
          on_error=self._handle_load_error,
          on_result=self._handle_load_result,
          on_finished=self._finish_load
      )
      
  def _load_csv_file_task(self, file_path, progress_callback):
      """
      Background task to load a CSV file.
      
      Args:
          file_path: Path to the CSV file
          progress_callback: Callback for progress updates
          
      Returns:
          Tuple of (success, message, dataframe)
      """
      try:
          progress_callback(0, "Starting file load...")
          
          # Load the file using data manager
          df, success, message = self.data_manager.load_file(file_path)
          
          if not success:
              return False, message, None
              
          progress_callback(50, "Processing data...")
          
          # Process the data
          processed_df = self.data_manager.process_data(df)
          
          progress_callback(80, "Analyzing data...")
          
          # Analyze the data
          self.data_manager.analyze_data(processed_df)
          
          progress_callback(100, "Load complete")
          
          return True, "File loaded successfully", processed_df
          
      except Exception as e:
          import traceback
          return False, f"Error loading file: {str(e)}", None
          
  def _update_load_progress(self, percentage, message):
      """Update the UI with load progress."""
      self.statusBar().showMessage(f"{message} ({percentage}%)")
      
  def _handle_load_error(self, error, traceback):
      """Handle errors during file loading."""
      self.statusBar().showMessage(f"Error loading file: {error}")
      
      # Show error dialog
      QMessageBox.critical(self, "Error Loading File", error)
      
  def _handle_load_result(self, result):
      """Handle the result of file loading."""
      success, message, df = result
      
      if success:
          # Update the model with the loaded data
          self.raw_data = df
          self.processed_data = df.copy()
          
          # Update UI
          self._update_ui_after_load()
          
          # Enable all tabs
          self.enable_all_tabs()
          
          # Update status
          self.statusBar().showMessage(message)
      else:
          # Show error message
          self.statusBar().showMessage(message)
          
  def _finish_load(self):
      """Clean up after file loading completes."""
      # Re-enable the import button
      if hasattr(self, 'import_area'):
          self.import_area.select_button.setEnabled(True)
  ```

### 6.6. Encoding Detection Reliability

- [ ] **Create an EncodingDetector class:**
  ```python
  # src/utils/encoding_detector.py
  from typing import List, Dict, Any, Tuple, Optional
  import codecs
  import chardet
  import ftfy
  from charset_normalizer import detect
  import unicodedata
  
  class EncodingDetector:
      """
      Advanced encoding detection and text fixing.
      """
      
      # Common encoding patterns for specific languages
      LANGUAGE_ENCODINGS = {
          'german': ['cp1252', 'latin1', 'iso-8859-1', 'windows-1252'],
          'french': ['cp1252', 'latin1', 'iso-8859-1', 'windows-1252'],
          'spanish': ['cp1252', 'latin1', 'iso-8859-15', 'windows-1252'],
          'russian': ['cp1251', 'koi8-r', 'windows-1251', 'iso-8859-5'],
          'chinese': ['gb2312', 'gbk', 'gb18030', 'big5'],
          'japanese': ['shift_jis', 'euc-jp', 'iso-2022-jp'],
          'korean': ['euc-kr', 'cp949', 'iso-2022-kr']
      }
      
      # Default encodings to try in order
      DEFAULT_ENCODINGS = ['utf-8', 'cp1252', 'latin1', 'iso-8859-1', 'windows-1252']
      
      # Patterns that indicate mojibake for German text
      GERMAN_MOJIBAKE_PATTERNS = {
          'Ã¤': 'ä',  # ä
          'Ã¶': 'ö',  # ö
          'Ã¼': 'ü',  # ü
          'Ã„': 'Ä',  # Ä
          'Ã–': 'Ö',  # Ö
          'Ãœ': 'Ü',  # Ü
          'ÃŸ': 'ß',  # ß
      }
      
      @staticmethod
      def detect_encoding(data: bytes, language_hint: Optional[str] = None) -> List[str]:
          """
          Detect the encoding of binary data with language hints.
          
          Args:
              data: Binary data
              language_hint: Optional language hint (e.g. 'german')
              
          Returns:
              List of probable encodings in order of likelihood
          """
          encodings = []
          
          # Try charset-normalizer first
          detection_result = detect(data)
          if detection_result:
              encodings.append(detection_result[0].encoding)
              
          # Try chardet
          detection_result = chardet.detect(data)
          if detection_result and detection_result['encoding']:
              # Only add if different from previous result
              if not encodings or encodings[0] != detection_result['encoding']:
                  encodings.append(detection_result['encoding'])
                  
          # Add language-specific encodings if provided
          if language_hint and language_hint.lower() in EncodingDetector.LANGUAGE_ENCODINGS:
              for enc in EncodingDetector.LANGUAGE_ENCODINGS[language_hint.lower()]:
                  if enc not in encodings:
                      encodings.append(enc)
                      
          # Add default encodings
          for enc in EncodingDetector.DEFAULT_ENCODINGS:
              if enc not in encodings:
                  encodings.append(enc)
                  
          return encodings
          
      @staticmethod
      def fix_text(text: str, language_hint: Optional[str] = None) -> str:
          """
          Fix encoding and normalization issues in text.
          
          Args:
              text: Text to fix
              language_hint: Optional language hint (e.g. 'german')
              
          Returns:
              Fixed text
          """
          if not isinstance(text, str):
              return str(text)
              
          # Use ftfy to fix encoding issues
          fixed_text = ftfy.fix_text(text)
          
          # Normalize Unicode to consistent form
          fixed_text = unicodedata.normalize('NFC', fixed_text)
          
          # Apply language-specific fixes
          if language_hint == 'german':
              # Fix common mojibake patterns for German
              for pattern, replacement in EncodingDetector.GERMAN_MOJIBAKE_PATTERNS.items():
                  fixed_text = fixed_text.replace(pattern, replacement)
                  
          return fixed_text
          
      @staticmethod
      def decode_with_fallback(data: bytes, encodings: Optional[List[str]] = None) -> Tuple[str, str]:
          """
          Decode binary data with a list of encodings, falling back as needed.
          
          Args:
              data: Binary data to decode
              encodings: List of encodings to try
              
          Returns:
              Tuple of (decoded text, encoding used)
          """
          encodings = encodings or EncodingDetector.DEFAULT_ENCODINGS
          
          # Try each encoding
          for encoding in encodings:
              try:
                  text = data.decode(encoding)
                  return text, encoding
              except UnicodeDecodeError:
                  continue
                  
          # If all fail, use replace errors
          text = data.decode(encodings[0], errors='replace')
          return text, f"{encodings[0]} (with errors)"
          
      @staticmethod
      def score_encoding_quality(text: str, language_hint: Optional[str] = None) -> int:
          """
          Score the quality of an encoding based on the text content.
          
          Args:
              text: Text to evaluate
              language_hint: Optional language hint (e.g. 'german')
              
          Returns:
              Quality score (higher is better)
          """
          score = 0
          
          # Check for replacement characters which indicate encoding problems
          replacement_chars = text.count('\ufffd')
          score -= replacement_chars * 10
          
          # Check for question marks which might be replacement characters
          question_marks = text.count('?')
          score -= question_marks
          
          # Check for language-specific characters
          if language_hint == 'german':
              # Common German characters
              german_chars = sum(text.count(c) for c in 'äöüÄÖÜß')
              score += german_chars * 5
              
              # Common mojibake patterns
              mojibake_patterns = sum(text.count(pattern) for pattern in EncodingDetector.GERMAN_MOJIBAKE_PATTERNS.keys())
              score -= mojibake_patterns * 5
              
          return score
          
      @classmethod
      def find_best_encoding(cls, data: bytes, language_hint: Optional[str] = None) -> Tuple[str, str]:
          """
          Find the best encoding for binary data based on quality scoring.
          
          Args:
              data: Binary data to decode
              language_hint: Optional language hint (e.g. 'german')
              
          Returns:
              Tuple of (decoded text, encoding used)
          """
          # Get potential encodings
          encodings = cls.detect_encoding(data, language_hint)
          
          best_text = ""
          best_encoding = ""
          best_score = float('-inf')
          
          # Try each encoding and score the result
          for encoding in encodings:
              try:
                  text = data.decode(encoding)
                  score = cls.score_encoding_quality(text, language_hint)
                  
                  if score > best_score:
                      best_score = score
                      best_text = text
                      best_encoding = encoding
              except UnicodeDecodeError:
                  continue
                  
          # If no encoding worked, fall back to replacement
          if not best_encoding:
              best_text, best_encoding = cls.decode_with_fallback(data)
              
          # Fix any remaining issues
          best_text = cls.fix_text(best_text, language_hint)
          
          return best_text, best_encoding
  ```

- [ ] **Use EncodingDetector in DataProcessor:**
  ```python
  # In DataProcessor.read_csv_with_encoding_fix
  from utils.encoding_detector import EncodingDetector
  
  def read_csv_with_encoding_fix(filepath: Path):
      """Read a CSV file with automatic encoding detection and text fixing."""
      try:
          # Read the file as binary
          with open(filepath, 'rb') as f:
              content = f.read()
              
          # Detect the encoding with German language hint
          text, encoding = EncodingDetector.find_best_encoding(content, 'german')
          
          # Create a StringIO object from the decoded text
          import io
          csv_io = io.StringIO(text)
          
          # Read the CSV
          df = pd.read_csv(csv_io)
          
          # Apply fixes to text columns
          text_columns = df.select_dtypes(include=['object']).columns
          if text_columns.any():
              for col in text_columns:
                  df[col] = df[col].astype(str)
                  df[col] = df[col].apply(lambda x: EncodingDetector.fix_text(x, 'german'))
                  
          return df, True, ""
          
      except Exception as e:
          return None, False, f"Error reading CSV: {str(e)}"
  ```

### 6.7. Configuration Persistence Issues

- [ ] **Create a ConfigPersistenceManager class:**
  ```python
  # src/core/config/config_persistence_manager.py
  from pathlib import Path
  from typing import Dict, Any, Optional, Union
  import json
  import os
  import shutil
  import tempfile
  import copy
  import time
  from utils.path_utils import PathUtils
  
  class ConfigPersistenceManager:
      """
      Manages configuration persistence with robust error handling.
      """
      
      def __init__(
          self,
          config_file: Union[str, Path],
          backup_dir: Optional[Union[str, Path]] = None,
          max_backups: int = 5,
          save_delay: float = 1.0
      ):
          self.config_file = PathUtils.ensure_path(config_file)
          self.backup_dir = PathUtils.ensure_path(backup_dir) if backup_dir else self.config_file.parent / "backups"
          self.max_backups = max_backups
          self.save_delay = save_delay
          self.last_save_time = 0
          self.pending_save = False
          self.modified_config = None
          
          # Create directories if they don't exist
          self.config_file.parent.mkdir(parents=True, exist_ok=True)
          self.backup_dir.mkdir(parents=True, exist_ok=True)
          
      def load_config(self, default_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
          """
          Load configuration from file.
          
          Args:
              default_config: Default configuration if file doesn't exist
              
          Returns:
              Configuration dictionary
          """
          default_config = default_config or {}
          
          if not self.config_file.exists():
              return copy.deepcopy(default_config)
              
          try:
              with open(self.config_file, 'r', encoding='utf-8') as f:
                  config = json.load(f)
                  
              # Merge with default config to ensure all required keys exist
              merged_config = copy.deepcopy(default_config)
              self._deep_update(merged_config, config)
              return merged_config
              
          except json.JSONDecodeError:
              # Try to load backup
              backup_config = self._load_from_backup()
              if backup_config:
                  return backup_config
              return copy.deepcopy(default_config)
          except Exception:
              return copy.deepcopy(default_config)
              
      def save_config(self, config: Dict[str, Any], force: bool = False) -> bool:
          """
          Save configuration to file.
          
          Args:
              config: Configuration to save
              force: Whether to force save even if within save delay
              
          Returns:
              True if saved, False otherwise
          """
          # Store the modified config
          self.modified_config = copy.deepcopy(config)
          
          # Check if we need to delay the save
          current_time = time.time()
          time_since_last_save = current_time - self.last_save_time
          
          if not force and time_since_last_save < self.save_delay:
              # Schedule delayed save
              self.pending_save = True
              return False
              
          # Create backup before saving
          self._create_backup()
          
          try:
              # Use atomic write to prevent corruption
              with tempfile.NamedTemporaryFile(
                  mode='w',
                  encoding='utf-8',
                  dir=self.config_file.parent,
                  delete=False
              ) as temp_file:
                  json.dump(config, temp_file, indent=2)
                  temp_file_path = temp_file.name
                  
              # Replace the config file with the temp file
              shutil.move(temp_file_path, self.config_file)
              
              # Update state
              self.last_save_time = current_time
              self.pending_save = False
              
              return True
              
          except Exception:
              return False
              
      def process_pending_save(self) -> bool:
          """
          Process a pending save if one exists.
          
          Returns:
              True if a save was processed, False otherwise
          """
          if self.pending_save and self.modified_config:
              return self.save_config(self.modified_config, force=True)
          return False
          
      def _create_backup(self) -> bool:
          """
          Create a backup of the current config file.
          
          Returns:
              True if successful, False otherwise
          """
          if not self.config_file.exists():
              return False
              
          try:
              # Generate backup filename with timestamp
              timestamp = time.strftime("%Y%m%d_%H%M%S")
              backup_file = self.backup_dir / f"{self.config_file.stem}_{timestamp}{self.config_file.suffix}"
              
              # Copy the file
              shutil.copy2(self.config_file, backup_file)
              
              # Limit the number of backups
              self._cleanup_old_backups()
              
              return True
              
          except Exception:
              return False
              
      def _cleanup_old_backups(self) -> None:
          """Clean up old backup files to limit the number of backups."""
          backup_files = sorted(
              self.backup_dir.glob(f"{self.config_file.stem}_*{self.config_file.suffix}"),
              key=lambda x: x.stat().st_mtime
          )
          
          # Remove oldest backups if we exceed the maximum
          while len(backup_files) > self.max_backups:
              oldest = backup_files.pop(0)
              try:
                  oldest.unlink()
              except Exception:
                  pass
                  
      def _load_from_backup(self) -> Optional[Dict[str, Any]]:
          """
          Load configuration from the most recent backup.
          
          Returns:
              Configuration dictionary or None if no backups exist
          """
          backup_files = sorted(
              self.backup_dir.glob(f"{self.config_file.stem}_*{self.config_file.suffix}"),
              key=lambda x: x.stat().st_mtime,
              reverse=True
          )
          
          for backup_file in backup_files:
              try:
                  with open(backup_file, 'r', encoding='utf-8') as f:
                      return json.load(f)
              except Exception:
                  continue
                  
          return None
          
      def _deep_update(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
          """
          Update target dictionary with values from source dictionary, recursively.
          
          Args:
              target: Target dictionary to update
              source: Source dictionary to update from
          """
          for key, value in source.items():
              if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                  # Recursively update nested dictionaries
                  self._deep_update(target[key], value)
              else:
                  # Replace or add the value
                  target[key] = value
  ```

- [ ] **Update AppConfig to use ConfigPersistenceManager:**
  ```python
  # src/core/config/app_config.py
  from pathlib import Path
  from typing import Dict, Any, Optional
  from .config_persistence_manager import ConfigPersistenceManager
  from utils.path_utils import PathUtils
  import time
  
  class AppConfig:
      """Application configuration manager."""
      
      def __init__(self, config_file: Path = None, auto_save: bool = True):
          self.config_file = config_file or PathUtils.get_app_config_directory("TotalBattleAnalyzer") / "config.json"
          self.auto_save = auto_save
          self.persistence_manager = ConfigPersistenceManager(
              self.config_file,
              save_delay=1.0  # 1 second delay between saves
          )
          self.config = self.persistence_manager.load_config(self._get_default_config())
          self.last_modified = time.time()
          
          # Start auto-save timer if enabled
          if self.auto_save:
              self._setup_auto_save()
              
      def _setup_auto_save(self):
          """Set up auto-save timer."""
          try:
              from PySide6.QtCore import QTimer
              self.auto_save_timer = QTimer()
              self.auto_save_timer.timeout.connect(self._auto_save_timeout)
              self.auto_save_timer.start(2000)  # Check every 2 seconds
          except ImportError:
              # No Qt available, disable auto-save
              self.auto_save = False
              
      def _auto_save_timeout(self):
          """Handle auto-save timer timeout."""
          # Process any pending saves
          self.persistence_manager.process_pending_save()
          
          # Check if we need to save due to modifications
          if self.last_modified > self.persistence_manager.last_save_time:
              self.save_config()
              
      def _get_default_config(self) -> Dict[str, Any]:
          """Get default configuration."""
          return {
              "general": {
                  "theme": "dark",
                  "language": "en",
                  "debug": False
              },
              "paths": {
                  "import_dir": str(Path.cwd() / "data" / "imports"),
                  "export_dir": str(Path.cwd() / "data" / "exports"),
                  "cache_dir": str(Path.cwd() / "cache")
              },
              "ui": {
                  "window_width": 1200,
                  "window_height": 800,
                  "splitter_positions": {}
              },
              "files": {
                  "recent_files": [],
                  "max_recent_files": 10
              },
              "charts": {
                  "default_chart_type": "Bar Chart",
                  "show_values": True,
                  "show_grid": True,
                  "colors": ["#D4AF37", "#5991C4", "#6EC1A7", "#D46A5F"]
              },
              "encoding": {
                  "default_encoding": "utf-8",
                  "alternative_encodings": ["latin1", "cp1252", "iso-8859-1"]
              }
          }
          
      def get(self, section: str, key: str, default: Any = None) -> Any:
          """Get a configuration value."""
          if section in self.config and key in self.config[section]:
              return self.config[section][key]
          return default
          
      def set(self, section: str, key: str, value: Any) -> None:
          """Set a configuration value."""
          if section not in self.config:
              self.config[section] = {}
              
          # Check if value is actually changing
          if section in self.config and key in self.config[section] and self.config[section][key] == value:
              return
              
          self.config[section][key] = value
          self.last_modified = time.time()
          
          # Save if auto-save is not enabled
          if not self.auto_save:
              self.save_config()
              
      def save_config(self) -> bool:
          """Save configuration to file."""
          return self.persistence_manager.save_config(self.config)
          
      def get_path(self, key: str, default: Optional[Path] = None) -> Path:
          """Get a path from configuration."""
          path_str = self.get("paths", key, default)
          if path_str is None:
              return Path.cwd()
              
          return Path(path_str)
          
      def set_path(self, key: str, path: Path) -> None:
          """Set a path in configuration."""
          self.set("paths", key, str(path))
          
      def add_recent_file(self, file_path: Path) -> None:
          """Add a file to recent files list."""
          recent_files = self.get("files", "recent_files", [])
          max_recent = self.get("files", "max_recent_files", 10)
          
          # Convert to string for storage
          file_path_str = str(file_path)
          
          # Remove if already exists
          if file_path_str in recent_files:
              recent_files.remove(file_path_str)
              
          # Add to start of list
          recent_files.insert(0, file_path_str)
          
          # Limit to max recent files
          if len(recent_files) > max_recent:
              recent_files = recent_files[:max_recent]
              
          self.set("files", "recent_files", recent_files)
  ```

## 7. Codebase Refactoring Strategy

### 7.1. Package Reorganization

- [ ] **Create the following directory structure:**
  ```
  src/
    ├── core/              # Core application logic
    │   ├── data/          # Data models and processing
    │   │   ├── access/    # Data access layer
    │   │   ├── models/    # Data model classes
    │   │   └── transform/ # Data transformation
    │   ├── analysis/      # Analysis algorithms
    │   └── config/        # Configuration management
    ├── ui/                # UI components
    │   ├── main/          # Main window and application
    │   ├── tabs/          # Individual tab implementations
    │   ├── widgets/       # Reusable UI components
    │   ├── presenters/    # Presenter classes
    │   ├── styles/        # Styling utilities
    │   └── dialogs/       # Application dialogs
    ├── visualization/     # Visualization components
    │   ├── charts/        # Chart generation logic
    │   ├── styles/        # Chart styling
    │   └── reports/       # Report generation
    ├── utils/             # Utility functions and helpers
    └── resources/         # Application resources
        ├── icons/         # UI icons
        ├── styles/        # Style sheets
        └── templates/     # Report templates
  ```

- [ ] **Update imports to match the new structure:**
  ```python
  # Example of updated imports
  from core.data.models.chest_record import ChestRecord
  from core.data.access.csv_data_access import CSVDataAccess
  from core.data.transform.data_processor import DataProcessor
  from ui.widgets.enhanced_table_view import EnhancedTableView
  from ui.styles.theme_manager import ThemeManager
  from visualization.charts.chart_service import ChartService
  from utils.path_utils import PathUtils
  ```

### 7.2. MainWindow Refactoring

- [ ] **Reorganize MainWindow into a Application class and TabContainer:**
  ```python
  # src/ui/main/application.py
  from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
  from PySide6.QtCore import QSettings, QTimer
  from PySide6.QtGui import QIcon
  from core.config.app_config import AppConfig
  from ui.main.tab_container import TabContainer
  from ui.styles.theme_manager import ThemeManager
  from ui.main.menu_manager import MenuManager
  from core.data.data_manager import DataManager
  from utils.background_task import BackgroundTaskManager
  from pathlib import Path
  
  class Application(QMainWindow):
      """
      Main application window.
      """
      
      def __init__(self, debug=False):
          super().__init__()
          self.debug = debug
          
          # Initialize configuration
          self.config = AppConfig()
          
          # Initialize managers
          self.data_manager = DataManager(debug=debug)
          self.theme_manager = ThemeManager()
          self.task_manager = BackgroundTaskManager()
          
          # Set up the UI
          self.setup_ui()
          
          # Apply theme
          self.theme_manager.apply_theme(QApplication.instance())
          
          # Set window properties from config
          self.set_window_properties()
          
      def setup_ui(self):
          """Set up the user interface."""
          # Set window title
          self.setWindowTitle("Total Battle Analyzer")
          
          # Create tab container
          self.tab_container = TabContainer(self)
          self.setCentralWidget(self.tab_container)
          
          # Create menu manager
          self.menu_manager = MenuManager(self)
          self.menu_manager.setup_menus()
          
          # Set status bar
          self.statusBar().showMessage("Ready")
          
      def set_window_properties(self):
          """Set window properties from configuration."""
          # Set window size
          width = self.config.get("ui", "window_width", 1200)
          height = self.config.get("ui", "window_height", 800)
          self.resize(width, height)
          
          # Set window icon
          icon_path = Path(__file__).parent.parent.parent / "resources" / "icons" / "app_icon.png"
          if icon_path.exists():
              self.setWindowIcon(QIcon(str(icon_path)))
              
      def closeEvent(self, event):
          """Handle window close event."""
          # Save window size
          self.config.set("ui", "window_width", self.width())
          self.config.set("ui", "window_height", self.height())
          
          # Save splitter positions
          self.tab_container.save_splitter_positions()
          
          # Cancel any running tasks
          self.task_manager.cancel_all_tasks()
          
          # Process pending configuration saves
          self.config.save_config()
          
          event.accept()
  ```

- [ ] **Create a TabContainer class:**
  ```python
  # src/ui/main/tab_container.py
  from PySide6.QtWidgets import QTabWidget, QWidget
  from PySide6.QtCore import Signal
  from core.data.data_manager import DataManager
  from ui.tabs.import_tab import ImportTab
  from ui.tabs.raw_data_tab import RawDataTab
  from ui.tabs.analysis_tab import AnalysisTab
  from ui.tabs.charts_tab import ChartsTab
  from ui.tabs.report_tab import ReportTab
  
  class TabContainer(QTabWidget):
      """
      Container for application tabs.
      """
      
      tab_changed = Signal(str)  # Emitted with the name of the new active tab
      
      def __init__(self, parent):
          super().__init__(parent)
          self.main_window = parent
          self.tabs = {}
          
          # Set up the tabs
          self.setup_tabs()
          
          # Connect signals
          self.currentChanged.connect(self.on_tab_changed)
          
      def setup_tabs(self):
          """Set up the application tabs."""
          # Create tabs
          self.import_tab = ImportTab(self)
          self.raw_data_tab = RawDataTab(self)
          self.analysis_tab = AnalysisTab(self)
          self.charts_tab = ChartsTab(self)
          self.report_tab = ReportTab(self)
          
          # Add tabs to widget
          self.addTab(self.import_tab, "Import")
          self.addTab(self.raw_data_tab, "Raw Data")
          self.addTab(self.analysis_tab, "Analysis")
          self.addTab(self.charts_tab, "Charts")
          self.addTab(self.report_tab, "Report")
          
          # Store tabs in dictionary
          self.tabs = {
              "Import": self.import_tab,
              "Raw Data": self.raw_data_tab,
              "Analysis": self.analysis_tab,
              "Charts": self.charts_tab,
              "Report": self.report_tab
          }
          
          # Initially disable all tabs except Import (index 0)
          self.disable_tabs_except_import()
          
      def on_tab_changed(self, index):
          """Handle tab change events."""
          tab_name = self.tabText(index)
          self.tab_changed.emit(tab_name)
          
      def disable_tabs_except_import(self):
          """Disable all tabs except the Import tab (index 0)."""
          for i in range(1, self.count()):
              self.setTabEnabled(i, False)
              
      def enable_all_tabs(self):
          """Enable all tabs."""
          for i in range(self.count()):
              self.setTabEnabled(i, True)
              
      def save_splitter_positions(self):
          """Save splitter positions to configuration."""
          splitter_positions = {}
          
          # Collect splitter positions from tabs
          for name, tab in self.tabs.items():
              if hasattr(tab, 'get_splitter_positions'):
                  positions = tab.get_splitter_positions()
                  if positions:
                      splitter_positions[name] = positions
                      
          # Save to configuration
          if splitter_positions:
              self.main_window.config.set("ui", "splitter_positions", splitter_positions)
  ```

### 7.3. Individual Tab Refactoring

- [ ] **Create base tab class:**
  ```python
  # src/ui/tabs/base_tab.py
  from PySide6.QtWidgets import QWidget, QVBoxLayout
  from PySide6.QtCore import Signal
  
  class BaseTab(QWidget):
      """
      Base class for application tabs.
      """
      
      def __init__(self, parent):
          super().__init__(parent)
          self.main_window = self.get_main_window()
          self.data_manager = self.main_window.data_manager
          self.config = self.main_window.config
          self.setup_ui()
          
      def get_main_window(self):
          """Get the main window parent."""
          parent = self.parent()
          while parent is not None:
              if hasattr(parent, 'data_manager'):
                  return parent
              parent = parent.parent()
          return None
          
      def setup_ui(self):
          """Set up the tab UI - to be implemented by subclasses."""
          pass
          
      def on_data_loaded(self):
          """Handle data loading events - to be implemented by subclasses."""
          pass
          
      def get_splitter_positions(self):
          """Get positions of splitters in the tab - to be implemented by subclasses."""
          return {}
  ```

- [ ] **Create ImportTab class:**
  ```python
  # src/ui/tabs/import_tab.py
  from PySide6.QtWidgets import QVBoxLayout, QLabel, QSplitter
  from PySide6.QtCore import Qt, Signal
  from .base_tab import BaseTab
  from ui.widgets.import_area import ImportArea
  from pathlib import Path
  
  class ImportTab(BaseTab):
      """
      Tab for importing data files.
      """
      
      file_selected = Signal(str)  # Emitted when a file is selected
      
      def __init__(self, parent):
          super().__init__(parent)
          
      def setup_ui(self):
          """Set up the import tab UI."""
          layout = QVBoxLayout(self)
          layout.setContentsMargins(10, 10, 10, 10)
          layout.setSpacing(10)
          
          # Add file label
          self.file_label = QLabel("No file loaded")
          self.file_label.setAlignment(Qt.AlignCenter)
          layout.addWidget(self.file_label)
          
          # Create import area
          self.import_area = ImportArea(self)
          self.import_area.fileSelected.connect(self.on_file_selected)
          
          # Add to layout
          layout.addWidget(self.import_area)
          layout.addStretch()
          
      def on_file_selected(self, file_path):
          """Handle file selection event."""
          # Update file label
          self.file_label.setText(f"File: {Path(file_path).name}")
          
          # Emit signal to notify parent
          self.file_selected.emit(file_path)
  ```

- [ ] **Create RawDataTab class:**
  ```python
  # src/ui/tabs/raw_data_tab.py
  from PySide6.QtWidgets import QVBoxLayout, QSplitter, QHBoxLayout, QPushButton
  from PySide6.QtCore import Qt, Signal
  from .base_tab import BaseTab
  from ui.widgets.data_filter_panel import DataFilterPanel
  from ui.widgets.enhanced_table_view import EnhancedTableView
  
  class RawDataTab(BaseTab):
      """
      Tab for viewing and filtering raw data.
      """
      
      def __init__(self, parent):
          super().__init__(parent)
          
      def setup_ui(self):
          """Set up the raw data tab UI."""
          layout = QVBoxLayout(self)
          layout.setContentsMargins(10, 10, 10, 10)
          layout.setSpacing(10)
          
          # Create splitter
          self.splitter = QSplitter(Qt.Horizontal)
          
          # Create filter panel
          self.filter_panel = DataFilterPanel(title="Raw Data Filter")
          self.filter_panel.filterApplied.connect(self.apply_filter)
          self.filter_panel.filterCleared.connect(self.clear_filter)
          
          # Create table view
          self.table_view = EnhancedTableView()
          self.table_view.exportRequested.connect(self.export_data)
          
          # Add widgets to splitter
          self.splitter.addWidget(self.filter_panel)
          self.splitter.addWidget(self.table_view)
          
          # Set splitter sizes (30% filter, 70% table)
          self.splitter.setSizes([300, 700])
          
          # Export button
          export_layout = QHBoxLayout()
          self.export_button = QPushButton("Export Data")
          self.export_button.clicked.connect(self.export_data)
          export_layout.addWidget(self.export_button)
          export_layout.addStretch()
          
          # Add widgets to layout
          layout.addWidget(self.splitter)
          layout.addLayout(export_layout)
          
      def apply_filter(self, filter_settings):
          """Apply filter to raw data."""
          if not self.data_manager or not hasattr(self.data_manager, 'filter_data'):
              return
              
          # Get filter settings
          column = filter_settings.get('column')
          values = filter_settings.get('selected_values', [])
          
          # Apply filter through data manager
          self.data_manager.filter_raw_data(column, values)
          
          # Update table
          self.update_table()
          
      def clear_filter(self):
          """Clear filters."""
          if not self.data_manager:
              return
              
          # Clear filters through data manager
          self.data_manager.clear_raw_data_filters()
          
          # Update table
          self.update_table()
          
      def update_table(self):
          """Update the table with current data."""
          if not self.data_manager:
              return
              
          # Get processed data
          df = self.data_manager.get_processed_data()
          
          if df is not None:
              # Create table model
              from ui.models.custom_table_model import CustomTableModel
              model = CustomTableModel(df)
              
              # Set model to table
              self.table_view.setModel(model)
              
      def export_data(self, format_type="csv"):
          """Export data to file."""
          if not self.data_manager:
              return
              
          # Get processed data
          df = self.data_manager.get_processed_data()
          
          if df is not None:
              # Show file dialog
              from PySide6.QtWidgets import QFileDialog
              from pathlib import Path
              
              export_dir = self.config.get_path("export_dir")
              file_path, _ = QFileDialog.getSaveFileName(
                  self,
                  "Export Data",
                  str(export_dir / "raw_data.csv"),
                  "CSV Files (*.csv)"
              )
              
              if file_path:
                  # Remember the directory
                  self.config.set_path("export_dir", Path(file_path).parent)
                  
                  # Export the data
                  self.data_manager.export_data(df, file_path)
                  
      def on_data_loaded(self):
          """Handle data loading event."""
          # Update filter panel with available columns
          if hasattr(self.data_manager, 'get_raw_data'):
              df = self.data_manager.get_raw_data()
              if df is not None:
                  self.filter_panel.set_dataframe(df)
                  
          # Update table
          self.update_table()
          
      def get_splitter_positions(self):
          """Get splitter positions."""
          return self.splitter.sizes()
  ```

### 7.4. Implementation Strategy

- [ ] **Start by creating the directory structure:**
  ```bash
  mkdir -p src/core/data/access src/core/data/models src/core/data/transform
  mkdir -p src/core/analysis src/core/config
  mkdir -p src/ui/main src/ui/tabs src/ui/widgets src/ui/presenters src/ui/styles src/ui/dialogs
  mkdir -p src/visualization/charts src/visualization/styles src/visualization/reports
  mkdir -p src/utils
  mkdir -p src/resources/icons src/resources/styles src/resources/templates
  ```

- [ ] **Create core foundation classes first:**
  - Implement basic configuration system
  - Create data models
  - Implement data access layer
  - Create analysis services
  
- [ ] **Implement UI framework:**
  - Create base UI components
  - Implement theme management
  - Create Application and TabContainer classes
  
- [ ] **Implement tab classes one by one:**
  - Start with ImportTab
  - Move on to RawDataTab
  - Implement AnalysisTab
  - Create ChartsTab
  - Finally implement ReportTab
  
- [ ] **Ensure backward compatibility:**
  ```python
  # src/backward_compatibility.py
  """
  Module for backward compatibility during transition.
  
  This module allows older code to work with the new architecture
  by providing compatibility classes and functions.
  """
  
  import warnings
  
  class MainWindowCompat:
      """
      Compatibility class for code that expects MainWindow.
      
      This class delegates to the new Application class to
      maintain backward compatibility during the transition.
      """
      
      def __init__(self, app):
          self.app = app
          self._setup_compatibility()
          
      def _setup_compatibility(self):
          """Set up compatibility attributes."""
          # Map old MainWindow attributes to new Application attributes
          self.raw_data = self.app.data_manager.raw_data
          self.processed_data = self.app.data_manager.processed_data
          self.analysis_data = self.app.data_manager.analysis_data
          self.analysis_results = self.app.data_manager.analysis_results
          self.config_manager = self.app.config
          
          # Warn about deprecated usage
          warnings.warn(
              "MainWindow is deprecated. Use Application instead.",
              DeprecationWarning,
              stacklevel=2
          )
  ```

### 7.5. Migration Sequence

1. **Phase 1: Initial Structure**
   - Create directory structure
   - Move utility functions to src/utils
   - Create basic interfaces
   
2. **Phase 2: Data Foundation**
   - Create data model classes
   - Implement data access layer
   - Create DataManager
   
3. **Phase 3: Services Implementation**
   - Implement analysis services
   - Create chart services
   - Implement report services
   
4. **Phase 4: UI Components**
   - Create reusable widgets
   - Implement basic tab classes
   - Create theme management
   
5. **Phase 5: Application Framework**
   - Implement Application class
   - Create TabContainer
   - Add event management
   
6. **Phase 6: Final Integration**
   - Connect all components
   - Implement backward compatibility
   - Write tests
   
7. **Phase 7: Cleanup and Documentation**
   - Remove obsolete code
   - Finalize documentation
   - Optimize performance
