#!/bin/bash
# Release utility functions for automatic dependency updates
# This script contains reusable functions for processing Dependabot PRs and creating releases

set -euo pipefail

# Extract dependency information from Dependabot PR title
# Usage: extract_dependency_info "Bump ossf/scorecard-action from v2.4.1 to v2.4.2"
extract_dependency_info() {
    local pr_title="$1"
    
    # Extract action name (e.g., "ossf/scorecard-action")
    local action_name
    action_name=$(echo "$pr_title" | grep -oE '[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+' | head -1 || echo "")
    
    # Extract versions (from/to pattern in Dependabot PRs)
    local versions=()
    readarray -t versions < <(echo "$pr_title" | grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+' || true)
    
    local old_version="${versions[0]:-unknown}"
    local new_version="${versions[1]:-${versions[0]:-latest}}"
    
    # Validate extraction
    if [[ -z "$action_name" ]]; then
        echo "⚠️ Warning: Could not extract action name from: $pr_title" >&2
        action_name="unknown-action"
    fi
    
    echo "action_name=$action_name"
    echo "old_version=$old_version"
    echo "new_version=$new_version"
    
    echo "📦 Extracted: $action_name $old_version → $new_version" >&2
}

# Fetch release notes from upstream GitHub repository
# Usage: fetch_upstream_notes "ossf/scorecard-action" "v2.4.2" "v2.4.1"
fetch_upstream_notes() {
    local action_name="$1"
    local new_version="$2" 
    local old_version="${3:-unknown}"
    
    echo "📥 Fetching upstream notes for $action_name $new_version" >&2
    
    # Try to fetch upstream release notes via GitHub API
    local notes
    if notes=$(gh api "repos/$action_name/releases/tags/$new_version" --jq '.body' 2>/dev/null) && [[ -n "$notes" && "$notes" != "null" ]]; then
        echo "✅ Successfully fetched upstream release notes" >&2
        # Limit length and clean up formatting
        echo "$notes" | head -50
    else
        echo "⚠️ Could not fetch upstream notes, generating fallback content" >&2
        generate_fallback_notes "$action_name" "$new_version" "$old_version"
    fi
}

# Generate fallback release notes when upstream notes are unavailable
# Usage: generate_fallback_notes "ossf/scorecard-action" "v2.4.2" "v2.4.1"
generate_fallback_notes() {
    local action_name="$1"
    local new_version="$2"
    local old_version="$3"
    
    cat << EOF
## What's Changed

This update includes the latest improvements, bug fixes, and security updates from the upstream project.

### 🔗 For Detailed Information

- [📋 Full Release Notes](https://github.com/$action_name/releases/tag/$new_version)
- [📊 Compare Changes](https://github.com/$action_name/compare/$old_version...$new_version)
- [🏠 Project Repository](https://github.com/$action_name)

### 📦 Version Update

Updated from \`$old_version\` to \`$new_version\` with latest upstream improvements.
EOF
}

# Get the next semantic version for our action
# Usage: get_next_version
get_next_version() {
    local current_version
    current_version=$(git tag -l "v*" --sort=-version:refname | head -1 || echo "")
    
    if [[ -z "$current_version" ]]; then
        echo "v1.0.1"
    else
        # Increment patch version
        echo "$current_version" | awk -F. -v OFS=. '{$NF++; print}'
    fi
}

# Generate comprehensive release notes
# Usage: generate_release_notes "v1.2.3" "ossf/scorecard-action" "v2.4.1" "v2.4.2" "upstream content"
generate_release_notes() {
    local our_version="$1"
    local action_name="$2"
    local old_version="$3"
    local new_version="$4"
    local upstream_content="$5"
    
    # Determine action category for better messaging
    local category_icon="📦"
    local category_name="Dependency"
    
    case "$action_name" in
        "ossf/scorecard-action")
            category_icon="🔒"
            category_name="Security Analysis"
            ;;
        "github/codeql-action"*)
            category_icon="🛡️"
            category_name="Security Scanning"
            ;;
        "actions/checkout"|"actions/upload-artifact"|"actions/cache")
            category_icon="🏗️"
            category_name="Infrastructure"
            ;;
        "slackapi/slack-github-action")
            category_icon="🔗"
            category_name="Integration"
            ;;
    esac
    
    cat << EOF
# $category_icon $category_name Update $our_version

**Updated**: \`$action_name\` from \`$old_version\` → \`$new_version\`

## 📋 Upstream Changes

$upstream_content

## 🚀 Usage

Update your workflows to use the latest version:

\`\`\`yaml
uses: broadsage/scorecard-action@v1
\`\`\`

## 🔗 Links

- [📋 Full Upstream Release](https://github.com/$action_name/releases/tag/$new_version)
- [📊 Compare Changes](https://github.com/$action_name/compare/$old_version...$new_version)
- [🏠 This Action's Repository](https://github.com/broadsage/scorecard-action)

## ✅ Compatibility

- All existing workflows continue to work unchanged
- No breaking changes to inputs/outputs  
- Enhanced functionality from latest upstream updates

---
*This release was automatically created from upstream dependency updates*
EOF
}

# Create and publish a GitHub release
# Usage: create_and_publish_release "v1.2.3" "ossf/scorecard-action"
create_and_publish_release() {
    local version="$1"
    local action_name="$2"
    
    echo "🚀 Creating release $version" >&2
    
    # Configure git for automated commits
    git config user.name "github-actions[bot]"
    git config user.email "github-actions[bot]@users.noreply.github.com"
    
    # Create and push version tag
    git tag -a "$version" -m "chore: update $action_name dependency"
    git push origin "$version"
    
    # Update major version tag for GitHub Actions best practice
    local major_version
    major_version=$(echo "$version" | cut -d. -f1)
    git tag -f "$major_version" "$version"
    git push origin "$major_version" --force
    
    # Create GitHub release
    if [[ -f "release_notes.md" ]]; then
        gh release create "$version" \
            --title "$category_icon Dependency Update $version" \
            --notes-file release_notes.md \
            --latest
    else
        echo "❌ Error: release_notes.md not found" >&2
        return 1
    fi
    
    echo "✅ Successfully released $version" >&2
}

# Validate required environment and tools
# Usage: validate_environment  
validate_environment() {
    local missing_tools=()
    
    # Check required tools
    command -v git >/dev/null 2>&1 || missing_tools+=("git")
    command -v gh >/dev/null 2>&1 || missing_tools+=("gh")
    command -v awk >/dev/null 2>&1 || missing_tools+=("awk")
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        echo "❌ Error: Missing required tools: ${missing_tools[*]}" >&2
        return 1
    fi
    
    # Check GitHub token
    if [[ -z "${GITHUB_TOKEN:-}" && -z "${GH_TOKEN:-}" ]]; then
        echo "❌ Error: GITHUB_TOKEN or GH_TOKEN environment variable is required" >&2
        return 1
    fi
    
    echo "✅ Environment validation passed" >&2
}

# Main function to orchestrate the entire release process
# Usage: main "PR title from Dependabot"
main() {
    local pr_title="$1"
    
    echo "🚀 Starting automated release process" >&2
    
    # Validate environment
    validate_environment
    
    # Extract dependency information
    local dep_info
    dep_info=$(extract_dependency_info "$pr_title")
    
    # Parse the extracted information
    local action_name old_version new_version
    action_name=$(echo "$dep_info" | grep "^action_name=" | cut -d= -f2)
    old_version=$(echo "$dep_info" | grep "^old_version=" | cut -d= -f2) 
    new_version=$(echo "$dep_info" | grep "^new_version=" | cut -d= -f2)
    
    # Fetch upstream release notes
    local upstream_content
    upstream_content=$(fetch_upstream_notes "$action_name" "$new_version" "$old_version")
    
    # Get our next version
    local our_new_version
    our_new_version=$(get_next_version)
    
    echo "📦 Our new version: $our_new_version" >&2
    
    # Generate release notes
    generate_release_notes "$our_new_version" "$action_name" "$old_version" "$new_version" "$upstream_content" > release_notes.md
    
    # Create and publish the release
    create_and_publish_release "$our_new_version" "$action_name"
    
    echo "🎉 Release process completed successfully!" >&2
    echo "📋 Release: https://github.com/broadsage/scorecard-action/releases/tag/$our_new_version" >&2
}

# Export functions for use in other scripts
export -f extract_dependency_info
export -f fetch_upstream_notes
export -f generate_fallback_notes
export -f get_next_version
export -f generate_release_notes
export -f create_and_publish_release
export -f validate_environment
export -f main