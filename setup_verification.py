#!/usr/bin/env python3
"""Quick verification script to test CodeAtlas installation."""

import sys
from pathlib import Path

def verify_installation():
    """Verify CodeAtlas installation."""
    print("Verifying CodeAtlas installation...")
    
    # Check imports
    try:
        import codeatlas
        print(f"✓ CodeAtlas v{codeatlas.__version__} imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import codeatlas: {e}")
        return False
    
    # Check CLI entrypoint
    try:
        from codeatlas.cli import app
        print("✓ CLI entrypoint loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load CLI: {e}")
        return False
    
    # Check core modules
    modules = [
        "codeatlas.scanner",
        "codeatlas.language_detector",
        "codeatlas.comment_parser",
        "codeatlas.comment_editor",
        "codeatlas.export",
        "codeatlas.tree_generator",
        "codeatlas.git_integration",
        "codeatlas.cleanup",
        "codeatlas.plugin_system",
        "codeatlas.config",
    ]
    
    for module_name in modules:
        try:
            __import__(module_name)
            print(f"✓ {module_name} imported")
        except Exception as e:
            print(f"✗ Failed to import {module_name}: {e}")
            return False
    
    print("\n✓ All checks passed! CodeAtlas is ready to use.")
    print("\nTry running: codeatlas --help")
    return True

if __name__ == "__main__":
    success = verify_installation()
    sys.exit(0 if success else 1)

