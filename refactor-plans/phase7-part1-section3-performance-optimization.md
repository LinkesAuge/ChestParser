# Phase 7 Part 1 - Section 3: Performance Optimization

## Overview
This document details the implementation of performance optimization techniques for the advanced analytics and machine learning capabilities in the Total Battle Analyzer application. These optimizations will ensure that computationally intensive operations run efficiently, providing users with responsive analytics even when dealing with large datasets.

## Key Components

### 1. Caching System
- In-memory caching for frequent calculations
- Persistent caching for long-term storage
- Cache invalidation strategies
- TTL (Time-To-Live) management

### 2. Data Processing Optimization
- Vectorized operations
- Batch processing for large datasets
- Database query optimization
- Data preprocessing improvements

### 3. Parallel Processing
- Multi-threading for I/O-bound operations
- Multiprocessing for CPU-bound tasks
- Task distribution and management
- Resource management and throttling

### 4. Performance Monitoring
- Execution time tracking
- Memory usage monitoring
- Bottleneck identification
- Resource utilization analysis

## Implementation Details

### 3.1 Caching System

```python
# src/goob_ai/cache/cache_manager.py
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
import time
import pickle
import hashlib
import functools
from pathlib import Path
import redis
from functools import lru_cache

class CacheManager:
    """Central caching system for analytics results."""
    
    def __init__(self, cache_dir: Path, redis_url: Optional[str] = None) -> None:
        """
        Initialize the cache manager.
        
        Args:
            cache_dir: Directory for persistent cache storage
            redis_url: Optional Redis connection URL for distributed caching
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Redis connection if URL provided
        self.redis = None
        if redis_url:
            try:
                self.redis = redis.from_url(redis_url)
                self.redis.ping()  # Test connection
            except Exception as e:
                print(f"Redis connection failed: {str(e)}")
                self.redis = None
                
        # In-memory cache for fastest access
        self.memory_cache: Dict[str, Tuple[Any, float]] = {}
        
    def _generate_key(self, prefix: str, args: Tuple, kwargs: Dict) -> str:
        """
        Generate a cache key from function arguments.
        
        Args:
            prefix: Function name or prefix
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            str: Unique cache key
        """
        # Create a string representation of arguments
        key_parts = [prefix]
        
        # Add positional args
        for arg in args:
            key_parts.append(str(arg))
            
        # Add keyword args (sorted for consistency)
        for k in sorted(kwargs.keys()):
            key_parts.append(f"{k}={kwargs[k]}")
            
        # Generate MD5 hash of the combined string
        key_string = '_'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
        
    def get_from_cache(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache hierarchy.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[Any]: Cached value or None if not found
        """
        # Try memory cache first (fastest)
        if key in self.memory_cache:
            value, expiry = self.memory_cache[key]
            if expiry == 0 or expiry > time.time():
                return value
            else:
                # Expired, remove from memory cache
                del self.memory_cache[key]
                
        # Try Redis next if available
        if self.redis:
            cached_value = self.redis.get(key)
            if cached_value:
                try:
                    value = pickle.loads(cached_value)
                    # Store in memory cache for faster future access
                    self.memory_cache[key] = (value, 0)  # No expiry in memory cache
                    return value
                except Exception:
                    pass
                    
        # Try file cache last
        cache_file = self.cache_dir / f"{key}.cache"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                    # Check if expired
                    if data['expiry'] == 0 or data['expiry'] > time.time():
                        value = data['value']
                        # Store in memory cache for faster future access
                        self.memory_cache[key] = (value, data['expiry'])
                        return value
                    else:
                        # Expired, remove the file
                        cache_file.unlink(missing_ok=True)
            except Exception:
                pass
                
        return None
        
    def store_in_cache(self, key: str, value: Any, ttl: int = 0) -> None:
        """
        Store a value in the cache hierarchy.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (0 = no expiry)
        """
        # Calculate expiry time
        expiry = 0 if ttl == 0 else time.time() + ttl
        
        # Store in memory cache
        self.memory_cache[key] = (value, expiry)
        
        # Store in Redis if available
        if self.redis:
            try:
                pickled_value = pickle.dumps(value)
                if ttl > 0:
                    self.redis.setex(key, ttl, pickled_value)
                else:
                    self.redis.set(key, pickled_value)
            except Exception as e:
                print(f"Redis caching error: {str(e)}")
                
        # Store in file cache
        cache_file = self.cache_dir / f"{key}.cache"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump({'value': value, 'expiry': expiry}, f)
        except Exception as e:
            print(f"File caching error: {str(e)}")
            
    def invalidate_cache(self, key_prefix: str = "") -> None:
        """
        Invalidate cache entries starting with prefix.
        
        Args:
            key_prefix: Prefix of keys to invalidate (empty for all)
        """
        # Clear memory cache
        if key_prefix:
            self.memory_cache = {k: v for k, v in self.memory_cache.items() 
                               if not k.startswith(key_prefix)}
        else:
            self.memory_cache.clear()
            
        # Clear Redis cache if available
        if self.redis:
            try:
                if key_prefix:
                    keys = self.redis.keys(f"{key_prefix}*")
                    if keys:
                        self.redis.delete(*keys)
                else:
                    self.redis.flushdb()
            except Exception as e:
                print(f"Redis invalidation error: {str(e)}")
                
        # Clear file cache
        try:
            if key_prefix:
                for cache_file in self.cache_dir.glob(f"{key_prefix}*.cache"):
                    cache_file.unlink()
            else:
                for cache_file in self.cache_dir.glob("*.cache"):
                    cache_file.unlink()
        except Exception as e:
            print(f"File cache invalidation error: {str(e)}")
            
    def cached(self, ttl: int = 3600, prefix: Optional[str] = None):
        """
        Decorator to cache function results.
        
        Args:
            ttl: Time to live in seconds
            prefix: Cache key prefix (defaults to function name)
            
        Returns:
            Callable: Decorated function
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                key_prefix = prefix or func.__name__
                key = self._generate_key(key_prefix, args, kwargs)
                
                # Try to get from cache
                cached_result = self.get_from_cache(key)
                if cached_result is not None:
                    return cached_result
                    
                # Execute function and cache result
                result = func(*args, **kwargs)
                self.store_in_cache(key, result, ttl)
                return result
            return wrapper
        return decorator
```

