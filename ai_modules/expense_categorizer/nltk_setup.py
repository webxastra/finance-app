#!/usr/bin/env python3
"""
NLTK Resource Setup Script

This script ensures all required NLTK resources are properly downloaded and accessible.
It creates the necessary directory structure and verifies each resource works correctly.
"""

import os
import sys
import subprocess
import shutil
import nltk
import logging
from pathlib import Path
import importlib

# Setup logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("nltk_setup")

def create_nltk_directories():
    """Create all necessary NLTK data directories with proper structure"""
    # Standard user directory
    home_dir = str(Path.home())
    user_nltk_dir = os.path.join(home_dir, 'nltk_data')
    
    # Also set up conda environment directory if available
    conda_env = os.environ.get('CONDA_PREFIX')
    conda_nltk_dir = None
    if conda_env:
        conda_nltk_dir = os.path.join(conda_env, 'nltk_data')
    
    # Create main directories
    directories = [user_nltk_dir]
    if conda_nltk_dir:
        directories.append(conda_nltk_dir)
    
    # Create required subdirectories
    for base_dir in directories:
        if not os.path.exists(base_dir):
            os.makedirs(base_dir, exist_ok=True)
            logger.info(f"Created NLTK data directory: {base_dir}")
        
        # Create standard NLTK subdirectories
        for subdir in ['corpora', 'tokenizers', 'taggers', 'chunkers', 'stemmers']:
            subdir_path = os.path.join(base_dir, subdir)
            os.makedirs(subdir_path, exist_ok=True)
            logger.info(f"Created NLTK subdirectory: {subdir_path}")
    
    # Return the created directories
    return user_nltk_dir, conda_nltk_dir

def configure_nltk_paths(user_nltk_dir, conda_nltk_dir=None):
    """Configure NLTK to look in the right places for data"""
    # Clear existing paths to avoid duplicates
    nltk.data.path = []
    
    # First add the specified directories
    nltk.data.path.append(user_nltk_dir)
    if conda_nltk_dir:
        nltk.data.path.append(conda_nltk_dir)
    
    # Standard system directories
    standard_dirs = [
        '/usr/share/nltk_data',
        '/usr/local/share/nltk_data',
        '/usr/lib/nltk_data',
        '/usr/local/lib/nltk_data'
    ]
    
    # Add standard directories if they exist
    for dir_path in standard_dirs:
        if os.path.exists(dir_path) and dir_path not in nltk.data.path:
            nltk.data.path.append(dir_path)
    
    # Set environment variable
    os.environ['NLTK_DATA'] = user_nltk_dir
    
    logger.info(f"NLTK search paths configured: {nltk.data.path}")
    
    return nltk.data.path

def download_resource(resource, target_dir):
    """Download a specific NLTK resource to the target directory"""
    logger.info(f"Downloading {resource} to {target_dir}...")
    try:
        download_result = nltk.download(resource, download_dir=target_dir, quiet=False)
        if download_result:
            logger.info(f"Successfully downloaded {resource}")
            return True
        else:
            logger.warning(f"Download failed for {resource}")
            return False
    except Exception as e:
        logger.error(f"Error downloading {resource}: {str(e)}")
        return False

def verify_wordnet():
    """Explicitly test WordNet functionality by using it"""
    try:
        # Try to import and use wordnet
        from nltk.corpus import wordnet as wn
        synsets = wn.synsets('test')
        if synsets and len(synsets) > 0:
            sample_synset = synsets[0]
            definition = sample_synset.definition()
            lemma_names = sample_synset.lemma_names()
            logger.info(f"✓ WordNet verified! Found {len(synsets)} synsets for 'test'")
            logger.info(f"  First synset: {sample_synset.name()}")
            logger.info(f"  Definition: {definition}")
            logger.info(f"  Lemmas: {lemma_names}")
            return True
        else:
            logger.error("✗ WordNet failed verification - no synsets found")
            return False
    except Exception as e:
        logger.error(f"✗ WordNet verification failed with error: {str(e)}")
        return False

def verify_resource(resource_name, resource_path, verification_func=None):
    """Verify a specific NLTK resource is accessible and working"""
    try:
        # Try to find the resource
        nltk.data.find(resource_path)
        logger.info(f"✓ Resource {resource_name} is accessible at {resource_path}")
        
        # If there's a custom verification function, use it
        if verification_func:
            return verification_func()
        
        return True
    except LookupError as e:
        logger.error(f"✗ Resource {resource_name} verification failed: {str(e)}")
        return False

