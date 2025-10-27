# scripts/cleanup.py

#!/usr/bin/env python3
"""
Centralized cleanup script for test artifacts.
Clean, simple, and effective.
"""
import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.utils.cleanup import CleanupManager


def main():
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

    # Initialize cleanup manager
    manager = CleanupManager(retention_days=args.days)

    if args.stats:
        # Show statistics
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

    # Perform cleanup
    print(f"🔍 {'DRY RUN' if args.dry_run else 'CLEANUP'} MODE")
    print(f"📅 Retention period: {args.days} days")
    if args.targets:
        print(f"🎯 Targets: {', '.join(args.targets)}")
    print("=" * 60)

    stats = manager.cleanup_all(dry_run=args.dry_run, targets=args.targets)

    # Show summary
    print("=" * 60)
    total_deleted = sum(target_stats["deleted"] for target_stats in stats.values())
    
    if args.dry_run:
        print(f"📋 DRY RUN COMPLETE: {total_deleted} files would be deleted")
        print("💡 Run without --dry-run to actually delete files")
    else:
        print(f"✅ CLEANUP COMPLETE: {total_deleted} files deleted")


if __name__ == "__main__":
    main()