# Contributing

Thanks for your interest in contributing! This action enhances OpenSSF Scorecard with workflow features like notifications, thresholds, and reporting.

## 🐛 Issues & Features

- **Bug reports**: Use [GitHub Issues](https://github.com/broadsage/scorecard-action/issues)
- **Feature requests**: Describe the use case and include examples
- **Questions**: Check the [README](README.md) first

## 🔧 Development

### Quick Start

1. Fork and clone the repo
2. Make your changes to `action.yml` or examples
3. Test with a real repository
4. Submit a pull request

### Testing Locally

```bash
# Validate YAML syntax
yamllint action.yml examples/*.yml

# Test action (requires act or real repo)
act -j test-action
```

## 📋 Guidelines

### Action Development

- **Inputs/Outputs**: Follow GitHub Actions conventions
- **Steps**: Use meaningful names and descriptions
- **Error Handling**: Include proper validation and fallbacks
- **Documentation**: Update README for any new features

### Examples

- **Working Examples**: All examples must actually work
- **Real Features**: Only use implemented inputs/outputs
- **Clear Use Cases**: Show practical scenarios

### Release Process

This project uses automated releases with semantic-release:

- **Commits**: Use [Conventional Commits](https://www.conventionalcommits.org/) format
- **Versioning**: Follow [Semantic Versioning](https://semver.org/) (major.minor.patch)
- **Releases**: Created automatically when commits are pushed to main
- **Changelog**: Generated automatically from conventional commits

**Creating a Release:**

1. Ensure all changes are merged to `main`
2. Push commits using conventional commit format (feat:, fix:, etc.)
3. Semantic-release workflow runs automatically
4. Release appears on GitHub with generated changelog and version tags

## 🎯 Focus Areas

This action enhances OpenSSF Scorecard by:

- **Score Processing**: Extract numerical scores from results
- **Notifications**: Slack and webhook integrations  
- **Workflow Integration**: GitHub Actions outputs
- **Reporting**: Enhanced summaries and formatting

## 📞 Questions?

- **Issues**: [GitHub Issues](https://github.com/broadsage/scorecard-action/issues)
- **Security**: [security@broadsage.com](mailto:security@broadsage.com)
