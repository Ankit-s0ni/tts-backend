"""Voice Manager for dynamic Piper voice loading with LRU caching.

This module provides on-demand loading of Piper TTS voices with an LRU cache
to keep frequently used models in memory. This enables multi-language support
without requiring multiple HTTP servers or pre-loading all voices at startup.

Key features:
- Dynamic voice loading from ONNX model files
- LRU cache (max 5-8 voices) to optimize memory usage
- Thread-safe access for concurrent Celery workers
- Automatic eviction of least-recently-used voices when cache is full
"""
import logging
import os
from collections import OrderedDict
from pathlib import Path
from threading import Lock
from typing import Optional

try:
    from piper.voice import PiperVoice
except ImportError:
    PiperVoice = None  # Will be available after installing piper-tts

_LOGGER = logging.getLogger(__name__)

# Configuration
MAX_CACHED_VOICES = int(os.getenv("MAX_CACHED_VOICES", "5"))
MODELS_BASE_PATH = Path(os.getenv("MODELS_DIR", "/models"))


class VoiceManager:
    """Manages dynamic loading and caching of Piper voices.
    
    Uses an LRU (Least Recently Used) cache to keep frequently accessed
    voices in memory while automatically evicting older ones when the
    cache limit is reached.
    
    Thread-safe for use in multi-worker Celery environments.
    """
    
    def __init__(self, max_cache_size: int = MAX_CACHED_VOICES):
        """Initialize the voice manager.
        
        Args:
            max_cache_size: Maximum number of voices to keep in cache (default: 5)
        """
        self._cache: OrderedDict[str, "PiperVoice"] = OrderedDict()
        self._lock = Lock()
        self._max_cache_size = max_cache_size
        _LOGGER.info(f"VoiceManager initialized with max cache size: {max_cache_size}")
    
    def get_voice(self, model_path: str, use_cuda: bool = False) -> Optional["PiperVoice"]:
        """Get a Piper voice, loading it if necessary.
        
        This method implements LRU caching:
        - If the voice is already cached, it's moved to the end (marked as recently used)
        - If not cached, it's loaded from disk and added to the cache
        - If cache is full, the least recently used voice is evicted
        
        Args:
            model_path: Absolute path to the ONNX model file
            use_cuda: Whether to use GPU acceleration (default: False)
            
        Returns:
            PiperVoice instance, or None if loading fails
            
        Thread-safe: Uses a lock to prevent race conditions in multi-threaded environments.
        """
        if PiperVoice is None:
            _LOGGER.error("piper-tts package not installed. Install with: pip install piper-tts")
            return None
        
        # Normalize path for consistent cache keys
        model_path = str(Path(model_path).resolve())
        
        with self._lock:
            # Check if voice is already cached
            if model_path in self._cache:
                _LOGGER.debug(f"Voice cache HIT: {model_path}")
                # Move to end (mark as recently used)
                self._cache.move_to_end(model_path)
                return self._cache[model_path]
            
            # Voice not in cache - need to load it
            _LOGGER.info(f"Voice cache MISS: Loading {model_path}")
            
            # Verify model file exists
            if not Path(model_path).exists():
                _LOGGER.error(f"Model file not found: {model_path}")
                return None
            
            try:
                # Load the voice model
                voice = PiperVoice.load(model_path, use_cuda=use_cuda)
                
                # Add to cache
                self._cache[model_path] = voice
                _LOGGER.info(f"Loaded voice: {model_path} (cache size: {len(self._cache)})")
                
                # Evict least recently used voice if cache is full
                if len(self._cache) > self._max_cache_size:
                    evicted_path, evicted_voice = self._cache.popitem(last=False)
                    _LOGGER.info(f"Cache full - evicted LRU voice: {evicted_path}")
                    # Clean up resources if needed
                    try:
                        del evicted_voice
                    except Exception:
                        pass
                
                return voice
                
            except Exception as e:
                _LOGGER.error(f"Failed to load voice {model_path}: {e}", exc_info=True)
                return None
    
    def clear_cache(self):
        """Clear all cached voices from memory.
        
        Useful for manual memory management or testing.
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            _LOGGER.info(f"Cleared voice cache ({count} voices removed)")
    
    def get_cache_info(self) -> dict:
        """Get information about the current cache state.
        
        Returns:
            Dictionary with cache statistics including size and loaded models
        """
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self._max_cache_size,
                "cached_models": list(self._cache.keys())
            }


# Global instance - singleton pattern for use across worker processes
_voice_manager_instance: Optional[VoiceManager] = None


def get_voice_manager() -> VoiceManager:
    """Get the global VoiceManager instance.
    
    Creates the instance on first call (lazy initialization).
    This singleton pattern ensures all worker threads share the same cache.
    
    Returns:
        Global VoiceManager instance
    """
    global _voice_manager_instance
    if _voice_manager_instance is None:
        _voice_manager_instance = VoiceManager()
    return _voice_manager_instance