def create_symlinks(user_nltk_dir, conda_nltk_dir=None):
    """Create symbolic links to ensure correct directory structure"""
    directories = [user_nltk_dir]
    if conda_nltk_dir:
        directories.append(conda_nltk_dir)
    
    for base_dir in directories:
        # WordNet symlinks - omw-1.4 may expect wordnet in its directory
        wordnet_src = os.path.join(base_dir, 'corpora', 'wordnet')
        omw_dir = os.path.join(base_dir, 'corpora', 'omw-1.4')
        wordnet_dest = os.path.join(omw_dir, 'wordnet')
        
        # Create omw directory if it doesn't exist
        os.makedirs(omw_dir, exist_ok=True)
        
        if os.path.exists(wordnet_src) and not os.path.exists(wordnet_dest):
            try:
                # On Windows, may need special permissions or different approach
                if os.name == 'nt':  # Windows
                    # Try directory junction on Windows
                    os.system(f'mklink /J "{wordnet_dest}" "{wordnet_src}"')
                else:
                    # Create symbolic link on Unix-like systems
                    os.symlink(wordnet_src, wordnet_dest)
                logger.info(f"Created symbolic link from {wordnet_src} to {wordnet_dest}")
            except Exception as e:
                logger.error(f"Failed to create symbolic link: {str(e)}")
                # If symlink fails, try a copy as last resort
                try:
                    if os.path.isdir(wordnet_src):
                        shutil.copytree(wordnet_src, wordnet_dest)
                    else:
                        shutil.copy2(wordnet_src, wordnet_dest)
                    logger.info(f"Copied {wordnet_src} to {wordnet_dest} (symlink failed)")
                except Exception as copy_error:
                    logger.error(f"Failed to copy as fallback: {str(copy_error)}")

def direct_system_download(resource, directories):
    """Use system Python to download resources directly"""
    logger.info(f"Attempting direct system download for {resource}...")
    
    for target_dir in directories:
        if not target_dir:
            continue
            
        try:
            # Create subprocess to download the resource
            cmd = f"python -c \"import nltk; nltk.download('{resource}', download_dir='{target_dir}')\""
            result = subprocess.call(cmd, shell=True)
            
            if result == 0:
                logger.info(f"Direct system download of {resource} to {target_dir} succeeded")
                return True
        except Exception as e:
            logger.error(f"Direct system download failed: {str(e)}")
    
    return False

def copy_resource_to_expected_location(resource_name, user_nltk_dir, conda_nltk_dir=None):
    """Try to find and copy resource to expected location if it exists elsewhere"""
    # Possible standard locations
    standard_dirs = [
        '/usr/share/nltk_data',
        '/usr/local/share/nltk_data',
        '/usr/lib/nltk_data',
        '/usr/local/lib/nltk_data'
    ]
    
    # Add anaconda/miniconda system directories
    if 'CONDA_PREFIX' in os.environ:
        conda_base = os.environ['CONDA_PREFIX']
        if conda_base:
            conda_root = os.path.dirname(os.path.dirname(conda_base))
            standard_dirs.extend([
                os.path.join(conda_root, 'nltk_data'),
                os.path.join(conda_root, 'share', 'nltk_data')
            ])
    
    # Add pip installation directory
    try:
        import site
        site_packages = site.getsitepackages()
        for site_pkg in site_packages:
            standard_dirs.append(os.path.join(site_pkg, 'nltk_data'))
    except Exception:
        pass
    
    # Determine resource path pattern based on resource name
    if resource_name == 'wordnet':
        resource_pattern = os.path.join('corpora', 'wordnet')
    elif resource_name == 'omw-1.4':
        resource_pattern = os.path.join('corpora', 'omw-1.4')
    elif resource_name == 'stopwords':
        resource_pattern = os.path.join('corpora', 'stopwords')
    elif resource_name == 'punkt':
        resource_pattern = os.path.join('tokenizers', 'punkt')
    else:
        resource_pattern = resource_name
    
    # Check all standard directories for this resource
    for dir_path in standard_dirs:
        src_path = os.path.join(dir_path, resource_pattern)
        if os.path.exists(src_path):
            logger.info(f"Found {resource_name} at {src_path}")
            
            # Copy to user directory
            user_dest = os.path.join(user_nltk_dir, resource_pattern)
            if not os.path.exists(user_dest):
                try:
                    # Create destination directory if needed
                    os.makedirs(os.path.dirname(user_dest), exist_ok=True)
                    
                    # Copy directory or file
                    if os.path.isdir(src_path):
                        shutil.copytree(src_path, user_dest)
                    else:
                        shutil.copy2(src_path, user_dest)
                    logger.info(f"Copied {resource_name} from {src_path} to {user_dest}")
                    return True
                except Exception as e:
                    logger.error(f"Failed to copy {resource_name}: {str(e)}")
            
            # Also copy to conda directory if specified
            if conda_nltk_dir:
                conda_dest = os.path.join(conda_nltk_dir, resource_pattern)
                if not os.path.exists(conda_dest):
                    try:
                        os.makedirs(os.path.dirname(conda_dest), exist_ok=True)
                        if os.path.isdir(src_path):
                            shutil.copytree(src_path, conda_dest)
                        else:
                            shutil.copy2(src_path, conda_dest)
                        logger.info(f"Copied {resource_name} from {src_path} to {conda_dest}")
                    except Exception as e:
                        logger.error(f"Failed to copy {resource_name} to conda dir: {str(e)}")
    
    logger.warning(f"Could not find {resource_name} in any standard location")
    return False

