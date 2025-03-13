# Total Battle Analyzer Refactoring Plan: Phase 3

## Services Implementation

This phase focuses on implementing the service layer of the application, which will separate business logic from the UI and data layers. The service layer will handle analysis, chart generation, reporting, and other operations that transform data for presentation.

### 1. Phase Setup

- [ ] **Branch Management**
  - [ ] Create a new branch `refactoring-phase3` from the completed Phase 2 branch
  - [ ] Ensure all Phase 2 tasks were completed successfully
  - [ ] Pull latest changes if working in a team environment

- [ ] **Project Structure Validation**
  - [ ] Run the tests from Phase 2 to ensure data layer functionality
  - [ ] Verify all required directories exist for services implementation
  - [ ] Create any missing service directories:
    ```bash
    mkdir -p src/core/services
    mkdir -p src/visualization/services
    ```

### 2. Core Service Implementation

#### 2.1. Analysis Service

- [ ] **Create AnalysisService Interface**
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

- [ ] **Create PlayerAnalysisService implementation**
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

- [ ] **Create ChestAnalysisService implementation**
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

- [ ] **Create SourceAnalysisService implementation**
  ```python
  # src/core/services/source_analysis_service.py
  import pandas as pd
  import numpy as np
  from typing import Dict, Any, Optional, List
  from .analysis_service import AnalysisService

  class SourceAnalysisService(AnalysisService):
      """Service for source analysis."""
      
      def __init__(self, debug: bool = False):
          self.debug = debug
          
      def analyze_player_performance(self, data: pd.DataFrame) -> Dict[str, Any]:
          """Analyze player performance by source."""
          if data is None or data.empty:
              return {}
              
          try:
              # Calculate player performance by source
              player_source_performance = data.groupby(['PLAYER', 'SOURCE']).agg({
                  'SCORE': ['sum', 'mean', 'count']
              }).reset_index()
              
              # Flatten multi-level columns
              player_source_performance.columns = ['PLAYER', 'SOURCE', 'TOTAL_SCORE', 'AVG_SCORE', 'COUNT']
              
              # Sort by player and total score
              player_source_performance = player_source_performance.sort_values(['PLAYER', 'TOTAL_SCORE'], ascending=[True, False])
              
              # Get most profitable source per player
              best_source_per_player = player_source_performance.groupby('PLAYER').first().reset_index()
              
              return {
                  'player_source_performance': player_source_performance,
                  'best_source_per_player': best_source_per_player
              }
              
          except Exception as e:
              if self.debug:
                  print(f"Error in player performance analysis: {str(e)}")
                  import traceback
                  traceback.print_exc()
              return {}
              
      def analyze_chest_distribution(self, data: pd.DataFrame) -> Dict[str, Any]:
          """Analyze chest distribution by source."""
          if data is None or data.empty:
              return {}
              
          try:
              # Calculate chest distribution by source
              source_chest_distribution = pd.crosstab(
                  data['SOURCE'],
                  data['CHEST'],
                  values=data['SCORE'],
                  aggfunc='sum',
                  normalize='index'
              ).reset_index()
              
              # Calculate most common chest type per source
              chest_by_source = data.groupby(['SOURCE', 'CHEST']).size().reset_index(name='COUNT')
              chest_by_source = chest_by_source.sort_values(['SOURCE', 'COUNT'], ascending=[True, False])
              common_chest_by_source = chest_by_source.groupby('SOURCE').first().reset_index()
              
              return {
                  'source_chest_distribution': source_chest_distribution,
                  'common_chest_by_source': common_chest_by_source
              }
              
          except Exception as e:
              if self.debug:
                  print(f"Error in chest distribution analysis: {str(e)}")
                  import traceback
                  traceback.print_exc()
              return {}
              
      def analyze_source_effectiveness(self, data: pd.DataFrame) -> Dict[str, Any]:
          """Analyze source effectiveness."""
          if data is None or data.empty:
              return {}
              
          try:
              # Calculate source statistics
              source_stats = data.groupby('SOURCE').agg({
                  'SCORE': ['sum', 'mean', 'std', 'count']
              }).reset_index()
              
              # Flatten multi-level columns
              source_stats.columns = ['SOURCE', 'TOTAL_SCORE', 'AVG_SCORE', 'STD_SCORE', 'COUNT']
              
              # Sort by total score
              source_stats = source_stats.sort_values('TOTAL_SCORE', ascending=False)
              
              # Calculate source efficiency (average score)
              source_stats['EFFICIENCY'] = source_stats['AVG_SCORE']
              
              # Calculate source consistency (lower std deviation = more consistent)
              source_stats['CONSISTENCY'] = 1 - (source_stats['STD_SCORE'] / source_stats['AVG_SCORE'].replace(0, 1))
              source_stats['CONSISTENCY'] = source_stats['CONSISTENCY'].clip(0, 1)  # Ensure between 0 and 1
              
              # Calculate source value (efficiency * consistency)
              source_stats['VALUE'] = source_stats['EFFICIENCY'] * source_stats['CONSISTENCY']
              
              return {
                  'source_stats': source_stats,
                  'top_sources_by_score': source_stats.head(5),
                  'top_sources_by_efficiency': source_stats.sort_values('EFFICIENCY', ascending=False).head(5),
                  'top_sources_by_consistency': source_stats.sort_values('CONSISTENCY', ascending=False).head(5),
                  'top_sources_by_value': source_stats.sort_values('VALUE', ascending=False).head(5)
              }
              
          except Exception as e:
              if self.debug:
                  print(f"Error in source effectiveness analysis: {str(e)}")
                  import traceback
                  traceback.print_exc()
              return {}
              
      def analyze_time_trends(self, data: pd.DataFrame) -> Dict[str, Any]:
          """Analyze time trends for sources."""
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
              
              # Calculate monthly trends per source
              monthly_trends = data.groupby(['SOURCE', 'YEAR', 'MONTH']).agg({
                  'SCORE': ['sum', 'mean', 'count']
              }).reset_index()
              
              # Flatten the multi-level columns
              monthly_trends.columns = ['SOURCE', 'YEAR', 'MONTH', 'TOTAL_SCORE', 'AVG_SCORE', 'COUNT']
              
              # Get most profitable source by month
              source_profit_by_month = monthly_trends.sort_values(['YEAR', 'MONTH', 'TOTAL_SCORE'], ascending=[True, True, False])
              best_source_by_month = source_profit_by_month.groupby(['YEAR', 'MONTH']).first().reset_index()
              
              return {
                  'monthly_trends': monthly_trends,
                  'best_source_by_month': best_source_by_month
              }
              
          except Exception as e:
              if self.debug:
                  print(f"Error in time trends analysis: {str(e)}")
                  import traceback
                  traceback.print_exc()
              return {}
              
      def get_overview_statistics(self, data: pd.DataFrame) -> Dict[str, Any]:
          """Get overview statistics for sources."""
          if data is None or data.empty:
              return {}
              
          try:
              # Calculate basic source statistics
              total_sources = data['SOURCE'].nunique()
              total_score = data['SCORE'].sum()
              total_chests = len(data)
              avg_score_per_source = data.groupby('SOURCE')['SCORE'].mean().mean()
              
              # Get most profitable sources
              source_profits = data.groupby('SOURCE')['SCORE'].sum().sort_values(ascending=False).head(5).to_dict()
              
              # Get most common sources
              source_counts = data['SOURCE'].value_counts().head(5).to_dict()
              
              return {
                  'total_sources': total_sources,
                  'total_score': total_score,
                  'total_chests': total_chests,
                  'avg_score_per_source': avg_score_per_source,
                  'most_profitable_sources': source_profits,
                  'most_common_sources': source_counts
              }
              
          except Exception as e:
              if self.debug:
                  print(f"Error in overview statistics: {str(e)}")
                  import traceback
                  traceback.print_exc()
              return {}
  ```

