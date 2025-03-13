# Phase 7 Part 1 - Section 1: Statistical Analysis Framework

## Overview
This document details the implementation of the advanced statistical analysis framework for the Total Battle Analyzer application. This framework will enable sophisticated statistical modeling of battle data to provide users with deeper insights and predictive capabilities.

## Key Components

### 1. Statistical Models for Battle Analysis
- Time-series analysis of battle performance
- Correlation analysis between unit compositions and outcomes
- Variance analysis for evaluating strategy consistency
- Hypothesis testing for validating strategic assumptions

### 2. Predictive Analytics Engine
- Win probability modeling based on army compositions
- Outcome prediction using historical battle data
- Resource optimization recommendations
- Trend analysis and forecasting

### 3. Data Preprocessing Pipeline
- Raw data cleaning and normalization
- Feature extraction from battle reports
- Dimensionality reduction for complex datasets
- Data transformation for statistical compatibility

## Implementation Details

### 1.1 Statistical Core Library

```python
# src/goob_ai/analytics/stats_core.py
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.preprocessing import StandardScaler
from pathlib import Path

class StatisticalCore:
    """Core statistical functions for battle analysis."""
    
    def __init__(self) -> None:
        """Initialize the statistical core with default configurations."""
        self.scaler = StandardScaler()
        self.confidence_level = 0.95
        
    def calculate_confidence_interval(self, data: List[float]) -> Tuple[float, float]:
        """
        Calculate confidence interval for a dataset.
        
        Args:
            data: List of numeric values
            
        Returns:
            Tuple[float, float]: Lower and upper bounds of confidence interval
        """
        data_array = np.array(data)
        mean = np.mean(data_array)
        std_error = stats.sem(data_array)
        interval = std_error * stats.t.ppf((1 + self.confidence_level) / 2, len(data_array) - 1)
        
        return (mean - interval, mean + interval)
    
    def test_significance(self, group1: List[float], group2: List[float]) -> Dict[str, Any]:
        """
        Perform t-test to compare two groups.
        
        Args:
            group1: First group of values
            group2: Second group of values
            
        Returns:
            Dict[str, Any]: T-test results including p-value and interpretation
        """
        t_stat, p_value = stats.ttest_ind(group1, group2, equal_var=False)
        is_significant = p_value < (1 - self.confidence_level)
        
        return {
            't_statistic': t_stat,
            'p_value': p_value,
            'is_significant': is_significant,
            'interpretation': f"The difference is {'statistically significant' if is_significant else 'not statistically significant'}"
        }
    
    def normalize_dataset(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize a dataset using standard scaling.
        
        Args:
            data: DataFrame to normalize
            
        Returns:
            pd.DataFrame: Normalized DataFrame
        """
        numeric_cols = data.select_dtypes(include=['float64', 'int64']).columns
        data_normalized = data.copy()
        data_normalized[numeric_cols] = self.scaler.fit_transform(data[numeric_cols])
        
        return data_normalized
```

### 1.2 Battle Statistics Analysis

```python
# src/goob_ai/analytics/battle_statistics.py
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from pathlib import Path
from .stats_core import StatisticalCore

class BattleStatistics:
    """Advanced statistical analysis for battle data."""
    
    def __init__(self, battle_data: List[Dict[str, Any]]) -> None:
        """
        Initialize with battle data.
        
        Args:
            battle_data: List of battle records
        """
        self.data = pd.DataFrame(battle_data)
        self.stats_core = StatisticalCore()
        self._preprocess_data()
        
    def _preprocess_data(self) -> None:
        """Preprocess the battle data for analysis."""
        # Convert date strings to datetime
        if 'battle_date' in self.data.columns:
            self.data['battle_date'] = pd.to_datetime(self.data['battle_date'])
        
        # Clean and normalize numeric fields
        numeric_fields = self.data.select_dtypes(include=['float64', 'int64']).columns
        self.data = self.stats_core.normalize_dataset(self.data)
        
    def calculate_win_probability(self, army_composition: Dict[str, int]) -> float:
        """
        Calculate win probability based on army composition.
        
        Args:
            army_composition: Dictionary of unit types and quantities
            
        Returns:
            float: Probability of winning (0.0 to 1.0)
        """
        # Create feature vector from army composition
        army_features = self._extract_army_features(army_composition)
        
        # Find similar army compositions in historical data
        similar_battles = self._find_similar_battles(army_features)
        
        # Calculate win rate from similar battles
        if len(similar_battles) > 0:
            win_count = similar_battles['victory'].sum()
            total_count = len(similar_battles)
            win_probability = win_count / total_count
            
            # Apply confidence adjustment based on sample size
            if total_count < 10:
                # Adjust probability toward 0.5 for small sample sizes
                adjustment_factor = min(1.0, total_count / 10)
                win_probability = (win_probability * adjustment_factor) + (0.5 * (1 - adjustment_factor))
                
            return win_probability
        else:
            # Return 0.5 (neutral) if no similar battles found
            return 0.5
        
    def _extract_army_features(self, army_composition: Dict[str, int]) -> np.ndarray:
        """
        Extract feature vector from army composition.
        
        Args:
            army_composition: Dictionary of unit types and quantities
            
        Returns:
            np.ndarray: Feature vector
        """
        # Implementation of feature extraction
        # This would convert the army composition into a normalized feature vector
        pass
        
    def _find_similar_battles(self, army_features: np.ndarray) -> pd.DataFrame:
        """
        Find battles with similar army compositions.
        
        Args:
            army_features: Feature vector of army composition
            
        Returns:
            pd.DataFrame: Subset of battles with similar compositions
        """
        # Implementation of similarity search
        # This would find historical battles with similar army compositions
        pass
        
    def analyze_unit_effectiveness(self) -> Dict[str, Dict[str, float]]:
        """
        Analyze effectiveness of different unit types in various scenarios.
        
        Returns:
            Dict[str, Dict[str, float]]: Effectiveness scores for each unit type in different scenarios
        """
        # Group battles by scenario
        scenarios = self.data.groupby('battle_type')
        
        results = {}
        for scenario_name, scenario_battles in scenarios:
            # Calculate unit effectiveness for this scenario
            unit_effectiveness = self._calculate_unit_effectiveness(scenario_battles)
            results[scenario_name] = unit_effectiveness
            
        return results
        
    def _calculate_unit_effectiveness(self, battles: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate unit effectiveness for a set of battles.
        
        Args:
            battles: DataFrame of battles
            
        Returns:
            Dict[str, float]: Effectiveness scores for each unit type
        """
        # Implementation of effectiveness calculation
        # This would analyze how well each unit type performs
        pass
```

