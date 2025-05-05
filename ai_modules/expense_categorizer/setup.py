#!/usr/bin/env python3
"""
NLTK Setup Script

This script ensures that all required NLTK resources are properly downloaded
and accessible in the Docker container before the application starts.
"""

import os
import sys
import logging
import nltk
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("nltk_setup")

def setup_nltk_data():
    """Set up NLTK data paths and download required resources"""
    # Get NLTK_DATA from environment or use default
    nltk_data_path = os.environ.get('NLTK_DATA', '/app/nltk_data')
    
    # Create directory if it doesn't exist
    os.makedirs(nltk_data_path, exist_ok=True)
    logger.info(f"Using NLTK data directory: {nltk_data_path}")
    
    # Set NLTK data path
    nltk.data.path = [nltk_data_path]
    
    # Create required directories
    corpus_dir = os.path.join(nltk_data_path, 'corpora')
    tokenizers_dir = os.path.join(nltk_data_path, 'tokenizers')
    
    os.makedirs(corpus_dir, exist_ok=True)
    os.makedirs(tokenizers_dir, exist_ok=True)
    
    # Download required resources
    resources = [
        ('stopwords', 'corpora/stopwords'),
        ('wordnet', 'corpora/wordnet'),
        ('omw-1.4', 'corpora/omw-1.4'),
        ('punkt', 'tokenizers/punkt')
    ]
    
    for resource_name, resource_path in resources:
        logger.info(f"Downloading {resource_name}...")
        try:
            nltk.download(resource_name, download_dir=nltk_data_path)
            
            # Verify resource was downloaded successfully
            full_path = os.path.join(nltk_data_path, resource_path)
            if os.path.exists(full_path):
                logger.info(f"Successfully downloaded {resource_name} to {full_path}")
            else:
                logger.error(f"Resource directory not found after download: {full_path}")
        except Exception as e:
            logger.error(f"Error downloading {resource_name}: {e}")
    
    # Special handling for wordnet/omw as they can be problematic
    try:
        # Verify wordnet with a test use
        from nltk.corpus import wordnet as wn
        test_synsets = wn.synsets('test')
        if test_synsets:
            logger.info(f"WordNet verification successful: found {len(test_synsets)} synsets for 'test'")
        else:
            logger.warning("WordNet is accessible but returned no synsets")
    except Exception as e:
        logger.error(f"WordNet test failed: {e}")
    
    # Set permissions to ensure resources are accessible by all processes
    try:
        shutil.chown(nltk_data_path, user=os.environ.get('USER', 'root'), group=os.environ.get('GROUP', 'root'))
        os.chmod(nltk_data_path, 0o777)
        logger.info(f"Set permissions for {nltk_data_path}")
        
        # Recursively set permissions for all subdirectories
        for root, dirs, files in os.walk(nltk_data_path):
            for d in dirs:
                os.chmod(os.path.join(root, d), 0o777)
            for f in files:
                os.chmod(os.path.join(root, f), 0o777)
    except Exception as e:
        logger.error(f"Error setting permissions: {e}")

if __name__ == "__main__":
    logger.info("Starting NLTK resource setup...")
    setup_nltk_data()
    logger.info("NLTK setup completed.") 