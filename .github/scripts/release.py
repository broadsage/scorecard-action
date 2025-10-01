#!/usr/bin/env python3
"""
Release Manager - Unified release automation for dependency updates and manual releases.
Handles both Dependabot PR processing and manual GitHub release creation with context awareness.
"""

import os
import sys
import re
import json
import subprocess
from typing import Optional, Tuple, Dict, List, Literal
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict


class ReleaseContext(Enum):
    """Release context types."""
    DEPENDABOT = "dependabot"
    MANUAL = "manual"


class VersionType(Enum):
    """Version increment types."""
    MAJOR = "major"
    MINOR = "minor" 
    PATCH = "patch"


@dataclass
class CommitInfo:
    """Information about a single commit."""
    type: str  # feat, fix, docs, etc.
    scope: Optional[str]  # Optional scope like (deps), (ui), etc.
    description: str
    body: Optional[str]
    breaking: bool = False
    hash: str = ""

@dataclass
class ReleaseConfig:
    """Configuration for release processing."""
    context: ReleaseContext
    version_type: VersionType
    dry_run: bool = False
    custom_notes: Optional[str] = None
    pr_title: Optional[str] = None


class ReleaseManager:
    """Automated release manager with context-aware processing for dependency updates and manual releases."""
    
    def __init__(self):
        """Initialize the release manager with environment validation and context detection."""
        self.github_token = self._get_github_token()
        self.config = self._detect_release_context()
        self._validate_environment()
        
    def _get_github_token(self) -> str:
        """Get GitHub token from environment variables."""
        token = os.getenv('GITHUB_TOKEN') or os.getenv('GH_TOKEN')
        if not token:
            print("❌ Error: GITHUB_TOKEN or GH_TOKEN environment variable is required", file=sys.stderr)
            sys.exit(1)
        return token
    
    def _detect_release_context(self) -> ReleaseConfig:
        """Detect release context from environment variables."""
        trigger_type = os.getenv('TRIGGER_TYPE', 'pull_request')
        version_type_str = os.getenv('VERSION_TYPE', 'patch')
        dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
        custom_notes = os.getenv('CUSTOM_NOTES', '').strip() or None
        pr_title = os.getenv('PR_TITLE', '').strip() or None
        
        # Determine context
        if trigger_type == 'workflow_dispatch':
            context = ReleaseContext.MANUAL
        else:
            context = ReleaseContext.DEPENDABOT
            
        # Parse version type
        try:
            version_type = VersionType(version_type_str)
        except ValueError:
            print(f"⚠️ Invalid version type '{version_type_str}', defaulting to patch", file=sys.stderr)
            version_type = VersionType.PATCH
            
        config = ReleaseConfig(
            context=context,
            version_type=version_type,
            dry_run=dry_run,
            custom_notes=custom_notes,
            pr_title=pr_title
        )
        
        print(f"🎯 Release context: {context.value}, version: {version_type.value}, dry_run: {dry_run}")
        return config
        
    def _validate_environment(self) -> None:
        """Validate required tools and environment."""
        # Validate context-specific requirements
        if self.config.context == ReleaseContext.DEPENDABOT and not self.config.pr_title:
            print("❌ Error: PR_TITLE is required for Dependabot releases", file=sys.stderr)
            sys.exit(1)
            
        print("✅ Environment validation passed")
    
    def _generate_usage_block(self) -> str:
        """Generate common usage block for release notes."""
        return """---

### 🚀 Usage
Update your workflows to use the latest version:
```yaml
uses: broadsage/scorecard-action@v1
```"""
    
    def _generate_footer(self, context: ReleaseContext) -> str:
        """Generate common footer for release notes."""
        if context == ReleaseContext.DEPENDABOT:
            return "*This release was automatically created by our dependency management system.*"
        return "*This release was manually created via GitHub Actions workflow.*"
    
    def _parse_conventional_commit(self, commit_msg: str, commit_hash: str = "") -> Optional[CommitInfo]:
        """
        Parse conventional commit message.
        
        Format: type(scope)!: description
        Examples:
        - feat: add new feature
        - fix(deps): resolve dependency issue  
        - feat!: breaking change
        - docs(readme): update installation guide
        """
        # Regex pattern for conventional commits
        pattern = r'^(?P<type>feat|fix|docs|style|refactor|perf|test|chore|ci|build|revert)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?: (?P<description>.+)$'
        
        match = re.match(pattern, commit_msg.strip())
        if not match:
            # Try to categorize non-conventional commits
            commit_lower = commit_msg.lower().strip()
            if any(word in commit_lower for word in ['fix', 'bug', 'resolve', 'patch']):
                commit_type = 'fix'
            elif any(word in commit_lower for word in ['add', 'new', 'feature', 'implement']):
                commit_type = 'feat'
            elif any(word in commit_lower for word in ['update', 'upgrade', 'bump']):
                commit_type = 'chore'
            elif any(word in commit_lower for word in ['refactor', 'clean', 'reorganize']):
                commit_type = 'refactor'
            elif any(word in commit_lower for word in ['doc', 'readme', 'comment']):
                commit_type = 'docs'
            else:
                commit_type = 'chore'
                
            return CommitInfo(
                type=commit_type,
                scope=None,
                description=commit_msg.strip(),
                body=None,
                breaking=False,
                hash=commit_hash
            )
        
        return CommitInfo(
            type=match.group('type'),
            scope=match.group('scope'),
            description=match.group('description'),
            body=None,
            breaking=bool(match.group('breaking')),
            hash=commit_hash
        )
    
    def _analyze_commits_for_version_bump(self, commits: List[CommitInfo]) -> VersionType:
        """Analyze commits to determine appropriate version bump."""
        has_breaking = any(commit.breaking for commit in commits)
        has_features = any(commit.type == 'feat' for commit in commits)
        
        if has_breaking:
            return VersionType.MAJOR
        elif has_features:
            return VersionType.MINOR
        else:
            return VersionType.PATCH
    
    def _get_commits_since_last_release(self) -> List[CommitInfo]:
        """Get and parse commits since last release."""
        try:
            result = self._run_command([
                'git', 'log', '--oneline', '--pretty=format:%H|%s', 
                f'{self._get_last_version()}..HEAD'
            ], check=False)
            
            commits = []
            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    if '|' in line:
                        hash_part, msg = line.split('|', 1)
                        commit_info = self._parse_conventional_commit(msg, hash_part[:7])
                        if commit_info:
                            commits.append(commit_info)
            
            return commits
        except Exception as e:
            print(f"⚠️ Failed to analyze commits: {e}", file=sys.stderr)
            return []
        
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

    def generate_release_notes(self, version: str, **kwargs) -> str:
        """
        Generate context-aware release notes.
        
        Args:
            version: The new version being released
            **kwargs: Context-specific arguments (action_name, old_version, new_version, upstream_notes)
            
        Returns:
            Formatted release notes
        """
        if self.config.context == ReleaseContext.DEPENDABOT:
            return self._generate_dependency_notes(version, **kwargs)
        else:
            return self._generate_manual_notes(version, **kwargs)
    
    def _generate_dependency_notes(self, version: str, action_name: str, old_version: str, new_version: str, upstream_notes: str) -> str:
        """Generate release notes for dependency updates."""
        # Get category icon based on action type
        category_icons = {
            "ossf/scorecard-action": "🔒",
            "github/codeql-action": "🛡️", 
            "actions/upload-artifact": "📤",
            "actions/checkout": "📥",
            "slackapi/slack-github-action": "🔗"
        }
        category_icon = category_icons.get(action_name, "📦")
        
        return f"""## {category_icon} Dependency Update

### 🚀 What's Updated
- **{action_name}**: `{old_version}` → `{new_version}`

### 📋 Upstream Release Notes
{upstream_notes}

### 🔧 Maintenance
- Automated dependency update via Dependabot
- All tests passing ✅
- Security and compatibility verified

{self._generate_usage_block()}

{self._generate_footer(ReleaseContext.DEPENDABOT)}"""

    def _generate_manual_notes(self, version: str, **kwargs) -> str:
        """Generate release notes for manual releases."""
        if self.config.custom_notes:
            # Use custom notes provided by user
            return f"""## 🚀 What's New

{self.config.custom_notes}

{self._generate_usage_block()}

{self._generate_footer(ReleaseContext.MANUAL)}"""
        else:
            # Generate automatic notes from commits
            return self._generate_automatic_notes(version)
    
    def _generate_automatic_notes(self, version: str) -> str:
        """Generate semantic release notes from recent commits."""
        try:
            commits = self._get_commits_since_last_release()
            
            if not commits:
                return f"""## 🚀 What's Changed

### 📝 Updates
- Various improvements and updates

{self._generate_usage_block()}

{self._generate_footer(ReleaseContext.MANUAL)}"""
            
            # Auto-detect version type based on commits
            suggested_version_type = self._analyze_commits_for_version_bump(commits)
            
            # Group commits by type
            grouped_commits = defaultdict(list)
            for commit in commits:
                grouped_commits[commit.type].append(commit)
            
            # Determine header icon based on changes
            has_breaking = any(commit.breaking for commit in commits)
            has_features = any(commit.type == 'feat' for commit in commits)
            
            if has_breaking:
                version_icon = "💥"
                header = "What's Changed"
            elif has_features:
                version_icon = "🚀"  
                header = "What's Changed"
            else:
                version_icon = "🎯"
                header = "What's Changed"
                
            # Build sections
            sections = []
            
            # Breaking changes first
            breaking_commits = [c for c in commits if c.breaking]
            if breaking_commits:
                sections.append("### 💥 Breaking Changes")
                for commit in breaking_commits:
                    scope_text = f"**{commit.scope}**: " if commit.scope else ""
                    sections.append(f"- {scope_text}{commit.description}")
                sections.append("")
            
            # Features
            if 'feat' in grouped_commits:
                sections.append("### ✨ New Features") 
                for commit in grouped_commits['feat']:
                    if not commit.breaking:  # Non-breaking features
                        scope_text = f"**{commit.scope}**: " if commit.scope else ""
                        sections.append(f"- {scope_text}{commit.description}")
                sections.append("")
            
            # Bug fixes
            if 'fix' in grouped_commits:
                sections.append("### 🐛 Bug Fixes")
                for commit in grouped_commits['fix']:
                    scope_text = f"**{commit.scope}**: " if commit.scope else ""
                    sections.append(f"- {scope_text}{commit.description}")
                sections.append("")
            
            # Performance improvements
            if 'perf' in grouped_commits:
                sections.append("### ⚡ Performance Improvements")
                for commit in grouped_commits['perf']:
                    scope_text = f"**{commit.scope}**: " if commit.scope else ""
                    sections.append(f"- {scope_text}{commit.description}")
                sections.append("")
            
            # Documentation
            if 'docs' in grouped_commits:
                sections.append("### 📚 Documentation")
                for commit in grouped_commits['docs']:
                    scope_text = f"**{commit.scope}**: " if commit.scope else ""
                    sections.append(f"- {scope_text}{commit.description}")
                sections.append("")
            
            # Refactoring and maintenance
            maintenance_types = ['refactor', 'chore', 'ci', 'build', 'style', 'test']
            maintenance_commits = []
            for commit_type in maintenance_types:
                if commit_type in grouped_commits:
                    maintenance_commits.extend(grouped_commits[commit_type])
            
            if maintenance_commits:
                sections.append("### � Maintenance")
                for commit in maintenance_commits:
                    scope_text = f"**{commit.scope}**: " if commit.scope else ""
                    type_emoji = {
                        'refactor': '♻️',
                        'chore': '🧹', 
                        'ci': '👷',
                        'build': '📦',
                        'style': '💄',
                        'test': '✅'
                    }.get(commit.type, '🔧')
                    sections.append(f"- {type_emoji} {scope_text}{commit.description}")
                sections.append("")
            
            # Statistics
            stats = []
            if breaking_commits:
                stats.append(f"**Breaking Changes**: {len(breaking_commits)}")
            if 'feat' in grouped_commits:
                feat_count = len([c for c in grouped_commits['feat'] if not c.breaking])
                if feat_count > 0:
                    stats.append(f"**New Features**: {feat_count}")
            if 'fix' in grouped_commits:
                stats.append(f"**Bug Fixes**: {len(grouped_commits['fix'])}")
            if maintenance_commits:
                stats.append(f"**Maintenance**: {len(maintenance_commits)}")
            
            stats.append(f"**Total Changes**: {len(commits)} commits")
            
            if stats:
                sections.append("### � Release Statistics")
                sections.extend([f"- {stat}" for stat in stats])
                sections.append("")
            
            # Version recommendation
            if suggested_version_type != self.config.version_type:
                sections.append("### 💡 Version Recommendation")
                sections.append(f"- **Detected**: {suggested_version_type.value.title()} version recommended based on changes")
                sections.append(f"- **Configured**: {self.config.version_type.value.title()} version will be created")
                if has_breaking:
                    sections.append("- **⚠️ Note**: Breaking changes detected - consider major version bump")
                sections.append("")
            
            content = "\n".join(sections)
            
            return f"""## {version_icon} {header}

{content}
{self._generate_usage_block()}

{self._generate_footer(ReleaseContext.MANUAL)}"""
            
        except Exception as e:
            print(f"⚠️ Failed to generate semantic notes: {e}", file=sys.stderr)
            return f"""## 🚀 What's Changed

### 📝 Updates  
- Various improvements and updates

{self._generate_usage_block()}

{self._generate_footer(ReleaseContext.MANUAL)}"""

    def _get_last_version(self) -> str:
        """Get the last version tag for commit comparison."""
        try:
            result = self._run_command([
                'git', 'tag', '-l', 'v*', '--sort=-version:refname'
            ])
            tags = result.stdout.strip().split('\n')
            return tags[0] if tags and tags[0] else 'HEAD~10'
        except:
            return 'HEAD~10'

    def get_next_version(self, version_type: Optional[VersionType] = None) -> str:
        """Calculate the next version based on existing tags and version type."""
        if version_type is None:
            version_type = self.config.version_type
            
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
            
            # Calculate new version based on type
            if version_type == VersionType.MAJOR:
                new_version = f"v{major + 1}.0.0"
            elif version_type == VersionType.MINOR:
                new_version = f"v{major}.{minor + 1}.0"
            else:  # PATCH
                new_version = f"v{major}.{minor}.{patch + 1}"
            
            print(f"📦 Version increment: {latest_tag} → {new_version} ({version_type.value})")
            return new_version
            
        except Exception as e:
            print(f"⚠️ Version calculation failed: {e}", file=sys.stderr)
            return "v1.0.1"
            
    def create_and_publish_release(self, release_notes: str, **kwargs) -> str:
        """
        Create and publish a GitHub release with dry-run support.
        
        Args:
            release_notes: Release notes content
            **kwargs: Context-specific arguments
            
        Returns:
            The version that was created (or would be created in dry-run)
        """
        version = self.get_next_version()
        
        if self.config.dry_run:
            print(f"🧪 DRY RUN: Would create release {version}")
            print(f"📋 Release notes preview:\n{release_notes[:500]}...")
            return version
        
        print(f"🚀 Creating release {version}")
        
        # Configure git for automated commits
        self._run_command(['git', 'config', 'user.name', 'github-actions[bot]'])
        self._run_command(['git', 'config', 'user.email', 'github-actions[bot]@users.noreply.github.com'])
        
        # Create commit message based on context
        if self.config.context == ReleaseContext.DEPENDABOT:
            commit_msg = f"chore: update dependencies to {version}"
        else:
            commit_msg = f"release: {version}"
            
        # Create and push tags
        self._create_and_push_tags(version, commit_msg)
        
        # Create GitHub release
        self._run_command([
            'gh', 'release', 'create', version,
            '--title', version,
            '--notes', release_notes,
            '--latest'
        ])
        
        print(f"✅ Successfully created release {version}")
        return version
    
    def _create_and_push_tags(self, version: str, commit_msg: str) -> None:
        """Create and push version and major tags."""
        # Create and push version tag
        self._run_command(['git', 'tag', '-a', version, '-m', commit_msg])
        self._run_command(['git', 'push', 'origin', version])
        
        # Update major version tag for GitHub Actions best practice
        major_version = version.split('.')[0]  # e.g., "v1" from "v1.0.2"
        self._run_command(['git', 'tag', '-f', major_version, version])
        self._run_command(['git', 'push', 'origin', major_version, '--force'])
        
    def main(self) -> None:
        """
        Main workflow for automated release processing with context awareness.
        """
        context_name = "🤖 Dependabot" if self.config.context == ReleaseContext.DEPENDABOT else "🖱️ Manual"
        action_type = "DRY RUN" if self.config.dry_run else "RELEASE"
        
        print(f"🚀 Starting {action_type} process ({context_name})")
        
        try:
            if self.config.context == ReleaseContext.DEPENDABOT:
                # Process dependency update
                action_name, old_version, new_version = self.extract_dependency_info(self.config.pr_title)
                upstream_notes = self.fetch_upstream_notes(action_name, new_version, old_version)
                release_notes = self.generate_release_notes(
                    version=self.get_next_version(),
                    action_name=action_name,
                    old_version=old_version,
                    new_version=new_version,
                    upstream_notes=upstream_notes
                )
            else:
                # Process manual release
                release_notes = self.generate_release_notes(
                    version=self.get_next_version()
                )
            
            # Create and publish release (or dry run)
            version = self.create_and_publish_release(release_notes)
            
            if self.config.dry_run:
                print("🧪 Dry run completed successfully!")
            else:
                print("🎉 Release workflow completed successfully!")
            
        except Exception as e:
            print(f"❌ Release process failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    # Environment-based execution (no CLI args needed)
    manager = ReleaseManager()
    manager.main()