### 1.3 Predictive Analytics

```python
# src/goob_ai/analytics/battle_predictor.py
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from pathlib import Path
from .stats_core import StatisticalCore

class BattlePredictor:
    """Predictive analytics for battle outcomes."""
    
    def __init__(self, historical_data: List[Dict[str, Any]]) -> None:
        """
        Initialize with historical battle data.
        
        Args:
            historical_data: List of historical battle records
        """
        self.data = pd.DataFrame(historical_data)
        self.stats_core = StatisticalCore()
        self.model = RandomForestClassifier(n_estimators=100, max_depth=None, min_samples_split=2, random_state=42)
        self._preprocess_data()
        
    def _preprocess_data(self) -> None:
        """Preprocess the historical data for model training."""
        # Convert categorical variables to numeric
        for col in self.data.select_dtypes(['object']).columns:
            if col != 'outcome':  # Don't encode the target variable yet
                self.data[col] = self.data[col].astype('category').cat.codes
                
        # Normalize numeric features
        self.data = self.stats_core.normalize_dataset(self.data)
        
    def train_model(self) -> Dict[str, float]:
        """
        Train the predictive model and return performance metrics.
        
        Returns:
            Dict[str, float]: Model performance metrics
        """
        # Separate features and target
        if 'outcome' not in self.data.columns:
            raise ValueError("Training data must contain 'outcome' column")
            
        X = self.data.drop('outcome', axis=1)
        y = self.data['outcome']
        
        # Split into training and validation sets
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train the model
        self.model.fit(X_train, y_train)
        
        # Evaluate on validation set
        accuracy = self.model.score(X_val, y_val)
        
        return {
            'accuracy': accuracy,
            'feature_importance': dict(zip(X.columns, self.model.feature_importances_))
        }
        
    def predict_outcome(self, battle_conditions: Dict[str, Any]) -> Dict[str, float]:
        """
        Predict battle outcome based on conditions.
        
        Args:
            battle_conditions: Current battle conditions
            
        Returns:
            Dict[str, float]: Prediction probabilities for each outcome
        """
        # Convert conditions to feature vector
        features = pd.DataFrame([battle_conditions])
        
        # Encode categorical variables
        for col in features.select_dtypes(['object']).columns:
            features[col] = features[col].astype('category').cat.codes
            
        # Ensure all expected columns are present
        for col in self.model.feature_names_in_:
            if col not in features.columns:
                features[col] = 0
                
        # Make prediction
        probabilities = self.model.predict_proba(features)[0]
        outcome_classes = self.model.classes_
        
        return dict(zip(outcome_classes, probabilities))
```

## Integration with Existing Application

### Data Flow Integration
1. The statistical framework will integrate with the existing `DataManager` class to access historical battle data.
2. Results from statistical analysis will be provided to the UI layer through the service layer.
3. User requests for predictions will flow from the UI through the service layer to the prediction engine.

### UI Integration
1. New UI components will be added to display statistical insights:
   - Win probability indicators
   - Unit effectiveness charts
   - Trend analysis graphs
2. Interactive elements will allow users to:
   - Adjust army compositions and see prediction changes
   - Compare different strategic approaches
   - View confidence intervals for predictions

## Implementation Steps

### Week 1: Core Statistical Framework
1. Implement `StatisticalCore` class with fundamental statistical functions
2. Add data preprocessing pipelines
3. Create unit tests for core statistical functions
4. Integrate with data access layer

### Week 2: Battle Analysis Implementation
1. Implement `BattleStatistics` class for army analysis
2. Develop unit effectiveness calculation algorithms
3. Create visualization data preparation functions
4. Build integration tests for battle analysis

### Week 3: Predictive Analytics
1. Implement `BattlePredictor` class
2. Develop model training and evaluation procedures
3. Create prediction functions with confidence scoring
4. Build comprehensive tests for prediction accuracy

## Dependencies
- NumPy (1.20+)
- Pandas (1.3+)
- SciPy (1.7+)
- Scikit-learn (0.24+)

## Testing Strategy
1. Unit tests for all statistical functions
2. Integration tests with sample datasets
3. Accuracy validation tests for predictive models
4. Performance benchmarks for optimization

## Success Criteria
1. Statistical core functions achieve 95%+ test coverage
2. Prediction accuracy exceeds 70% on validation datasets
3. Performance meets targets (analysis completes within 5 seconds)
4. All integrations with existing codebase pass tests
5. Documentation complete with examples 