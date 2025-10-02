# Changelog

All notable changes to this project will be documented in this file.
See [Conventional Commits](https://conventionalcommits.org) for commit guidelines.

## [unreleased]

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md for v2.3.3 - ([8040766](https://github.com/broadsage/scorecard-action/commit/80407661fc8a8582653e12ab80fe183e57cf18ba))


## [2.3.3](https://github.com/broadsage/scorecard-action/compare/v2.3.2..v2.3.3) - 2025-10-02

### ⛰️  Features

- Refactor release workflow using git-cliff repository pattern - ([7695c98](https://github.com/broadsage/scorecard-action/commit/7695c98af7485a4702dbaa04c402f52223245233))


## [2.3.2](https://github.com/broadsage/scorecard-action/compare/v2.3.1..v2.3.2) - 2025-10-02

### 🐛 Bug Fixes

- Use HEAD instead of non-existent tag in git-cliff range - ([e99f3a1](https://github.com/broadsage/scorecard-action/commit/e99f3a126755e5f55186089d2d30f31ca24e6115))


## [2.3.1](https://github.com/broadsage/scorecard-action/compare/v2.3.0..v2.3.1) - 2025-10-02

### 🐛 Bug Fixes

- Correct git-cliff args syntax and template engine compatibility - ([5e13407](https://github.com/broadsage/scorecard-action/commit/5e13407fa3c5980cb5120576a4adb24be73aac4d))


## [2.3.0](https://github.com/broadsage/scorecard-action/compare/v2.2.0..v2.3.0) - 2025-10-01

### 🐛 Bug Fixes

- Generate fresh release notes instead of reading existing changelog - ([fa83a52](https://github.com/broadsage/scorecard-action/commit/fa83a520e117e9f55b9bf5f8c0d6e3f9d20b2d5a))


## [2.2.0](https://github.com/broadsage/scorecard-action/compare/v2.0.0..v2.2.0) - 2025-10-01

### ⛰️  Features

- [**breaking**] Migrate to Git Cliff for modern changelog generation - ([ad0f423](https://github.com/broadsage/scorecard-action/commit/ad0f42356234e222edcf0cfb70c6b9ce5f5f10f4))

### 🐛 Bug Fixes

- Resolve git cliff command error in GitHub Actions - ([c3150f1](https://github.com/broadsage/scorecard-action/commit/c3150f18df664e2e3f43b93315a6259135b13396))


## [2.0.0](https://github.com/broadsage/scorecard-action/compare/v1.1.1..v2.0.0) - 2025-10-01

### ⛰️  Features

- Implement industry-standard semantic versioning and conventional commits - ([1420dbc](https://github.com/broadsage/scorecard-action/commit/1420dbcb900263d2b2f00a240ea07c02ffdf9ac4))


## [1.1.1](https://github.com/broadsage/scorecard-action/compare/v1.1.0..v1.1.1) - 2025-10-01

### 🚜 Refactor

- Comprehensive cleanup and optimization of release script - ([f7132f3](https://github.com/broadsage/scorecard-action/commit/f7132f34945681ea09e5d81e426a7198d8ecf6bd))


## [1.1.0](https://github.com/broadsage/scorecard-action/compare/v1.0.3..v1.1.0) - 2025-10-01

### ⛰️  Features

- Implement aggressive Dependabot strategy with enhanced auto-merge - ([aaca466](https://github.com/broadsage/scorecard-action/commit/aaca4669d664f2c8b2e8084db27b61f0f8b25538))
- Implement comprehensive metrics and analytics system - ([dc83915](https://github.com/broadsage/scorecard-action/commit/dc839153d99733abda92ae35fd545c0b13384a07))
- Implement enhanced dependency management with auto-merge system - ([85f7b58](https://github.com/broadsage/scorecard-action/commit/85f7b58e90f9231f815619c0cee2698d7fec2e76))
- Implement unified smart release workflow with manual trigger support - ([5acf0e6](https://github.com/broadsage/scorecard-action/commit/5acf0e6f1586e2a36add7d5ced91bba747fadb7a))

### 🐛 Bug Fixes

- Remove duplicate 'Release' prefix from release titles - ([2ad76d3](https://github.com/broadsage/scorecard-action/commit/2ad76d390166ec93ebf8351a6670abfc7d584389))
- Make release workflow more flexible and reliable - ([5e7a09d](https://github.com/broadsage/scorecard-action/commit/5e7a09d18ea2794bd05488558b819060f84df270))
- Enable Dependabot major version updates for actions - ([aac65af](https://github.com/broadsage/scorecard-action/commit/aac65af09566bbc89c42da32ca5bd31c7948f4d3))
- Resolve DORA metrics repository parsing issue - ([b8286a7](https://github.com/broadsage/scorecard-action/commit/b8286a79cd1490b2893006b978153ae9df4f1b6a))
- Resolve circular dependency in dependabot auto-merge workflow - ([8442ec9](https://github.com/broadsage/scorecard-action/commit/8442ec9ec92f27f0fce9e6f1d0ae9d06e3f20b8a))
- Remove invalid empty ignore array from Dependabot configuration - ([17852a4](https://github.com/broadsage/scorecard-action/commit/17852a4516af6c7095577505354af817f3f66229))
- Replace infinite CI check loop with appropriate action validation - ([6e0b1fa](https://github.com/broadsage/scorecard-action/commit/6e0b1fa9785b06a8affc4161722e49b165175a0a))
- Resolve GitHub Actions context access warnings in DORA metrics workflow - ([5553924](https://github.com/broadsage/scorecard-action/commit/5553924b071a07b8e9e1b5954746e9b12750934f))
- Resolve heredoc syntax error in release workflow - ([a8e839a](https://github.com/broadsage/scorecard-action/commit/a8e839a363007835908049e7d35e501946d3953a))
- Enhance GitHub workflow permissions for automated releases - ([b7b4035](https://github.com/broadsage/scorecard-action/commit/b7b40359c43343307f464ea3b19f54f7d8998429))

### 🚜 Refactor

- Simplify to industry-standard scorecard action structure - ([68d2a1d](https://github.com/broadsage/scorecard-action/commit/68d2a1d5fd72da8fe6491382cdde43e24d286aad))
- Restructure Dependabot configuration with conservative approach - ([33ffcf6](https://github.com/broadsage/scorecard-action/commit/33ffcf67315d4341ee8075df2aa5069bd7941fb6))
- Simplify label configuration to minimal requirements - ([166064b](https://github.com/broadsage/scorecard-action/commit/166064b43547052c187947fb00f9a86c2139110d))
- Adopt docker-template's proven auto-merge workflow approach - ([08443f0](https://github.com/broadsage/scorecard-action/commit/08443f041f6b5c01891fd050ba6263879f69353a))
- Simplify workflow architecture and standardize naming - ([2730f50](https://github.com/broadsage/scorecard-action/commit/2730f507bd67ccd492bd5888ec1d8409af70ff55))
- Migrate release automation from bash to Python - ([aa6d573](https://github.com/broadsage/scorecard-action/commit/aa6d573ce958a503b2323b34a893d4216e7d3cd8))


## [1.0.3](https://github.com/broadsage/scorecard-action/compare/v1.0.1..v1.0.3) - 2025-09-26

### 🐛 Bug Fixes

- Resolve unbound variable error in release utilities - ([f16f446](https://github.com/broadsage/scorecard-action/commit/f16f446fccb2f319c2aa8c6104db791fd35f25e8))


## [1.0.1](https://github.com/broadsage/scorecard-action/compare/v1.0.0..v1.0.1) - 2025-09-26

### ⛰️  Features

- Implement clean upstream release automation with reusable utilities - ([d984aee](https://github.com/broadsage/scorecard-action/commit/d984aee64316072a5b66ccb1362334593d8d4de5))
- Add Dependabot for automated dependency updates - ([041b960](https://github.com/broadsage/scorecard-action/commit/041b9602c85b7dc3564ca114d31e960c92426b56))

### 🚜 Refactor

- Simplify workflows with Dependabot automation - ([e04734f](https://github.com/broadsage/scorecard-action/commit/e04734fcb6cc39228855dc4d1110d09ff2dbe9f8))


## [1.0.0] - 2025-09-26

### ⛰️  Features

- OpenSSF Scorecard Workflow Enhancement - ([fd42f53](https://github.com/broadsage/scorecard-action/commit/fd42f53b84321243532ed685dff08d4736374e3a))


<!-- generated by git-cliff -->
