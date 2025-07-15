#!/usr/bin/env python3
"""
Setup script for Japan Stock Screener
This script will help you set up and run the stock screener application.
"""

import os
import subprocess
import sys

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    required_packages = ["streamlit", "requests", "pandas"]
    
    for package in required_packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")
            return False
    return True

def setup_api_key():
    """Help user set up API key"""
    print("\n🔑 API Key Setup")
    print("You need a Financial Modeling Prep API key to use this application.")
    print("Get one free at: https://financialmodelingprep.com/developer/docs")
    
    api_key = input("\nEnter your API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided!")
        return False
    
    # Method 1: Set environment variable
    os.environ['FMP_API_KEY'] = api_key
    print("✅ API key set for this session")
    
    # Method 2: Create secrets file
    try:
        os.makedirs('.streamlit', exist_ok=True)
        with open('.streamlit/secrets.toml', 'w') as f:
            f.write(f'FMP_API_KEY = "{api_key}"\n')
        print("✅ API key saved to .streamlit/secrets.toml")
    except Exception as e:
        print(f"⚠️ Could not save to secrets file: {e}")
    
    return True

def run_app():
    """Run the Streamlit application"""
    print("\n🚀 Starting the application...")
    print("📱 Your browser should open automatically")
    print("🛑 Press Ctrl+C to stop the application")
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "japan_stock_screener_fixed.py"])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except FileNotFoundError:
        print("❌ japan_stock_screener_fixed.py not found!")
        print("Make sure you have saved the fixed version in the same directory as this script")

def main():
    print("🎯 Japan Stock Screener Setup")
    print("=" * 50)
    
    # Check if the main file exists
    if not os.path.exists('japan_stock_screener_fixed.py'):
        print("❌ japan_stock_screener_fixed.py not found!")
        print("Please save the fixed version of the code as 'japan_stock_screener_fixed.py'")
        return
    
    # Install requirements
    if not install_requirements():
        print("❌ Failed to install required packages")
        return
    
    # Setup API key
    if not setup_api_key():
        print("❌ API key setup failed")
        return
    
    # Run the app
    run_app()

if __name__ == "__main__":
    main()