- [ ] **Create composite AnalysisManager**
  ```python
  # src/core/services/analysis_manager.py
  import pandas as pd
  from typing import Dict, Any, Optional, List
  from .player_analysis_service import PlayerAnalysisService
  from .chest_analysis_service import ChestAnalysisService
  from .source_analysis_service import SourceAnalysisService
  from core.data.cache import DataCache
  from pathlib import Path

  class AnalysisManager:
      """Manager for coordinating various analysis services."""
      
      def __init__(self, cache_dir: Optional[Path] = None, debug: bool = False):
          self.debug = debug
          self.player_service = PlayerAnalysisService(debug=debug)
          self.chest_service = ChestAnalysisService(debug=debug)
          self.source_service = SourceAnalysisService(debug=debug)
          
          # Initialize cache
          cache_path = cache_dir or Path.home() / ".totalbattle" / "analysis_cache"
          self.cache = DataCache(cache_path)
          
      def analyze_data(self, data: pd.DataFrame) -> Dict[str, Any]:
          """
          Perform comprehensive analysis on the data.
          
          Args:
              data: DataFrame containing the data to analyze
              
          Returns:
              Dictionary of all analysis results
          """
          if data is None or data.empty:
              return {}
              
          # Check if we have cached results
          cache_key = {
              "data_hash": hash(str(data.values.tobytes())),
              "columns": ','.join(data.columns)
          }
          
          cached_results = self.cache.get("comprehensive_analysis", cache_key)
          if cached_results is not None:
              return cached_results
              
          try:
              # Perform all analyses
              results = {}
              
              # Get overview statistics from each service
              results['player_overview'] = self.player_service.get_overview_statistics(data)
              results['chest_overview'] = self.chest_service.get_overview_statistics(data)
              results['source_overview'] = self.source_service.get_overview_statistics(data)
              
              # Comprehensive player analysis
              results['player_analysis'] = self.player_service.analyze_player_performance(data)
              results['player_chest_distribution'] = self.player_service.analyze_chest_distribution(data)
              results['player_source_effectiveness'] = self.player_service.analyze_source_effectiveness(data)
              results['player_time_trends'] = self.player_service.analyze_time_trends(data)
              
              # Comprehensive chest analysis
              results['chest_analysis'] = self.chest_service.analyze_chest_distribution(data)
              results['chest_source_effectiveness'] = self.chest_service.analyze_source_effectiveness(data)
              results['chest_time_trends'] = self.chest_service.analyze_time_trends(data)
              
              # Comprehensive source analysis
              results['source_analysis'] = self.source_service.analyze_source_effectiveness(data)
              results['source_chest_distribution'] = self.source_service.analyze_chest_distribution(data)
              results['source_time_trends'] = self.source_service.analyze_time_trends(data)
              
              # Cache the results
              self.cache.set("comprehensive_analysis", cache_key, results)
              
              return results
              
          except Exception as e:
              if self.debug:
                  print(f"Error in comprehensive analysis: {str(e)}")
                  import traceback
                  traceback.print_exc()
              return {}
      
      def get_player_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
          """Get player-focused analysis."""
          if data is None or data.empty:
              return {}
              
          # Check for cached results
          cache_key = {
              "data_hash": hash(str(data.values.tobytes())),
              "columns": ','.join(data.columns),
              "analysis_type": "player"
          }
          
          cached_results = self.cache.get("player_analysis", cache_key)
          if cached_results is not None:
              return cached_results
              
          try:
              results = {}
              results['overview'] = self.player_service.get_overview_statistics(data)
              results['performance'] = self.player_service.analyze_player_performance(data)
              results['chest_distribution'] = self.player_service.analyze_chest_distribution(data)
              results['source_effectiveness'] = self.player_service.analyze_source_effectiveness(data)
              results['time_trends'] = self.player_service.analyze_time_trends(data)
              
              # Cache the results
              self.cache.set("player_analysis", cache_key, results)
              
              return results
              
          except Exception as e:
              if self.debug:
                  print(f"Error in player analysis: {str(e)}")
              return {}
      
      def get_chest_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
          """Get chest-focused analysis."""
          if data is None or data.empty:
              return {}
              
          # Check for cached results
          cache_key = {
              "data_hash": hash(str(data.values.tobytes())),
              "columns": ','.join(data.columns),
              "analysis_type": "chest"
          }
          
          cached_results = self.cache.get("chest_analysis", cache_key)
          if cached_results is not None:
              return cached_results
              
          try:
              results = {}
              results['overview'] = self.chest_service.get_overview_statistics(data)
              results['distribution'] = self.chest_service.analyze_chest_distribution(data)
              results['source_effectiveness'] = self.chest_service.analyze_source_effectiveness(data)
              results['time_trends'] = self.chest_service.analyze_time_trends(data)
              
              # Cache the results
              self.cache.set("chest_analysis", cache_key, results)
              
              return results
              
          except Exception as e:
              if self.debug:
                  print(f"Error in chest analysis: {str(e)}")
              return {}
      
      def get_source_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
          """Get source-focused analysis."""
          if data is None or data.empty:
              return {}
              
          # Check for cached results
          cache_key = {
              "data_hash": hash(str(data.values.tobytes())),
              "columns": ','.join(data.columns),
              "analysis_type": "source"
          }
          
          cached_results = self.cache.get("source_analysis", cache_key)
          if cached_results is not None:
              return cached_results
              
          try:
              results = {}
              results['overview'] = self.source_service.get_overview_statistics(data)
              results['effectiveness'] = self.source_service.analyze_source_effectiveness(data)
              results['chest_distribution'] = self.source_service.analyze_chest_distribution(data)
              results['time_trends'] = self.source_service.analyze_time_trends(data)
              
              # Cache the results
              self.cache.set("source_analysis", cache_key, results)
              
              return results
              
          except Exception as e:
              if self.debug:
                  print(f"Error in source analysis: {str(e)}")
              return {}
      
      def clear_cache(self):
          """Clear the analysis cache."""
          self.cache.clear()
  ```

