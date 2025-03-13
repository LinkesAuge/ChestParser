# Phase 7 Part 1 - Section 2: Machine Learning Integration

## Overview
This document details the implementation of machine learning capabilities for the Total Battle Analyzer application. The ML integration will enable more sophisticated analysis of battle data, automated pattern recognition, and advanced predictive capabilities beyond traditional statistical methods.

## Key Components

### 1. ML Model Training Pipeline
- Model training workflow
- Hyperparameter optimization
- Cross-validation framework
- Feature importance analysis

### 2. Model Evaluation Framework
- Performance metrics calculation
- Model comparison tools
- Validation dataset management
- Confusion matrix visualization

### 3. Model Deployment System
- Model serialization and storage
- Versioning and rollback capabilities
- Runtime performance optimization
- Model metadata tracking

### 4. Monitoring and Maintenance
- Prediction quality tracking
- Drift detection
- Retraining triggers
- A/B testing framework

## Implementation Details

### 2.1 ML Model Management

```python
# src/goob_ai/ml/model_manager.py
from typing import Dict, Any, List, Optional, Tuple, Union
import os
import json
import datetime
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.model_selection import GridSearchCV

class ModelManager:
    """Manages machine learning models for the application."""
    
    def __init__(self, models_dir: Path) -> None:
        """
        Initialize the model manager with storage directory.
        
        Args:
            models_dir: Directory for model storage
        """
        self.models_dir = models_dir
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.models_metadata = self._load_metadata()
        self.active_models: Dict[str, BaseEstimator] = {}
        
    def _load_metadata(self) -> Dict[str, Dict[str, Any]]:
        """
        Load model metadata from storage.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of model metadata
        """
        metadata_path = self.models_dir / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                return json.load(f)
        return {}
        
    def _save_metadata(self) -> None:
        """Save model metadata to storage."""
        metadata_path = self.models_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(self.models_metadata, f, indent=2)
            
    def save_model(self, model_name: str, model: BaseEstimator, 
                  performance_metrics: Dict[str, float], 
                  metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Save a trained model with metadata.
        
        Args:
            model_name: Base name for the model
            model: Trained scikit-learn model
            performance_metrics: Dictionary of performance metrics
            metadata: Additional metadata to store
            
        Returns:
            str: Unique version ID for the saved model
        """
        # Generate version ID using timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        version_id = f"{model_name}_{timestamp}"
        
        # Create model directory
        model_dir = self.models_dir / version_id
        model_dir.mkdir(exist_ok=True)
        
        # Save model file
        model_path = model_dir / "model.joblib"
        joblib.dump(model, model_path)
        
        # Prepare metadata
        model_metadata = {
            "name": model_name,
            "version_id": version_id,
            "created_at": datetime.datetime.now().isoformat(),
            "performance_metrics": performance_metrics,
            "model_type": type(model).__name__,
            "is_active": False
        }
        
        # Add custom metadata if provided
        if metadata:
            model_metadata.update(metadata)
            
        # Update metadata registry
        self.models_metadata[version_id] = model_metadata
        self._save_metadata()
        
        return version_id
        
    def load_model(self, version_id: str) -> BaseEstimator:
        """
        Load a model by version ID.
        
        Args:
            version_id: Version ID of the model to load
            
        Returns:
            BaseEstimator: The loaded model
            
        Raises:
            ValueError: If model version not found
        """
        if version_id not in self.models_metadata:
            raise ValueError(f"Model version {version_id} not found")
            
        model_path = self.models_dir / version_id / "model.joblib"
        if not model_path.exists():
            raise ValueError(f"Model file for version {version_id} not found")
            
        model = joblib.load(model_path)
        self.active_models[version_id] = model
        
        return model
        
    def get_active_model(self, model_name: str) -> Tuple[str, BaseEstimator]:
        """
        Get the currently active model for a given name.
        
        Args:
            model_name: Base name of the model
            
        Returns:
            Tuple[str, BaseEstimator]: Version ID and model
            
        Raises:
            ValueError: If no active model found
        """
        # Find active model version
        active_version = None
        for version_id, metadata in self.models_metadata.items():
            if metadata["name"] == model_name and metadata.get("is_active", False):
                active_version = version_id
                break
                
        if not active_version:
            raise ValueError(f"No active model found for {model_name}")
            
        # Load model if not already in memory
        if active_version not in self.active_models:
            self.active_models[active_version] = self.load_model(active_version)
            
        return active_version, self.active_models[active_version]
        
    def activate_model(self, version_id: str) -> None:
        """
        Set a model version as active.
        
        Args:
            version_id: Version ID of the model to activate
            
        Raises:
            ValueError: If model version not found
        """
        if version_id not in self.models_metadata:
            raise ValueError(f"Model version {version_id} not found")
            
        # Deactivate current active model with same name
        model_name = self.models_metadata[version_id]["name"]
        for vid, metadata in self.models_metadata.items():
            if metadata["name"] == model_name and metadata.get("is_active", False):
                metadata["is_active"] = False
                
        # Activate the specified model
        self.models_metadata[version_id]["is_active"] = True
        self._save_metadata()
        
    def list_models(self, model_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available models with metadata.
        
        Args:
            model_name: Filter by model name (optional)
            
        Returns:
            List[Dict[str, Any]]: List of model metadata
        """
        result = []
        
        for version_id, metadata in self.models_metadata.items():
            if model_name is None or metadata["name"] == model_name:
                result.append(metadata)
                
        return sorted(result, key=lambda x: x["created_at"], reverse=True)
```

