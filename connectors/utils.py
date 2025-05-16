"""
Utility functions for API connectors
"""

import logging
import concurrent.futures
from typing import List, Dict, Callable, Any, TypeVar, Generic

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')

def parallel_execution(items: List[T], 
                       worker_func: Callable[[T], R], 
                       max_workers: int = 5, 
                       timeout: int = 30,
                       description: str = "items") -> Dict[T, R]:
    """
    Execute a function in parallel for a list of items
    
    Args:
        items: List of items to process
        worker_func: Function to execute for each item
        max_workers: Maximum number of parallel workers
        timeout: Maximum execution time in seconds
        description: Description of items for logging
        
    Returns:
        Dict: Mapping of input items to their results
    """
    if not items:
        return {}
        
    results = {}
    errors = []
    
    logger.info(f"Starting parallel execution for {len(items)} {description} with {max_workers} workers")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_item = {executor.submit(worker_func, item): item for item in items}
        
        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_item, timeout=timeout):
            item = future_to_item[future]
            try:
                result = future.result()
                results[item] = result
            except Exception as e:
                errors.append((item, str(e)))
                logger.error(f"Error processing {description} {item}: {str(e)}")
                
    if errors:
        logger.warning(f"Completed parallel execution with {len(errors)} errors: {len(items) - len(errors)} successful")
    else:
        logger.info(f"Completed parallel execution of {len(items)} {description} successfully")
        
    return results

def batch_process(items: List[T], 
                  batch_size: int,
                  process_func: Callable[[List[T]], Dict[T, R]]) -> Dict[T, R]:
    """
    Process items in batches to avoid overwhelming APIs
    
    Args:
        items: List of items to process
        batch_size: Size of each batch
        process_func: Function to process each batch
        
    Returns:
        Dict: Combined results from all batches
    """
    results = {}
    
    # Process in batches
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = process_func(batch)
        results.update(batch_results)
        
    return results 