### 3.2 Data Processing Optimization

```python
# src/goob_ai/processing/data_optimizer.py
from typing import List, Dict, Any, Optional, Callable
import numpy as np
import pandas as pd
from pathlib import Path
from ..cache.cache_manager import CacheManager

class DataOptimizer:
    """Optimizes data processing operations."""
    
    def __init__(self, cache_manager: CacheManager) -> None:
        """
        Initialize the data optimizer.
        
        Args:
            cache_manager: Cache manager instance
        """
        self.cache_manager = cache_manager
        
    def optimize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Optimize a DataFrame for memory usage.
        
        Args:
            df: DataFrame to optimize
            
        Returns:
            pd.DataFrame: Optimized DataFrame
        """
        # Make a copy to avoid modifying the original
        result = df.copy()
        
        # Optimize numeric columns
        for col in result.select_dtypes(include=['int']).columns:
            # Downcast integers to the smallest possible type
            result[col] = pd.to_numeric(result[col], downcast='integer')
            
        for col in result.select_dtypes(include=['float']).columns:
            # Downcast floats to the smallest possible type
            result[col] = pd.to_numeric(result[col], downcast='float')
            
        # Optimize categorical columns
        for col in result.select_dtypes(include=['object']).columns:
            # Check if column has few unique values
            if result[col].nunique() / len(result) < 0.5:  # Less than 50% unique values
                result[col] = result[col].astype('category')
                
        return result
        
    def batch_process(self, data: List[Any], process_func: Callable[[Any], Any], 
                     batch_size: int = 1000) -> List[Any]:
        """
        Process data in batches to reduce memory usage.
        
        Args:
            data: List of data items to process
            process_func: Processing function to apply
            batch_size: Size of each batch
            
        Returns:
            List[Any]: Processed results
        """
        results = []
        
        # Process data in batches
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            batch_results = [process_func(item) for item in batch]
            results.extend(batch_results)
            
        return results
        
    @staticmethod
    def vectorize_operation(func: Callable) -> Callable:
        """
        Decorator to vectorize operations for better performance.
        
        Args:
            func: Function to vectorize
            
        Returns:
            Callable: Vectorized function
        """
        def wrapper(data, *args, **kwargs):
            # Convert to numpy array if not already
            if isinstance(data, list):
                data = np.array(data)
                
            # Apply function using numpy vectorization
            if hasattr(np, func.__name__):
                # Use numpy's built-in function if available
                numpy_func = getattr(np, func.__name__)
                return numpy_func(data, *args, **kwargs)
            else:
                # Use numpy's vectorize function
                vectorized_func = np.vectorize(func)
                return vectorized_func(data, *args, **kwargs)
                
        return wrapper
        
    def precompute_common_aggregations(self, df: pd.DataFrame, 
                                      groupby_cols: List[str], 
                                      agg_funcs: Dict[str, List[str]]) -> Dict[str, pd.DataFrame]:
        """
        Precompute and cache common aggregations.
        
        Args:
            df: Source DataFrame
            groupby_cols: Columns to group by
            agg_funcs: Dictionary of column names and aggregation functions
            
        Returns:
            Dict[str, pd.DataFrame]: Dictionary of cached aggregations
        """
        cache_key = f"agg_{'_'.join(groupby_cols)}_{hash(frozenset(agg_funcs.items()))}"
        
        # Check cache first
        cached_result = self.cache_manager.get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
            
        # Compute aggregations
        results = {}
        for col, funcs in agg_funcs.items():
            agg_df = df.groupby(groupby_cols)[col].agg(funcs).reset_index()
            # Rename columns for clarity
            agg_df.columns = [f"{col}_{func}" if i >= len(groupby_cols) else col_name 
                             for i, (col_name, func) in enumerate(zip(agg_df.columns, funcs))]
            results[col] = agg_df
            
        # Cache results
        self.cache_manager.store_in_cache(cache_key, results, ttl=3600)
        
        return results
```

