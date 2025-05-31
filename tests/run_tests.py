#!/usr/bin/env python3
"""
Test runner script for TCG Agent Test Suite
Provides easy test execution with different modes and reporting
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_tests(test_type="all", verbose=False, integration=False, output_file=None):
    """
    Run tests with specified parameters
    
    Args:
        test_type: Type of tests to run ("all", "unit", "integration", "gumgum", "shopify", "langfuse", "remix")
        verbose: Enable verbose output
        integration: Include integration tests (requires real credentials)
        output_file: Output file for test results
    """
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test directory
    test_dir = Path(__file__).parent
    cmd.append(str(test_dir))
    
    # Configure output
    if verbose:
        cmd.extend(["-v", "-s"])
    else:
        cmd.append("-v")
    
    # Add markers based on test type
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
        integration = True  # Force integration mode
    elif test_type == "gumgum":
        cmd.append("test_gumgum_integration.py")
    elif test_type == "shopify":
        cmd.append("test_shopify_mcp.py")
    elif test_type == "langfuse":
        cmd.append("test_langfuse_integration.py")
    elif test_type == "remix":
        cmd.append("test_shopify_remix_integration.py")
    
    # Skip integration tests if not explicitly requested
    if not integration:
        cmd.extend(["-m", "not integration"])
    
    # Add output file if specified
    if output_file:
        cmd.extend(["--junit-xml", output_file])
    
    # Add colored output
    cmd.append("--color=yes")
    
    # Show test summary
    cmd.append("--tb=short")
    
    print(f"Running TCG Agent tests...")
    print(f"Command: {' '.join(cmd)}")
    print(f"Test type: {test_type}")
    print(f"Integration tests: {'enabled' if integration else 'disabled'}")
    print("-" * 50)
    
    # Run tests
    try:
        result = subprocess.run(cmd, cwd=test_dir.parent)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

def check_dependencies():
    """Check if test dependencies are installed"""
    try:
        import pytest
        import requests
        import boto3
        print("✅ Test dependencies are available")
        return True
    except ImportError as e:
        print(f"❌ Missing test dependencies: {e}")
        print("Install with: pip install -r tests/requirements.txt")
        return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="TCG Agent Test Runner")
    
    parser.add_argument(
        "--type", 
        choices=["all", "unit", "integration", "gumgum", "shopify", "langfuse", "remix"],
        default="all",
        help="Type of tests to run (default: all)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--integration", "-i",
        action="store_true",
        help="Include integration tests (requires real API credentials)"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output file for test results (JUnit XML format)"
    )
    
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check if test dependencies are installed"
    )
    
    args = parser.parse_args()
    
    # Check dependencies if requested
    if args.check_deps:
        return 0 if check_dependencies() else 1
    
    # Check dependencies before running tests
    if not check_dependencies():
        return 1
    
    # Run tests
    return run_tests(
        test_type=args.type,
        verbose=args.verbose,
        integration=args.integration,
        output_file=args.output
    )

if __name__ == "__main__":
    sys.exit(main())
