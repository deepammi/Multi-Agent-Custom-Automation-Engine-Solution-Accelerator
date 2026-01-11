#!/usr/bin/env python3
"""
Verification script for root directory organization.
Checks that all files are in their expected locations and structure is correct.
"""

import os
from pathlib import Path
from typing import List, Dict, Tuple

class OrganizationVerifier:
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.issues = []
        self.successes = []
    
    def log_success(self, message: str):
        """Log a successful verification"""
        self.successes.append(f"✅ {message}")
        print(f"✅ {message}")
    
    def log_issue(self, message: str):
        """Log a verification issue"""
        self.issues.append(f"❌ {message}")
        print(f"❌ {message}")
    
    def verify_directory_structure(self):
        """Verify the expected directory structure exists"""
        expected_dirs = [
            "backend",
            "src/frontend",
            "src/mcp_server", 
            "tests/root",
            "tests/integration",
            "scripts/setup",
            "scripts/integration",
            "config",
            "config/secrets",
            "docs/project",
            "temp/logs",
            "temp/test_results",
            "tools/development"
        ]
        
        print("🔍 Verifying directory structure...")
        for directory in expected_dirs:
            dir_path = self.root_path / directory
            if dir_path.exists() and dir_path.is_dir():
                self.log_success(f"Directory exists: {directory}")
            else:
                self.log_issue(f"Missing directory: {directory}")
    
    def verify_moved_files(self):
        """Verify that files were moved to correct locations"""
        expected_files = [
            # Test files
            "tests/root/test_bill_com_real.py",
            "tests/root/test_bill_com_real_api.py",
            "tests/root/test_detailed_invoice_retrieval.py",
            "tests/root/test_integration_simple.py",
            
            # Scripts
            "scripts/setup/start-dev.sh",
            "scripts/integration/bill_com_integration_test.py",
            "scripts/integration/bill_com_setup_check.py",
            
            # Config files
            "config/SAMPLE_TEAM_CONFIGURATION.json",
            "config/.flake8",
            "config/secrets/client_secret.json",
            
            # Documentation
            "docs/project/Microsoft_Multi_Agent_Accelerator_README.md",
            "docs/project/PRE_COMMIT_HOOK_README.md",
            "docs/project/QUICK_START.md",
            
            # Log files
            "temp/logs/backend.log",
            "temp/logs/frontend.log",
            "temp/logs/salesforce_server.log"
        ]
        
        print("\n🔍 Verifying moved files...")
        for file_path in expected_files:
            full_path = self.root_path / file_path
            if full_path.exists() and full_path.is_file():
                self.log_success(f"File in correct location: {file_path}")
            else:
                self.log_issue(f"Missing file: {file_path}")
    
    def verify_no_scattered_files(self):
        """Verify no test/log files remain scattered in root"""
        root_files = list(self.root_path.glob("*"))
        
        print("\n🔍 Verifying no scattered files in root...")
        
        # Check for scattered test files
        test_files = [f for f in root_files if f.name.startswith("test_") and f.suffix == ".py"]
        if test_files:
            for test_file in test_files:
                self.log_issue(f"Test file still in root: {test_file.name}")
        else:
            self.log_success("No test files scattered in root")
        
        # Check for scattered log files
        log_files = [f for f in root_files if f.suffix == ".log"]
        if log_files:
            for log_file in log_files:
                self.log_issue(f"Log file still in root: {log_file.name}")
        else:
            self.log_success("No log files scattered in root")
    
    def verify_readme_files(self):
        """Verify README files were created"""
        expected_readmes = [
            "README.md",
            "tests/README.md",
            "scripts/README.md",
            "config/README.md",
            "temp/README.md",
            "docs/README.md"
        ]
        
        print("\n🔍 Verifying README files...")
        for readme in expected_readmes:
            readme_path = self.root_path / readme
            if readme_path.exists() and readme_path.is_file():
                self.log_success(f"README exists: {readme}")
            else:
                self.log_issue(f"Missing README: {readme}")
    
    def verify_executable_scripts(self):
        """Verify scripts are executable"""
        scripts = [
            "scripts/setup/start-dev.sh"
        ]
        
        print("\n🔍 Verifying executable scripts...")
        for script in scripts:
            script_path = self.root_path / script
            if script_path.exists():
                if os.access(script_path, os.X_OK):
                    self.log_success(f"Script is executable: {script}")
                else:
                    self.log_issue(f"Script not executable: {script}")
            else:
                self.log_issue(f"Script missing: {script}")
    
    def verify_gitignore_updated(self):
        """Verify .gitignore was updated with new entries"""
        gitignore_path = self.root_path / ".gitignore"
        
        print("\n🔍 Verifying .gitignore updates...")
        if gitignore_path.exists():
            content = gitignore_path.read_text()
            
            expected_entries = [
                "temp/",
                "config/secrets/",
                "*.log"
            ]
            
            for entry in expected_entries:
                if entry in content:
                    self.log_success(f"Gitignore contains: {entry}")
                else:
                    self.log_issue(f"Gitignore missing: {entry}")
        else:
            self.log_issue(".gitignore file not found")
    
    def verify_organization_log(self):
        """Verify organization log was created"""
        log_path = self.root_path / "temp" / "organization_log.json"
        
        print("\n🔍 Verifying organization log...")
        if log_path.exists():
            self.log_success("Organization log exists: temp/organization_log.json")
            
            # Check log content
            try:
                import json
                with open(log_path) as f:
                    log_data = json.load(f)
                
                if isinstance(log_data, list) and len(log_data) > 0:
                    self.log_success(f"Organization log contains {len(log_data)} actions")
                else:
                    self.log_issue("Organization log is empty or invalid")
            except Exception as e:
                self.log_issue(f"Error reading organization log: {e}")
        else:
            self.log_issue("Organization log not found")
    
    def run_verification(self):
        """Run all verification checks"""
        print("🚀 Starting root directory organization verification...")
        print("=" * 60)
        
        self.verify_directory_structure()
        self.verify_moved_files()
        self.verify_no_scattered_files()
        self.verify_readme_files()
        self.verify_executable_scripts()
        self.verify_gitignore_updated()
        self.verify_organization_log()
        
        print("\n" + "=" * 60)
        print("📊 VERIFICATION SUMMARY")
        print("=" * 60)
        
        print(f"✅ Successful checks: {len(self.successes)}")
        print(f"❌ Issues found: {len(self.issues)}")
        
        if self.issues:
            print("\n🔧 Issues to address:")
            for issue in self.issues:
                print(f"  {issue}")
            return False
        else:
            print("\n🎉 All verification checks passed!")
            print("📁 Root directory is properly organized and GitHub ready!")
            return True

def main():
    """Main execution function"""
    verifier = OrganizationVerifier()
    success = verifier.run_verification()
    
    if success:
        print("\n✨ Next steps:")
        print("   1. Review the organized structure")
        print("   2. Test that scripts still work: ./scripts/setup/start-dev.sh")
        print("   3. Commit changes: git add . && git commit -m 'Organize root directory structure'")
        print("   4. Push to GitHub for clean, professional presentation")
    else:
        print("\n🔧 Please address the issues above before committing.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())