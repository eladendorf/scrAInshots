#!/usr/bin/env python3
"""
Complete Mind Evolution Pipeline
Runs the full extraction, analysis, and visualization pipeline
"""
import os
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path
import argparse

from config_manager import ConfigManager
from fireflies_extractor import FirefliesExtractor
from email_analyzer import EmailAnalyzer
from gemini_mind_processor import GeminiMindProcessor

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Set up logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('mind_evolution.log')
        ]
    )


def main():
    parser = argparse.ArgumentParser(description="Run complete mind evolution pipeline")
    parser.add_argument('--days', type=int, default=730, 
                       help='Number of days to analyze (default: 730 - 2 years)')
    parser.add_argument('--name', help='Your name for action item detection')
    parser.add_argument('--email', help='Your email for action item detection')
    parser.add_argument('--gemini-key', help='Gemini API key (or set GEMINI_API_KEY env var)')
    parser.add_argument('--skip-extraction', action='store_true', 
                       help='Skip extraction phase if already done')
    parser.add_argument('--skip-analysis', action='store_true',
                       help='Skip email analysis if already done')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    logger.info("=" * 60)
    logger.info("MIND EVOLUTION PIPELINE")
    logger.info("=" * 60)
    
    # Load configuration
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    # Use email from config if not provided
    if not args.email and config.get('email_address'):
        args.email = config['email_address']
        logger.info(f"Using email from config: {args.email}")
    
    # Phase 1: Extract Fireflies meetings
    if not args.skip_extraction:
        logger.info("\n" + "="*60)
        logger.info("PHASE 1: Extracting Fireflies Meetings")
        logger.info("="*60)
        
        try:
            fireflies = FirefliesExtractor(
                user_name=args.name,
                user_email=args.email
            )
            fireflies.run(days_back=args.days)
            logger.info("✅ Fireflies extraction complete")
        except Exception as e:
            logger.error(f"❌ Fireflies extraction failed: {e}")
            if not args.skip_analysis:
                logger.info("Continuing with email analysis...")
    
    # Phase 2: Analyze emails
    if not args.skip_analysis:
        logger.info("\n" + "="*60)
        logger.info("PHASE 2: Analyzing Email Communications")
        logger.info("="*60)
        
        try:
            email_analyzer = EmailAnalyzer()
            email_analyzer.run(days_back=args.days)
            logger.info("✅ Email analysis complete")
        except Exception as e:
            logger.error(f"❌ Email analysis failed: {e}")
            logger.info("Continuing with visualization...")
    
    # Phase 3: Process through Gemini for visualization
    logger.info("\n" + "="*60)
    logger.info("PHASE 3: Creating Mind Maps and Visualizations")
    logger.info("="*60)
    
    try:
        # Check for Gemini API key
        gemini_key = args.gemini_key or os.getenv('GEMINI_API_KEY')
        if not gemini_key:
            logger.error("❌ Gemini API key required! Set GEMINI_API_KEY env var or use --gemini-key")
            return
        
        processor = GeminiMindProcessor(api_key=gemini_key)
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
        
        # Process all months
        results = processor.run(start_date=start_date, end_date=end_date)
        
        logger.info("✅ Mind map generation complete")
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("PIPELINE COMPLETE!")
        logger.info("="*60)
        logger.info("\nOutputs generated:")
        logger.info(f"📁 Fireflies meetings: ~/FirefliesMeetings/")
        logger.info(f"📁 Email analysis: ~/EmailAnalysis/")
        logger.info(f"📁 Mind maps & visualizations: ~/MindMapEvolution/")
        logger.info("\nKey files:")
        logger.info(f"  - Evolution report: ~/MindMapEvolution/evolution_report.md")
        logger.info(f"  - Visualization index: ~/MindMapEvolution/README.md")
        logger.info("\nView your mind maps in any Mermaid-compatible viewer!")
        
    except Exception as e:
        logger.error(f"❌ Visualization generation failed: {e}")
        raise


if __name__ == "__main__":
    main()