#### 2.2. Chart Service

- [ ] **Create ChartService Interface**
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

- [ ] **Create ChartConfiguration class**
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

- [ ] **Implement MplChartService**
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
          # Create config with provided parameters
          config = ChartConfiguration(
              chart_type="pie",
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
              
          # Limit to top categories and group the rest as "Others"
          if len(df) > 10:
              top_df = df.head(9)
              others_value = df.iloc[9:][config.value_column].sum()
              
              # Create a new row for "Others"
              others_row = pd.DataFrame({
                  config.category_column: ["Others"],
                  config.value_column: [others_value]
              })
              
              # Concatenate with top categories
              df = pd.concat([top_df, others_row])
              
          # Create pie chart
          wedges, texts, autotexts = ax.pie(
              df[config.value_column],
              labels=df[config.category_column] if not config.show_values else None,
              autopct='%1.1f%%' if config.show_values else None,
              startangle=90,
              colors=config.colors,
              wedgeprops={'edgecolor': config.style['bg_color'], 'linewidth': 1}
          )
          
          # Style texts
          for text in texts:
              if text:
                  text.set_color(config.style['text_color'])
                  
          # Style percentage texts
          for autotext in autotexts:
              if autotext:
                  autotext.set_color('white')
                  autotext.set_fontweight('bold')
                  
          # Set title
          if config.title:
              ax.set_title(config.title)
              
          # Make the pie chart a circle
          ax.axis('equal')
          
          # Add legend if we have many categories and aren't showing labels
          if len(df) > 5 and config.show_values:
              ax.legend(
                  wedges, 
                  df[config.category_column],
                  loc="center left",
                  bbox_to_anchor=(1, 0, 0.5, 1)
              )
              
          # Adjust layout
          fig.tight_layout()
          
          return fig, ax
      
      def create_line_chart(
          self,
          data: pd.DataFrame,
          category_column: str,
          value_column: str,
          title: str = "",
          **kwargs
      ) -> Tuple[plt.Figure, plt.Axes]:
          """Create a line chart."""
          # Create config with provided parameters
          config = ChartConfiguration(
              chart_type="line",
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
              
          # Handle different x-axis types
          x_values = df[config.category_column]
          if pd.api.types.is_datetime64_any_dtype(x_values):
              # For datetime x values, keep as is
              pass
          elif pd.api.types.is_numeric_dtype(x_values):
              # For numeric x values, keep as is
              pass
          else:
              # For categorical x values, use indices and set x-tick labels
              x_values = range(len(df))
              ax.set_xticks(x_values)
              ax.set_xticklabels(df[config.category_column])
              
          # Create the line chart
          line = ax.plot(
              x_values,
              df[config.value_column],
              marker='o',
              color=config.style['line_color'],
              linewidth=config.style['line_width'],
              markersize=config.style['marker_size'],
              markerfacecolor=config.style['marker_color'],
              markeredgecolor=config.style['edge_color']
          )[0]
          
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
              
          # Add values at data points if requested
          if config.show_values:
              for i, value in enumerate(df[config.value_column]):
                  x = x_values[i] if not pd.api.types.is_categorical_dtype(x_values) else i
                  ax.text(
                      x,
                      value,
                      f'{value:,.0f}',
                      ha='center',
                      va='bottom',
                      color=config.style['text_color'],
                      fontweight='bold'
                  )
                  
          # Adjust layout
          fig.tight_layout()
          
          return fig, ax
          
      def create_scatter_chart(
          self,
          data: pd.DataFrame,
          x_column: str,
          y_column: str,
          title: str = "",
          **kwargs
      ) -> Tuple[plt.Figure, plt.Axes]:
          """Create a scatter chart."""
          # Create config with provided parameters
          config = ChartConfiguration(
              chart_type="scatter",
              category_column=x_column,  # Using x_column as category
              value_column=y_column,     # Using y_column as value
              title=title,
              **kwargs
          )
          
          # Create figure with styling
          fig, ax = self.create_figure(config)
          
          # Prepare data (but don't sort for scatter plots)
          df = data.copy()
          if df.empty or config.category_column not in df.columns or config.value_column not in df.columns:
              ax.text(
                  0.5, 0.5,
                  "No data available for chart",
                  ha='center',
                  va='center',
                  color=config.style['text_color'],
                  fontsize=14
              )
              return fig, ax
              
          # Create scatter plot
          scatter = ax.scatter(
              df[config.category_column],
              df[config.value_column],
              s=config.style['marker_size'] * 10,  # Larger markers for scatter
              c=config.colors[0],
              alpha=0.7,
              edgecolors=config.style['edge_color']
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
              
          # Add annotations if requested and we have labels
          if config.show_values and 'label_column' in kwargs:
              label_column = kwargs['label_column']
              if label_column in df.columns:
                  for i, row in df.iterrows():
                      ax.annotate(
                          row[label_column],
                          (row[config.category_column], row[config.value_column]),
                          xytext=(5, 5),
                          textcoords='offset points',
                          color=config.style['text_color'],
                          fontweight='bold'
                      )
                      
          # Adjust layout
          fig.tight_layout()
          
          return fig, ax
      
      def save_chart(
          self,
          fig: plt.Figure,
          file_path: Union[str, Path],
          **kwargs
      ) -> bool:
          """Save a chart to a file."""
          try:
              # Ensure file_path is a Path object
              file_path = Path(file_path)
              
              # Ensure directory exists
              file_path.parent.mkdir(parents=True, exist_ok=True)
              
              # Get file format from extension, default to png
              format_type = file_path.suffix[1:] if file_path.suffix else 'png'
              
              # Get DPI from kwargs or use default
              dpi = kwargs.get('dpi', 100)
              
              # Get the background color from kwargs or use default
              bg_color = kwargs.get('bg_color', '#1A2742')
              
              # Save figure
              fig.savefig(
                  file_path,
                  format=format_type,
                  dpi=dpi,
                  bbox_inches='tight',
                  facecolor=bg_color,
                  edgecolor='none'
              )
              
              return True
              
          except Exception as e:
              if self.debug:
                  print(f"Error saving chart: {str(e)}")
                  import traceback
                  traceback.print_exc()
              return False
      
      def get_available_chart_types(self) -> List[str]:
          """Get a list of available chart types."""
          return ["bar", "horizontal_bar", "pie", "line", "scatter"]
  ```

- [ ] **Implement ChartManager**
  ```python
  # src/visualization/services/chart_manager.py
  import pandas as pd
  import matplotlib.pyplot as plt
  from typing import Dict, Any, Optional, Tuple, List, Union
  from pathlib import Path
  import tempfile
  from .mpl_chart_service import MplChartService
  from .chart_configuration import ChartConfiguration

  class ChartManager:
      """Manager for chart generation and management."""
      
      def __init__(self, chart_service=None, debug: bool = False):
          self.debug = debug
          self.chart_service = chart_service or MplChartService(debug=debug)
          self.temp_files = []
          
      def create_chart(
          self,
          data: pd.DataFrame,
          chart_type: str,
          category_column: str,
          value_column: str,
          **kwargs
      ) -> Tuple[plt.Figure, plt.Axes]:
          """
          Create a chart based on the specified type.
          
          Args:
              data: DataFrame containing the data
              chart_type: Type of chart to create
              category_column: Column to use for categories
              value_column: Column to use for values
              **kwargs: Additional options
              
          Returns:
              Tuple of figure and axes
          """
          try:
              if chart_type == "bar":
                  return self.chart_service.create_bar_chart(
                      data, category_column, value_column, **kwargs
                  )
              elif chart_type == "horizontal_bar":
                  return self.chart_service.create_horizontal_bar_chart(
                      data, category_column, value_column, **kwargs
                  )
              elif chart_type == "pie":
                  return self.chart_service.create_pie_chart(
                      data, category_column, value_column, **kwargs
                  )
              elif chart_type == "line":
                  return self.chart_service.create_line_chart(
                      data, category_column, value_column, **kwargs
                  )
              elif chart_type == "scatter":
                  # Scatter needs x and y columns
                  return self.chart_service.create_scatter_chart(
                      data, category_column, value_column, **kwargs
                  )
              else:
                  if self.debug:
                      print(f"Unknown chart type: {chart_type}")
                  # Create a figure with error message
                  fig, ax = plt.subplots(figsize=(8, 6))
                  ax.text(
                      0.5, 0.5,
                      f"Unknown chart type: {chart_type}",
                      ha='center',
                      va='center',
                      color='white',
                      fontsize=14
                  )
                  return fig, ax
                  
          except Exception as e:
              if self.debug:
                  print(f"Error creating chart: {str(e)}")
                  import traceback
                  traceback.print_exc()
              # Create a figure with error message
              fig, ax = plt.subplots(figsize=(8, 6))
              ax.text(
                  0.5, 0.5,
                  f"Error creating chart: {str(e)}",
                  ha='center',
                  va='center',
                  color='white',
                  fontsize=14
              )
              return fig, ax
      
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
          return self.chart_service.save_chart(fig, file_path, **kwargs)
      
      def create_temp_chart(
          self,
          data: pd.DataFrame,
          chart_type: str,
          category_column: str,
          value_column: str,
          **kwargs
      ) -> Optional[str]:
          """
          Create a chart and save it to a temporary file.
          
          Args:
              data: DataFrame containing the data
              chart_type: Type of chart to create
              category_column: Column to use for categories
              value_column: Column to use for values
              **kwargs: Additional options
              
          Returns:
              Path to the temporary file, or None if an error occurred
          """
          try:
              # Create a temporary file
              temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
              temp_file.close()
              
              # Create and save the chart
              fig, ax = self.create_chart(
                  data, chart_type, category_column, value_column, **kwargs
              )
              
              success = self.save_chart(fig, temp_file.name, **kwargs)
              
              # Close the figure to free memory
              plt.close(fig)
              
              if success:
                  # Add to the list of temporary files
                  self.temp_files.append(temp_file.name)
                  return temp_file.name
              else:
                  return None
                  
          except Exception as e:
              if self.debug:
                  print(f"Error creating temporary chart: {str(e)}")
                  import traceback
                  traceback.print_exc()
              return None
      
      def cleanup_temp_files(self):
          """Clean up temporary files created by the manager."""
          import os
          for file_path in self.temp_files:
              try:
                  os.unlink(file_path)
              except Exception as e:
                  if self.debug:
                      print(f"Error deleting temporary file {file_path}: {str(e)}")
          
          # Clear the list
          self.temp_files = []
      
      def create_category_charts(self, analysis_results: Dict[str, Any], category: str) -> Dict[str, str]:
          """
          Create a set of charts for a specific category (PLAYER, CHEST, SOURCE).
          
          Args:
              analysis_results: Analysis results from AnalysisManager
              category: Category to create charts for (PLAYER, CHEST, SOURCE)
              
          Returns:
              Dictionary mapping chart names to temporary file paths
          """
          charts = {}
          
          try:
              # Get the appropriate data based on category
              if category == "PLAYER":
                  if 'player_analysis' in analysis_results:
                      player_data = analysis_results['player_analysis']
                      
                      # Create player performance chart
                      if 'performance' in player_data and 'player_totals' in player_data['performance']:
                          df = player_data['performance']['player_totals']
                          chart_path = self.create_temp_chart(
                              df,
                              "bar",
                              "PLAYER",
                              "SCORE",
                              title="Player Total Scores",
                              sort_data=True,
                              sort_ascending=False,
                              limit_categories=True,
                              category_limit=15
                          )
                          if chart_path:
                              charts['player_performance'] = chart_path
                              
                      # Create player chest distribution chart
                      if 'chest_distribution' in player_data and 'chest_distribution' in player_data['chest_distribution']:
                          df = player_data['chest_distribution']['chest_distribution']
                          chart_path = self.create_temp_chart(
                              df,
                              "pie",
                              "CHEST",
                              "COUNT",
                              title="Player Chest Distribution",
                              sort_data=True,
                              sort_ascending=False
                          )
                          if chart_path:
                              charts['player_chest_distribution'] = chart_path
                              
                      # Create player time trends chart
                      if 'time_trends' in player_data and 'monthly_trends' in player_data['time_trends']:
                          df = player_data['time_trends']['monthly_trends']
                          chart_path = self.create_temp_chart(
                              df,
                              "line",
                              "MONTH",
                              "TOTAL_SCORE",
                              title="Player Monthly Trends",
                              sort_data=True,
                              sort_ascending=True
                          )
                          if chart_path:
                              charts['player_time_trends'] = chart_path
                              
              elif category == "CHEST":
                  if 'chest_analysis' in analysis_results:
                      chest_data = analysis_results['chest_analysis']
                      
                      # Create chest distribution chart
                      if 'distribution' in chest_data and 'chest_stats' in chest_data['distribution']:
                          df = chest_data['distribution']['chest_stats']
                          chart_path = self.create_temp_chart(
                              df,
                              "bar",
                              "CHEST",
                              "TOTAL_SCORE",
                              title="Chest Total Scores",
                              sort_data=True,
                              sort_ascending=False,
                              limit_categories=True,
                              category_limit=15
                          )
                          if chart_path:
                              charts['chest_distribution'] = chart_path
                              
                      # Create chest value chart
                      if 'distribution' in chest_data and 'chest_stats' in chest_data['distribution']:
                          df = chest_data['distribution']['chest_stats']
                          chart_path = self.create_temp_chart(
                              df,
                              "pie",
                              "CHEST",
                              "AVG_SCORE",
                              title="Chest Average Scores",
                              sort_data=True,
                              sort_ascending=False
                          )
                          if chart_path:
                              charts['chest_value'] = chart_path
                              
                      # Create chest source effectiveness chart
                      if 'source_effectiveness' in chest_data and 'best_source_per_chest' in chest_data['source_effectiveness']:
                          df = chest_data['source_effectiveness']['best_source_per_chest']
                          chart_path = self.create_temp_chart(
                              df,
                              "horizontal_bar",
                              "CHEST",
                              "AVG_SCORE",
                              title="Best Source per Chest",
                              sort_data=True,
                              sort_ascending=False,
                              limit_categories=True,
                              category_limit=15
                          )
                          if chart_path:
                              charts['chest_source_effectiveness'] = chart_path
                              
              elif category == "SOURCE":
                  if 'source_analysis' in analysis_results:
                      source_data = analysis_results['source_analysis']
                      
                      # Create source effectiveness chart
                      if 'effectiveness' in source_data and 'source_stats' in source_data['effectiveness']:
                          df = source_data['effectiveness']['source_stats']
                          chart_path = self.create_temp_chart(
                              df,
                              "bar",
                              "SOURCE",
                              "TOTAL_SCORE",
                              title="Source Total Scores",
                              sort_data=True,
                              sort_ascending=False,
                              limit_categories=True,
                              category_limit=15
                          )
                          if chart_path:
                              charts['source_effectiveness'] = chart_path
                              
                      # Create source value chart
                      if 'effectiveness' in source_data and 'source_stats' in source_data['effectiveness']:
                          df = source_data['effectiveness']['source_stats']
                          chart_path = self.create_temp_chart(
                              df,
                              "pie",
                              "SOURCE",
                              "EFFICIENCY",
                              title="Source Efficiency",
                              sort_data=True,
                              sort_ascending=False
                          )
                          if chart_path:
                              charts['source_value'] = chart_path
                              
                      # Create source time trends chart
                      if 'time_trends' in source_data and 'monthly_trends' in source_data['time_trends']:
                          df = source_data['time_trends']['monthly_trends']
                          chart_path = self.create_temp_chart(
                              df,
                              "line",
                              "MONTH",
                              "TOTAL_SCORE",
                              title="Source Monthly Trends",
                              sort_data=True,
                              sort_ascending=True
                          )
                          if chart_path:
                              charts['source_time_trends'] = chart_path
                              
          except Exception as e:
              if self.debug:
                  print(f"Error creating category charts: {str(e)}")
                  import traceback
                  traceback.print_exc()
                  
          return charts
      
      def __del__(self):
          """Clean up temporary files on deletion."""
          self.cleanup_temp_files()
  ```

#### 2.3. Report Service

- [ ] **Create ReportService Interface**
  ```python
  # src/visualization/services/report_service.py
  from abc import ABC, abstractmethod
  from typing import Dict, Any, Optional, List, Union
  from pathlib import Path

  class ReportService(ABC):
      """Interface for report generation services."""
      
      @abstractmethod
      def generate_report(
          self,
          title: str,
          data: Dict[str, Any],
          sections: List[Dict[str, Any]],
          **kwargs
      ) -> str:
          """
          Generate a report from data and sections.
          
          Args:
              title: Report title
              data: Data to include in the report
              sections: Sections to include in the report
              **kwargs: Additional options
              
          Returns:
              HTML string of the generated report
          """
          pass
      
      @abstractmethod
      def export_report(
          self,
          html_content: str,
          file_path: Union[str, Path],
          format_type: str = "html",
          **kwargs
      ) -> bool:
          """
          Export a report to a file.
          
          Args:
              html_content: HTML content of the report
              file_path: Path to save the report to
              format_type: Format to save the report in
              **kwargs: Additional options
              
          Returns:
              True if successful, False otherwise
          """
          pass
      
      @abstractmethod
      def create_report_section(
          self,
          section_type: str,
          title: str,
          content: Any,
          **kwargs
      ) -> Dict[str, Any]:
          """
          Create a report section.
          
          Args:
              section_type: Type of section to create
              title: Section title
              content: Section content
              **kwargs: Additional options
              
          Returns:
              Dictionary representing the section
          """
          pass
  ```

- [ ] **Create HTMLReportService Implementation**
  ```python
  # src/visualization/services/html_report_service.py
  from typing import Dict, Any, Optional, List, Union
  from pathlib import Path
  from datetime import datetime
  import os
  import tempfile
  from .report_service import ReportService

  class HTMLReportService(ReportService):
      """HTML implementation of the ReportService interface."""
      
      def __init__(self, debug: bool = False):
          self.debug = debug
          self.style_settings = self._get_default_styles()
          
      def generate_report(
          self,
          title: str,
          data: Dict[str, Any],
          sections: List[Dict[str, Any]],
          **kwargs
      ) -> str:
          """Generate an HTML report."""
          # Get options from kwargs
          include_charts = kwargs.get('include_charts', True)
          include_tables = kwargs.get('include_tables', True)
          include_stats = kwargs.get('include_stats', True)
          
          # Generate HTML header
          html = self._generate_html_header(title)
          
          # Add report sections
          for section in sections:
              # Check if section should be included
              if not self._should_include_section(
                  section, include_charts, include_tables, include_stats
              ):
                  continue
                  
              # Add section HTML
              html += self._generate_section_html(section)
              
          # Add footer
          html += self._generate_html_footer()
          
          return html
      
      def export_report(
          self,
          html_content: str,
          file_path: Union[str, Path],
          format_type: str = "html",
          **kwargs
      ) -> bool:
          """Export a report to a file."""
          try:
              # Ensure file_path is a Path object
              file_path = Path(file_path)
              
              # Ensure directory exists
              file_path.parent.mkdir(parents=True, exist_ok=True)
              
              if format_type.lower() == "html":
                  # Write HTML file
                  with open(file_path, 'w', encoding='utf-8') as f:
                      f.write(html_content)
                  return True
                  
              elif format_type.lower() == "pdf":
                  # Convert HTML to PDF
                  try:
                      # Try to use WeasyPrint if available
                      from weasyprint import HTML
                      HTML(string=html_content).write_pdf(file_path)
                      return True
                  except ImportError:
                      if self.debug:
                          print("WeasyPrint not available, trying alternative PDF export")
                      
                      # Try alternative PDF export using Qt
                      try:
                          from PySide6.QtWebEngineWidgets import QWebEngineView
                          from PySide6.QtCore import QUrl
                          from PySide6.QtWidgets import QApplication
                          from PySide6.QtPrintSupport import QPrinter
                          
                          app = QApplication.instance() or QApplication([])
                          
                          # Create web view
                          web = QWebEngineView()
                          web.setHtml(html_content)
                          
                          # Create printer
                          printer = QPrinter(QPrinter.HighResolution)
                          printer.setOutputFormat(QPrinter.PdfFormat)
                          printer.setOutputFileName(str(file_path))
                          
                          # Print to PDF
                          def handle_print_finished(success):
                              pass
                              
                          web.print_(printer)
                          
                          # Ensure application processes events
                          if app.instance():
                              app.processEvents()
                              
                          return True
                          
                      except Exception as e:
                          if self.debug:
                              print(f"Alternative PDF export failed: {str(e)}")
                          return False
              else:
                  if self.debug:
                      print(f"Unsupported format type: {format_type}")
                  return False
                  
          except Exception as e:
              if self.debug:
                  print(f"Error exporting report: {str(e)}")
                  import traceback
                  traceback.print_exc()
              return False
      
      def create_report_section(
          self,
          section_type: str,
          title: str,
          content: Any,
          **kwargs
      ) -> Dict[str, Any]:
          """Create a report section."""
          section = {
              'type': section_type,
              'title': title,
              'content': content
          }
          
          # Add any additional properties from kwargs
          section.update(kwargs)
          
          return section
      
      def create_text_section(
          self,
          title: str,
          text: str,
          **kwargs
      ) -> Dict[str, Any]:
          """Create a text section."""
          return self.create_report_section('text', title, text, **kwargs)
      
      def create_table_section(
          self,
          title: str,
          dataframe,
          description: str = "",
          **kwargs
      ) -> Dict[str, Any]:
          """Create a table section from a DataFrame."""
          # Convert DataFrame to HTML table
          table_html = dataframe.to_html(index=False, classes="data-table")
          
          # Add description if provided
          content = f"{description}<br>{table_html}" if description else table_html
          
          return self.create_report_section('table', title, content, **kwargs)
      
      def create_chart_section(
          self,
          title: str,
          chart_path: str,
          description: str = "",
          **kwargs
      ) -> Dict[str, Any]:
          """Create a chart section from a chart file."""
          # Create HTML for the chart
          chart_html = f"""
          <div class="chart-container">
              <img src="file:///{chart_path}" alt="{title}" style="max-width:100%; height:auto;">
              {f"<p>{description}</p>" if description else ""}
          </div>
          """
          
          return self.create_report_section('chart', title, chart_html, **kwargs)
      
      def create_stats_section(
          self,
          title: str,
          stats: Dict[str, Any],
          description: str = "",
          **kwargs
      ) -> Dict[str, Any]:
          """Create a statistics section from a dictionary of statistics."""
          # Create HTML for the statistics
          stats_html = f"""
          <div class="stats-container">
          """
          
          # Add each statistic as a box
          for key, value in stats.items():
              # Format the key for display
              display_key = key.replace('_', ' ').title()
              
              # Format the value based on its type
              if isinstance(value, (int, float)):
                  formatted_value = f"{value:,.2f}" if isinstance(value, float) else f"{value:,}"
              else:
                  formatted_value = str(value)
                  
              stats_html += f"""
              <div class="stat-box">
                  <p>{display_key}</p>
                  <p class="stat-value">{formatted_value}</p>
              </div>
              """
              
          stats_html += """
          </div>
          """
          
          # Add description if provided
          if description:
              stats_html = f"<p>{description}</p>{stats_html}"
              
          return self.create_report_section('stats', title, stats_html, **kwargs)
      
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
          """Generate HTML header with styling."""
          return f"""
          <!DOCTYPE html>
          <html>
          <head>
              <meta charset="UTF-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
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

- [ ] **Create ReportGenerator Implementation**
  ```python
  # src/visualization/services/report_generator.py
  from typing import Dict, Any, Optional, List, Union
  from pathlib import Path
  import os
  import tempfile
  from .html_report_service import HTMLReportService
  from .chart_manager import ChartManager
  from core.services.analysis_manager import AnalysisManager

  class ReportGenerator:
      """Generator for comprehensive reports."""
      
      def __init__(
          self,
          report_service=None,
          chart_manager=None,
          analysis_manager=None,
          debug: bool = False
      ):
          self.debug = debug
          self.report_service = report_service or HTMLReportService(debug=debug)
          self.chart_manager = chart_manager or ChartManager(debug=debug)
          self.analysis_manager = analysis_manager
          
      def generate_player_report(
          self,
          data: Dict[str, Any],
          include_charts: bool = True,
          include_tables: bool = True,
          include_stats: bool = True
      ) -> str:
          """
          Generate a player performance report.
          
          Args:
              data: Analysis data
              include_charts: Whether to include charts
              include_tables: Whether to include tables
              include_stats: Whether to include statistics
              
          Returns:
              HTML string of the generated report
          """
          # Create report sections
          sections = []
          
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
                  
          # 3. Performance chart
          if include_charts:
              # Generate player charts
              player_charts = self.chart_manager.create_category_charts(data, "PLAYER")
              
              # Add player performance chart
              if 'player_performance' in player_charts:
                  sections.append(
                      self.report_service.create_chart_section(
                          "Player Performance",
                          player_charts['player_performance'],
                          "Total scores by player."
                      )
                  )
                  
              # Add player chest distribution chart
              if 'player_chest_distribution' in player_charts:
                  sections.append(
                      self.report_service.create_chart_section(
                          "