### 2.2 ML Training Pipeline

```python
# src/goob_ai/ml/training_pipeline.py
from typing import Dict, Any, List, Optional, Tuple, Union, Callable
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.base import BaseEstimator
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.metrics import make_scorer, accuracy_score, precision_score, recall_score, f1_score
from .model_manager import ModelManager

class MLTrainingPipeline:
    """Pipeline for training and evaluating ML models."""
    
    def __init__(self, model_manager: ModelManager) -> None:
        """
        Initialize the training pipeline.
        
        Args:
            model_manager: Model manager instance
        """
        self.model_manager = model_manager
        self.scoring_metrics = {
            'accuracy': make_scorer(accuracy_score),
            'precision': make_scorer(precision_score, average='weighted'),
            'recall': make_scorer(recall_score, average='weighted'),
            'f1': make_scorer(f1_score, average='weighted')
        }
        
    def train_model(self, model_name: str, model: BaseEstimator, 
                   X: pd.DataFrame, y: pd.Series,
                   param_grid: Optional[Dict[str, List[Any]]] = None,
                   test_size: float = 0.2,
                   random_state: int = 42,
                   custom_metrics: Optional[Dict[str, Callable]] = None) -> Dict[str, Any]:
        """
        Train a model with optional hyperparameter optimization.
        
        Args:
            model_name: Name for the model
            model: Scikit-learn model to train
            X: Feature DataFrame
            y: Target Series
            param_grid: Parameter grid for hyperparameter optimization
            test_size: Proportion of data to use for testing
            random_state: Random state for reproducibility
            custom_metrics: Additional custom metrics to calculate
            
        Returns:
            Dict[str, Any]: Training results including model version ID
        """
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        # Train model with or without hyperparameter optimization
        if param_grid:
            # Create grid search with cross-validation
            grid_search = GridSearchCV(
                model, param_grid, 
                scoring=self.scoring_metrics, 
                refit='f1',  # Refit on best model according to F1 score
                cv=5,
                n_jobs=-1
            )
            
            # Fit grid search
            grid_search.fit(X_train, y_train)
            
            # Get best model and parameters
            best_model = grid_search.best_estimator_
            best_params = grid_search.best_params_
            cv_results = grid_search.cv_results_
        else:
            # Train model directly
            model.fit(X_train, y_train)
            best_model = model
            best_params = None
            cv_results = None
            
        # Evaluate on test set
        y_pred = best_model.predict(X_test)
        
        # Calculate performance metrics
        performance_metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, average='weighted'),
            'recall': recall_score(y_test, y_pred, average='weighted'),
            'f1': f1_score(y_test, y_pred, average='weighted')
        }
        
        # Add custom metrics if provided
        if custom_metrics:
            for metric_name, metric_func in custom_metrics.items():
                performance_metrics[metric_name] = metric_func(y_test, y_pred)
                
        # Create metadata
        metadata = {
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'features': list(X.columns),
            'best_parameters': best_params,
            'target_distribution': y.value_counts().to_dict(),
            'feature_importance': self._get_feature_importance(best_model, X.columns)
        }
        
        # Save model
        version_id = self.model_manager.save_model(
            model_name=model_name,
            model=best_model,
            performance_metrics=performance_metrics,
            metadata=metadata
        )
        
        # Return results
        return {
            'version_id': version_id,
            'performance_metrics': performance_metrics,
            'best_parameters': best_params,
            'cv_results': cv_results,
            'metadata': metadata
        }
        
    def _get_feature_importance(self, model: BaseEstimator, 
                               feature_names: List[str]) -> Optional[Dict[str, float]]:
        """
        Extract feature importance if available.
        
        Args:
            model: Trained model
            feature_names: List of feature names
            
        Returns:
            Optional[Dict[str, float]]: Feature importance dictionary or None
        """
        # Try to extract feature importance based on model type
        if hasattr(model, 'feature_importances_'):
            return dict(zip(feature_names, model.feature_importances_))
        elif hasattr(model, 'coef_'):
            # For linear models
            if model.coef_.ndim > 1:
                # For multi-class problems, average across classes
                importance = np.abs(model.coef_).mean(axis=0)
            else:
                importance = np.abs(model.coef_)
            return dict(zip(feature_names, importance))
        else:
            return None
```

