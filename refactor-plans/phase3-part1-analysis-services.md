# Total Battle Analyzer Refactoring Plan: Phase 3 - Part 1
## Core Analysis Services

This document details the implementation of core analysis services for the Total Battle Analyzer application as part of Phase 3 refactoring.

### 1. Setup and Preparation

- [ ] **Directory Structure Verification**
  - [ ] Ensure the `src/core/services` directory exists
  - [ ] Create it if missing:
    ```bash
    mkdir -p src/core/services
    ```
  - [ ] Create the `__init__.py` file in the services directory:
    ```bash
    touch src/core/services/__init__.py
    ```

- [ ] **Integration Planning**
  - [ ] Review the data layer from Phase 2 to understand integration points
  - [ ] Identify which data layer components will be used by analysis services
  - [ ] Document any dependencies or potential issues

### 2. Analysis Service Interface

- [ ] **Define Analysis Service Interface**
  - [ ] Create `src/core/services/analysis_service.py` with the following content:
    ```python
    # src/core/services/analysis_service.py
    from abc import ABC, abstractmethod
    import pandas as pd
    from typing import Dict, Any, Optional, List

    class AnalysisService(ABC):
        """Interface for analysis services."""
        
        @abstractmethod
        def analyze_player_performance(self, data: pd.DataFrame) -> Dict[str, Any]:
            """
            Analyze player performance.
            
            Args:
                data: DataFrame containing the data to analyze
                
            Returns:
                Dictionary of analysis results
            """
            pass
            
        @abstractmethod
        def analyze_chest_distribution(self, data: pd.DataFrame) -> Dict[str, Any]:
            """
            Analyze chest distribution.
            
            Args:
                data: DataFrame containing the data to analyze
                
            Returns:
                Dictionary of analysis results
            """
            pass
            
        @abstractmethod
        def analyze_source_effectiveness(self, data: pd.DataFrame) -> Dict[str, Any]:
            """
            Analyze source effectiveness.
            
            Args:
                data: DataFrame containing the data to analyze
                
            Returns:
                Dictionary of analysis results
            """
            pass
            
        @abstractmethod
        def analyze_time_trends(self, data: pd.DataFrame) -> Dict[str, Any]:
            """
            Analyze time trends.
            
            Args:
                data: DataFrame containing the data to analyze
                
            Returns:
                Dictionary of analysis results
            """
            pass
            
        @abstractmethod
        def get_overview_statistics(self, data: pd.DataFrame) -> Dict[str, Any]:
            """
            Get overview statistics.
            
            Args:
                data: DataFrame containing the data to analyze
                
            Returns:
                Dictionary of overview statistics
            """
            pass
    ```

- [ ] **Test the Interface with Simple Implementation**
  - [ ] Create a simple test implementation to verify the interface
  - [ ] Ensure all methods are properly defined with correct signatures

### 3. Player Analysis Service

