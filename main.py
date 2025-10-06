"""
Main entry point for the Risk Assessment Agent.

This module provides the main entry point for both risk assessment
and goal tracking functionality.
"""

import sys
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.cli.assessment_cli import main as assessment_main
from src.cli.tracking_cli import main as tracking_main


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Risk Assessment Agent - Financial risk assessment and goal tracking system"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Assessment command
    assessment_parser = subparsers.add_parser('assessment', help='Run risk assessment')
    assessment_parser.set_defaults(func=assessment_main)
    
    # Tracking command
    tracking_parser = subparsers.add_parser('tracking', help='Track financial goals')
    tracking_parser.add_argument('--single', action='store_true', help='Track a single goal')
    tracking_parser.add_argument('--multi', action='store_true', help='Track multiple goals')
    tracking_parser.add_argument('--user-id', required=True, help='User identifier')
    tracking_parser.add_argument('--data-root', default='./data', help='Data root directory')
    tracking_parser.add_argument('--since', help='Filter transactions since date')
    tracking_parser.add_argument('--out', help='Output file path')
    tracking_parser.add_argument('--assessment-file', help='Assessment file for multi mode')
    tracking_parser.set_defaults(func=tracking_main)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'assessment':
        assessment_main()
    elif args.command == 'tracking':
        # Convert args to tracking_cli format
        tracking_args = argparse.Namespace()
        tracking_args.single = args.single
        tracking_args.multi = args.multi
        tracking_args.user_id = args.user_id
        tracking_args.data_root = args.data_root
        tracking_args.since = args.since
        tracking_args.out = args.out
        tracking_args.assessment_file = args.assessment_file
        
        # Temporarily replace sys.argv for tracking_main
        original_argv = sys.argv
        sys.argv = ['tracking_cli.py'] + [f'--{k.replace("_", "-")}' for k, v in vars(tracking_args).items() if v is not None and v is not False]
        if tracking_args.single:
            sys.argv.append('--single')
        if tracking_args.multi:
            sys.argv.append('--multi')
        
        try:
            tracking_main()
        finally:
            sys.argv = original_argv


if __name__ == "__main__":
    main()
