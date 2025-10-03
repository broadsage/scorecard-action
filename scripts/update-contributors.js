#!/usr/bin/env node
/**
 * Update Contributors Script
 * Automatically updates CONTRIBUTORS.md with GitHub contributors data
 * Called during semantic-release process
 */

const fs = require('fs');
const https = require('https');
const path = require('path');

const REPO_OWNER = 'broadsage';
const REPO_NAME = 'scorecard-action';
const CONTRIBUTORS_FILE = path.join(__dirname, '../CONTRIBUTORS.md');

/**
 * Make GitHub API request
 */
function makeGitHubRequest(path, authToken = null) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.github.com',
      path: path,
      method: 'GET',
      headers: {
        'User-Agent': 'scorecard-action-release-script',
        'Accept': 'application/vnd.github.v3+json'
      }
    };

    // Add authorization if token is available
    if (authToken) {
      options.headers['Authorization'] = `token ${authToken}`;
    }

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      res.on('end', () => {
        try {
          const result = JSON.parse(data);
          resolve({ data: result, status: res.statusCode });
        } catch (error) {
          reject(error);
        }
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    req.end();
  });
}

/**
 * Check repository owner type and get owner info
 */
async function getRepositoryOwnerInfo(authToken = null) {
  try {
    const response = await makeGitHubRequest(`/users/${REPO_OWNER}`, authToken);
    return {
      type: response.data.type, // 'User' or 'Organization'
      login: response.data.login,
      isOrganization: response.data.type === 'Organization'
    };
  } catch (error) {
    console.warn(`⚠️ Could not fetch owner info for ${REPO_OWNER}:`, error.message);
    return { type: 'Unknown', login: REPO_OWNER, isOrganization: false };
  }
}

/**
 * Check if user is organization member or owner (only for organization repos)
 */
async function checkOrganizationMembership(username, ownerInfo, authToken = null) {
  if (!ownerInfo.isOrganization) {
    return { isMember: false, role: null }; // Not an organization, so no org membership
  }
  
  try {
    // First try public membership
    const response = await makeGitHubRequest(`/orgs/${REPO_OWNER}/members/${username}`, authToken);
    if (response.status === 204) {
      // Check if they're an owner by checking their role
      try {
        const membershipResponse = await makeGitHubRequest(`/orgs/${REPO_OWNER}/memberships/${username}`, authToken);
        const role = membershipResponse.data.role; // 'admin' or 'member'
        return { isMember: true, role: role };
      } catch {
        return { isMember: true, role: 'member' }; // Default to member if we can't get role
      }
    }
  } catch (error) {
    // If we get 404, user might have private membership or not be a member
    // Try checking repository permissions to infer organization relationship
    try {
      const repoResponse = await makeGitHubRequest(`/repos/${REPO_OWNER}/${REPO_NAME}/collaborators/${username}/permission`, authToken);
      const permission = repoResponse.data.permission;
      
      if (permission === 'admin') {
        // Admin access likely means they're org owner with private membership
        return { isMember: true, role: 'admin' };
      }
    } catch {
      // No special permissions found
    }
  }
  
  return { isMember: false, role: null };
}

/**
 * Check if user is repository collaborator
 */
async function checkCollaboratorStatus(username, authToken = null) {
  try {
    const response = await makeGitHubRequest(`/repos/${REPO_OWNER}/${REPO_NAME}/collaborators/${username}`, authToken);
    return response.status === 204; // 204 means user is a collaborator
  } catch (error) {
    return false;
  }
}

/**
 * Check if user is the repository owner
 */
function isRepositoryOwner(username, ownerInfo) {
  return username.toLowerCase() === ownerInfo.login.toLowerCase();
}

/**
 * Fetch contributors from GitHub API with membership info
 */
async function fetchContributors() {
  try {
    const authToken = process.env.GITHUB_TOKEN;
    
    // First, get repository owner information
    const ownerInfo = await getRepositoryOwnerInfo(authToken);
    console.log(`📋 Repository owned by: ${ownerInfo.login} (${ownerInfo.type})`);
    
    const response = await makeGitHubRequest(`/repos/${REPO_OWNER}/${REPO_NAME}/contributors`, authToken);
    const contributors = response.data;
    
    console.log(`🔍 Checking membership status for ${contributors.length} contributors...`);
    
    // Enhance each contributor with membership info
    for (const contributor of contributors) {
      if (contributor.type === 'User') {
        const isOwner = isRepositoryOwner(contributor.login, ownerInfo);
        const orgMembership = await checkOrganizationMembership(contributor.login, ownerInfo, authToken);
        const isCollaborator = await checkCollaboratorStatus(contributor.login, authToken);
        
        contributor.isOwner = isOwner;
        contributor.isOrgMember = orgMembership.isMember;
        contributor.orgRole = orgMembership.role;
        contributor.isCollaborator = isCollaborator;
        contributor.membershipType = getMembershipType(isOwner, orgMembership.isMember, orgMembership.role, isCollaborator, ownerInfo.isOrganization);
        
        console.log(`  ${contributor.login}: owner=${isOwner}, orgMember=${orgMembership.isMember}, orgRole=${orgMembership.role}, collaborator=${isCollaborator} → ${contributor.membershipType}`);
      }
    }
    
    return contributors;
  } catch (error) {
    console.error('❌ Error fetching contributors:', error.message);
    throw error;
  }
}

/**
 * Determine membership type
 */
function getMembershipType(isOwner, isOrgMember, orgRole, isCollaborator, isOrgRepo) {
  if (isOwner) {
    return isOrgRepo ? 'Organization Owner' : 'Repository Owner';
  } else if (isOrgMember) {
    if (orgRole === 'admin') {
      return 'Organization Owner';
    } else {
      return 'Organization Member';
    }
  } else if (isCollaborator) {
    return 'External Collaborator';
  } else {
    return 'External Contributor';
  }
}