- [ ] **Create Player Analysis Service Implementation**
  - [ ] Create `src/core/services/player_analysis_service.py` with the following content:
    ```python
    # src/core/services/player_analysis_service.py
    import pandas as pd
    import numpy as np
    from typing import Dict, Any, Optional, List
    from .analysis_service import AnalysisService

    class PlayerAnalysisService(AnalysisService):
        """Service for player performance analysis."""
        
        def __init__(self, debug: bool = False):
            self.debug = debug
            
        def analyze_player_performance(self, data: pd.DataFrame) -> Dict[str, Any]:
            """Analyze player performance."""
            if data is None or data.empty:
                return {}
                
            try:
                # Calculate player totals
                player_totals = data.groupby('PLAYER')['SCORE'].sum().reset_index()
                player_totals = player_totals.sort_values('SCORE', ascending=False)
                
                # Add chest counts
                player_counts = data.groupby('PLAYER').size().reset_index(name='CHEST_COUNT')
                player_totals = player_totals.merge(player_counts, on='PLAYER', how='left')
                
                # Calculate efficiency (score per chest)
                player_totals['EFFICIENCY'] = player_totals['SCORE'] / player_totals['CHEST_COUNT']
                
                # Get top and bottom performers
                top_performers = player_totals.head(5)
                bottom_performers = player_totals.tail(5)
                
                # Calculate average score per player
                avg_score = player_totals['SCORE'].mean()
                median_score = player_totals['SCORE'].median()
                
                # Calculate score distribution statistics
                score_std = player_totals['SCORE'].std()
                score_min = player_totals['SCORE'].min()
                score_max = player_totals['SCORE'].max()
                score_quartiles = player_totals['SCORE'].quantile([0.25, 0.5, 0.75]).to_dict()
                
                # Return comprehensive analysis results
                return {
                    'player_totals': player_totals,
                    'top_performers': top_performers,
                    'bottom_performers': bottom_performers,
                    'statistics': {
                        'avg_score': avg_score,
                        'median_score': median_score,
                        'score_std': score_std,
                        'score_min': score_min,
                        'score_max': score_max,
                        'score_quartiles': score_quartiles,
                        'total_players': len(player_totals)
                    }
                }
                
            except Exception as e:
                if self.debug:
                    print(f"Error in player performance analysis: {str(e)}")
                    import traceback
                    traceback.print_exc()
                return {}
                
        def analyze_chest_distribution(self, data: pd.DataFrame) -> Dict[str, Any]:
            """Analyze chest distribution by player."""
            if data is None or data.empty:
                return {}
                
            try:
                # Get chest distribution by player
                chest_distribution = pd.crosstab(
                    data['PLAYER'], 
                    data['CHEST'], 
                    values=data['SCORE'], 
                    aggfunc='sum',
                    margins=True,
                    normalize='index'
                ).reset_index()
                
                # Find most common chest type per player
                player_chest_preferences = data.groupby(['PLAYER', 'CHEST']).size().reset_index(name='COUNT')
                player_chest_preferences = player_chest_preferences.sort_values(['PLAYER', 'COUNT'], ascending=[True, False])
                
                # Get most frequent chest for each player
                most_frequent_chest = player_chest_preferences.groupby('PLAYER').first().reset_index()
                
                return {
                    'chest_distribution': chest_distribution,
                    'most_frequent_chest': most_frequent_chest
                }
                
            except Exception as e:
                if self.debug:
                    print(f"Error in chest distribution analysis: {str(e)}")
                    import traceback
                    traceback.print_exc()
                return {}
                
        def analyze_source_effectiveness(self, data: pd.DataFrame) -> Dict[str, Any]:
            """Analyze source effectiveness by player."""
            if data is None or data.empty:
                return {}
                
            try:
                # Calculate effectiveness by source for each player
                player_source_stats = data.groupby(['PLAYER', 'SOURCE']).agg({
                    'SCORE': ['sum', 'mean', 'count']
                }).reset_index()
                
                # Flatten the multi-level columns
                player_source_stats.columns = ['PLAYER', 'SOURCE', 'TOTAL_SCORE', 'AVG_SCORE', 'COUNT']
                
                # Determine most effective source for each player
                most_effective_source = player_source_stats.sort_values(['PLAYER', 'AVG_SCORE'], ascending=[True, False])
                most_effective_source = most_effective_source.groupby('PLAYER').first().reset_index()
                
                return {
                    'player_source_stats': player_source_stats,
                    'most_effective_source': most_effective_source
                }
                
            except Exception as e:
                if self.debug:
                    print(f"Error in source effectiveness analysis: {str(e)}")
                    import traceback
                    traceback.print_exc()
                return {}
                
        def analyze_time_trends(self, data: pd.DataFrame) -> Dict[str, Any]:
            """Analyze time trends for players."""
            if data is None or data.empty or 'DATE' not in data.columns:
                return {}
                
            try:
                # Ensure DATE is datetime
                if not pd.api.types.is_datetime64_any_dtype(data['DATE']):
                    data = data.copy()
                    data['DATE'] = pd.to_datetime(data['DATE'], errors='coerce')
                    
                # Drop rows with invalid dates
                data = data.dropna(subset=['DATE'])
                
                # Extract time components
                data = data.copy()
                data['MONTH'] = data['DATE'].dt.month
                data['YEAR'] = data['DATE'].dt.year
                data['DAY'] = data['DATE'].dt.day
                
                # Calculate monthly trends per player
                monthly_trends = data.groupby(['PLAYER', 'YEAR', 'MONTH']).agg({
                    'SCORE': ['sum', 'count']
                }).reset_index()
                
                # Flatten the multi-level columns
                monthly_trends.columns = ['PLAYER', 'YEAR', 'MONTH', 'TOTAL_SCORE', 'CHEST_COUNT']
                
                # Calculate daily average per player
                daily_avg = data.groupby(['PLAYER', 'DATE']).agg({
                    'SCORE': ['sum', 'count']
                }).reset_index()
                
                # Flatten the multi-level columns
                daily_avg.columns = ['PLAYER', 'DATE', 'DAILY_SCORE', 'CHEST_COUNT']
                
                return {
                    'monthly_trends': monthly_trends,
                    'daily_avg': daily_avg
                }
                
            except Exception as e:
                if self.debug:
                    print(f"Error in time trends analysis: {str(e)}")
                    import traceback
                    traceback.print_exc()
                return {}
                
        def get_overview_statistics(self, data: pd.DataFrame) -> Dict[str, Any]:
            """Get overview statistics."""
            if data is None or data.empty:
                return {}
                
            try:
                # Get basic statistics
                total_score = data['SCORE'].sum()
                total_chests = len(data)
                avg_chest_score = data['SCORE'].mean()
                
                # Get unique player, chest, and source counts
                unique_players = data['PLAYER'].nunique()
                unique_chests = data['CHEST'].nunique()
                unique_sources = data['SOURCE'].nunique()
                
                # Get date range if available
                date_range = None
                if 'DATE' in data.columns:
                    if not pd.api.types.is_datetime64_any_dtype(data['DATE']):
                        data = data.copy()
                        data['DATE'] = pd.to_datetime(data['DATE'], errors='coerce')
                    
                    min_date = data['DATE'].min()
                    max_date = data['DATE'].max()
                    
                    if pd.notna(min_date) and pd.notna(max_date):
                        date_range = {
                            'min_date': min_date.strftime('%Y-%m-%d'),
                            'max_date': max_date.strftime('%Y-%m-%d'),
                            'days': (max_date - min_date).days
                        }
                
                return {
                    'total_score': total_score,
                    'total_chests': total_chests,
                    'avg_chest_score': avg_chest_score,
                    'unique_players': unique_players,
                    'unique_chests': unique_chests,
                    'unique_sources': unique_sources,
                    'date_range': date_range
                }
                
            except Exception as e:
                if self.debug:
                    print(f"Error in overview statistics: {str(e)}")
                    import traceback
                    traceback.print_exc()
                return {}
    ```

