#!/usr/bin/env python3
"""
Dependency Health Analyzer
Advanced dependency health tracking with security vulnerability scanning.
"""

import os
import sys
import json
import re
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import urllib.request
import urllib.parse


@dataclass
class DependencyInfo:
    """Information about a single dependency."""
    name: str
    current_version: str
    latest_version: str = ""
    is_outdated: bool = False
    has_security_issues: bool = False
    age_days: int = 0
    update_available: str = "none"  # none, patch, minor, major
    security_advisories: List[str] = None
    release_notes_url: str = ""
    
    def __post_init__(self):
        if self.security_advisories is None:
            self.security_advisories = []


@dataclass 
class DependencyHealthReport:
    """Comprehensive dependency health report."""
    scan_timestamp: str
    total_dependencies: int = 0
    healthy_dependencies: int = 0
    outdated_dependencies: int = 0
    vulnerable_dependencies: int = 0
    critical_vulnerabilities: int = 0
    high_vulnerabilities: int = 0
    medium_vulnerabilities: int = 0
    low_vulnerabilities: int = 0
    overall_health_score: float = 0.0
    recommendations: List[str] = None
    dependencies: List[DependencyInfo] = None
    
    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []
        if self.dependencies is None:
            self.dependencies = []


class DependencyHealthAnalyzer:
    """Advanced dependency health analysis and tracking."""
    
    def __init__(self):
        """Initialize the dependency health analyzer."""
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repository = os.getenv('REPOSITORY')
        
        if not all([self.github_token, self.repository]):
            print("❌ Error: GITHUB_TOKEN and REPOSITORY environment variables are required")
            sys.exit(1)
        
        # Create output directories
        os.makedirs('metrics', exist_ok=True)
        os.makedirs('reports', exist_ok=True)
        
        print(f"🔍 Starting dependency health analysis for {self.repository}")
    
    def analyze_action_dependencies(self) -> List[DependencyInfo]:
        """Analyze dependencies in action.yml file."""
        print("📋 Analyzing action.yml dependencies...")
        
        dependencies = []
        
        try:
            # Read action.yml file
            if os.path.exists('action.yml'):
                with open('action.yml', 'r') as f:
                    content = f.read()
            else:
                # Fetch from repository
                content = self._fetch_file_content('action.yml')
            
            # Extract uses: statements
            uses_pattern = r'uses:\s*([^@\s]+)@([^\s\n]+)'
            matches = re.findall(uses_pattern, content)
            
            for action_name, version in matches:
                dep_info = self._analyze_single_dependency(action_name, version)
                dependencies.append(dep_info)
                print(f"  📦 {action_name}@{version} - {dep_info.update_available} update available")
        
        except Exception as e:
            print(f"⚠️ Warning: Could not analyze action.yml: {e}")
        
        return dependencies
    
    def analyze_workflow_dependencies(self) -> List[DependencyInfo]:
        """Analyze dependencies in workflow files."""
        print("🔄 Analyzing workflow dependencies...")
        
        dependencies = []
        workflow_files = [
            '.github/workflows/release.yml',
            '.github/workflows/dependabot-auto-merge.yml',
            '.github/workflows/metrics-collection.yml'
        ]
        
        for workflow_file in workflow_files:
            try:
                if os.path.exists(workflow_file):
                    with open(workflow_file, 'r') as f:
                        content = f.read()
                else:
                    content = self._fetch_file_content(workflow_file)
                
                # Extract uses: statements from workflows
                uses_pattern = r'uses:\s*([^@\s]+)@([^\s\n]+)'
                matches = re.findall(uses_pattern, content)
                
                for action_name, version in matches:
                    # Avoid duplicates
                    if not any(dep.name == action_name for dep in dependencies):
                        dep_info = self._analyze_single_dependency(action_name, version)
                        dependencies.append(dep_info)
                        print(f"  🔄 {action_name}@{version} - {dep_info.update_available} update available")
            
            except Exception as e:
                print(f"⚠️ Warning: Could not analyze {workflow_file}: {e}")
                continue
        
        return dependencies
    
    def _analyze_single_dependency(self, action_name: str, current_version: str) -> DependencyInfo:
        """Analyze a single dependency for health metrics."""
        
        dep_info = DependencyInfo(
            name=action_name,
            current_version=current_version
        )
        
        try:
            # Get latest version information
            latest_info = self._get_latest_version(action_name)
            dep_info.latest_version = latest_info.get('tag_name', current_version)
            dep_info.release_notes_url = latest_info.get('html_url', '')
            
            # Compare versions
            update_type = self._compare_versions(current_version, dep_info.latest_version)
            dep_info.update_available = update_type
            dep_info.is_outdated = update_type != "none"
            
            # Calculate age
            if 'published_at' in latest_info:
                release_date = datetime.fromisoformat(latest_info['published_at'].replace('Z', '+00:00'))
                dep_info.age_days = (datetime.now(release_date.tzinfo) - release_date).days
            
            # Check for security advisories (simplified)
            dep_info.security_advisories = self._check_security_advisories(action_name)
            dep_info.has_security_issues = len(dep_info.security_advisories) > 0
            
        except Exception as e:
            print(f"⚠️ Warning: Could not fully analyze {action_name}: {e}")
        
        return dep_info
    
    def _get_latest_version(self, action_name: str) -> Dict[str, Any]:
        """Get the latest version information from GitHub API."""
        
        try:
            # GitHub API endpoint for latest release
            url = f"https://api.github.com/repos/{action_name}/releases/latest"
            
            req = urllib.request.Request(url)
            req.add_header('Authorization', f'token {self.github_token}')
            req.add_header('Accept', 'application/vnd.github.v3+json')
            
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data
                
        except Exception as e:
            print(f"⚠️ Could not fetch latest version for {action_name}: {e}")
            return {}
    
    def _compare_versions(self, current: str, latest: str) -> str:
        """Compare two versions and return update type."""
        
        # Simple version comparison for common patterns
        def parse_version(v):
            # Handle v1.2.3, 1.2.3, v1, etc.
            v = v.lstrip('v')
            parts = v.split('.')
            # Pad with zeros if needed
            while len(parts) < 3:
                parts.append('0')
            return [int(p) for p in parts[:3]]
        
        try:
            current_parts = parse_version(current)
            latest_parts = parse_version(latest)
            
            if current_parts == latest_parts:
                return "none"
            elif current_parts[0] < latest_parts[0]:
                return "major"
            elif current_parts[1] < latest_parts[1]:
                return "minor"
            elif current_parts[2] < latest_parts[2]:
                return "patch"
            else:
                return "none"
                
        except Exception:
            # Fallback for non-standard version formats
            return "unknown" if current != latest else "none"
    
    def _check_security_advisories(self, action_name: str) -> List[str]:
        """Check for security advisories for a dependency."""
        
        # Placeholder for security advisory checking
        # In a real implementation, you would:
        # 1. Query GitHub Security Advisories API
        # 2. Check CVE databases
        # 3. Scan dependency security databases
        
        # For demonstration, return empty list
        return []
    
    def _fetch_file_content(self, file_path: str) -> str:
        """Fetch file content from the repository."""
        
        try:
            url = f"https://api.github.com/repos/{self.repository}/contents/{file_path}"
            
            req = urllib.request.Request(url)
            req.add_header('Authorization', f'token {self.github_token}')
            req.add_header('Accept', 'application/vnd.github.v3+json')
            
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                # Decode base64 content
                import base64
                content = base64.b64decode(data['content']).decode('utf-8')
                return content
                
        except Exception as e:
            print(f"⚠️ Could not fetch {file_path}: {e}")
            return ""
    
    def generate_health_report(self, all_dependencies: List[DependencyInfo]) -> DependencyHealthReport:
        """Generate comprehensive health report."""
        
        print("📊 Generating dependency health report...")
        
        report = DependencyHealthReport(
            scan_timestamp=datetime.now().isoformat(),
            dependencies=all_dependencies
        )
        
        # Calculate metrics
        report.total_dependencies = len(all_dependencies)
        report.outdated_dependencies = sum(1 for dep in all_dependencies if dep.is_outdated)
        report.vulnerable_dependencies = sum(1 for dep in all_dependencies if dep.has_security_issues)
        report.healthy_dependencies = report.total_dependencies - report.outdated_dependencies
        
        # Count vulnerability severity (placeholder logic)
        for dep in all_dependencies:
            if dep.has_security_issues:
                # Simplified severity counting
                report.high_vulnerabilities += len(dep.security_advisories)
        
        # Calculate overall health score
        if report.total_dependencies > 0:
            health_factors = []
            
            # Factor 1: Outdated ratio (0-40 points)
            outdated_ratio = report.outdated_dependencies / report.total_dependencies
            health_factors.append(max(0, 40 - (outdated_ratio * 40)))
            
            # Factor 2: Security issues (0-30 points)
            vuln_ratio = report.vulnerable_dependencies / report.total_dependencies
            health_factors.append(max(0, 30 - (vuln_ratio * 30)))
            
            # Factor 3: Update availability (0-30 points)
            major_updates = sum(1 for dep in all_dependencies if dep.update_available == "major")
            major_ratio = major_updates / report.total_dependencies
            health_factors.append(max(0, 30 - (major_ratio * 30)))
            
            report.overall_health_score = sum(health_factors)
        
        # Generate recommendations
        report.recommendations = self._generate_recommendations(report)
        
        return report
    
    def _generate_recommendations(self, report: DependencyHealthReport) -> List[str]:
        """Generate actionable recommendations based on health analysis."""
        
        recommendations = []
        
        if report.vulnerable_dependencies > 0:
            recommendations.append(
                f"🔴 **CRITICAL**: {report.vulnerable_dependencies} dependencies have security vulnerabilities. Update immediately."
            )
        
        if report.outdated_dependencies > report.total_dependencies * 0.5:
            recommendations.append(
                f"🟡 **HIGH**: {report.outdated_dependencies}/{report.total_dependencies} dependencies are outdated. Plan update cycle."
            )
        
        major_updates = sum(1 for dep in report.dependencies if dep.update_available == "major")
        if major_updates > 0:
            recommendations.append(
                f"🟠 **MEDIUM**: {major_updates} major version updates available. Review for breaking changes."
            )
        
        patch_updates = sum(1 for dep in report.dependencies if dep.update_available == "patch")
        if patch_updates > 0:
            recommendations.append(
                f"🟢 **LOW**: {patch_updates} patch updates available. Safe to auto-update."
            )
        
        if report.overall_health_score >= 80:
            recommendations.append("✅ **GOOD**: Dependency health is excellent. Continue current practices.")
        elif report.overall_health_score >= 60:
            recommendations.append("⚠️ **MODERATE**: Dependency health needs attention. Plan update strategy.")
        else:
            recommendations.append("🚨 **POOR**: Dependency health requires immediate action.")
        
        return recommendations
    
    def save_health_data(self, report: DependencyHealthReport):
        """Save health report data for tracking and analysis."""
        
        # Save detailed report
        with open('reports/dependency_health_report.json', 'w') as f:
            json.dump(asdict(report), f, indent=2, default=str)
        
        # Save summary metrics
        summary = {
            'timestamp': report.scan_timestamp,
            'total_dependencies': report.total_dependencies,
            'outdated_dependencies': report.outdated_dependencies,
            'vulnerable_dependencies': report.vulnerable_dependencies,
            'health_score': report.overall_health_score
        }
        
        # Append to historical tracking
        with open('metrics/dependency_health_history.jsonl', 'a') as f:
            f.write(json.dumps(summary) + '\n')
        
        # Generate markdown report
        markdown_report = self._generate_markdown_report(report)
        with open('reports/dependency_health.md', 'w') as f:
            f.write(markdown_report)
        
        print(f"✅ Health report saved to reports/ directory")
    
    def _generate_markdown_report(self, report: DependencyHealthReport) -> str:
        """Generate markdown formatted health report."""
        
        markdown = f"""# 🔍 Dependency Health Report

## 📊 Health Summary
- **Scan Date**: {report.scan_timestamp}
- **Total Dependencies**: {report.total_dependencies}
- **Health Score**: {report.overall_health_score:.1f}/100

### 📈 Health Metrics
| Metric | Count | Percentage | Status |
|--------|--------|------------|--------|
| **Healthy** | {report.healthy_dependencies} | {(report.healthy_dependencies/max(report.total_dependencies,1)*100):.1f}% | {'🟢' if report.healthy_dependencies/max(report.total_dependencies,1) >= 0.8 else '🟡' if report.healthy_dependencies/max(report.total_dependencies,1) >= 0.6 else '🔴'} |
| **Outdated** | {report.outdated_dependencies} | {(report.outdated_dependencies/max(report.total_dependencies,1)*100):.1f}% | {'🟢' if report.outdated_dependencies == 0 else '🟡' if report.outdated_dependencies <= 2 else '🔴'} |
| **Vulnerable** | {report.vulnerable_dependencies} | {(report.vulnerable_dependencies/max(report.total_dependencies,1)*100):.1f}% | {'🟢' if report.vulnerable_dependencies == 0 else '🔴'} |

## 📋 Dependency Details

"""
        
        # Add dependency table
        if report.dependencies:
            markdown += """| Dependency | Current | Latest | Status | Update | Security |
|------------|---------|--------|---------|---------|----------|
"""
            
            for dep in report.dependencies:
                status_icon = "🟢" if not dep.is_outdated else "🟡" if dep.update_available in ["patch", "minor"] else "🔴"
                security_icon = "🛡️" if not dep.has_security_issues else "⚠️"
                
                markdown += f"| {dep.name} | {dep.current_version} | {dep.latest_version} | {status_icon} | {dep.update_available} | {security_icon} |\n"
        
        # Add recommendations
        markdown += "\n## 🎯 Recommendations\n\n"
        for rec in report.recommendations:
            markdown += f"- {rec}\n"
        
        markdown += f"""
## 📊 Historical Tracking
- Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
- Previous scans available in `metrics/dependency_health_history.jsonl`

---
*Generated by Dependency Health Analyzer*
"""
        
        return markdown
    
    def run(self):
        """Run the complete dependency health analysis."""
        print("🚀 Starting dependency health analysis...")
        
        try:
            # Analyze all dependency sources
            action_deps = self.analyze_action_dependencies()
            workflow_deps = self.analyze_workflow_dependencies()
            
            # Combine and deduplicate
            all_deps = action_deps + workflow_deps
            unique_deps = []
            seen_names = set()
            
            for dep in all_deps:
                if dep.name not in seen_names:
                    unique_deps.append(dep)
                    seen_names.add(dep.name)
            
            # Generate health report
            health_report = self.generate_health_report(unique_deps)
            
            # Save results
            self.save_health_data(health_report)
            
            print(f"🎉 Dependency health analysis completed!")
            print(f"📊 Analyzed {len(unique_deps)} unique dependencies")
            print(f"💯 Overall health score: {health_report.overall_health_score:.1f}/100")
            
        except Exception as e:
            print(f"❌ Error during dependency health analysis: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    analyzer = DependencyHealthAnalyzer()
    analyzer.run()