### 3.3 Parallel Processing

```python
# src/goob_ai/processing/parallel_processor.py
from typing import List, Dict, Any, Optional, Callable, TypeVar, Generic, Iterator
import concurrent.futures
import multiprocessing
import threading
import queue
import time
from tqdm import tqdm

T = TypeVar('T')  # Input type
R = TypeVar('R')  # Result type

class ParallelProcessor:
    """Parallel processing system for analytics."""
    
    def __init__(self, max_workers: Optional[int] = None, 
                use_processes: bool = False) -> None:
        """
        Initialize the parallel processor.
        
        Args:
            max_workers: Maximum number of workers (defaults to CPU count)
            use_processes: Use processes instead of threads
        """
        self.max_workers = max_workers or multiprocessing.cpu_count()
        self.use_processes = use_processes
        
    def process_batch(self, items: List[T], process_func: Callable[[T], R], 
                     show_progress: bool = False) -> List[R]:
        """
        Process items in parallel.
        
        Args:
            items: List of items to process
            process_func: Processing function
            show_progress: Show progress bar
            
        Returns:
            List[R]: Processed results
        """
        executor_class = (concurrent.futures.ProcessPoolExecutor 
                         if self.use_processes else 
                         concurrent.futures.ThreadPoolExecutor)
        
        results = []
        
        with executor_class(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_item = {executor.submit(process_func, item): i for i, item in enumerate(items)}
            
            # Process results as they complete
            if show_progress:
                futures = tqdm(concurrent.futures.as_completed(future_to_item), 
                              total=len(items), desc="Processing")
            else:
                futures = concurrent.futures.as_completed(future_to_item)
                
            # Collect results, preserving original order
            ordered_results = [None] * len(items)
            for future in futures:
                index = future_to_item[future]
                try:
                    result = future.result()
                    ordered_results[index] = result
                except Exception as e:
                    ordered_results[index] = e
                    
            # Filter out exceptions if any
            results = [r for r in ordered_results if not isinstance(r, Exception)]
            
        return results
        
    def process_batched(self, items: List[T], process_func: Callable[[T], R], 
                       batch_size: int = 1000, show_progress: bool = False) -> List[R]:
        """
        Process items in parallel batches to manage memory usage.
        
        Args:
            items: List of items to process
            process_func: Processing function
            batch_size: Size of each batch
            show_progress: Show progress bar
            
        Returns:
            List[R]: Processed results
        """
        all_results = []
        
        # Split items into batches
        batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
        
        if show_progress:
            batches = tqdm(batches, desc="Processing batches")
            
        # Process each batch in parallel
        for batch in batches:
            batch_results = self.process_batch(batch, process_func, show_progress=False)
            all_results.extend(batch_results)
            
        return all_results

class TaskQueue(Generic[T, R]):
    """Task queue for continuous parallel processing."""
    
    def __init__(self, process_func: Callable[[T], R], 
                max_workers: int = None, 
                use_processes: bool = False) -> None:
        """
        Initialize task queue.
        
        Args:
            process_func: Function to process each task
            max_workers: Maximum number of worker threads/processes
            use_processes: Use processes instead of threads
        """
        self.process_func = process_func
        self.max_workers = max_workers or multiprocessing.cpu_count()
        self.use_processes = use_processes
        self.task_queue: queue.Queue = queue.Queue()
        self.result_queue: queue.Queue = queue.Queue()
        self.workers = []
        self.running = False
        
    def _worker_loop(self) -> None:
        """Worker thread/process main loop."""
        while self.running:
            try:
                # Get task with timeout to check running flag periodically
                task_id, task = self.task_queue.get(timeout=0.1)
                try:
                    # Process task
                    result = self.process_func(task)
                    self.result_queue.put((task_id, result))
                except Exception as e:
                    # Put exception in result queue
                    self.result_queue.put((task_id, e))
                finally:
                    self.task_queue.task_done()
            except queue.Empty:
                continue
                
    def start(self) -> None:
        """Start the worker threads/processes."""
        if self.running:
            return
            
        self.running = True
        
        # Create and start workers
        for _ in range(self.max_workers):
            if self.use_processes:
                worker = multiprocessing.Process(target=self._worker_loop)
            else:
                worker = threading.Thread(target=self._worker_loop)
                
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
            
    def stop(self) -> None:
        """Stop the worker threads/processes."""
        self.running = False
        
        # Wait for all workers to finish
        for worker in self.workers:
            if worker.is_alive():
                worker.join(timeout=1.0)
                
        self.workers = []
        
    def add_task(self, task_id: Any, task: T) -> None:
        """
        Add a task to the queue.
        
        Args:
            task_id: Unique identifier for the task
            task: Task data
        """
        self.task_queue.put((task_id, task))
        
    def get_results(self, block: bool = True, timeout: Optional[float] = None) -> Iterator[Tuple[Any, R]]:
        """
        Get completed task results.
        
        Args:
            block: Whether to block waiting for results
            timeout: Timeout for blocking
            
        Returns:
            Iterator[Tuple[Any, R]]: Iterator of (task_id, result) tuples
        """
        while not self.result_queue.empty():
            try:
                yield self.result_queue.get(block=block, timeout=timeout)
                self.result_queue.task_done()
            except queue.Empty:
                break
```

