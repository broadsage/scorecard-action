# OpenSSF Scorecard Action

[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/broadsage/scorecard-action/badge)](https://securityscorecards.dev/viewer/?uri=github.com/broadsage/scorecard-action)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**Workflow enhancements for OpenSSF Scorecard** with notifications, thresholds, and enhanced reporting. Built on top of the official `ossf/scorecard-action`.

## 🎯 What This Action Does

This action **uses the official OpenSSF Scorecard** and adds **workflow enhancements** around it:

✅ **Real OpenSSF Scorecard Data** (via `ossf/scorecard-action`)

- Authentic security analysis with 15+ security checks
- Official scoring algorithm (0-10 scale)
- SARIF output for GitHub Code Scanning integration
- Results publishing to OpenSSF API

✅ **Workflow Enhancements** (our value-add)

- Score threshold validation with failure options
- Rich Slack notifications with interactive blocks
- Generic webhook integration for custom dashboards  
- Enhanced reporting with score interpretation
- Configurable artifact retention and naming

## 🚀 Quick Start

### Basic Usage

```yaml
name: Security Analysis
on:
  push:
    branches: [main]
  schedule:
    - cron: '0 2 * * 1'  # Weekly analysis

jobs:
  security-scan:
    name: Security Analysis
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: broadsage/scorecard-action@v1
        with:
          publish_results: true
```

### Enhanced Usage with Notifications

```yaml
jobs:
  security-scan:
    name: Security Analysis  
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: broadsage/scorecard-action@v1
        with:
          # Official Scorecard Configuration
          publish_results: true
          results_format: 'sarif'
          
          # Workflow Enhancements
          minimum_score_threshold: '7.0'
          fail_on_score: true
          
          # Notifications
          slack_bot_token: ${{ secrets.SLACK_BOT_TOKEN }}
          slack_channel_id: ${{ secrets.SLACK_CHANNEL_ID }}
          webhook_url: ${{ secrets.SECURITY_WEBHOOK }}
```

## 📋 Inputs

### Core Configuration (passed to official OpenSSF Scorecard)

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `repo_token` | GitHub token for analysis | No | `${{ github.token }}` |
| `results_file` | Path to save scorecard results | No | `scorecard-results.sarif` |
| `results_format` | Output format (sarif, json) | No | `sarif` |
| `publish_results` | Publish results to OpenSSF API | No | `true` |

### Workflow Enhancement Features

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `minimum_score_threshold` | Minimum acceptable score (0.0-10.0) | No | `6.0` |
| `fail_on_score` | Fail action if score below threshold | No | `false` |
| `retention_days` | Days to retain artifacts | No | `30` |
| `artifact_name` | Name for uploaded artifacts | No | `scorecard-analysis-results` |

### Notifications

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `slack_bot_token` | Slack Bot Token for official integration | No | `''` |
| `slack_channel_id` | Slack channel ID for bot notifications | No | `''` |
| `webhook_url` | Generic webhook URL for custom integrations | No | `''` |

## 📊 Outputs

### Core Outputs (from OpenSSF Scorecard)

| Output | Description |
|--------|-------------|
| `overall_score` | Overall OpenSSF Scorecard score (0.0-10.0) |
| `passed_checks` | Number of checks passed |
| `total_checks` | Total number of checks performed |
| `failed_checks` | Number of checks failed |

### Workflow Enhancement Outputs

| Output | Description |
|--------|-------------|
| `threshold_met` | Whether score meets minimum threshold |
| `analysis_success` | Whether analysis completed successfully |

## 📈 Usage Examples

### Score Threshold Validation

```yaml
name: PR Security Gate
on:
  pull_request:
    branches: [main]

jobs:
  security-gate:
    name: Security Gate
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: broadsage/scorecard-action@v1
        with:
          minimum_score_threshold: '8.0'
          fail_on_score: true  # Block PR if score too low
          slack_bot_token: ${{ secrets.SLACK_BOT_TOKEN }}
          slack_channel_id: ${{ secrets.SLACK_CHANNEL_ID }}
```

### Scheduled Security Assessment

```yaml
name: Weekly Security Assessment  
on:
  schedule:
    - cron: '0 2 * * 1'  # Monday 2 AM UTC

jobs:
  security-assessment:
    name: Security Assessment
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write  
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: broadsage/scorecard-action@v1
        with:
          minimum_score_threshold: '7.0'
          slack_bot_token: ${{ secrets.SLACK_BOT_TOKEN }}
          slack_channel_id: ${{ secrets.SLACK_CHANNEL_ID }}
          webhook_url: ${{ secrets.SECURITY_DASHBOARD_WEBHOOK }}
          retention_days: 90
```

### Custom Workflow Integration

```yaml
name: Custom Security Analysis
on:
  workflow_dispatch:
    inputs:
      threshold:
        description: 'Minimum score threshold'
        required: true
        default: '6.0'

jobs:
  analysis:
    name: Analysis
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: broadsage/scorecard-action@v1
        with:
          minimum_score_threshold: ${{ github.event.inputs.threshold }}
          results_format: 'json'  # Get JSON instead of SARIF
          webhook_url: ${{ secrets.CUSTOM_WEBHOOK }}
```

## 📊 Generated Reports

### Artifacts Created

- `scorecard-results.sarif` - SARIF format results for code scanning alerts
- `scorecard-results.json` - JSON format for custom processing (when format=json)
- `scorecard-summary.json` - Action-generated summary with parsed score and key metrics

### GitHub Integration

- **Code Scanning** - SARIF results uploaded automatically for security alerts
- **Job Summary** - Rich summary displayed in GitHub Actions interface  
- **Artifacts** - All reports available as downloadable artifacts with configurable retention

## 🔔 Notification Examples

### Slack Integration

Using the official Slack Bot Token for rich notifications:

```yaml
- uses: broadsage/scorecard-action@v1
  with:
    slack_bot_token: ${{ secrets.SLACK_BOT_TOKEN }}
    slack_channel_id: ${{ secrets.SLACK_CHANNEL_ID }}  # e.g., C1234567890
    minimum_score_threshold: '7.0'
```

### Custom Webhook

```yaml  
- uses: broadsage/scorecard-action@v1
  with:
    webhook_url: 'https://security-dashboard.company.com/webhook'
    minimum_score_threshold: '7.0'
```

### Complete Notification Setup

```yaml
- uses: broadsage/scorecard-action@v1
  with:
    # Official Slack integration (preferred)
    slack_bot_token: ${{ secrets.SLACK_BOT_TOKEN }}
    slack_channel_id: ${{ secrets.SLACK_CHANNEL_ID }}
    
    # Custom webhook for dashboards
    webhook_url: ${{ secrets.SECURITY_WEBHOOK }}
    
    # Threshold configuration
    minimum_score_threshold: '7.0'
    fail_on_score: true
```

## 🏢 Enterprise Deployment

### Organization-wide Configuration

Create a centralized workflow template:

```yaml
# .github/workflows/security-analysis.yml
name: Security Analysis
on:
  push:
    branches: [main]
  schedule:
    - cron: '0 2 * * 1'

jobs:
  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: broadsage/scorecard-action@v1
        with:
          minimum_score_threshold: ${{ vars.MIN_SECURITY_SCORE }}
          slack_bot_token: ${{ secrets.SLACK_BOT_TOKEN }}
          slack_channel_id: ${{ secrets.SLACK_CHANNEL_ID }}
          webhook_url: ${{ secrets.SECURITY_WEBHOOK }}
          fail_on_score: ${{ vars.FAIL_ON_LOW_SCORE }}
```

### Repository Variables

- `MIN_SECURITY_SCORE`: 7.0
- `FAIL_ON_LOW_SCORE`: true

### Organization Secrets

- `SLACK_BOT_TOKEN`: Slack Bot Token for official integration
- `SLACK_CHANNEL_ID`: Primary security channel ID  
- `SECURITY_WEBHOOK`: Custom dashboard webhook URL for metrics collection

## 🔧 Troubleshooting

### Common Issues

#### Authentication Errors

```yaml
# Ensure proper token permissions
- uses: broadsage/scorecard-action@v1
  with:
    repo_token: ${{ secrets.GITHUB_TOKEN }}
```

#### Missing Dependencies

The action automatically installs required tools (jq, bc). No additional setup needed.

#### Score Threshold Issues

```yaml
# Adjust threshold for stricter requirements  
- uses: broadsage/scorecard-action@v1
  with:
    minimum_score_threshold: '8.5'  # Very strict
    fail_on_score: false  # Don't fail, just warn
```

### Debug Mode

```yaml
- uses: broadsage/scorecard-action@v1
  env:
    ACTIONS_STEP_DEBUG: true
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development & Release Process

This project uses **fully automated releases** with [semantic-release](https://semantic-release.gitbook.io/) and conventional commits.

**Automated Releases (Recommended):**

1. Push changes to `main` with [conventional commits](https://www.conventionalcommits.org/)
   - `feat:` → Minor release (v1.1.0)
   - `fix:` → Patch release (v1.0.1)
   - `feat!:` or `fix!:` → Major release (v2.0.0)
2. **Semantic-release workflow analyzes commits and creates releases automatically**
3. GitHub releases are created with changelog and version tags

**Manual Releases (When needed):**

```bash
# Test semantic-release locally (dry run)
npm run semantic-release -- --dry-run

# Force release (if needed)
npm run semantic-release -- --no-ci
```

**Testing Locally:**

```bash
# Install dependencies and test semantic-release configuration
npm ci
npm run semantic-release -- --dry-run
```

**The automated process:**

- 🤖 **Auto-detects** version bumps from conventional commits
- 🏷️ **Auto-creates** semantic version tags
- ✅ **Auto-validates** action.yml and examples
- 📝 **Auto-generates** changelog from commits  
- 🚀 **Auto-publishes** GitHub release with artifacts
- 🔄 **Auto-updates** major version tags (v1 → v1.2.3)

> **Why automated releases?** Following conventional commits enables zero-touch releases. The system is smart enough to determine appropriate version bumps and only releases when meaningful changes are detected.

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Projects

- [OpenSSF Scorecard](https://github.com/ossf/scorecard) - The underlying security analysis tool

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/broadsage/scorecard-action/issues)
- **Security**: [security@broadsage.com](mailto:security@broadsage.com)

---

Built with ❤️ by the Broadsage Security Team

Run OSSF Scorecard checks and output results in SARIF format
