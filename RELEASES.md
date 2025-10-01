# Release Automation with Git Cliff

This repository uses [Git Cliff](https://git-cliff.org/) for automated changelog generation and release management.

## 🚀 Features

- **Modern Performance**: Rust-based implementation for lightning-fast changelog generation
- **Conventional Commits**: Full support for conventional commit specifications
- **Semantic Versioning**: Automatic version bumping based on commit types
- **Professional Output**: Industry-standard changelog formatting with emojis and sections
- **GitHub Integration**: Native GitHub Actions support via `orhun/git-cliff-action@v4`

## 📋 Configuration

The release automation is configured through:

- **`cliff.toml`**: Git Cliff configuration with custom templates
- **`.github/workflows/release.yml`**: GitHub Actions workflow for automated releases

## 🔄 Release Process

### Automatic Releases
Releases are automatically triggered when:
- Dependabot PRs are merged
- PRs with `feat`, `fix`, or `chore` in the title are merged
- PRs labeled with `release` are merged

### Manual Releases
Use GitHub Actions workflow dispatch:
```yaml
workflow_dispatch:
  inputs:
    version_type: 'patch' | 'minor' | 'major'
    release_notes: 'Optional custom notes'
    dry_run: true/false
```

### Version Bumping
- **Patch**: `fix:` commits, general updates
- **Minor**: `feat:` commits, new features  
- **Major**: `feat!:` or `fix!:` commits (breaking changes)

## 📊 Output Format

Generated changelogs include:
- **Breaking Changes**: `💥` Critical updates requiring attention
- **New Features**: `✨` Feature additions and enhancements
- **Bug Fixes**: `🐛` Problem resolutions and patches
- **Performance**: `⚡` Performance improvements
- **Documentation**: `📚` Documentation updates
- **Maintenance**: `🔧` Refactoring, chores, CI, build, style, tests
- **Statistics**: `📊` Release metrics and commit counts

## 🚀 Usage

```yaml
# Use the latest version in your workflows
uses: broadsage/scorecard-action@v1

# Or pin to a specific version
uses: broadsage/scorecard-action@v1.0.3
```

## 📚 Documentation

- [Git Cliff Documentation](https://git-cliff.org/docs/)
- [Conventional Commits](https://conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)

---

**Migration Date**: October 1, 2025  
**Status**: ✅ Production Ready