<!-- Context: standards/releases | Priority: high | Version: 1.0 | Updated: 2026-03-01 -->

# Versioning and Release Standards (Home Assistant Custom Integration)

## Quick Reference

**Golden Rule**: Use Semantic Versioning (SemVer) with a `v` prefix for tags. HACS relies on this format to detect updates.

**Tag Format**: `vMAJOR.MINOR.PATCH` (e.g., `v1.2.0`)
**Release Title**: Same as the tag, or Tag + Short Description (e.g., `v1.2.0 - Fan Support`)

---

## 1. Semantic Versioning (SemVer)

All releases must follow Semantic Versioning:

- **MAJOR** (`v2.0.0`): Breaking changes.
  - Examples: Changing entity IDs, removing configuration options, dropping support for older Home Assistant versions, changing the data structure in the Config Entry.
- **MINOR** (`v1.1.0`): New features (backwards-compatible).
  - Examples: Adding a new sensor type, adding a new service action, supporting a new device model.
- **PATCH** (`v1.0.1`): Bug fixes (backwards-compatible).
  - Examples: Fixing a typo, fixing a crash on a specific firmware, updating a dependency.

## 2. Git Tags

- **Always use the `v` prefix**: `v1.0.0`, `v2.1.3`.
- **Pre-releases**: Append a hyphen and an identifier for betas or release candidates: `v1.0.0-beta.1`, `v2.0.0-rc.2`. HACS supports pre-releases if the user enables beta versions in the HACS UI.

## 3. GitHub Releases

Every tag must have an associated GitHub Release.

### Release Title
The title should be the tag name. For major or significant minor releases, you can append a short, catchy description.
- Good: `v1.2.0`
- Good: `v2.0.0 - The Performance Update`
- Bad: `Version 1.2` (Missing `v` and patch number)
- Bad: `Update` (Not descriptive)

### Release Notes Structure
Release notes should be automatically or manually generated based on merged Pull Requests or commits. Group changes logically:

```markdown
## What's Changed

### 🚀 Features
* Add support for Fan RPM sensors (#12)
* Add custom service to reload data (#15)

### 🐛 Bug Fixes
* Fix memory calculation for ADM 4.0+ (#18)
* Handle timeout gracefully when NAS is offline (#19)

### ⚠️ Breaking Changes
* **Entity ID Change**: The CPU temperature sensor ID changed from `sensor.cpu_temp` to `sensor.nas_cpu_temperature`. You may need to update your dashboards. (#22)

### 📚 Documentation
* Update README with memory calculation explanation (#25)

### ⬆️ Dependencies
* Bump pysnmp-lextudio from 6.1.3 to 6.1.4 (#28)

**Full Changelog**: https://github.com/NdR91/ha-assustor-nas/compare/v1.1.0...v1.2.0
```

## 4. HACS Specifics

- HACS reads the GitHub Releases of the repository.
- HACS strips the `v` prefix internally, so `v1.2.0` becomes version `1.2.0` in the Home Assistant UI.
- If you publish a release marked as "Pre-release" on GitHub, HACS will only show it to users who have toggled "Show beta versions" for your integration.
- **Never** change the `version` key in `manifest.json` manually for HACS integrations. HACS ignores the `manifest.json` version and uses the GitHub Release tag instead. (However, keeping it updated for consistency is a good practice).

## Best Practices

✅ Always write clear, user-facing release notes.
✅ Highlight Breaking Changes prominently at the top of the release notes.
✅ Use Conventional Commits (`feat:`, `fix:`, `docs:`, `BREAKING CHANGE:`) to make generating release notes easier.
✅ Test the integration locally before tagging a release.