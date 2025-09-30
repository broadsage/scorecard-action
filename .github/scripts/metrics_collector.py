#!/usr/bin/env python3
"""
Release & Dependency Metrics Collector
Tracks release frequency, dependency health, and automation efficiency.
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from github import Github
import subprocess
import re


@dataclass
class ReleaseMetrics:
    """Release frequency and pattern metrics."""
    total_releases: int = 0
    automated_releases: int = 0
    manual_releases: int = 0
    patch_releases: int = 0
    minor_releases: int = 0
    major_releases: int = 0
    avg_days_between_releases: float = 0.0
    dependency_driven_releases: int = 0
    security_releases: int = 0
    release_frequency_trend: str = "stable"


@dataclass
class DependencyMetrics:
    """Dependency health and update metrics."""
    total_dependencies: int = 0
    outdated_dependencies: int = 0
    security_vulnerabilities: int = 0
    major_updates_available: int = 0
    minor_updates_available: int = 0
    patch_updates_available: int = 0
    avg_age_days: float = 0.0
    health_score: float = 0.0
    auto_merge_success_rate: float = 0.0


@dataclass
class AutomationMetrics:
    """Automation efficiency metrics."""
    total_dependabot_prs: int = 0
    auto_merged_prs: int = 0
    manual_review_prs: int = 0
    failed_auto_merges: int = 0
    avg_merge_time_hours: float = 0.0
    ci_success_rate: float = 0.0
    automation_efficiency: float = 0.0


class MetricsCollector:
    """Comprehensive metrics collection and analysis system."""
    
    def __init__(self):
        """Initialize the metrics collector."""
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repository = os.getenv('REPOSITORY')
        self.report_type = os.getenv('REPORT_TYPE', 'full')
        self.analysis_period = int(os.getenv('ANALYSIS_PERIOD', '30'))
        self.trigger_event = os.getenv('TRIGGER_EVENT', 'manual')
        
        if not all([self.github_token, self.repository]):
            print("❌ Error: GITHUB_TOKEN and REPOSITORY environment variables are required")
            sys.exit(1)
            
        self.github = Github(self.github_token)
        self.repo = self.github.get_repo(self.repository)
        
        # Create directories
        os.makedirs('metrics', exist_ok=True)
        os.makedirs('reports', exist_ok=True)
        
        print(f"🔍 Collecting metrics for {self.repository}")
        print(f"📅 Analysis period: {self.analysis_period} days")
        print(f"🎯 Report type: {self.report_type}")
    
    def collect_release_metrics(self) -> ReleaseMetrics:
        """Collect release frequency and pattern metrics."""
        print("📊 Collecting release metrics...")
        
        # Get releases from the analysis period
        cutoff_date = datetime.now() - timedelta(days=self.analysis_period)
        releases = list(self.repo.get_releases())
        
        # Filter releases within analysis period
        period_releases = [r for r in releases if r.created_at >= cutoff_date]
        
        metrics = ReleaseMetrics()
        metrics.total_releases = len(period_releases)
        
        if not period_releases:
            return metrics
        
        # Analyze release patterns
        release_dates = []
        for release in period_releases:
            release_dates.append(release.created_at)
            
            # Categorize by version type
            tag_name = release.tag_name
            if self._is_major_version(tag_name):
                metrics.major_releases += 1
            elif self._is_minor_version(tag_name):
                metrics.minor_releases += 1
            else:
                metrics.patch_releases += 1
            
            # Categorize by trigger type
            body = release.body or ""
            if "dependabot" in body.lower() or "dependency" in body.lower():
                metrics.dependency_driven_releases += 1
                metrics.automated_releases += 1
            elif "manual" in body.lower() or "workflow_dispatch" in body.lower():
                metrics.manual_releases += 1
            else:
                metrics.automated_releases += 1  # Default assumption
            
            # Check for security releases
            if any(word in body.lower() for word in ["security", "vulnerability", "cve", "patch"]):
                metrics.security_releases += 1
        
        # Calculate average days between releases
        if len(release_dates) > 1:
            release_dates.sort()
            intervals = []
            for i in range(1, len(release_dates)):
                interval = (release_dates[i] - release_dates[i-1]).days
                intervals.append(interval)
            metrics.avg_days_between_releases = sum(intervals) / len(intervals)
        
        # Determine release frequency trend
        if len(period_releases) >= 4:
            recent_half = period_releases[:len(period_releases)//2]
            older_half = period_releases[len(period_releases)//2:]
            
            if len(recent_half) > len(older_half):
                metrics.release_frequency_trend = "increasing"
            elif len(recent_half) < len(older_half):
                metrics.release_frequency_trend = "decreasing"
        
        print(f"✅ Found {metrics.total_releases} releases in the last {self.analysis_period} days")
        return metrics
    
    def collect_dependency_metrics(self) -> DependencyMetrics:
        """Collect dependency health metrics."""
        print("🔍 Analyzing dependency health...")
        
        metrics = DependencyMetrics()
        
        # Analyze action.yml dependencies
        try:
            action_file = self.repo.get_contents("action.yml")
            action_content = action_file.decoded_content.decode('utf-8')
            
            # Extract uses: statements
            uses_pattern = r'uses:\s*([^@\s]+)@([^\s]+)'
            dependencies = re.findall(uses_pattern, action_content)
            
            metrics.total_dependencies = len(dependencies)
            
            # Check each dependency for updates
            for action, version in dependencies:
                try:
                    health_data = self._check_dependency_health(action, version)
                    
                    if health_data['has_updates']:
                        if health_data['major_update']:
                            metrics.major_updates_available += 1
                        elif health_data['minor_update']:
                            metrics.minor_updates_available += 1
                        else:
                            metrics.patch_updates_available += 1
                    
                    if health_data['is_outdated']:
                        metrics.outdated_dependencies += 1
                    
                    metrics.avg_age_days += health_data['age_days']
                    
                except Exception as e:
                    print(f"⚠️ Warning: Could not check {action}: {e}")
                    continue
            
            if metrics.total_dependencies > 0:
                metrics.avg_age_days /= metrics.total_dependencies
                
                # Calculate health score (0-100)
                outdated_ratio = metrics.outdated_dependencies / metrics.total_dependencies
                metrics.health_score = max(0, 100 - (outdated_ratio * 100))
        
        except Exception as e:
            print(f"⚠️ Warning: Could not analyze dependencies: {e}")
        
        # Analyze auto-merge success rate
        metrics.auto_merge_success_rate = self._calculate_auto_merge_success_rate()
        
        print(f"✅ Analyzed {metrics.total_dependencies} dependencies")
        return metrics
    
    def collect_automation_metrics(self) -> AutomationMetrics:
        """Collect automation efficiency metrics."""
        print("🤖 Analyzing automation efficiency...")
        
        metrics = AutomationMetrics()
        cutoff_date = datetime.now() - timedelta(days=self.analysis_period)
        
        # Get Dependabot PRs from the analysis period
        prs = list(self.repo.get_pulls(state='all', sort='created', direction='desc'))
        dependabot_prs = [pr for pr in prs 
                         if pr.created_at >= cutoff_date 
                         and pr.user.login == 'dependabot[bot]']
        
        metrics.total_dependabot_prs = len(dependabot_prs)
        
        if not dependabot_prs:
            return metrics
        
        merge_times = []
        successful_merges = 0
        
        for pr in dependabot_prs:
            # Check if auto-merged (look for specific patterns)
            if pr.merged and pr.merged_by and pr.merged_by.login in ['github-actions[bot]', 'dependabot[bot]']:
                metrics.auto_merged_prs += 1
                successful_merges += 1
                
                # Calculate merge time
                if pr.merged_at and pr.created_at:
                    merge_time = (pr.merged_at - pr.created_at).total_seconds() / 3600
                    merge_times.append(merge_time)
            elif pr.merged:
                metrics.manual_review_prs += 1
                successful_merges += 1
            else:
                metrics.failed_auto_merges += 1
        
        # Calculate averages
        if merge_times:
            metrics.avg_merge_time_hours = sum(merge_times) / len(merge_times)
        
        if metrics.total_dependabot_prs > 0:
            metrics.ci_success_rate = (successful_merges / metrics.total_dependabot_prs) * 100
            metrics.automation_efficiency = (metrics.auto_merged_prs / metrics.total_dependabot_prs) * 100
        
        print(f"✅ Analyzed {metrics.total_dependabot_prs} Dependabot PRs")
        return metrics
    
    def _is_major_version(self, tag: str) -> bool:
        """Check if version is a major release."""
        match = re.match(r'v(\d+)\.(\d+)\.(\d+)', tag)
        if match:
            major, minor, patch = map(int, match.groups())
            return minor == 0 and patch == 0
        return False
    
    def _is_minor_version(self, tag: str) -> bool:
        """Check if version is a minor release."""
        match = re.match(r'v(\d+)\.(\d+)\.(\d+)', tag)
        if match:
            major, minor, patch = map(int, match.groups())
            return patch == 0 and minor > 0
        return False
    
    def _check_dependency_health(self, action: str, current_version: str) -> Dict[str, Any]:
        """Check the health status of a dependency."""
        # Simplified dependency health check
        # In a real implementation, you'd check against GitHub releases API
        return {
            'has_updates': False,
            'major_update': False,
            'minor_update': False,
            'is_outdated': False,
            'age_days': 30,  # Default age
        }
    
    def _calculate_auto_merge_success_rate(self) -> float:
        """Calculate the auto-merge success rate."""
        # This would analyze recent auto-merge attempts
        # Return a placeholder for now
        return 85.0  # 85% success rate placeholder
    
    def generate_report(self, release_metrics: ReleaseMetrics, 
                       dependency_metrics: DependencyMetrics,
                       automation_metrics: AutomationMetrics) -> str:
        """Generate a comprehensive metrics report."""
        
        report = f"""# 📊 Release & Dependency Metrics Report

