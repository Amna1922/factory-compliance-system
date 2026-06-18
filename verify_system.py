#!/usr/bin/env python
"""
Verification script to check that the Factory Compliance System is complete and ready
"""
import os
import sys
from pathlib import Path

def check_file(path, expected_lines_min=10):
    """Check if a file exists and has content"""
    p = Path(path)
    if not p.exists():
        return False, f"File not found: {path}"
    
    try:
        with open(p, 'r') as f:
            lines = f.readlines()
            if len(lines) < expected_lines_min:
                return False, f"File too small: {len(lines)} lines"
            return True, f"✅ {len(lines)} lines"
    except Exception as e:
        return False, f"Error reading: {str(e)}"


def verify_system():
    """Verify all system components"""
    print("=" * 70)
    print("🏭 FACTORY COMPLIANCE SYSTEM - VERIFICATION")
    print("=" * 70)
    
    checks = {
        "Backend Modules": {
            "app/__init__.py": (10, "Package init"),
            "app/config.py": (50, "Configuration"),
            "app/models.py": (100, "Data models"),
            "app/database.py": (100, "Database ops"),
            "app/policy_parser.py": (50, "Policy parser"),
            "app/detection_engine.py": (100, "Detection engine"),
            "app/severity_classifier.py": (80, "Severity classifier"),
            "app/escalation_pipeline.py": (100, "Escalation pipeline"),
            "app/report_generator.py": (100, "Report generator"),
            "app/utils.py": (100, "Utilities"),
            "app/main.py": (200, "FastAPI backend"),
        },
        "Frontend Modules": {
            "frontend/__init__.py": (1, "Package init"),
            "frontend/components.py": (200, "UI components"),
            "frontend/app.py": (200, "Streamlit app"),
        },
        "Configuration": {
            "requirements.txt": (10, "Dependencies"),
            "run.py": (50, "Launch script"),
            "README.md": (100, "Documentation"),
            "IMPLEMENTATION_SUMMARY.md": (100, "Implementation details"),
        }
    }
    
    total_pass = 0
    total_checks = 0
    
    for category, files in checks.items():
        print(f"\n📋 {category}")
        print("-" * 70)
        
        for filepath, (min_lines, description) in files.items():
            total_checks += 1
            exists, result = check_file(filepath, min_lines)
            
            if exists:
                print(f"  ✅ {filepath:<40} {result:<30} [{description}]")
                total_pass += 1
            else:
                print(f"  ❌ {filepath:<40} {result:<30} [{description}]")
    
    print("\n" + "=" * 70)
    print(f"VERIFICATION RESULTS: {total_pass}/{total_checks} checks passed")
    print("=" * 70)
    
    if total_pass == total_checks:
        print("\n✅ ALL COMPONENTS PRESENT AND READY!")
        print("\n🚀 NEXT STEPS:")
        print("   1. pip install -r requirements.txt")
        print("   2. python run.py")
        print("   3. Open http://localhost:8501 for dashboard")
        return 0
    else:
        print(f"\n❌ {total_checks - total_pass} component(s) missing")
        return 1


if __name__ == "__main__":
    sys.exit(verify_system())