### 3.4 Performance Monitoring

```python
# src/goob_ai/monitoring/performance_monitor.py
from typing import Dict, Any, List, Optional, Callable
import time
import threading
import psutil
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import matplotlib.pyplot as plt
import numpy as np

class Timer:
    """Utility for timing code execution."""
    
    def __init__(self, name: str = "") -> None:
        """
        Initialize timer.
        
        Args:
            name: Timer name for reference
        """
        self.name = name
        self.start_time = 0.0
        self.end_time = 0.0
        self.elapsed = 0.0
        
    def __enter__(self) -> 'Timer':
        """Start timing when entering context."""
        self.start_time = time.time()
        return self
        
    def __exit__(self, *args) -> None:
        """Stop timing when exiting context."""
        self.end_time = time.time()
        self.elapsed = self.end_time - self.start_time
        
    def start(self) -> None:
        """Manually start the timer."""
        self.start_time = time.time()
        
    def stop(self) -> float:
        """
        Manually stop the timer.
        
        Returns:
            float: Elapsed time in seconds
        """
        self.end_time = time.time()
        self.elapsed = self.end_time - self.start_time
        return self.elapsed
        
    def reset(self) -> None:
        """Reset the timer."""
        self.start_time = 0.0
        self.end_time = 0.0
        self.elapsed = 0.0

class PerformanceMonitor:
    """Monitors application performance metrics."""
    
    def __init__(self, log_dir: Path) -> None:
        """
        Initialize performance monitor.
        
        Args:
            log_dir: Directory for performance logs
        """
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        self.logger = logging.getLogger('performance_monitor')
        self.logger.setLevel(logging.INFO)
        
        # Add file handler
        log_file = log_dir / 'performance.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Add formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Performance data
        self.execution_times: Dict[str, List[float]] = {}
        self.memory_usage: List[Dict[str, float]] = []
        
        # Monitoring thread
        self.monitoring = False
        self.monitor_thread = None
        
    def time_function(self, func_name: str = None):
        """
        Decorator to time function execution.
        
        Args:
            func_name: Custom name for the function
            
        Returns:
            Callable: Decorated function
        """
        def decorator(func):
            nonlocal func_name
            if func_name is None:
                func_name = func.__name__
                
            def wrapper(*args, **kwargs):
                with Timer() as timer:
                    result = func(*args, **kwargs)
                    
                # Log and store execution time
                self.log_execution_time(func_name, timer.elapsed)
                return result
            return wrapper
        return decorator
        
    def log_execution_time(self, name: str, elapsed: float) -> None:
        """
        Log function execution time.
        
        Args:
            name: Function name
            elapsed: Execution time in seconds
        """
        if name not in self.execution_times:
            self.execution_times[name] = []
            
        self.execution_times[name].append(elapsed)
        self.logger.info(f"Execution time - {name}: {elapsed:.6f} seconds")
        
    def start_monitoring(self, interval: float = 1.0) -> None:
        """
        Start background monitoring of system resources.
        
        Args:
            interval: Monitoring interval in seconds
        """
        if self.monitoring:
            return
            
        self.monitoring = True
        
        def monitor_resources():
            while self.monitoring:
                # Get current process
                process = psutil.Process()
                
                # Memory usage
                memory_info = process.memory_info()
                memory_percent = process.memory_percent()
                
                # CPU usage
                cpu_percent = process.cpu_percent(interval=0.1)
                
                # Collect data
                data = {
                    'timestamp': time.time(),
                    'rss': memory_info.rss / (1024 * 1024),  # RSS in MB
                    'vms': memory_info.vms / (1024 * 1024),  # VMS in MB
                    'memory_percent': memory_percent,
                    'cpu_percent': cpu_percent
                }
                
                self.memory_usage.append(data)
                
                # Log data
                self.logger.info(f"Memory usage - RSS: {data['rss']:.2f} MB, "
                               f"VMS: {data['vms']:.2f} MB, "
                               f"Memory: {data['memory_percent']:.2f}%, "
                               f"CPU: {data['cpu_percent']:.2f}%")
                
                # Sleep for specified interval
                time.sleep(interval)
                
        # Start monitoring in a separate thread
        self.monitor_thread = threading.Thread(target=monitor_resources)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        self.monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2.0)
            
    def generate_performance_report(self, output_dir: Optional[Path] = None) -> Path:
        """
        Generate performance report with visualizations.
        
        Args:
            output_dir: Output directory (defaults to log_dir)
            
        Returns:
            Path: Path to the generated report
        """
        if output_dir is None:
            output_dir = self.log_dir
            
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / 'performance_report.html'
        
        # Generate execution time visualizations
        if self.execution_times:
            plt.figure(figsize=(12, 6))
            
            # Plot average execution times
            avg_times = {name: np.mean(times) for name, times in self.execution_times.items()}
            names = list(avg_times.keys())
            times = list(avg_times.values())
            
            plt.barh(names, times)
            plt.xlabel('Average Execution Time (seconds)')
            plt.title('Function Performance')
            plt.tight_layout()
            
            exec_time_chart = output_dir / 'execution_times.png'
            plt.savefig(exec_time_chart)
            plt.close()
            
        # Generate memory usage visualization
        if self.memory_usage:
            plt.figure(figsize=(12, 6))
            
            # Extract data
            timestamps = [d['timestamp'] - self.memory_usage[0]['timestamp'] for d in self.memory_usage]
            rss = [d['rss'] for d in self.memory_usage]
            cpu = [d['cpu_percent'] for d in self.memory_usage]
            
            # Plot memory usage
            plt.subplot(2, 1, 1)
            plt.plot(timestamps, rss, 'b-', label='RSS Memory')
            plt.ylabel('Memory Usage (MB)')
            plt.title('Memory and CPU Usage')
            plt.legend()
            
            # Plot CPU usage
            plt.subplot(2, 1, 2)
            plt.plot(timestamps, cpu, 'r-', label='CPU Usage')
            plt.xlabel('Time (seconds)')
            plt.ylabel('CPU Usage (%)')
            plt.legend()
            
            plt.tight_layout()
            
            resource_chart = output_dir / 'resource_usage.png'
            plt.savefig(resource_chart)
            plt.close()
            
        # Generate HTML report
        with open(report_path, 'w') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Performance Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .chart {{ margin: 20px 0; max-width: 100%; }}
    </style>
</head>
<body>
    <h1>Performance Report</h1>
    <h2>Function Execution Times</h2>
    <table>
        <tr>
            <th>Function</th>
            <th>Min (s)</th>
            <th>Max (s)</th>
            <th>Average (s)</th>
            <th>Count</th>
        </tr>
""")
            
            # Add execution time data
            for name, times in self.execution_times.items():
                f.write(f"""        <tr>
            <td>{name}</td>
            <td>{min(times):.6f}</td>
            <td>{max(times):.6f}</td>
            <td>{np.mean(times):.6f}</td>
            <td>{len(times)}</td>
        </tr>
""")
                
            f.write("""    </table>
""")
            
            # Add charts if available
            if self.execution_times:
                f.write(f"""    <h2>Execution Time Chart</h2>
    <img class="chart" src="{exec_time_chart.name}" alt="Execution Times" />
""")
                
            if self.memory_usage:
                f.write(f"""    <h2>Resource Usage</h2>
    <img class="chart" src="{resource_chart.name}" alt="Resource Usage" />
""")
                
            f.write("""</body>
</html>""")
            
        return report_path
```