### 2.3 Model Evaluation

```python
# src/goob_ai/ml/evaluation.py
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.base import BaseEstimator
from .model_manager import ModelManager

class ModelEvaluator:
    """Evaluates and compares model performance."""
    
    def __init__(self, model_manager: ModelManager) -> None:
        """
        Initialize the model evaluator.
        
        Args:
            model_manager: Model manager instance
        """
        self.model_manager = model_manager
        
    def evaluate_model(self, version_id: str, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """
        Evaluate a model on a dataset.
        
        Args:
            version_id: Model version ID
            X: Feature DataFrame
            y: Target Series
            
        Returns:
            Dict[str, Any]: Evaluation results
        """
        # Load model
        model = self.model_manager.load_model(version_id)
        
        # Make predictions
        y_pred = model.predict(X)
        
        # Create report
        clf_report = classification_report(y, y_pred, output_dict=True)
        
        # Generate confusion matrix
        cm = confusion_matrix(y, y_pred)
        
        # Calculate prediction probabilities if available
        probas = None
        if hasattr(model, 'predict_proba'):
            probas = model.predict_proba(X)
            
        # Get model metadata
        metadata = self.model_manager.models_metadata.get(version_id, {})
        
        return {
            'version_id': version_id,
            'model_name': metadata.get('name', 'Unknown'),
            'classification_report': clf_report,
            'confusion_matrix': cm.tolist(),
            'accuracy': clf_report['accuracy'],
            'prediction_probabilities': probas,
            'sample_count': len(X)
        }
        
    def compare_models(self, version_ids: List[str], X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """
        Compare multiple models on the same dataset.
        
        Args:
            version_ids: List of model version IDs to compare
            X: Feature DataFrame
            y: Target Series
            
        Returns:
            Dict[str, Any]: Comparison results
        """
        results = {}
        
        for version_id in version_ids:
            results[version_id] = self.evaluate_model(version_id, X, y)
            
        # Determine best model based on accuracy
        accuracies = {v_id: res['accuracy'] for v_id, res in results.items()}
        best_model = max(accuracies.items(), key=lambda x: x[1])[0]
        
        return {
            'model_results': results,
            'best_model_id': best_model,
            'accuracy_comparison': accuracies
        }
        
    def generate_evaluation_report(self, evaluation_results: Dict[str, Any], 
                                  output_dir: Path) -> Path:
        """
        Generate an evaluation report with visualizations.
        
        Args:
            evaluation_results: Results from evaluate_model
            output_dir: Directory to save report
            
        Returns:
            Path: Path to the generated report
        """
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract data
        version_id = evaluation_results['version_id']
        model_name = evaluation_results['model_name']
        cm = np.array(evaluation_results['confusion_matrix'])
        clf_report = evaluation_results['classification_report']
        
        # Generate confusion matrix plot
        plt.figure(figsize=(8, 6))
        plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
        plt.title(f'Confusion Matrix - {model_name}')
        plt.colorbar()
        
        # Add class labels if available
        classes = list(clf_report.keys())
        classes = [c for c in classes if c not in ['accuracy', 'macro avg', 'weighted avg']]
        
        tick_marks = np.arange(len(classes))
        plt.xticks(tick_marks, classes, rotation=45)
        plt.yticks(tick_marks, classes)
        
        # Add numbers to confusion matrix
        thresh = cm.max() / 2.0
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                plt.text(j, i, format(cm[i, j], 'd'),
                        horizontalalignment="center",
                        color="white" if cm[i, j] > thresh else "black")
                
        plt.tight_layout()
        plt.ylabel('True label')
        plt.xlabel('Predicted label')
        
        # Save plot
        cm_path = output_dir / f"{version_id}_confusion_matrix.png"
        plt.savefig(cm_path)
        plt.close()
        
        # Generate classification report as CSV
        report_df = pd.DataFrame(clf_report).T
        report_path = output_dir / f"{version_id}_classification_report.csv"
        report_df.to_csv(report_path)
        
        # Generate summary report
        summary_path = output_dir / f"{version_id}_summary.txt"
        with open(summary_path, 'w') as f:
            f.write(f"Model Evaluation Report\n")
            f.write(f"=======================\n\n")
            f.write(f"Model: {model_name} (Version: {version_id})\n")
            f.write(f"Accuracy: {clf_report['accuracy']:.4f}\n\n")
            f.write(f"Classification Report:\n")
            f.write(f"---------------------\n")
            for class_name, metrics in clf_report.items():
                if isinstance(metrics, dict):
                    f.write(f"{class_name}:\n")
                    for metric_name, value in metrics.items():
                        if isinstance(value, float):
                            f.write(f"  {metric_name}: {value:.4f}\n")
                        else:
                            f.write(f"  {metric_name}: {value}\n")
            
        return summary_path
```