- [ ] **Test the Player Analysis Service**
  - [ ] Create a simple test script to verify functionality
  - [ ] Test with sample data to ensure correct analysis results

### 4. Chest Analysis Service

- [ ] **Create Chest Analysis Service Implementation**
  - [ ] Create `src/core/services/chest_analysis_service.py` with the following content:
    ```python
    # src/core/services/chest_analysis_service.py
    import pandas as pd
    import numpy as np
    from typing import Dict, Any, Optional, List
    from .analysis_service import AnalysisService

    class ChestAnalysisService(AnalysisService):
        """Service for chest analysis."""
        
        def __init__(self, debug: bool = False):
            self.debug = debug
            
        def analyze_player_performance(self, data: pd.DataFrame) -> Dict[str, Any]:
            """Analyze player performance from chest perspective."""
            if data is None or data.empty:
                return {}
                
            try:
                # Calculate average chest value per player
                player_avg_chest = data.groupby('PLAYER')['SCORE'].mean().reset_index()
                player_avg_chest = player_avg_chest.sort_values('SCORE', ascending=False)
                
                # Get player distribution by chest type
                player_chest_distribution = pd.crosstab(
                    data['CHEST'],
                    data['PLAYER'],
                    values=data['SCORE'],
                    aggfunc='sum',
                    normalize='index'
                ).reset_index()
                
                return {
                    'player_avg_chest': player_avg_chest,
                    'player_chest_distribution': player_chest_distribution
                }
                
            except Exception as e:
                if self.debug:
                    print(f"Error in player performance analysis: {str(e)}")
                    import traceback
                    traceback.print_exc()
                return {}
                
        def analyze_chest_distribution(self, data: pd.DataFrame) -> Dict[str, Any]:
            """Analyze chest distribution."""
            if data is None or data.empty:
                return {}
                
            try:
                # Calculate chest counts and total scores
                chest_stats = data.groupby('CHEST').agg({
                    'SCORE': ['sum', 'mean', 'std', 'count']
                }).reset_index()
                
                # Flatten multi-level columns
                chest_stats.columns = ['CHEST', 'TOTAL_SCORE', 'AVG_SCORE', 'STD_SCORE', 'COUNT']
                
                # Sort by total score
                chest_stats = chest_stats.sort_values('TOTAL_SCORE', ascending=False)
                
                # Calculate chest rarity (less common = more rare)
                total_chests = len(data)
                chest_stats['RARITY'] = 1 - (chest_stats['COUNT'] / total_chests)
                
                # Calculate chest value (average score)
                chest_stats['VALUE'] = chest_stats['AVG_SCORE']
                
                # Calculate chest consistency (lower std deviation = more consistent)
                chest_stats['CONSISTENCY'] = 1 - (chest_stats['STD_SCORE'] / chest_stats['AVG_SCORE'].replace(0, 1))
                chest_stats['CONSISTENCY'] = chest_stats['CONSISTENCY'].clip(0, 1)  # Ensure between 0 and 1
                
                # Calculate chest efficiency (value / rarity)
                chest_stats['EFFICIENCY'] = chest_stats['VALUE'] / (chest_stats['RARITY'] + 0.1)  # Add 0.1 to avoid division by zero
                
                return {
                    'chest_stats': chest_stats,
                    'top_chests_by_score': chest_stats.head(5),
                    'top_chests_by_value': chest_stats.sort_values('AVG_SCORE', ascending=False).head(5),
                    'top_chests_by_consistency': chest_stats.sort_values('CONSISTENCY', ascending=False).head(5),
                    'top_chests_by_efficiency': chest_stats.sort_values('EFFICIENCY', ascending=False).head(5)
                }
                
            except Exception as e:
                if self.debug:
                    print(f"Error in chest distribution analysis: {str(e)}")
                    import traceback
                    traceback.print_exc()
                return {}
                
        def analyze_source_effectiveness(self, data: pd.DataFrame) -> Dict[str, Any]:
            """Analyze source effectiveness for chest types."""
            if data is None or data.empty:
                return {}
                
            try:
                # Calculate effectiveness by source for each chest type
                chest_source_stats = data.groupby(['CHEST', 'SOURCE']).agg({
                    'SCORE': ['sum', 'mean', 'count']
                }).reset_index()
                
                # Flatten the multi-level columns
                chest_source_stats.columns = ['CHEST', 'SOURCE', 'TOTAL_SCORE', 'AVG_SCORE', 'COUNT']
                
                # Determine best source for each chest type
                best_source_per_chest = chest_source_stats.sort_values(['CHEST', 'AVG_SCORE'], ascending=[True, False])
                best_source_per_chest = best_source_per_chest.groupby('CHEST').first().reset_index()
                
                return {
                    'chest_source_stats': chest_source_stats,
                    'best_source_per_chest': best_source_per_chest
                }
                
            except Exception as e:
                if self.debug:
                    print(f"Error in source effectiveness analysis: {str(e)}")
                    import traceback
                    traceback.print_exc()
                return {}
                
        def analyze_time_trends(self, data: pd.DataFrame) -> Dict[str, Any]:
            """Analyze time trends for chest types."""
            if data is None or data.empty or 'DATE' not in data.columns:
                return {}
                
            try:
                # Ensure DATE is datetime
                if not pd.api.types.is_datetime64_any_dtype(data['DATE']):
                    data = data.copy()
                    data['DATE'] = pd.to_datetime(data['DATE'], errors='coerce')
                    
                # Drop rows with invalid dates
                data = data.dropna(subset=['DATE'])
                
                # Extract time components
                data = data.copy()
                data['MONTH'] = data['DATE'].dt.month
                data['YEAR'] = data['DATE'].dt.year
                
                # Calculate monthly trends per chest type
                monthly_trends = data.groupby(['CHEST', 'YEAR', 'MONTH']).agg({
                    'SCORE': ['sum', 'mean', 'count']
                }).reset_index()
                
                # Flatten the multi-level columns
                monthly_trends.columns = ['CHEST', 'YEAR', 'MONTH', 'TOTAL_SCORE', 'AVG_SCORE', 'COUNT']
                
                # Get most frequent chest type by month
                chest_frequency_by_month = data.groupby(['YEAR', 'MONTH', 'CHEST']).size().reset_index(name='COUNT')
                chest_frequency_by_month = chest_frequency_by_month.sort_values(['YEAR', 'MONTH', 'COUNT'], ascending=[True, True, False])
                most_frequent_by_month = chest_frequency_by_month.groupby(['YEAR', 'MONTH']).first().reset_index()
                
                return {
                    'monthly_trends': monthly_trends,
                    'most_frequent_by_month': most_frequent_by_month
                }
                
            except Exception as e:
                if self.debug:
                    print(f"Error in time trends analysis: {str(e)}")
                    import traceback
                    traceback.print_exc()
                return {}
                
        def get_overview_statistics(self, data: pd.DataFrame) -> Dict[str, Any]:
            """Get overview statistics for chests."""
            if data is None or data.empty:
                return {}
                
            try:
                # Calculate basic chest statistics
                total_chests = len(data)
                unique_chest_types = data['CHEST'].nunique()
                avg_score_per_chest = data['SCORE'].mean()
                median_score_per_chest = data['SCORE'].median()
                score_std = data['SCORE'].std()
                
                # Get most common chest types
                chest_counts = data['CHEST'].value_counts().head(5).to_dict()
                
                # Get highest scoring chest types
                chest_scores = data.groupby('CHEST')['SCORE'].mean().sort_values(ascending=False).head(5).to_dict()
                
                return {
                    'total_chests': total_chests,
                    'unique_chest_types': unique_chest_types,
                    'avg_score_per_chest': avg_score_per_chest,
                    'median_score_per_chest': median_score_per_chest,
                    'score_std': score_std,
                    'most_common_chests': chest_counts,
                    'highest_scoring_chests': chest_scores
                }
                
            except Exception as e:
                if self.debug:
                    print(f"Error in overview statistics: {str(e)}")
                    import traceback
                    traceback.print_exc()
                return {}
    ```