/**
 * Update CONTRIBUTORS.md file
 */
function updateContributorsFile(contributors) {
  try {
    let content = fs.readFileSync(CONTRIBUTORS_FILE, 'utf8');
    
    // Generate beautiful contributors section
    const contributorsTable = generateContributorsTable(contributors);

    // Update content between markers
    const startMarker = '<!-- CONTRIBUTORS_START -->';
    const endMarker = '<!-- CONTRIBUTORS_END -->';
    
    const beforeMarker = content.substring(0, content.indexOf(startMarker) + startMarker.length);
    const afterMarker = content.substring(content.indexOf(endMarker));
    
    const updatedContent = `${beforeMarker}\n${contributorsTable}\n${afterMarker}`;
    
    fs.writeFileSync(CONTRIBUTORS_FILE, updatedContent, 'utf8');
    console.log(`✅ Updated CONTRIBUTORS.md with ${contributors.length} contributors`);
    
    return true;
  } catch (error) {
    console.error('❌ Error updating CONTRIBUTORS.md:', error.message);
    return false;
  }
}

/**
 * Generate contributor statistics
 */
function generateContributorStats(contributors) {
  const totalContributors = contributors.length;
  const owners = contributors.filter(c => c.membershipType === 'Repository Owner' || c.membershipType === 'Organization Owner').length;
  const orgMembers = contributors.filter(c => c.membershipType === 'Organization Member').length;
  const externalCollaborators = contributors.filter(c => c.membershipType === 'External Collaborator').length;
  const externalContributors = contributors.filter(c => c.membershipType === 'External Contributor').length;
  const totalCommits = contributors.reduce((sum, c) => sum + c.contributions, 0);

  let stats = `### 📊 Contributor Statistics

- **Total Contributors:** ${totalContributors}`;

  if (owners > 0) {
    stats += `\n- **Owners:** ${owners} 👑`;
  }
  if (orgMembers > 0) {
    stats += `\n- **Organization Members:** ${orgMembers} 🏢`;
  }
  if (externalCollaborators > 0) {
    stats += `\n- **External Collaborators:** ${externalCollaborators} 🤝`;
  }
  if (externalContributors > 0) {
    stats += `\n- **External Contributors:** ${externalContributors} 🌍`;
  }
  
  stats += `\n- **Total Commits:** ${totalCommits}

### 👥 Contributors`;

  return stats;
}

/**
 * Generate beautiful contributors table
 */
function generateContributorsTable(contributors) {
  const userContributors = contributors.filter(c => c.type === 'User');
  
  if (userContributors.length === 0) {
    return '\n*No contributors found yet. Be the first to contribute!*\n';
  }

  // Sort by contributions (descending)
  userContributors.sort((a, b) => b.contributions - a.contributions);

  // Generate statistics
  const stats = generateContributorStats(userContributors);
  
  let table = `\n${stats}\n\n<table>\n<tr>\n`;
  
  // Generate table rows (4 contributors per row)
  userContributors.forEach((contributor, index) => {
    if (index > 0 && index % 4 === 0) {
      table += '</tr>\n<tr>\n';
    }
    
    const contributionBadge = getContributionBadge(contributor.contributions, contributor.membershipType);
    const avatarSize = 100;
    
    table += `  <td align="center" valign="top" width="25%">
    <a href="${contributor.html_url}">
      <img src="${contributor.avatar_url}" width="${avatarSize}" height="${avatarSize}" alt="${contributor.login}"/><br />
      <sub><b>${contributor.login}</b></sub>
    </a><br />
    <sub>${contributionBadge}</sub><br />
    <sub>${contributor.contributions} commits</sub>
  </td>\n`;
  });
  
  // Close the final row
  table += '</tr>\n</table>\n';
  
  return table;
}

/**
 * Get membership badge based on status
 */
function getMembershipBadge(membershipType) {
  switch (membershipType) {
    case 'Repository Owner':
      return '👑 Repository Owner';
    case 'Organization Owner':
      return '👑 Organization Owner';
    case 'Organization Member':
      return '🏢 Organization Member';
    case 'External Collaborator':
      return '🤝 External Collaborator';
    case 'External Contributor':
      return '🌍 External Contributor';
    default:
      return '👤 Contributor';
  }
}

/**
 * Get contribution badge based on commit count and membership
 */
function getContributionBadge(commits, membershipType = null) {
  let badge = '';
  
  // Determine contribution level
  if (commits >= 100) badge = '🏆 Core Maintainer';
  else if (commits >= 50) badge = '⭐ Major Contributor';
  else if (commits >= 20) badge = '🌟 Active Contributor';
  else if (commits >= 10) badge = '✨ Regular Contributor';
  else if (commits >= 5) badge = '🚀 Contributor';
  else badge = '� New Contributor';
  
  // Add membership context for non-org members
  if (membershipType === 'External Contributor') {
    badge = badge.replace('Contributor', 'Community Contributor');
  }
  
  return badge;
}

/**
 * Main execution
 */
async function main() {
  try {
    console.log('🔄 Fetching contributors from GitHub API...');
    const contributors = await fetchContributors();
    
    console.log(`📋 Found ${contributors.length} contributors`);
    
    const success = updateContributorsFile(contributors);
    
    if (success) {
      console.log('✅ Contributors file updated successfully');
      process.exit(0);
    } else {
      console.log('❌ Failed to update contributors file');
      process.exit(1);
    }
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

// Run only if called directly
if (require.main === module) {
  main();
}

module.exports = { fetchContributors, updateContributorsFile };