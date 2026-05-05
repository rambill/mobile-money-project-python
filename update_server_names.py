#!/usr/bin/env python3
"""
Update all server names - remove "MoMo" prefix
"""

import os
import re

# Files to update
files_to_update = [
    "README.md",
    "QUICKSTART.md",
    "CLIENT_DISCOVERS_ALL_SERVERS.md",
    "START_HERE_REPLICATION.md",
    "WEB_CLIENT_SETUP.md",
    "TEST_AUTO_SYNC.md",
    "SYNC_DATABASES.md",
    "SYNC_ALL_SERVERS.md",
    "DEPLOYMENT.md",
    "templates/mobile.html"
]

# Replacements
replacements = {
    "MoMo-Kampala": "Kampala",
    "MoMo-Mbarara": "Mbarara",
    "MoMo-Gulu": "Gulu",
    "MoMo-Kasese": "Kasese",
    "MoMo-Kabale": "Kabale",
    "MoMo-Mbale": "Mbale",
    "MoMo-Jinja": "Jinja",
    "MoMo-Rukungiri": "Rukungiri",
    "MoMo-Fort Portal": "Fort Portal",
    "MoMo-Arua": "Arua",
    "MoMo-Server": "Server",
    "MoMo-Soroti": "Soroti",
    "MoMo RPC": "Mobile Money RPC",
    "MoMo Discovery": "Mobile Money Discovery",
    "momo-system": "mobile-money-system",
}

def update_file(filepath):
    """Update a single file"""
    if not os.path.exists(filepath):
        print(f"⚠ Skipping {filepath} (not found)")
        return
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply all replacements
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Updated {filepath}")
        else:
            print(f"  No changes needed in {filepath}")
    
    except Exception as e:
        print(f"✗ Error updating {filepath}: {e}")

def main():
    print("=" * 60)
    print("UPDATING SERVER NAMES")
    print("=" * 60)
    print("\nRemoving 'MoMo' prefix from all server names...\n")
    
    for filepath in files_to_update:
        update_file(filepath)
    
    print("\n" + "=" * 60)
    print("UPDATE COMPLETE!")
    print("=" * 60)
    print("\nAll server names updated:")
    print("  MoMo-Kampala → Kampala")
    print("  MoMo-Mbarara → Mbarara")
    print("  MoMo-Gulu → Gulu")
    print("  etc.")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