## Integration with Existing Application

### Service Layer Integration
1. Create a new `MLService` class that will:
   - Coordinate with the `DataManager` to retrieve training data
   - Interface with the ML components for training and prediction
   - Provide results to the UI through the existing service layer architecture

```python
# src/goob_ai/services/ml_service.py
from typing import Dict, Any, List, Optional
import pandas as pd
from pathlib import Path
from ..data.data_manager import DataManager
from ..ml.model_manager import ModelManager
from ..ml.training_pipeline import MLTrainingPipeline
from ..ml.evaluation import ModelEvaluator

class MLService:
    """Service for machine learning operations."""
    
    def __init__(self, data_manager: DataManager, models_dir: Path) -> None:
        """
        Initialize ML service.
        
        Args:
            data_manager: Data manager instance
            models_dir: Directory for model storage
        """
        self.data_manager = data_manager
        self.model_manager = ModelManager(models_dir)
        self.training_pipeline = MLTrainingPipeline(self.model_manager)
        self.model_evaluator = ModelEvaluator(self.model_manager)
        
    def train_battle_prediction_model(self) -> Dict[str, Any]:
        """
        Train a battle prediction model.
        
        Returns:
            Dict[str, Any]: Training results
        """
        # Get battle data
        battle_data = self.data_manager.get_all_battles()
        
        # Convert to DataFrame
        df = pd.DataFrame(battle_data)
        
        # Prepare features and target
        X = df.drop(['outcome', 'id'], axis=1, errors='ignore')
        y = df['outcome']
        
        # Configure model parameters
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(random_state=42)
        
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [None, 10, 20, 30],
            'min_samples_split': [2, 5, 10]
        }
        
        # Train model
        results = self.training_pipeline.train_model(
            model_name='battle_prediction',
            model=model,
            X=X,
            y=y,
            param_grid=param_grid
        )
        
        # Activate the model
        self.model_manager.activate_model(results['version_id'])
        
        return results
        
    def predict_battle_outcome(self, battle_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict battle outcome.
        
        Args:
            battle_conditions: Current battle conditions
            
        Returns:
            Dict[str, Any]: Prediction results
        """
        try:
            # Get active model
            version_id, model = self.model_manager.get_active_model('battle_prediction')
            
            # Convert conditions to DataFrame
            features = pd.DataFrame([battle_conditions])
            
            # Make prediction
            if hasattr(model, 'predict_proba'):
                probas = model.predict_proba(features)[0]
                classes = model.classes_
                prediction_probas = dict(zip(classes, probas))
                predicted_class = classes[probas.argmax()]
            else:
                predicted_class = model.predict(features)[0]
                prediction_probas = {predicted_class: 1.0}
                
            return {
                'predicted_outcome': predicted_class,
                'probabilities': prediction_probas,
                'model_version': version_id
            }
            
        except Exception as e:
            # Log error and return a default prediction
            print(f"Prediction error: {str(e)}")
            return {
                'predicted_outcome': None,
                'probabilities': {},
                'error': str(e)
            }
```

