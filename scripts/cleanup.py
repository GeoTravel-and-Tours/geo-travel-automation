#!/usr/bin/env python3
"""
INDEPENDENT cleanup script - Zero external dependencies
Same interface and naming as original for backward compatibility
"""
import os
import time
import argparse
from pathlib import Path


class CleanupManager:
    """
    Centralized cleanup utility for the entire framework.
    Simple, robust, and easy to maintain.
    SAME CLASS NAME as original for backward compatibility
    """

    def __init__(self, retention_days=30, logger=None, base_dir=None):
        self.retention_days = retention_days
        self.logger = self._setup_logger()  # Simple built-in logging
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        
        # SAME cleanup targets structure as original
        self.cleanup_targets = {
            "logs": {
                "directory": self.base_dir / "logs",
                "patterns": ["*.log", "*.txt"],
            },
            "report_logs": {
                "directory": self.base_dir / "reports" / "logs",
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
            },
            # "docs": {
            #     "directory": self.base_dir / "docs" / "screenshots" / "failures",
            #     "patterns": ["*.png", "*.jpg", "*.jpeg"],
            # },
            # "failed_responses": {
            #     "directory": self.base_dir / "reports" / "failed_responses",
            #     "patterns": ["*.json", "*.txt"],
            #     "recursive": True,
            # },
        }

    def _setup_logger(self):
        """Simple logger without external dependencies"""
        class SimpleLogger:
            def info(self, msg): print(f"INFO: {msg}")
            def debug(self, msg): pass  # Silent in production
            def warning(self, msg): print(f"WARNING: {msg}")
            def error(self, msg): print(f"ERROR: {msg}")
        return SimpleLogger()

    def cleanup_all(self, dry_run=False, targets=None):
        """
        Clean up all file types.
        Returns summary statistics - SAME INTERFACE as original
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
        """Clean up files for a specific target - SAME LOGIC as original"""
        directory = Path(config["directory"])
        patterns = config.get("patterns", ["*"])
        recursive = config.get("recursive", False)
        
        if not directory.exists():
            self.logger.info(f"Directory not found: {directory}")
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
                            self.logger.info(f"Deleted: {file_path}")
                        deleted_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to delete {file_path}: {e}")

        return deleted_count

    def get_cleanup_stats(self):
        """Get statistics about files that would be cleaned up - SAME INTERFACE"""
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
        Useful for other components to call - SAME INTERFACE
        """
        config = {
            "directory": directory,
            "patterns": patterns,
            "recursive": recursive
        }
        return self._cleanup_target(config, dry_run)
    
    def _cleanup_directory(self, directory, patterns=None, recursive=False, dry_run=False):
        """
        Alias method for backward compatibility with reporting module
        """
        if patterns is None:
            patterns = ["*"]

        return self.cleanup_old_files(directory, patterns, recursive, dry_run)


# SAME factory function for backward compatibility
_cleanup_manager_instance = None

def get_cleanup_manager(retention_days=30):
    """Get cleanup manager instance - SAME FUNCTION NAME"""
    global _cleanup_manager_instance
    if _cleanup_manager_instance is None:
        _cleanup_manager_instance = CleanupManager(retention_days=retention_days)
    return _cleanup_manager_instance


def main():
    """Main function - SAME INTERFACE as original script"""
    parser = argparse.ArgumentParser(description="Clean up old test artifacts")
    parser.add_argument(
        "--days", 
        type=int, 
        default=30, 
        help="Delete files older than this number of days (default: 30)"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Show what would be deleted without actually deleting"
    )
    parser.add_argument(
        "--stats", 
        action="store_true", 
        help="Show statistics only"
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        help="Specific targets to clean (e.g., logs screenshots reports)"
    )
    
    args = parser.parse_args()

    # Initialize cleanup manager - SAME CODE as original
    manager = CleanupManager(retention_days=args.days)

    if args.stats:
        # Show statistics - SAME OUTPUT as original
        stats = manager.get_cleanup_stats()
        print("\n📊 CLEANUP STATISTICS")
        print("=" * 50)
        total_files = 0
        total_size = 0
        
        for target, data in stats.items():
            files = data["file_count"]
            size = data["total_size_mb"]
            status = "✅ EXISTS" if data["exists"] else "❌ MISSING"
            
            print(f"  {target.upper():<12} {status:>10}")
            print(f"    Files: {files:>3} | Size: {size:>6} MB")
            if data["exists"]:
                print(f"    Path: {data['directory']}")
            print()
            
            total_files += files
            total_size += size
        
        print("=" * 50)
        print(f"  TOTAL: {total_files} files | {total_size:.1f} MB")
        print(f"  Retention: {args.days} days")
        return

    # Perform cleanup - SAME OUTPUT as original
    print(f"🔍 {'DRY RUN' if args.dry_run else 'CLEANUP'} MODE")
    print(f"📅 Retention period: {args.days} days")
    if args.targets:
        print(f"🎯 Targets: {', '.join(args.targets)}")
    print("=" * 60)

    stats = manager.cleanup_all(dry_run=args.dry_run, targets=args.targets)

    # Show summary - SAME OUTPUT as original
    print("=" * 60)
    total_deleted = sum(target_stats["deleted"] for target_stats in stats.values())
    
    if args.dry_run:
        print(f"📋 DRY RUN COMPLETE: {total_deleted} files would be deleted")
        print("💡 Run without --dry-run to actually delete files")
    else:
        print(f"✅ CLEANUP COMPLETE: {total_deleted} files deleted")


if __name__ == "__main__":
    main()