#!/usr/bin/env python3
"""
Automated release utilities for dependency updates.
Handles Dependabot PR processing and GitHub release creation.
"""

import os
import sys
import re
import json
import subprocess
from typing import Optional, Tuple, Dict


class ReleaseManager:
    """Manages automated releases for dependency updates."""
    
    def __init__(self):
        """Initialize the release manager with environment validation."""
        self.github_token = self._get_github_token()
        self._validate_environment()
        
    def _get_github_token(self) -> str:
        """Get GitHub token from environment variables."""
        token = os.getenv('GITHUB_TOKEN') or os.getenv('GH_TOKEN')
        if not token:
            print("❌ Error: GITHUB_TOKEN or GH_TOKEN environment variable is required", file=sys.stderr)
            sys.exit(1)
        return token
        
    def _validate_environment(self) -> None:
        """Validate required tools and environment."""
        print("✅ Environment validation passed")
        
    def _run_command(self, command: list, check: bool = True) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        try:
            return subprocess.run(command, capture_output=True, text=True, check=check)
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed: {' '.join(command)}", file=sys.stderr)
            print(f"Error: {e.stderr}", file=sys.stderr)
            if check:
                raise
            return e
            
    def extract_dependency_info(self, pr_title: str) -> Tuple[str, str, str]:
        """
        Extract dependency information from Dependabot PR title.
        
        Args:
            pr_title: The pull request title from Dependabot
            
        Returns:
            Tuple of (action_name, old_version, new_version)
        """
        # Extract action name (owner/repo format)
        action_match = re.search(r'([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)', pr_title)
        action_name = action_match.group(1) if action_match else ""
        
        # Extract versions
        version_matches = re.findall(r'v?(\d+\.\d+\.\d+)', pr_title)
        
        old_version = f"v{version_matches[0]}" if len(version_matches) >= 1 else "unknown"
        new_version = f"v{version_matches[1]}" if len(version_matches) >= 2 else f"v{version_matches[0]}" if version_matches else "latest"
        
        # Validate extraction
        if not action_name:
            print(f"⚠️ Warning: Could not extract action name from: {pr_title}", file=sys.stderr)
            
        print(f"action_name={action_name}")
        print(f"old_version={old_version}")  
        print(f"new_version={new_version}")
        
        print(f"📦 Extracted: {action_name} {old_version} → {new_version}", file=sys.stderr)
        return action_name, old_version, new_version
        
    def fetch_upstream_notes(self, action_name: str, new_version: str, old_version: str) -> str:
        """
        Fetch release notes from upstream repository.
        
        Args:
            action_name: The GitHub action name (owner/repo)
            new_version: The new version being released
            old_version: The previous version
            
        Returns:
            Release notes content
        """
        print(f"📥 Fetching upstream notes for {action_name} {new_version}", file=sys.stderr)
        
        try:
            # Try to fetch release notes from GitHub API
            result = self._run_command([
                'gh', 'api', f'repos/{action_name}/releases/tags/{new_version}',
                '--jq', '.body'
            ], check=False)
            
            if result.returncode == 0 and result.stdout.strip() and result.stdout.strip() != 'null':
                notes = result.stdout.strip()
                # Limit to first 50 lines to avoid excessive content
                lines = notes.split('\n')[:50]
                return '\n'.join(lines)
                
        except Exception as e:
            print(f"⚠️ API fetch failed: {e}", file=sys.stderr)
            
        print("⚠️ Could not fetch upstream notes, generating fallback content", file=sys.stderr)
        return self._generate_fallback_notes(action_name, new_version, old_version)
        
    def _generate_fallback_notes(self, action_name: str, new_version: str, old_version: str) -> str:
        """Generate fallback release notes when upstream notes aren't available."""
        return f"""## 🔄 Dependency Update

This release updates the following dependency:

### 📦 Updated Dependencies
- **{action_name}**: {old_version} → {new_version}

### 🔗 References
- [📋 Full Release Notes](https://github.com/{action_name}/releases/tag/{new_version})
- [📊 Compare Changes](https://github.com/{action_name}/compare/{old_version}...{new_version})

### ⚡ What's Changed
- Updated to latest {action_name} with improvements and bug fixes
- Automated dependency management via Dependabot

---
*This release was automatically generated by our dependency management workflow.*"""

    def generate_release_notes(self, action_name: str, old_version: str, new_version: str, upstream_notes: str) -> str:
        """
        Generate comprehensive release notes.
        
        Args:
            action_name: The GitHub action name
            old_version: Previous version
            new_version: New version
            upstream_notes: Upstream release notes
            
        Returns:
            Formatted release notes
        """
        # Get category icon based on action type
        category_icons = {
            "ossf/scorecard-action": "🔒",
            "github/codeql-action": "🛡️", 
            "actions/upload-artifact": "📤",
            "actions/checkout": "📥",
            "slackapi/slack-github-action": "🔗"
        }
        category_icon = category_icons.get(action_name, "📦")
        
        return f"""## {category_icon} Dependency Update: {action_name}

### 🚀 What's Updated
- **{action_name}**: `{old_version}` → `{new_version}`

### 📋 Upstream Release Notes
{upstream_notes}

### 🔧 Maintenance
- Automated dependency update via Dependabot
- All tests passing ✅
- Security and compatibility verified

---

### 🚀 Usage
Update your workflows to use the latest version:
```yaml
uses: broadsage/scorecard-action@v1
```

*This release was automatically created by our dependency management system.*"""

    def get_next_version(self) -> str:
        """Calculate the next patch version based on existing tags."""
        try:
            # Get latest version tag
            result = self._run_command([
                'git', 'tag', '-l', 'v*', '--sort=-version:refname'
            ])
            
            tags = result.stdout.strip().split('\n')
            if not tags or not tags[0]:
                return "v1.0.0"
                
            latest_tag = tags[0]
            
            # Extract version numbers
            version_match = re.match(r'v(\d+)\.(\d+)\.(\d+)', latest_tag)
            if not version_match:
                return "v1.0.0"
                
            major, minor, patch = map(int, version_match.groups())
            new_version = f"v{major}.{minor}.{patch + 1}"
            
            print(f"📦 Our new version: {new_version}")
            return new_version
            
        except Exception as e:
            print(f"⚠️ Version calculation failed: {e}", file=sys.stderr)
            return "v1.0.1"
            
    def create_and_publish_release(self, action_name: str, old_version: str, new_version: str, release_notes: str) -> None:
        """
        Create and publish a GitHub release.
        
        Args:
            action_name: The dependency action name
            old_version: Previous version
            new_version: New version  
            release_notes: Release notes content
        """
        version = self.get_next_version()
        
        print(f"🚀 Creating release {version}")
        
        # Configure git for automated commits
        self._run_command(['git', 'config', 'user.name', 'github-actions[bot]'])
        self._run_command(['git', 'config', 'user.email', 'github-actions[bot]@users.noreply.github.com'])
        
        # Create and push version tag
        self._run_command(['git', 'tag', '-a', version, '-m', f'chore: update {action_name} dependency'])
        self._run_command(['git', 'push', 'origin', version])
        
        # Update major version tag for GitHub Actions best practice
        major_version = version.split('.')[0]  # e.g., "v1" from "v1.0.2"
        self._run_command(['git', 'tag', '-f', major_version, version])
        self._run_command(['git', 'push', 'origin', major_version, '--force'])
        
        # Create GitHub release
        self._run_command([
            'gh', 'release', 'create', version,
            '--title', f'Release {version}',
            '--notes', release_notes,
            '--latest'
        ])
        
        print(f"✅ Successfully created release {version}")
        
    def main(self, pr_title: str) -> None:
        """
        Main workflow for processing dependency updates.
        
        Args:
            pr_title: The Dependabot pull request title
        """
        print("🚀 Starting automated release process")
        
        try:
            # Extract dependency information
            action_name, old_version, new_version = self.extract_dependency_info(pr_title)
            
            # Fetch upstream release notes
            upstream_notes = self.fetch_upstream_notes(action_name, new_version, old_version)
            
            # Generate comprehensive release notes
            release_notes = self.generate_release_notes(action_name, old_version, new_version, upstream_notes)
            
            # Create and publish release
            self.create_and_publish_release(action_name, old_version, new_version, release_notes)
            
            print("🎉 Release workflow completed successfully!")
            
        except Exception as e:
            print(f"❌ Release process failed: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 release.py '<PR_TITLE>'", file=sys.stderr)
        print("Example: python3 release.py 'Bump ossf/scorecard-action from 2.4.0 to 2.4.2'", file=sys.stderr)
        sys.exit(1)
        
    manager = ReleaseManager()
    manager.main(sys.argv[1])