- [ ] **Test the Chest Analysis Service**
  - [ ] Create a simple test script to verify functionality
  - [ ] Test with sample data to ensure correct analysis results

### 5. Source Analysis Service

- [ ] **Create Source Analysis Service Implementation**
  - [ ] Create `src/core/services/source_analysis_service.py`
  - [ ] Implement the `SourceAnalysisService` class with methods for analyzing sources
  - [ ] Add robust error handling and debugging output

- [ ] **Test the Source Analysis Service**
  - [ ] Create a simple test script to verify functionality
  - [ ] Test with sample data to ensure correct analysis results

### 6. Analysis Manager

- [ ] **Create Analysis Manager Implementation**
  - [ ] Create `src/core/services/analysis_manager.py`
  - [ ] Implement the `AnalysisManager` class to coordinate analysis services
  - [ ] Add caching capabilities for analysis results
  - [ ] Implement methods for different types of analysis

- [ ] **Test the Analysis Manager**
  - [ ] Create a simple test script to verify functionality
  - [ ] Test with sample data to ensure correct coordination of services

### 7. Integration with Data Layer

- [ ] **Create Integration Tests**
  - [ ] Create tests that use the data layer to load data
  - [ ] Pass the loaded data to analysis services
  - [ ] Verify that the integration works correctly

- [ ] **Optimize Performance**
  - [ ] Profile analysis performance with large datasets
  - [ ] Implement optimizations for slow operations
  - [ ] Test optimizations to ensure they improve performance

### 8. Documentation

- [ ] **Update Analysis Service Documentation**
  - [ ] Add detailed docstrings to all classes and methods
  - [ ] Create examples for common analysis tasks
  - [ ] Document error handling and debugging procedures

- [ ] **Create Analysis Service Guide**
  - [ ] Create a guide for using the analysis services
  - [ ] Include examples of common analysis scenarios
  - [ ] Add troubleshooting section for common issues

### 9. Part 1 Validation

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

After completing Part 1 of Phase 3, please provide feedback on the following aspects:

1. Are the analysis services comprehensive enough for your needs?
2. Are there any additional analysis methods that should be included?
3. Is the error handling approach sufficient for production use?
4. Does the implementation align with the overall refactoring goals?
5. Any suggestions for improvements before proceeding to Part 2? 