### UI Layer Integration
1. Create new UI components to interact with ML features:
   - Model training controls
   - Prediction results visualization
   - Model performance displays

```python
# Example integration with UI controllers
# src/goob_ai/controllers/ml_controller.py
from typing import Dict, Any
from ..services.ml_service import MLService

class MLController:
    """Controller for ML-related UI interactions."""
    
    def __init__(self, ml_service: MLService) -> None:
        """
        Initialize with ML service.
        
        Args:
            ml_service: ML service instance
        """
        self.ml_service = ml_service
        
    def handle_train_model_request(self) -> Dict[str, Any]:
        """
        Handle user request to train a model.
        
        Returns:
            Dict[str, Any]: Status and results
        """
        try:
            results = self.ml_service.train_battle_prediction_model()
            return {
                'status': 'success',
                'results': results
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
            
    def handle_prediction_request(self, battle_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle prediction request from UI.
        
        Args:
            battle_conditions: Battle conditions from UI
            
        Returns:
            Dict[str, Any]: Prediction results
        """
        return self.ml_service.predict_battle_outcome(battle_conditions)
```

## Implementation Steps

### Week 1: ML Infrastructure (Days 1-5)
1. Set up ML file structure
2. Implement `ModelManager` class
3. Create testing framework for ML components
4. Add model serialization and versioning

### Week 2: Training Pipeline (Days 6-10)
1. Implement `MLTrainingPipeline` class
2. Create hyperparameter optimization framework
3. Add performance metrics calculation
4. Implement feature importance extraction

### Week 3: Integration & UI (Days 11-15)
1. Implement `MLService` class
2. Create UI components for ML features
3. Add model evaluation visualization
4. Integrate with existing service layer

## Dependencies
- NumPy (1.20+)
- Pandas (1.3+)
- Scikit-learn (0.24+)
- Matplotlib (3.4+)
- Joblib (1.0+)

## Testing Strategy
1. Unit tests for model management functions
2. Integration tests with sample models
3. End-to-end tests for training and prediction
4. Performance tests for model loading times

## Success Criteria
1. Model management functions pass all tests
2. Training pipeline successfully optimizes hyperparameters
3. Model versions can be saved and loaded reliably
4. UI components correctly display prediction results
5. Integration with service layer works seamlessly 