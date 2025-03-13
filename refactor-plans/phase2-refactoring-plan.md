# Total Battle Analyzer Refactoring Plan: Phase 2

## Data Foundation Implementation

This phase focuses on establishing a robust data layer with proper modeling, access patterns, and management. We'll implement the core data infrastructure that will support the rest of the application.

### 1. Phase Setup

- [ ] **Branch Management**
  - [ ] Create a new branch `refactoring-phase2` from the completed Phase 1 branch
  - [ ] Ensure all Phase 1 tasks were completed successfully

- [ ] **Review Data Requirements**
  - [ ] Analyze the existing data structures in the application
  - [ ] Identify core entities (Chest, Player, Source, Score, etc.)
  - [ ] Document relationships between entities
  - [ ] Define data validation requirements

### 2. Data Model Implementation

- [ ] **Create Basic Record Models**
  - [ ] **Implement ChestRecord class**
    ```python
    # src/core/data/models/chest_record.py
    from dataclasses import dataclass
    from datetime import date
    from typing import Optional
    
    @dataclass
    class ChestRecord:
        """Model representing a chest record."""
        date: date
        player: str
        source: str
        chest: str
        score: float
        clan: Optional[str] = None
        
        @classmethod
        def from_dict(cls, data: dict) -> 'ChestRecord':
            """Create a ChestRecord from a dictionary."""
            return cls(
                date=data['DATE'],
                player=data['PLAYER'],
                source=data['SOURCE'],
                chest=data['CHEST'],
                score=float(data['SCORE']),
                clan=data.get('CLAN')
            )
            
        def to_dict(self) -> dict:
            """Convert to dictionary representation."""
            return {
                'DATE': self.date,
                'PLAYER': self.player,
                'SOURCE': self.source,
                'CHEST': self.chest,
                'SCORE': self.score,
                'CLAN': self.clan
            }
    ```

  - [ ] **Implement PlayerSummary class**
    ```python
    # src/core/data/models/player_summary.py
    from dataclasses import dataclass
    from typing import Dict, Optional
    
    @dataclass
    class PlayerSummary:
        """Summary model for player performance."""
        player: str
        total_score: float
        chest_count: int
        sources: Dict[str, float]
        clan: Optional[str] = None
        
        @property
        def efficiency(self) -> float:
            """Calculate points per chest."""
            return self.total_score / self.chest_count if self.chest_count > 0 else 0
    ```

  - [ ] **Implement ChestSummary class**
    ```python
    # src/core/data/models/chest_summary.py
    from dataclasses import dataclass
    
    @dataclass
    class ChestSummary:
        """Summary model for chest performance."""
        chest_type: str
        total_score: float
        chest_count: int
        
        @property
        def average_score(self) -> float:
            """Calculate average score per chest."""
            return self.total_score / self.chest_count if self.chest_count > 0 else 0
    ```

  - [ ] **Implement SourceSummary class**
    ```python
    # src/core/data/models/source_summary.py
    from dataclasses import dataclass
    
    @dataclass
    class SourceSummary:
        """Summary model for source performance."""
        source: str
        total_score: float
        chest_count: int
        
        @property
        def average_score(self) -> float:
            """Calculate average score per chest from this source."""
            return self.total_score / self.chest_count if self.chest_count > 0 else 0
    ```

