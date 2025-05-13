import json
import os
import hashlib
from typing import Callable, Any, Optional
from functools import wraps

def generate_cache_key(func: Callable, *args, **kwargs) -> str:
    """
    Generate a stable cache key from function and its arguments.
    
    Args:
        func (Callable): The function being cached
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        str: A stable hash key
    """
    # Get class name if it's a method
    class_name = ""
    if args and hasattr(args[0], '__class__'):
        class_name = args[0].__class__.__name__
    
    # Create a custom JSON encoder to handle object instances
    class ObjectEncoder(json.JSONEncoder):
        def default(self, obj):
            if hasattr(obj, '__class__'):
                return f"{obj.__class__.__name__}"
            return str(obj)
    
    # Create a stable string representation of arguments
    args_str = json.dumps(args, sort_keys=True, cls=ObjectEncoder)
    kwargs_str = json.dumps(kwargs, sort_keys=True, cls=ObjectEncoder)
    
    # Combine all components
    key_string = f"{class_name}_{func.__name__}_{args_str}_{kwargs_str}"
    
    # Create a hash of the key string
    return hashlib.md5(key_string.encode()).hexdigest()

def cache_json_result(cache_dir: str = "cache") -> Callable:
    """
    Decorator that caches function results in JSON files.
    
    Args:
        cache_dir (str): Directory to store cache files. Defaults to "cache".
    
    Returns:
        Callable: Decorated function that implements caching.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Create cache directory if it doesn't exist
            os.makedirs(cache_dir, exist_ok=True)
            
            # Generate cache key
            cache_key = generate_cache_key(func, *args, **kwargs)
            cache_file = os.path.join(cache_dir, f"{cache_key}.json")
            
            # Check if cache exists
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except json.JSONDecodeError:
                    # If cache file is corrupted, remove it and continue
                    os.remove(cache_file)
            
            # If no cache exists or it was corrupted, run the function
            result = func(*args, **kwargs)
            
            # Save result to cache
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            except (TypeError, ValueError) as e:
                print(f"Warning: Could not cache result: {e}")
            
            return result
        
        return wrapper
    return decorator

def get_cached_result(
    func: Callable,
    *args,
    cache_dir: str = "cache",
    **kwargs
) -> Any:
    """
    Function that implements caching for any function.
    
    Args:
        func (Callable): Function to cache
        *args: Positional arguments for the function
        cache_dir (str): Directory to store cache files
        **kwargs: Keyword arguments for the function
    
    Returns:
        Any: Cached or newly computed result
    """
    # Create cache directory if it doesn't exist
    os.makedirs(cache_dir, exist_ok=True)
    
    # Generate cache key
    cache_key = generate_cache_key(func, *args, **kwargs)
    cache_file = os.path.join(cache_dir, f"{cache_key}.json")
    
    # Check if cache exists
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            # If cache file is corrupted, remove it and continue
            os.remove(cache_file)
    
    # If no cache exists or it was corrupted, run the function
    result = func(*args, **kwargs)
    
    # Save result to cache
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except (TypeError, ValueError) as e:
        print(f"Warning: Could not cache result: {e}")
    
    return result