#!/usr/bin/env python3
"""
Scan and process screenshots from MacOS Photos app
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime

from integrations.macos_photos import MacOSPhotosIntegration, PhotosScreenshotWatcher
from screenshot_processor import ScreenshotProcessor
from database_manager import DatabaseManager
from config_manager import ConfigManager

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Set up logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    parser = argparse.ArgumentParser(description="Scan MacOS Photos for screenshots")
    parser.add_argument('--days', type=int, default=30,
                       help='Number of days to look back (default: 30)')
    parser.add_argument('--limit', type=int, default=50,
                       help='Maximum number of screenshots to process (default: 50)')
    parser.add_argument('--output-dir', type=str,
                       default=os.path.expanduser('~/Desktop/photos_screenshots'),
                       help='Output directory for exported screenshots')
    parser.add_argument('--watch', action='store_true',
                       help='Watch for new screenshots continuously')
    parser.add_argument('--watch-interval', type=int, default=300,
                       help='Check interval in seconds when watching (default: 300)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    logger.info("=" * 60)
    logger.info("MacOS Photos Screenshot Scanner")
    logger.info("=" * 60)
    
    # Initialize components
    try:
        photos = MacOSPhotosIntegration()
        logger.info("✅ Connected to Photos app")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Photos app: {e}")
        sys.exit(1)
    
    # Initialize processor and database
    config_manager = ConfigManager()
    processor = ScreenshotProcessor()
    db_manager = DatabaseManager()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.watch:
        # Watch mode
        logger.info(f"Starting watch mode (checking every {args.watch_interval} seconds)")
        logger.info("Press Ctrl+C to stop")
        
        watcher = PhotosScreenshotWatcher(
            photos, 
            processor, 
            check_interval=args.watch_interval
        )
        
        try:
            import time
            while True:
                logger.info(f"\nChecking for new screenshots at {datetime.now().strftime('%H:%M:%S')}")
                results = watcher.process_new_screenshots(output_dir)
                
                if results['new_screenshots'] > 0:
                    logger.info(f"✅ Processed {results['processed']} new screenshots")
                else:
                    logger.info("No new screenshots found")
                
                time.sleep(args.watch_interval)
                
        except KeyboardInterrupt:
            logger.info("\nStopping watch mode")
            
    else:
        # One-time scan
        logger.info(f"Scanning Photos for screenshots from last {args.days} days")
        logger.info(f"Maximum screenshots to process: {args.limit}")
        
        # Test getting screenshots list first
        logger.info("\nChecking Screenshots album...")
        screenshots = photos.get_recent_screenshots(days=args.days)
        
        if not screenshots:
            logger.warning("No screenshots found in Photos app")
            logger.info("\nTroubleshooting tips:")
            logger.info("1. Make sure Photos app is running")
            logger.info("2. Check if you have a 'Screenshots' album")
            logger.info("3. Grant Terminal/Python access to Photos in System Preferences > Privacy")
            sys.exit(0)
        
        logger.info(f"Found {len(screenshots)} screenshots")
        
        # Show sample of what was found
        logger.info("\nMost recent screenshots:")
        for i, photo in enumerate(screenshots[:5]):
            logger.info(f"  {i+1}. {photo['filename']} - {photo['datetime'].strftime('%Y-%m-%d %H:%M')}")
        
        # Process screenshots
        logger.info(f"\nProcessing up to {args.limit} screenshots...")
        results = photos.scan_and_process_screenshots(
            processor=processor,
            output_dir=output_dir,
            days=args.days,
            limit=args.limit
        )
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("SUMMARY")
        logger.info("="*60)
        logger.info(f"Screenshots processed: {results['processed']}")
        logger.info(f"Errors: {results['errors']}")
        logger.info(f"Output directory: {output_dir}")
        
        if results['processed'] > 0:
            logger.info("\n✅ Screenshots have been:")
            logger.info("  - Exported from Photos to local files")
            logger.info("  - Analyzed with AI")
            logger.info("  - Added to the screenshot database")
            logger.info("\nYou can now view them in the Screenshot Viewer app!")


if __name__ == "__main__":
    main()