- [ ] **Create Dataset Model**
  - [ ] **Implement DatasetModel class**
    ```python
    # src/core/data/models/dataset_model.py
    import pandas as pd
    from typing import List, Dict, Optional, Any
    from .chest_record import ChestRecord
    
    class DatasetModel:
        """Model managing a collection of chest records."""
        
        def __init__(self, records: Optional[List[ChestRecord]] = None):
            self.records = records or []
            
        @classmethod
        def from_dataframe(cls, df: pd.DataFrame) -> 'DatasetModel':
            """Create a DatasetModel from a pandas DataFrame."""
            records = [ChestRecord.from_dict(row) for _, row in df.iterrows()]
            return cls(records)
            
        def to_dataframe(self) -> pd.DataFrame:
            """Convert the records to a pandas DataFrame."""
            return pd.DataFrame([record.to_dict() for record in self.records])
            
        def filter_by_player(self, player: str) -> 'DatasetModel':
            """Filter records by player name."""
            filtered = [r for r in self.records if r.player == player]
            return DatasetModel(filtered)
            
        def filter_by_column(self, column: str, values: List[str]) -> 'DatasetModel':
            """Filter records by column values."""
            if not values:
                return DatasetModel(self.records.copy())
                
            filtered = []
            for record in self.records:
                if column == 'PLAYER' and record.player in values:
                    filtered.append(record)
                elif column == 'SOURCE' and record.source in values:
                    filtered.append(record)
                elif column == 'CHEST' and record.chest in values:
                    filtered.append(record)
                    
            return DatasetModel(filtered)
    ```

### 3. Data Access Layer Implementation

- [ ] **Implement Data Access Interface**
  - [ ] **Create DataAccess abstract base class**
    ```python
    # src/core/data/access/data_access.py
    from abc import ABC, abstractmethod
    import pandas as pd
    from typing import Tuple, Optional
    from pathlib import Path
    
    class DataAccess(ABC):
        """Interface for data access operations."""
        
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

- [ ] **Implement CSV Data Access**
  - [ ] **Create CSVDataAccess class**
    ```python
    # src/core/data/access/csv_data_access.py
    import pandas as pd
    from typing import Tuple, Optional, List
    from pathlib import Path
    from .data_access import DataAccess
    from utils.encoding_detector import EncodingDetector
    
    class CSVDataAccess(DataAccess):
        """CSV implementation of the DataAccess interface."""
        
        def __init__(self, encodings: List[str] = None, debug: bool = False):
            self.encodings = encodings or ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
            self.debug = debug
            self.encoding_detector = EncodingDetector()
            
        def load_data(self, file_path: Path) -> Tuple[Optional[pd.DataFrame], bool, str]:
            """Load data from a CSV file."""
            if not file_path.exists():
                return None, False, f"File not found: {file_path}"
                
            try:
                # Read file as binary first
                with open(file_path, 'rb') as f:
                    content = f.read()
                    
                # Detect encoding - favor German detection since app has German users
                text, encoding = self.encoding_detector.find_best_encoding(
                    content, language_hint='german'
                )
                
                # Parse CSV from the decoded text
                import io
                csv_io = io.StringIO(text)
                
                # Try comma as separator
                try:
                    df = pd.read_csv(csv_io)
                    if self.debug:
                        print(f"Successfully loaded with {encoding} encoding and comma separator")
                    
                    # Reset stream position for potential reuse
                    csv_io.seek(0)
                    return df, True, f"File loaded with {encoding} encoding"
                except Exception as e:
                    if self.debug:
                        print(f"Failed with comma separator: {str(e)}")
                    
                    # Try with semicolon separator
                    try:
                        csv_io.seek(0)  # Reset stream position
                        df = pd.read_csv(csv_io, sep=';')
                        if self.debug:
                            print(f"Successfully loaded with {encoding} encoding and semicolon separator")
                        return df, True, f"File loaded with {encoding} encoding and semicolon separator"
                    except Exception as e:
                        if self.debug:
                            print(f"Failed with semicolon separator: {str(e)}")
                        return None, False, f"Failed to parse CSV: {str(e)}"
                        
            except Exception as e:
                return None, False, f"Error loading file: {str(e)}"
                
        def save_data(self, df: pd.DataFrame, file_path: Path) -> Tuple[bool, str]:
            """Save data to a CSV file."""
            try:
                # Ensure directory exists
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Save with UTF-8 encoding to preserve special characters
                df.to_csv(file_path, index=False, encoding='utf-8')
                return True, f"Data saved to {file_path}"
            except Exception as e:
                return False, f"Error saving data: {str(e)}"
    ```

- [ ] **Implement Encoding Detector Utility**
  - [ ] **Create EncodingDetector class**
    ```python
    # src/utils/encoding_detector.py
    from typing import List, Dict, Any, Tuple, Optional
    import chardet
    import ftfy
    from charset_normalizer import detect
    import unicodedata
    
    class EncodingDetector:
        """Advanced encoding detection and text fixing."""
        
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
                    score = cls._score_encoding_quality(text, language_hint)
                    
                    if score > best_score:
                        best_score = score
                        best_text = text
                        best_encoding = encoding
                except UnicodeDecodeError:
                    continue
                    
            # If no encoding worked, fall back to replacement
            if not best_encoding:
                best_text = data.decode(encodings[0], errors='replace')
                best_encoding = f"{encodings[0]} (with errors)"
                
            # Fix any remaining issues
            best_text = cls.fix_text(best_text, language_hint)
            
            return best_text, best_encoding
            
        @staticmethod
        def _score_encoding_quality(text: str, language_hint: Optional[str] = None) -> int:
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
                mojibake_patterns = sum(
                    text.count(pattern) for pattern 
                    in EncodingDetector.GERMAN_MOJIBAKE_PATTERNS.keys()
                )
                score -= mojibake_patterns * 5
                
            return score
    ```

### 4. Data Manager Implementation

- [ ] **Create Data Transformation Service**
  - [ ] **Implement DataTransformer class**
    ```python
    # src/core/data/transform/data_transformer.py
    import pandas as pd
    from typing import List, Callable, Dict, Any
    
    class DataTransformer:
        """A class to apply a sequence of transformations to data."""
        
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

  - [ ] **Implement standard transformations**
    ```python
    # src/core/data/transform/standard_transformations.py
    import pandas as pd
    from datetime import datetime
    
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
        
    def drop_na_values(df: pd.DataFrame) -> pd.DataFrame:
        """Drop rows with NA values in required columns."""
        required_columns = ['DATE', 'PLAYER', 'SOURCE', 'CHEST', 'SCORE']
        columns_to_check = [col for col in required_columns if col in df.columns]
        return df.dropna(subset=columns_to_check)
        
    def fix_text_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Fix encoding issues in text columns."""
        from utils.encoding_detector import EncodingDetector
        
        text_columns = df.select_dtypes(include=['object']).columns
        
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].astype(str)
                df[col] = df[col].apply(lambda x: EncodingDetector.fix_text(x, 'german'))
                
        return df
    ```

