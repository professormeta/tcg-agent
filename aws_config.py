#!/usr/bin/env python3
"""
AWS Configuration Module

Sets AWS region configuration for all boto3 clients to ensure consistent region usage
across the application, particularly for Bedrock model access.
"""

import os
import logging

# Configure logging
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Set AWS region for all boto3 clients
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
logger.info(f"AWS region set to {os.environ['AWS_DEFAULT_REGION']}")

# Set Bedrock-specific environment variables
os.environ['BEDROCK_AWS_REGION'] = 'us-east-1'
logger.info(f"Bedrock AWS region set to {os.environ['BEDROCK_AWS_REGION']}")