def extract_nltk_zip_file(resource_name, user_nltk_dir, conda_nltk_dir=None):
    """Try to find and extract the downloaded zip file for a resource"""
    import zipfile
    
    directories = [user_nltk_dir]
    if conda_nltk_dir:
        directories.append(conda_nltk_dir)
    
    for base_dir in directories:
        # Check if there's a downloaded zip file
        zip_path = os.path.join(base_dir, f"{resource_name}.zip")
        if os.path.exists(zip_path):
            logger.info(f"Found zip file at {zip_path}")
            
            try:
                # Extract it to the appropriate directory
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # Determine extraction directory based on resource type
                    if resource_name in ['wordnet', 'omw-1.4', 'stopwords']:
                        extract_dir = os.path.join(base_dir, 'corpora')
                    elif resource_name == 'punkt':
                        extract_dir = os.path.join(base_dir, 'tokenizers')
                    else:
                        extract_dir = base_dir
                    
                    # Extract files
                    zip_ref.extractall(extract_dir)
                logger.info(f"Extracted {resource_name}.zip to {extract_dir}")
                return True
            except Exception as e:
                logger.error(f"Failed to extract {resource_name}.zip: {str(e)}")
    
    logger.warning(f"No zip file found for {resource_name}")
    return False

def download_from_internet(resource_name, user_nltk_dir, conda_nltk_dir=None):
    """Try to download the resource directly from NLTK's servers"""
    import urllib.request
    
    # NLTK's download URLs
    resource_urls = {
        'wordnet': 'https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/wordnet.zip',
        'omw-1.4': 'https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/omw-1.4.zip',
        'stopwords': 'https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/stopwords.zip',
        'punkt': 'https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/tokenizers/punkt.zip',
    }
    
    if resource_name not in resource_urls:
        logger.warning(f"No direct download URL known for {resource_name}")
        return False
    
    url = resource_urls[resource_name]
    temp_zip = os.path.join(user_nltk_dir, f"{resource_name}.zip")
    
    try:
        # Download the zip file
        logger.info(f"Downloading {resource_name} from {url}")
        urllib.request.urlretrieve(url, temp_zip)
        
        # Extract the zip file
        extract_nltk_zip_file(resource_name, user_nltk_dir, conda_nltk_dir)
        
        return True
    except Exception as e:
        logger.error(f"Failed to download {resource_name} from {url}: {str(e)}")
        return False