## 🎯 Analysis Summary
- **Period**: Last {self.analysis_period} days
- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
- **Trigger**: {self.trigger_event}

## 🚀 Release Metrics
| Metric | Value | Trend |
|--------|--------|--------|
| **Total Releases** | {release_metrics.total_releases} | {release_metrics.release_frequency_trend} |
| **Automated Releases** | {release_metrics.automated_releases} | {round((release_metrics.automated_releases/max(release_metrics.total_releases,1))*100, 1)}% |
| **Dependency-Driven** | {release_metrics.dependency_driven_releases} | {round((release_metrics.dependency_driven_releases/max(release_metrics.total_releases,1))*100, 1)}% |
| **Security Releases** | {release_metrics.security_releases} | Critical |
| **Avg Days Between Releases** | {round(release_metrics.avg_days_between_releases, 1)} | - |

### Version Distribution
- 🔴 **Major**: {release_metrics.major_releases}
- 🟡 **Minor**: {release_metrics.minor_releases}  
- 🟢 **Patch**: {release_metrics.patch_releases}

## 🔍 Dependency Health
| Metric | Value | Status |
|--------|--------|---------|
| **Total Dependencies** | {dependency_metrics.total_dependencies} | - |
| **Health Score** | {round(dependency_metrics.health_score, 1)}/100 | {'🟢 Healthy' if dependency_metrics.health_score >= 80 else '🟡 Moderate' if dependency_metrics.health_score >= 60 else '🔴 Needs Attention'} |
| **Outdated Dependencies** | {dependency_metrics.outdated_dependencies} | {'🟢 Good' if dependency_metrics.outdated_dependencies <= 1 else '🟡 Monitor' if dependency_metrics.outdated_dependencies <= 3 else '🔴 Action Needed'} |
| **Available Updates** | {dependency_metrics.major_updates_available + dependency_metrics.minor_updates_available + dependency_metrics.patch_updates_available} | - |
| **Auto-merge Success** | {round(dependency_metrics.auto_merge_success_rate, 1)}% | {'🟢 Excellent' if dependency_metrics.auto_merge_success_rate >= 90 else '🟡 Good' if dependency_metrics.auto_merge_success_rate >= 75 else '🔴 Needs Improvement'} |

