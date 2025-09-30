#!/usr/bin/env python3
"""
Metrics Dashboard Generator
Creates and updates a comprehensive metrics dashboard for GitHub Pages.
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import glob


class MetricsDashboard:
    """Generate and update metrics dashboard."""
    
    def __init__(self):
        """Initialize dashboard generator."""
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repository = os.getenv('REPOSITORY')
        
        # Create dashboard directory
        os.makedirs('dashboard', exist_ok=True)
        
        print(f"📊 Generating metrics dashboard for {self.repository}")
    
    def load_historical_data(self) -> List[Dict]:
        """Load historical metrics data."""
        
        historical_data = []
        
        # Load from historical_data.jsonl
        if os.path.exists('metrics/historical_data.jsonl'):
            with open('metrics/historical_data.jsonl', 'r') as f:
                for line in f:
                    if line.strip():
                        historical_data.append(json.loads(line.strip()))
        
        return historical_data
    
    def load_current_metrics(self) -> Dict[str, Any]:
        """Load current metrics data."""
        
        current_metrics = {}
        
        # Load individual metrics files
        metrics_files = [
            'metrics/release_metrics.json',
            'metrics/dependency_metrics.json', 
            'metrics/automation_metrics.json'
        ]
        
        for file_path in metrics_files:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    key = os.path.basename(file_path).replace('.json', '')
                    current_metrics[key] = json.load(f)
        
        return current_metrics
    
    def generate_dashboard_html(self, historical_data: List[Dict], current_metrics: Dict) -> str:
        """Generate HTML dashboard with charts and metrics."""
        
        # Prepare data for charts
        chart_data = self._prepare_chart_data(historical_data)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Release & Dependency Metrics - {self.repository}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f6f8fa;
            color: #24292f;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .metric-card h3 {{
            margin-top: 0;
            color: #0969da;
            border-bottom: 2px solid #f1f3f4;
            padding-bottom: 10px;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #1f2328;
            margin: 10px 0;
        }}
        .metric-trend {{
            font-size: 0.9em;
            color: #656d76;
        }}
        .status-good {{ color: #1a7f37; }}
        .status-warning {{ color: #bf8700; }}
        .status-error {{ color: #cf222e; }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .recommendations {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .recommendation {{
            margin: 10px 0;
            padding: 10px;
            border-left: 4px solid #0969da;
            background-color: #f6f8fa;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            color: #656d76;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Release & Dependency Metrics</h1>
            <h2>{self.repository}</h2>
            <p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        </div>
        
        <div class="metrics-grid">
            {self._generate_metric_cards(current_metrics)}
        </div>
        
        <div class="chart-container">
            <h3>📈 Release Frequency Trend</h3>
            <canvas id="releaseChart" width="400" height="200"></canvas>
        </div>
        
        <div class="chart-container">
            <h3>🔍 Dependency Health Score</h3>
            <canvas id="healthChart" width="400" height="200"></canvas>
        </div>
        
        <div class="chart-container">
            <h3>🤖 Automation Efficiency</h3>
            <canvas id="automationChart" width="400" height="200"></canvas>
        </div>
        
        <div class="recommendations">
            <h3>🎯 Current Recommendations</h3>
            {self._generate_recommendations_html(current_metrics)}
        </div>
        
        <div class="footer">
            <p>Generated by Release & Dependency Metrics System</p>
            <p>Data refreshed daily at 06:00 UTC</p>
        </div>
    </div>
    
    <script>
        {self._generate_chart_scripts(chart_data)}
    </script>
</body>
</html>"""
        
        return html
    
    def _generate_metric_cards(self, current_metrics: Dict) -> str:
        """Generate metric card HTML."""
        
        cards_html = ""
        
        # Release metrics card
        if 'release_metrics' in current_metrics:
            rm = current_metrics['release_metrics']
            automation_rate = round((rm.get('automated_releases', 0) / max(rm.get('total_releases', 1), 1)) * 100, 1)
            
            cards_html += f"""
            <div class="metric-card">
                <h3>🚀 Release Metrics</h3>
                <div class="metric-value">{rm.get('total_releases', 0)}</div>
                <div class="metric-trend">Total Releases (30 days)</div>
                <p><strong>Automation Rate:</strong> <span class="{'status-good' if automation_rate >= 80 else 'status-warning' if automation_rate >= 60 else 'status-error'}">{automation_rate}%</span></p>
                <p><strong>Avg Days Between:</strong> {round(rm.get('avg_days_between_releases', 0), 1)}</p>
                <p><strong>Security Releases:</strong> {rm.get('security_releases', 0)}</p>
            </div>
            """
        
        # Dependency metrics card
        if 'dependency_metrics' in current_metrics:
            dm = current_metrics['dependency_metrics']
            health_score = dm.get('health_score', 0)
            
            cards_html += f"""
            <div class="metric-card">
                <h3>🔍 Dependency Health</h3>
                <div class="metric-value {'status-good' if health_score >= 80 else 'status-warning' if health_score >= 60 else 'status-error'}">{round(health_score, 1)}/100</div>
                <div class="metric-trend">Overall Health Score</div>
                <p><strong>Total Dependencies:</strong> {dm.get('total_dependencies', 0)}</p>
                <p><strong>Outdated:</strong> <span class="{'status-good' if dm.get('outdated_dependencies', 0) == 0 else 'status-warning'}">{dm.get('outdated_dependencies', 0)}</span></p>
                <p><strong>Auto-merge Rate:</strong> {round(dm.get('auto_merge_success_rate', 0), 1)}%</p>
            </div>
            """
        
        # Automation metrics card
        if 'automation_metrics' in current_metrics:
            am = current_metrics['automation_metrics']
            efficiency = am.get('automation_efficiency', 0)
            
            cards_html += f"""
            <div class="metric-card">
                <h3>🤖 Automation Efficiency</h3>
                <div class="metric-value {'status-good' if efficiency >= 80 else 'status-warning' if efficiency >= 60 else 'status-error'}">{round(efficiency, 1)}%</div>
                <div class="metric-trend">Auto-merge Success Rate</div>
                <p><strong>Dependabot PRs:</strong> {am.get('total_dependabot_prs', 0)}</p>
                <p><strong>Auto-merged:</strong> {am.get('auto_merged_prs', 0)}</p>
                <p><strong>Avg Merge Time:</strong> {round(am.get('avg_merge_time_hours', 0), 1)}h</p>
            </div>
            """
        
        return cards_html
    
    def _generate_recommendations_html(self, current_metrics: Dict) -> str:
        """Generate recommendations HTML."""
        
        recommendations = []
        
        # Analyze metrics and generate recommendations
        if 'dependency_metrics' in current_metrics:
            dm = current_metrics['dependency_metrics']
            health_score = dm.get('health_score', 0)
            
            if health_score < 60:
                recommendations.append("🔴 **Critical**: Dependency health score below 60%. Immediate updates required.")
            elif health_score < 80:
                recommendations.append("🟡 **Warning**: Dependency health score below 80%. Plan update cycle.")
            else:
                recommendations.append("🟢 **Good**: Dependency health is excellent.")
        
        if 'automation_metrics' in current_metrics:
            am = current_metrics['automation_metrics']
            efficiency = am.get('automation_efficiency', 0)
            
            if efficiency < 60:
                recommendations.append("🔴 **Critical**: Automation efficiency below 60%. Review auto-merge criteria.")
            elif efficiency < 80:
                recommendations.append("🟡 **Warning**: Automation efficiency could be improved.")
        
        if not recommendations:
            recommendations.append("✅ **All Good**: No immediate action items detected.")
        
        html = ""
        for rec in recommendations:
            html += f'<div class="recommendation">{rec}</div>'
        
        return html
    
    def _prepare_chart_data(self, historical_data: List[Dict]) -> Dict:
        """Prepare data for charts."""
        
        # Sort by timestamp
        sorted_data = sorted(historical_data, key=lambda x: x.get('timestamp', ''))
        
        # Extract time series data
        timestamps = []
        release_counts = []
        health_scores = []
        automation_rates = []
        
        for entry in sorted_data[-30:]:  # Last 30 data points
            timestamps.append(entry.get('timestamp', ''))
            
            rm = entry.get('release_metrics', {})
            dm = entry.get('dependency_metrics', {})
            am = entry.get('automation_metrics', {})
            
            release_counts.append(rm.get('total_releases', 0))
            health_scores.append(dm.get('health_score', 0))
            automation_rates.append(am.get('automation_efficiency', 0))
        
        return {
            'timestamps': timestamps,
            'release_counts': release_counts,
            'health_scores': health_scores,
            'automation_rates': automation_rates
        }
    
    def _generate_chart_scripts(self, chart_data: Dict) -> str:
        """Generate JavaScript for charts."""
        
        return f"""
        // Release frequency chart
        const releaseCtx = document.getElementById('releaseChart').getContext('2d');
        new Chart(releaseCtx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(chart_data['timestamps'][-14:])},
                datasets: [{{
                    label: 'Releases',
                    data: {json.dumps(chart_data['release_counts'][-14:])},
                    borderColor: '#0969da',
                    backgroundColor: 'rgba(9, 105, 218, 0.1)',
                    tension: 0.1
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            stepSize: 1
                        }}
                    }}
                }}
            }}
        }});
        
        // Health score chart
        const healthCtx = document.getElementById('healthChart').getContext('2d');
        new Chart(healthCtx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(chart_data['timestamps'][-14:])},
                datasets: [{{
                    label: 'Health Score',
                    data: {json.dumps(chart_data['health_scores'][-14:])},
                    borderColor: '#1a7f37',
                    backgroundColor: 'rgba(26, 127, 55, 0.1)',
                    tension: 0.1
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        min: 0,
                        max: 100
                    }}
                }}
            }}
        }});
        
        // Automation efficiency chart
        const automationCtx = document.getElementById('automationChart').getContext('2d');
        new Chart(automationCtx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(chart_data['timestamps'][-14:])},
                datasets: [{{
                    label: 'Automation Rate (%)',
                    data: {json.dumps(chart_data['automation_rates'][-14:])},
                    borderColor: '#8250df',
                    backgroundColor: 'rgba(130, 80, 223, 0.1)',
                    tension: 0.1
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        min: 0,
                        max: 100
                    }}
                }}
            }}
        }});
        """
    
    def generate_readme_badge(self, current_metrics: Dict) -> str:
        """Generate README badges with current metrics."""
        
        badges = []
        
        if 'dependency_metrics' in current_metrics:
            health_score = current_metrics['dependency_metrics'].get('health_score', 0)
            color = "brightgreen" if health_score >= 80 else "yellow" if health_score >= 60 else "red"
            badges.append(f"![Dependency Health](https://img.shields.io/badge/Dependency%20Health-{health_score:.0f}%25-{color})")
        
        if 'automation_metrics' in current_metrics:
            automation_rate = current_metrics['automation_metrics'].get('automation_efficiency', 0)
            color = "brightgreen" if automation_rate >= 80 else "yellow" if automation_rate >= 60 else "red"
            badges.append(f"![Automation Rate](https://img.shields.io/badge/Automation%20Rate-{automation_rate:.0f}%25-{color})")
        
        if 'release_metrics' in current_metrics:
            total_releases = current_metrics['release_metrics'].get('total_releases', 0)
            badges.append(f"![Releases](https://img.shields.io/badge/Releases%20(30d)-{total_releases}-blue)")
        
        return " ".join(badges)
    
    def run(self):
        """Generate and update the dashboard."""
        print("🚀 Generating metrics dashboard...")
        
        try:
            # Load data
            historical_data = self.load_historical_data()
            current_metrics = self.load_current_metrics()
            
            # Generate dashboard HTML
            dashboard_html = self.generate_dashboard_html(historical_data, current_metrics)
            
            # Save dashboard
            with open('dashboard/index.html', 'w') as f:
                f.write(dashboard_html)
            
            # Generate README badges
            badges = self.generate_readme_badge(current_metrics)
            with open('dashboard/badges.md', 'w') as f:
                f.write(f"# Metrics Badges\\n\\n{badges}\\n")
            
            print("✅ Dashboard generated successfully!")
            print(f"📊 Dashboard available at: dashboard/index.html")
            
        except Exception as e:
            print(f"❌ Error generating dashboard: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    dashboard = MetricsDashboard()
    dashboard.run()