def pip_install_nltk_data():
    """Try to install NLTK data via pip as a last resort"""
    try:
        logger.info("Attempting to install nltk_data via pip...")
        result = subprocess.call([sys.executable, "-m", "pip", "install", "nltk_data"], 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if result == 0:
            logger.info("Successfully installed nltk_data via pip")
            return True
        else:
            logger.warning("Failed to install nltk_data via pip")
            return False
    except Exception as e:
        logger.error(f"Error during pip install: {str(e)}")
        return False

def reload_nltk_modules():
    """Ensure NLTK modules are correctly initialized with updated paths"""
    try:
        # Instead of reloading, just import the modules to verify they work
        import nltk.corpus
        import nltk.tokenize
        import nltk.stem
        
        # Simple verification that critical modules are accessible
        from nltk.corpus import wordnet, stopwords
        from nltk.tokenize import word_tokenize
        from nltk.stem import WordNetLemmatizer
        
        # Verify they actually work with minimal examples
        try:
            stopwords.words('english')[:5]
            word_tokenize("This is a test")
            lemmatizer = WordNetLemmatizer()
            lemmatizer.lemmatize("running")
            logger.info("NLTK modules verified as working correctly")
            return True
        except Exception as e:
            logger.error(f"NLTK modules imported but failed verification: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"Failed to import NLTK modules: {str(e)}")
        return False

def main():
    """Main function to install and verify all required NLTK resources"""
    logger.info("Starting NLTK Resource Setup")
    
    # Step 1: Create required directories
    user_nltk_dir, conda_nltk_dir = create_nltk_directories()
    
    # Step 2: Configure NLTK paths
    configure_nltk_paths(user_nltk_dir, conda_nltk_dir)
    
    # Required resources to install
    resources = [
        {'name': 'stopwords', 'path': 'corpora/stopwords', 'verification': None},
        {'name': 'wordnet', 'path': 'corpora/wordnet', 'verification': verify_wordnet},
        {'name': 'omw-1.4', 'path': 'corpora/omw-1.4', 'verification': None},
        {'name': 'punkt', 'path': 'tokenizers/punkt', 'verification': None}
    ]
    
    # Step 3: Download and verify each resource with multiple attempts and fallbacks
    for resource in resources:
        resource_name = resource['name']
        resource_path = resource['path']
        verification_func = resource['verification']
        
        logger.info(f"\n===== Processing resource: {resource_name} =====")
        
        # First attempt: standard download to user directory
        download_resource(resource_name, user_nltk_dir)
        
        # Also download to conda directory if available
        if conda_nltk_dir:
            download_resource(resource_name, conda_nltk_dir)
        
        # Create symbolic links for proper directory structure
        create_symlinks(user_nltk_dir, conda_nltk_dir)
        
        # Verify resource is accessible
        if verify_resource(resource_name, resource_path, verification_func):
            logger.info(f"Resource {resource_name} successfully set up!")
            continue
        
        # If verification failed, try alternative approaches:
        
        # 1. Try direct system download
        logger.info(f"Attempting alternative download methods for {resource_name}...")
        directories = [d for d in [user_nltk_dir, conda_nltk_dir] if d]
        direct_system_download(resource_name, directories)
        
        # 2. Try to find and copy from standard locations
        copy_resource_to_expected_location(resource_name, user_nltk_dir, conda_nltk_dir)
        
        # 3. Try to extract from zip files if they exist
        extract_nltk_zip_file(resource_name, user_nltk_dir, conda_nltk_dir)
        
        # 4. Try direct download from NLTK's servers
        download_from_internet(resource_name, user_nltk_dir, conda_nltk_dir)
        
        # Create symlinks again after all these attempts
        create_symlinks(user_nltk_dir, conda_nltk_dir)
        
        # Final verification
        if verify_resource(resource_name, resource_path, verification_func):
            logger.info(f"Resource {resource_name} successfully set up after alternative methods!")
        else:
            logger.error(f"Failed to set up {resource_name} after all attempts")
            
            # Last resort for wordnet and omw-1.4 which are critical
            if resource_name in ['wordnet', 'omw-1.4']:
                logger.info("Attempting last-resort method: pip install nltk_data")
                pip_install_nltk_data()
                
                # Final verification after pip install
                if verify_resource(resource_name, resource_path, verification_func):
                    logger.info(f"Resource {resource_name} successfully set up after pip install!")
                else:
                    logger.error(f"CRITICAL: Resource {resource_name} could not be set up by any method.")
    
    # Final step: Reload NLTK modules
    reload_nltk_modules()
    
    # Summarize results
    logger.info("\n===== NLTK Resource Setup Summary =====")
    all_resources_ok = True
    for resource in resources:
        resource_name = resource['name']
        resource_path = resource['path']
        verification_func = resource['verification']
        
        is_ok = verify_resource(resource_name, resource_path, verification_func)
        status = "✓ SUCCESS" if is_ok else "✗ FAILED"
        logger.info(f"{resource_name}: {status}")
        
        if not is_ok:
            all_resources_ok = False
    
    if all_resources_ok:
        logger.info("All NLTK resources are successfully set up and verified!")
        return 0
    else:
        logger.error("Some NLTK resources could not be set up properly.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 