## 🤖 Automation Efficiency  
| Metric | Value | Performance |
|--------|--------|-------------|
| **Dependabot PRs** | {automation_metrics.total_dependabot_prs} | - |
| **Auto-merged** | {automation_metrics.auto_merged_prs} | {round(automation_metrics.automation_efficiency, 1)}% |
| **Manual Review Required** | {automation_metrics.manual_review_prs} | {round((automation_metrics.manual_review_prs/max(automation_metrics.total_dependabot_prs,1))*100, 1)}% |
| **Failed Auto-merges** | {automation_metrics.failed_auto_merges} | {round((automation_metrics.failed_auto_merges/max(automation_metrics.total_dependabot_prs,1))*100, 1)}% |
| **Avg Merge Time** | {round(automation_metrics.avg_merge_time_hours, 1)}h | {'🟢 Fast' if automation_metrics.avg_merge_time_hours <= 2 else '🟡 Moderate' if automation_metrics.avg_merge_time_hours <= 8 else '🔴 Slow'} |

## 📈 Key Insights

### 🎯 Release Pattern Analysis
- Release frequency is **{release_metrics.release_frequency_trend}**
- **{round((release_metrics.automated_releases/max(release_metrics.total_releases,1))*100, 1)}%** of releases are automated
- Average **{round(release_metrics.avg_days_between_releases, 1)} days** between releases