## Integration with Existing Application

### Service Layer Integration
1. Create a `PerformanceService` class that will:
   - Manage the performance monitoring and optimization components
   - Provide performance metrics to the UI
   - Apply optimization strategies based on application usage patterns

```python
# src/goob_ai/services/performance_service.py
from typing import Dict, Any, List, Optional
from pathlib import Path
import pandas as pd
from ..cache.cache_manager import CacheManager
from ..processing.data_optimizer import DataOptimizer
from ..processing.parallel_processor import ParallelProcessor
from ..monitoring.performance_monitor import PerformanceMonitor

class PerformanceService:
    """Service for performance optimization and monitoring."""
    
    def __init__(self, app_data_dir: Path) -> None:
        """
        Initialize the performance service.
        
        Args:
            app_data_dir: Application data directory
        """
        # Set up directories
        self.cache_dir = app_data_dir / "cache"
        self.log_dir = app_data_dir / "logs" / "performance"
        
        # Initialize components
        self.cache_manager = CacheManager(self.cache_dir)
        self.data_optimizer = DataOptimizer(self.cache_manager)
        self.parallel_processor = ParallelProcessor()
        self.performance_monitor = PerformanceMonitor(self.log_dir)
        
        # Start monitoring
        self.performance_monitor.start_monitoring(interval=5.0)
        
    def optimize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Optimize a DataFrame for better performance.
        
        Args:
            df: Input DataFrame
            
        Returns:
            pd.DataFrame: Optimized DataFrame
        """
        return self.data_optimizer.optimize_dataframe(df)
        
    def process_in_parallel(self, items: List[Any], process_func: callable, 
                           show_progress: bool = False) -> List[Any]:
        """
        Process items in parallel for better performance.
        
        Args:
            items: Items to process
            process_func: Processing function
            show_progress: Show progress bar
            
        Returns:
            List[Any]: Processed results
        """
        return self.parallel_processor.process_batch(items, process_func, show_progress)
        
    def get_execution_time_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Get execution time statistics.
        
        Returns:
            Dict[str, Dict[str, float]]: Statistics by function
        """
        stats = {}
        
        for name, times in self.performance_monitor.execution_times.items():
            if times:
                stats[name] = {
                    'min': min(times),
                    'max': max(times),
                    'avg': sum(times) / len(times),
                    'count': len(times)
                }
                
        return stats
        
    def generate_report(self) -> Path:
        """
        Generate performance report.
        
        Returns:
            Path: Path to the generated report
        """
        return self.performance_monitor.generate_performance_report()
        
    def cleanup(self) -> None:
        """Cleanup resources and stop monitoring."""
        self.performance_monitor.stop_monitoring()
        
    def get_memory_usage(self) -> Dict[str, float]:
        """
        Get current memory usage.
        
        Returns:
            Dict[str, float]: Memory usage metrics
        """
        if not self.performance_monitor.memory_usage:
            return {}
            
        # Return the latest memory usage
        latest = self.performance_monitor.memory_usage[-1]
        return {
            'rss_mb': latest['rss'],
            'vms_mb': latest['vms'],
            'memory_percent': latest['memory_percent'],
            'cpu_percent': latest['cpu_percent']
        }
```

