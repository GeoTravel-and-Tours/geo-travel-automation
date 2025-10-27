# src/utils/cleanup.py

import os
import time
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import logging


class CleanupManager:
    """
    Centralized cleanup utility for the entire framework.
    Simple, robust, and easy to maintain.
    """
    
    def __init__(self, retention_days=30, logger=None, base_dir=None):
        self.retention_days = retention_days
        self.logger = logger or self._setup_logger()
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parent.parent.parent
        
        # Define cleanup targets
        self.cleanup_targets = {
            "logs": {
                "directory": self.base_dir / "logs",
                "patterns": ["*.log", "*.txt"],
            },
            "reports": {
                "directory": self.base_dir / "reports", 
                "patterns": ["*.json", "*.html", "*.xml"],
            },
            "screenshots": {
                "directory": self.base_dir / "reports" / "screenshots",
                "patterns": ["*.png", "*.jpg", "*.jpeg"],
                "recursive": True,
            }
        }

    def _setup_logger(self):
        """Setup a simple logger"""
        logger = logging.getLogger("CleanupManager")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def cleanup_all(self, dry_run=False, targets=None):
        """
        Clean up all file types.
        Returns summary statistics.
        """
        self.logger.info(f"🧹 Starting cleanup - Retention: {self.retention_days} days | Dry run: {dry_run}")
        
        stats = {}
        selected_targets = targets or list(self.cleanup_targets.keys())
        
        for target_name in selected_targets:
            config = self.cleanup_targets.get(target_name)
            if not config:
                continue
                
            deleted_count = self._cleanup_target(config, dry_run)
            stats[target_name] = {
                "deleted": deleted_count,
                "directory": str(config["directory"])
            }
            
            action = "would be" if dry_run else ""
            self.logger.info(f"  {target_name}: {deleted_count} files {action} deleted")
        
        total_deleted = sum(stat["deleted"] for stat in stats.values())
        
        if dry_run:
            self.logger.info(f"Dry run complete: {total_deleted} files would be deleted")
        else:
            self.logger.info(f"Cleanup complete: {total_deleted} files deleted")
            
        return stats

    def _cleanup_target(self, config, dry_run=False):
        """Clean up files for a specific target"""
        directory = Path(config["directory"])
        patterns = config.get("patterns", ["*"])
        recursive = config.get("recursive", False)
        
        if not directory.exists():
            self.logger.debug(f"Directory not found: {directory}")
            return 0

        deleted_count = 0
        cutoff_time = time.time() - (self.retention_days * 24 * 60 * 60)

        for pattern in patterns:
            # Get files matching pattern
            files = directory.rglob(pattern) if recursive else directory.glob(pattern)
            
            for file_path in files:
                if not file_path.is_file():
                    continue  # Skip directories
                    
                try:
                    # Check if file is older than retention period
                    if file_path.stat().st_mtime < cutoff_time:
                        if dry_run:
                            self.logger.info(f"DRY RUN: Would delete {file_path}")
                        else:
                            file_path.unlink()
                            self.logger.debug(f"Deleted: {file_path}")
                        deleted_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to delete {file_path}: {e}")

        return deleted_count

    def get_cleanup_stats(self):
        """Get statistics about files that would be cleaned up"""
        stats = {}
        
        for target_name, config in self.cleanup_targets.items():
            directory = Path(config["directory"])
            recursive = config.get("recursive", False)
            
            if not directory.exists():
                stats[target_name] = {
                    "exists": False,
                    "file_count": 0,
                    "total_size_mb": 0.0,
                    "directory": str(directory)
                }
                continue

            total_size = 0
            file_count = 0
            cutoff_time = time.time() - (self.retention_days * 24 * 60 * 60)
            
            for pattern in config["patterns"]:
                files = directory.rglob(pattern) if recursive else directory.glob(pattern)
                
                for file_path in files:
                    if file_path.is_file():
                        try:
                            # Only count files that would be cleaned up
                            if file_path.stat().st_mtime < cutoff_time:
                                file_count += 1
                                total_size += file_path.stat().st_size
                        except Exception:
                            pass

            stats[target_name] = {
                "exists": True,
                "file_count": file_count,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "directory": str(directory)
            }
        
        return stats

    def cleanup_old_files(self, directory, patterns, recursive=False, dry_run=False):
        """
        Generic method to clean files in any directory.
        Useful for other components to call.
        """
        config = {
            "directory": directory,
            "patterns": patterns,
            "recursive": recursive
        }
        return self._cleanup_target(config, dry_run)


# Factory function to avoid circular imports
_cleanup_manager_instance = None

def get_cleanup_manager(retention_days=30):
    """Get cleanup manager instance"""
    global _cleanup_manager_instance
    if _cleanup_manager_instance is None:
        _cleanup_manager_instance = CleanupManager(retention_days=retention_days)
    return _cleanup_manager_instance