- [ ] **Implement DataAnalysisService**
  - [ ] **Create DataAnalysisService class**
    ```python
    # src/core/analysis/data_analysis_service.py
    import pandas as pd
    from typing import Dict, List, Any, Optional
    
    class DataAnalysisService:
        """Service for data analysis operations."""
        
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
                    import traceback
                    traceback.print_exc()
                return {}
                
        def filter_data(
            self, 
            df: pd.DataFrame, 
            column: str, 
            values: List[str],
            date_range: Optional[tuple] = None
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

- [ ] **Create DataCache class**
  - [ ] **Implement DataCache**
    ```python
    # src/core/data/cache.py
    import pandas as pd
    from typing import Dict, List, Any, Optional
    import hashlib
    import pickle
    from pathlib import Path
    import os
    import time
    
    class DataCache:
        """Cache for data processing results."""
        
        def __init__(self, cache_dir: Path):
            self.cache_dir = cache_dir
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.memory_cache = {}
            self.max_memory_entries = 100
            self.max_disk_entries = 50
            self.cleanup_interval = 3600  # 1 hour
            self.last_cleanup = 0
            
        def get_cache_key(self, data_id: str, params: Dict[str, Any]) -> str:
            """Generate a unique cache key based on data ID and parameters."""
            param_str = str(sorted(params.items()))
            combined = f"{data_id}:{param_str}".encode('utf-8')
            return hashlib.md5(combined).hexdigest()
            
        def get(self, data_id: str, params: Dict[str, Any]) -> Optional[Any]:
            """Get cached data if available."""
            # Check cleanup
            if time.time() - self.last_cleanup > self.cleanup_interval:
                self._cleanup()
                
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
            
            # Limit memory cache size
            if len(self.memory_cache) > self.max_memory_entries:
                # Remove oldest entries (assuming Python 3.7+ which preserves insertion order)
                items = list(self.memory_cache.items())
                self.memory_cache = dict(items[-self.max_memory_entries:])
            
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
                    try:
                        os.unlink(cache_file)
                    except OSError:
                        pass
            else:
                # Clear cache for specific data ID
                keys_to_remove = [k for k in self.memory_cache if k.startswith(data_id)]
                for key in keys_to_remove:
                    del self.memory_cache[key]
                    
                pattern = f"{self.get_cache_key(data_id, {})[0:8]}*"
                for cache_file in self.cache_dir.glob(pattern):
                    try:
                        os.unlink(cache_file)
                    except OSError:
                        pass
                        
        def _cleanup(self) -> None:
            """Clean up old cache files."""
            # Update cleanup timestamp
            self.last_cleanup = time.time()
            
            # Get all cache files
            cache_files = list(self.cache_dir.glob("*.pkl"))
            
            # Keep only the newest max_disk_entries
            if len(cache_files) > self.max_disk_entries:
                # Sort by modification time (newest first)
                cache_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                # Delete oldest files
                for old_file in cache_files[self.max_disk_entries:]:
                    try:
                        os.unlink(old_file)
                    except OSError:
                        pass
    ```

- [ ] **Create Central DataManager**
  - [ ] **Implement DataManager class**
    ```python
    # src/core/data/data_manager.py
    import pandas as pd
    from typing import Dict, List, Any, Optional, Tuple, Union
    from pathlib import Path
    
    from core.data.access.data_access import DataAccess
    from core.data.access.csv_data_access import CSVDataAccess
    from core.data.transform.data_transformer import DataTransformer
    from core.data.transform.standard_transformations import (
        clean_column_names, convert_date_column, 
        convert_numeric_columns, drop_na_values, fix_text_columns
    )
    from core.analysis.data_analysis_service import DataAnalysisService
    from core.data.models.dataset_model import DatasetModel
    from core.data.cache import DataCache
    from utils.path_utils import PathUtils
    
    class DataManager:
        """Manages application data operations."""
        
        def __init__(
            self, 
            data_access: Optional[DataAccess] = None,
            analysis_service: Optional[DataAnalysisService] = None,
            cache_dir: Optional[Union[str, Path]] = None,
            debug: bool = False
        ):
            self.debug = debug
            
            # Initialize components
            self.data_access = data_access or CSVDataAccess(debug=debug)
            self.analysis_service = analysis_service or DataAnalysisService(debug=debug)
            
            # Initialize data transformer
            self.transformer = DataTransformer()
            self.transformer.add_transformation("Clean Column Names", clean_column_names)
            self.transformer.add_transformation("Convert Dates", convert_date_column)
            self.transformer.add_transformation("Convert Numerics", convert_numeric_columns)
            self.transformer.add_transformation("Drop NA Values", drop_na_values)
            self.transformer.add_transformation("Fix Text Columns", fix_text_columns)
            
            # Initialize cache
            cache_path = Path(cache_dir) if cache_dir else Path.home() / ".totalbattle" / "cache"
            self.cache = DataCache(cache_path)
            
            # Initialize data storage
            self.raw_data = None
            self.processed_data = None
            self.dataset_model = None
            self.analysis_results = {}
            self.current_file_path = None
            
        def load_file(self, file_path: Union[str, Path]) -> Tuple[bool, str]:
            """
            Load a file and process the data.
            
            Args:
                file_path: Path to the file
                
            Returns:
                Tuple of (success, message)
            """
            # Ensure file_path is a Path object
            file_path = PathUtils.ensure_path(file_path)
            
            if self.debug:
                print(f"Loading file: {file_path}")
                
            try:
                # Use data access to load file
                df, success, message = self.data_access.load_data(file_path)
                
                if not success:
                    return False, message
                    
                # Store raw data
                self.raw_data = df
                
                # Process the data
                self.processed_data = self.process_data(df)
                
                # Create dataset model
                self.dataset_model = DatasetModel.from_dataframe(self.processed_data)
                
                # Store file path
                self.current_file_path = file_path
                
                # Analyze the data
                self.analyze_data()
                
                return True, "File loaded successfully"
                
            except Exception as e:
                if self.debug:
                    print(f"Error loading file: {str(e)}")
                    import traceback
                    traceback.print_exc()
                return False, f"Error loading file: {str(e)}"
                
        def process_data(self, df: pd.DataFrame) -> pd.DataFrame:
            """
            Process data through transformation pipeline.
            
            Args:
                df: DataFrame to process
                
            Returns:
                Processed DataFrame
            """
            if df is None or df.empty:
                return pd.DataFrame()
                
            try:
                # Apply transformations
                processed_df = self.transformer.apply(df)
                
                return processed_df
                
            except Exception as e:
                if self.debug:
                    print(f"Error processing data: {str(e)}")
                    import traceback
                    traceback.print_exc()
                # Return original data on error
                return df.copy()
                
        def analyze_data(self) -> Dict[str, Any]:
            """
            Analyze the processed data.
            
            Returns:
                Dictionary of analysis results
            """
            if self.processed_data is None or self.processed_data.empty:
                return {}
                
            # Check if we have cached results
            cache_key = {
                "data_hash": hash(str(self.processed_data.values.tobytes())),
                "columns": ','.join(self.processed_data.columns)
            }
            
            cached_results = self.cache.get("analysis", cache_key)
            if cached_results is not None:
                self.analysis_results = cached_results
                return cached_results
                
            # Perform analysis
            results = self.analysis_service.analyze_data(self.processed_data)
            
            # Cache the results
            if results:
                self.cache.set("analysis", cache_key, results)
                
            # Store results
            self.analysis_results = results
                
            return results
            
        def get_raw_data(self) -> Optional[pd.DataFrame]:
            """Get the raw data."""
            return self.raw_data.copy() if self.raw_data is not None else None
            
        def get_processed_data(self) -> Optional[pd.DataFrame]:
            """Get the processed data."""
            return self.processed_data.copy() if self.processed_data is not None else None
            
        def filter_raw_data(self, column: str, values: List[str]) -> pd.DataFrame:
            """
            Filter raw data based on column and values.
            
            Args:
                column: Column to filter on
                values: Values to include
                
            Returns:
                Filtered DataFrame
            """
            if self.raw_data is None:
                return pd.DataFrame()
                
            # Apply filter
            filtered_data = self.analysis_service.filter_data(self.raw_data, column, values)
            
            # Update processed data
            self.processed_data = filtered_data
            
            # Update dataset model
            self.dataset_model = DatasetModel.from_dataframe(filtered_data)
            
            # Rerun analysis
            self.analyze_data()
            
            return filtered_data
            
        def clear_raw_data_filters(self) -> None:
            """Clear filters and reset to original raw data."""
            if self.raw_data is None:
                return
                
            # Reset processed data to raw data
            self.processed_data = self.raw_data.copy()
            
            # Reset dataset model
            self.dataset_model = DatasetModel.from_dataframe(self.processed_data)
            
            # Rerun analysis
            self.analyze_data()
            
        def export_data(
            self, 
            df: pd.DataFrame, 
            file_path: Union[str, Path],
            format_type: str = "csv"
        ) -> Tuple[bool, str]:
            """
            Export data to a file.
            
            Args:
                df: DataFrame to export
                file_path: Path to export to
                format_type: Export format type
                
            Returns:
                Tuple of (success, message)
            """
            file_path = PathUtils.ensure_path(file_path)
            
            if format_type.lower() == "csv":
                return self.data_access.save_data(df, file_path)
            else:
                return False, f"Unsupported format: {format_type}"
                
        def cleanup(self) -> None:
            """Clean up resources."""
            # Clear cache
            self.cache.clear()
    ```

### 5. Testing Data Layer Implementation

- [ ] **Create test data**
  - [ ] Prepare a small sample CSV file for testing

- [ ] **Create simple data layer test script**
  - [ ] **Create test_data_layer.py**
    ```python
    # src/tests/test_data_layer.py
    import sys
    import os
    from pathlib import Path
    
    # Add the src directory to the Python path
    src_dir = Path(__file__).parent.parent
    sys.path.append(str(src_dir))
    
    from core.data.data_manager import DataManager
    from core.data.access.csv_data_access import CSVDataAccess
    from core.analysis.data_analysis_service import DataAnalysisService
    
    def test_data_loading():
        """Test data loading functionality."""
        print("Testing data loading...")
        
        # Create a DataManager with debug mode
        data_manager = DataManager(debug=True)
        
        # Path to a sample CSV file
        sample_file = src_dir / "data" / "sample.csv"
        if not sample_file.exists():
            print(f"Sample file not found: {sample_file}")
            return False
        
        # Load the sample file
        success, message = data_manager.load_file(sample_file)
        
        print(f"Load result: {success}, Message: {message}")
        
        if not success:
            return False
            
        # Check if we have raw data
        raw_data = data_manager.get_raw_data()
        print(f"Raw data loaded: {raw_data is not None}")
        
        if raw_data is not None:
            print(f"Raw data shape: {raw_data.shape}")
            print(f"Raw data columns: {raw_data.columns.tolist()}")
            
        # Check if we have processed data
        processed_data = data_manager.get_processed_data()
        print(f"Processed data: {processed_data is not None}")
        
        if processed_data is not None:
            print(f"Processed data shape: {processed_data.shape}")
            
        # Check if analysis results are available
        analysis_results = data_manager.analysis_results
        print(f"Analysis results: {bool(analysis_results)}")
        
        if analysis_results:
            print(f"Analysis result keys: {list(analysis_results.keys())}")
            
        return True
        
    def test_data_filtering():
        """Test data filtering functionality."""
        print("\nTesting data filtering...")
        
        # Create a DataManager with debug mode
        data_manager = DataManager(debug=True)
        
        # Path to a sample CSV file
        sample_file = src_dir / "data" / "sample.csv"
        success, message = data_manager.load_file(sample_file)
        
        if not success:
            print(f"Failed to load file: {message}")
            return False
            
        # Get raw data
        raw_data = data_manager.get_raw_data()
        
        if raw_data is None:
            print("No raw data available")
            return False
            
        # Get a sample column and value
        column = "PLAYER"
        all_values = raw_data[column].unique().tolist()
        
        if not all_values:
            print(f"No values found in column {column}")
            return False
            
        # Filter on a single value
        test_value = all_values[0]
        print(f"Filtering on {column} = {test_value}")
        
        filtered_data = data_manager.filter_raw_data(column, [test_value])
        
        print(f"Original data shape: {raw_data.shape}")
        print(f"Filtered data shape: {filtered_data.shape}")
        
        # Check if filtered correctly
        if not filtered_data.empty:
            filtered_values = filtered_data[column].unique().tolist()
            print(f"Filtered values: {filtered_values}")
            
            if test_value not in filtered_values:
                print(f"Filter failed: {test_value} not in filtered values")
                return False
                
        # Clear filters
        data_manager.clear_raw_data_filters()
        
        # Check if filters were cleared
        unfiltered_data = data_manager.get_processed_data()
        print(f"Unfiltered data shape: {unfiltered_data.shape}")
        
        if unfiltered_data.shape != raw_data.shape:
            print("Filter clearing failed")
            return False
            
        return True
        
    def run_tests():
        """Run all tests."""
        tests = [
            test_data_loading,
            test_data_filtering
        ]
        
        success_count = 0
        
        for test in tests:
            if test():
                success_count += 1
                print(f"{test.__name__} passed!")
            else:
                print(f"{test.__name__} failed!")
                
        print(f"\n{success_count}/{len(tests)} tests passed.")
        
    if __name__ == "__main__":
        run_tests()
    ```

- [ ] **Run tests and validate implementation**
  - [ ] Execute the test script
  - [ ] Fix any issues found

### 6. Phase 2 Documentation

- [ ] **Create Data Layer Architecture Document**
  - [ ] **Create data_layer.md**
    ```markdown
    # Total Battle Analyzer - Data Layer Architecture
    
    This document describes the data layer architecture for the Total Battle Analyzer application.
    
    ## Overview
    
    The data layer is responsible for managing application data, including:
    - Reading and writing data files
    - Data validation and transformation
    - Data models and representations
    - Data analysis and filtering
    - Caching for performance optimization
    
    ## Components
    
    ### Data Models
    
    The application uses the following data models:
    
    - **ChestRecord**: Core model representing a single chest record
    - **PlayerSummary**: Summary model for player performance
    - **ChestSummary**: Summary model for chest performance
    - **SourceSummary**: Summary model for source performance
    - **DatasetModel**: Collection of ChestRecord objects with filtering capabilities
    
    ### Data Access
    
    Data access is handled through the following components:
    
    - **DataAccess**: Interface for data access operations
    - **CSVDataAccess**: Implementation for CSV file access
    - **EncodingDetector**: Utility for detecting and fixing text encoding issues
    
    ### Data Transformation
    
    Data transformation is managed through:
    
    - **DataTransformer**: Pipeline for applying data transformations
    - **Standard Transformations**: Common transformations like cleaning column names
    
    ### Data Analysis
    
    Data analysis is performed by:
    
    - **DataAnalysisService**: Service for analyzing data and creating summaries
    
    ### Data Management
    
    Overall data management is coordinated by:
    
    - **DataManager**: Central manager for all data operations
    - **DataCache**: Caching mechanism for expensive operations
    
    ## Data Flow
    
    1. The user selects a CSV file to load
    2. DataManager uses CSVDataAccess to load the file
    3. The raw data is transformed using DataTransformer
    4. The processed data is converted to a DatasetModel
    5. The data is analyzed using DataAnalysisService
    6. Analysis results are cached for future use
    7. User interactions like filtering update the processed data
    
    ## Key Design Decisions
    
    - **Separation of Concerns**: Each component has a single responsibility
    - **Interface-based Design**: Components interact through well-defined interfaces
    - **Data Immutability**: Original data is preserved while working with copies
    - **Caching**: Expensive operations are cached for performance
    - **Robust Error Handling**: All data operations include error handling
    - **Encoding Robustness**: Special attention to handling text encoding issues
    ```

- [ ] **Update Core Data Classes Documentation**
  - [ ] Ensure all classes have proper docstrings
  - [ ] Add examples where appropriate
  - [ ] Document public interfaces thoroughly

### 7. Phase 2 Validation

- [ ] **Review implementation against requirements**
  - [ ] Verify all data models are implemented
  - [ ] Check that the data access layer works correctly
  - [ ] Ensure the data manager provides all required functionality

- [ ] **Test with existing application data**
  - [ ] Load actual application data files
  - [ ] Verify data is processed correctly
  - [ ] Compare analysis results with original application

- [ ] **Document current state**
  - [ ] Create a summary of what has been accomplished
  - [ ] List any deviations from the plan and their justifications
  - [ ] Identify any issues that need addressing in Phase 3

## Next Steps

After completing Phase 2, we will:
1. Gather feedback on the implementation
2. Address any issues or concerns
3. Proceed to Phase 3