## Implementation Steps

### Week 1: Caching Framework (Days 1-4)
1. Implement `CacheManager` class
2. Create hierarchy of cache levels
3. Add cache invalidation strategies
4. Write comprehensive tests for caching

### Week 2: Processing Optimization (Days 5-8)
1. Implement `DataOptimizer` class
2. Add batch processing capabilities
3. Create data preprocessing optimizations
4. Integrate caching with processing

### Week 3: Parallel Processing & Monitoring (Days 9-12)
1. Implement `ParallelProcessor` class
2. Create task queue for continuous processing
3. Add `PerformanceMonitor` for metrics tracking
4. Develop visualization and reporting

### Week 4: Integration & Testing (Days 13-15)
1. Create `PerformanceService` for service layer integration
2. Integrate monitoring with existing UI
3. Implement performance dashboard
4. Conduct performance benchmarks and optimization

## Dependencies
- NumPy (1.20+)
- Pandas (1.3+)
- Matplotlib (3.4+)
- Redis (optional, for distributed caching)
- psutil (for system monitoring)
- tqdm (for progress visualization)

## Testing Strategy
1. Unit tests for caching functions
2. Integration tests for parallel processing
3. Performance benchmarks to verify optimizations
4. Load testing for scalability

## Success Criteria
1. All critical operations execute within performance targets:
   - Simple analytics: < 1 second
   - Complex analytics: < 5 seconds
   - Batch processing: < 30 seconds for 10,000 records
2. Memory usage remains within acceptable limits
3. Caching improves repeat operation performance by at least 80%
4. Parallel processing scales effectively with available resources 