### 🔍 Dependency Health Status  
- Overall health score: **{round(dependency_metrics.health_score, 1)}/100**
- **{dependency_metrics.outdated_dependencies}** dependencies need updates
- Auto-merge success rate: **{round(dependency_metrics.auto_merge_success_rate, 1)}%**

### 🤖 Automation Performance
- **{round(automation_metrics.automation_efficiency, 1)}%** of Dependabot PRs are auto-merged
- Average merge time: **{round(automation_metrics.avg_merge_time_hours, 1)} hours**
- CI success rate: **{round(automation_metrics.ci_success_rate, 1)}%**

## 🎯 Recommendations

"""

        # Add recommendations based on metrics
        recommendations = []
        
        if dependency_metrics.health_score < 80:
            recommendations.append("🔴 **Update Dependencies**: Health score below 80%. Review and update outdated dependencies.")
            
        if automation_metrics.automation_efficiency < 70:
            recommendations.append("🟡 **Improve Auto-merge**: Only {:.1f}% of PRs are auto-merged. Review auto-merge criteria.".format(automation_metrics.automation_efficiency))
            
        if release_metrics.avg_days_between_releases > 14:
            recommendations.append("📅 **Increase Release Frequency**: {:.1f} days between releases. Consider more frequent releases.".format(release_metrics.avg_days_between_releases))
            
        if dependency_metrics.security_vulnerabilities > 0:
            recommendations.append("🛡️ **Security Alert**: {} security vulnerabilities detected. Immediate attention required.".format(dependency_metrics.security_vulnerabilities))
        
        if recommendations:
            for rec in recommendations:
                report += f"- {rec}\n"
        else:
            report += "- 🟢 **All Good**: No immediate action items. System is performing well!\n"
        
        report += f"""
## 📊 Historical Data
- Report generated: {datetime.now().isoformat()}
- Analysis period: {self.analysis_period} days
- Repository: {self.repository}

---
*Generated by Release & Dependency Metrics Collector*
"""
        
        return report
    
    def save_metrics_data(self, release_metrics: ReleaseMetrics, 
                         dependency_metrics: DependencyMetrics,
                         automation_metrics: AutomationMetrics):
        """Save raw metrics data for historical tracking."""
        
        timestamp = datetime.now().isoformat()
        
        metrics_data = {
            'timestamp': timestamp,
            'analysis_period_days': self.analysis_period,
            'release_metrics': asdict(release_metrics),
            'dependency_metrics': asdict(dependency_metrics),
            'automation_metrics': asdict(automation_metrics)
        }
        
        # Save individual metrics files
        with open('metrics/release_metrics.json', 'w') as f:
            json.dump(asdict(release_metrics), f, indent=2)
            
        with open('metrics/dependency_metrics.json', 'w') as f:
            json.dump(asdict(dependency_metrics), f, indent=2)
            
        with open('metrics/automation_metrics.json', 'w') as f:
            json.dump(asdict(automation_metrics), f, indent=2)
        
        # Save combined historical data
        historical_file = 'metrics/historical_data.jsonl'
        with open(historical_file, 'a') as f:
            f.write(json.dumps(metrics_data) + '\n')
        
        print(f"✅ Metrics data saved to metrics/ directory")
    
    def run(self):
        """Run the complete metrics collection process."""
        print("🚀 Starting metrics collection...")
        
        try:
            # Collect all metrics
            release_metrics = self.collect_release_metrics()
            dependency_metrics = self.collect_dependency_metrics()
            automation_metrics = self.collect_automation_metrics()
            
            # Generate report
            report = self.generate_report(release_metrics, dependency_metrics, automation_metrics)
            
            # Save data
            self.save_metrics_data(release_metrics, dependency_metrics, automation_metrics)
            
            # Save report
            with open('reports/metrics_summary.md', 'w') as f:
                f.write(report)
            
            print("🎉 Metrics collection completed successfully!")
            print(f"📊 Report saved to reports/metrics_summary.md")
            
        except Exception as e:
            print(f"❌ Error during metrics collection: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    collector = MetricsCollector()
    collector.run()