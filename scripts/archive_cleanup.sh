#!/bin/bash
# archive_cleanup.sh - Safe archival instead of deletion
# Team Alpha - Infrastructure Sprint 1

set -euo pipefail

ARCHIVE_DATE=$(date +%Y-%m-%d_%H%M%S)
ARCHIVE_DIR="archive/${ARCHIVE_DATE}_repository_cleanup"

echo "🚀 Starting repository cleanup with archival strategy..."
echo "📁 Archive directory: ${ARCHIVE_DIR}"

# Create archive directory structure
mkdir -p "${ARCHIVE_DIR}"/{sprint_docs,debug_reports,legacy_docs,duplicate_files,team_assignments,old_releases}

# Archive function - safe move instead of delete
archive_file() {
    local source_file="$1"
    local archive_category="$2"
    local reason="$3"
    
    if [[ -f "$source_file" ]]; then
        echo "📦 Archiving: $source_file -> ${ARCHIVE_DIR}/${archive_category}/"
        mv "$source_file" "${ARCHIVE_DIR}/${archive_category}/"
        
        # Log the archival
        echo "$(date): $source_file -> $reason" >> "${ARCHIVE_DIR}/ARCHIVE_LOG.txt"
    elif [[ -d "$source_file" ]]; then
        echo "📦 Archiving directory: $source_file -> ${ARCHIVE_DIR}/${archive_category}/"
        mv "$source_file" "${ARCHIVE_DIR}/${archive_category}/"
        
        # Log the archival
        echo "$(date): $source_file (directory) -> $reason" >> "${ARCHIVE_DIR}/ARCHIVE_LOG.txt"
    else
        echo "⚠️  Warning: $source_file not found, skipping..."
    fi
}

echo "📋 Starting archival process..."

# Archive sprint-related documentation
echo "🏃 Archiving sprint documentation..."
archive_file "SPRINT7_TEAM_KICKOFF.md" "sprint_docs" "Sprint completion - moved to archive"
archive_file "SPRINT_COMPLETION_SUMMARY.md" "sprint_docs" "Sprint completion - moved to archive"
archive_file "SPRINT_EXECUTION_LOG.md" "sprint_docs" "Sprint completion - moved to archive"

# Archive debug reports
echo "🐛 Archiving debug reports..."
archive_file "debug-report-20250901-215108.txt" "debug_reports" "Debug session completed"
archive_file "debug-report-20250901-215149.txt" "debug_reports" "Debug session completed"

# Archive duplicate/legacy documentation
echo "📚 Archiving legacy documentation..."
archive_file "COMPREHENSIVE_TESTING_GUIDE.md" "legacy_docs" "Superseded by COMPREHENSIVE_TESTING_GUIDE_FINAL.md"
archive_file "COMPREHENSIVE_USER_GUIDE_WITH_VISUALS.md" "legacy_docs" "Superseded by VISUAL_USER_GUIDE_IMPORT_FEATURE.md"

# Archive team assignment files
echo "👥 Archiving team assignments..."
archive_file "TEAM_ALPHA_INFRASTRUCTURE_TASKS.md" "team_assignments" "Team tasks completed - moved to archive"
archive_file "TEAM_BETA_ARCHITECTURE_TASKS.md" "team_assignments" "Team tasks completed - moved to archive"
archive_file "TEAM_DELTA_SECURITY_TASKS.md" "team_assignments" "Team tasks completed - moved to archive"
archive_file "TEAM_EPSILON_TESTING_TASKS.md" "team_assignments" "Team tasks completed - moved to archive"
archive_file "TEAM_GAMMA_DATABASE_TASKS.md" "team_assignments" "Team tasks completed - moved to archive"
archive_file "TEAM_ZETA_FRONTEND_TASKS.md" "team_assignments" "Team tasks completed - moved to archive"

# Archive old release notes
echo "📦 Archiving old releases..."
archive_file "RELEASE_NOTES_v20250902_051242.md" "old_releases" "Release notes archived - current version maintained"

# Archive comprehensive analysis files that are superseded
echo "📊 Archiving superseded analysis files..."
archive_file "COMPREHENSIVE_IMPORT_ANALYSIS_SPRINT_PLAN.md" "legacy_docs" "Superseded by current implementation"
archive_file "COMPREHENSIVE_SECURITY_ANALYSIS_REPORT.md" "legacy_docs" "Superseded by current implementation"
archive_file "COMPREHENSIVE_SPRINT_PLAN.md" "legacy_docs" "Superseded by current implementation"
archive_file "COMPREHENSIVE_TESTING_GUIDE_FINAL.md" "legacy_docs" "Superseded by current implementation"

# Archive old deployment and feature guides
echo "🚀 Archiving old deployment guides..."
archive_file "FEATURE_DEPLOYMENT_GUIDE.md" "legacy_docs" "Superseded by current implementation"
archive_file "IMPORT_FEATURE_EXECUTIVE_SUMMARY.md" "legacy_docs" "Superseded by current implementation"
archive_file "IMPORT_FEATURE_IMPLEMENTATION_ROADMAP.md" "legacy_docs" "Superseded by current implementation"
archive_file "IMPORT_FEATURE_TEAM_ASSIGNMENTS.md" "legacy_docs" "Superseded by current implementation"
archive_file "IMPORT_FEATURE_TECHNICAL_ARCHITECTURE.md" "legacy_docs" "Superseded by current implementation"
archive_file "IMPORT_WORKFLOW_VISUAL_GUIDE.md" "legacy_docs" "Superseded by current implementation"

# Archive old theme and sprint documentation
echo "🎨 Archiving theme documentation..."
archive_file "THEME_IMPLEMENTATION_EXECUTIVE_SUMMARY.md" "legacy_docs" "Superseded by current implementation"
archive_file "THEME_SPRINT_TIMELINE.md" "legacy_docs" "Superseded by current implementation"
archive_file "CUSTOM_THEME_SPRINT_PLAN.md" "legacy_docs" "Superseded by current implementation"

# Archive old completion reports
echo "✅ Archiving completion reports..."
archive_file "ULTIMATE_COMPLETION_REPORT.md" "legacy_docs" "Superseded by current implementation"
archive_file "COMPLETE_EXECUTION_REPORT.md" "legacy_docs" "Superseded by current implementation"
archive_file "FINAL_DEPLOYMENT_READY_STATUS.md" "legacy_docs" "Superseded by current implementation"
archive_file "FINAL_RELEASE_SUMMARY_v20250902_051242.md" "old_releases" "Release summary archived"
archive_file "FINAL_SPRINT_SUMMARY.md" "legacy_docs" "Superseded by current implementation"
archive_file "DEPLOYMENT_SUMMARY.md" "legacy_docs" "Superseded by current implementation"
archive_file "DEPLOYMENT_VALIDATION.md" "legacy_docs" "Superseded by current implementation"
archive_file "DOCUMENTATION_CODEBASE_REVIEW.md" "legacy_docs" "Superseded by current implementation"
archive_file "IMPLEMENTATION_SUMMARY.md" "legacy_docs" "Superseded by current implementation"
archive_file "GITHUB_ISSUES_CREATED.md" "legacy_docs" "Superseded by current implementation"

# Archive old analysis files
echo "🔍 Archiving old analysis files..."
archive_file "WEBAPP_CRITICAL_ANALYSIS.md" "legacy_docs" "Superseded by current implementation"
archive_file "IMPORT_ANALYSIS_FEATURE_REQUIREMENTS.md" "legacy_docs" "Superseded by current implementation"
archive_file "WEB_GUI_INTEGRATION.md" "legacy_docs" "Superseded by current implementation"

# Archive old security documentation
echo "🔒 Archiving old security documentation..."
archive_file "SECURITY_REMEDIATION_SPRINT_PLAN.md" "legacy_docs" "Superseded by current implementation"
archive_file "PENETRATION_TEST_SIMULATION_REPORT.md" "legacy_docs" "Superseded by current implementation"

# Archive old configuration and architecture files
echo "⚙️ Archiving old configuration files..."
archive_file "CONFIGURATION_SYSTEM.md" "legacy_docs" "Superseded by current implementation"
archive_file "ARCHITECTURE_ANALYSIS.md" "legacy_docs" "Superseded by current implementation"
archive_file "ARCHITECTURE_DECISION_RECORD.md" "legacy_docs" "Superseded by current implementation"
archive_file "BUG_FIXES.md" "legacy_docs" "Superseded by current implementation"
archive_file "CI_CD_PIPELINE.md" "legacy_docs" "Superseded by current implementation"

# Archive old testing and documentation files
echo "🧪 Archiving old testing files..."
archive_file "TESTING_ARCHITECTURE.md" "legacy_docs" "Superseded by current implementation"
archive_file "VISUAL_DOCUMENTATION.md" "legacy_docs" "Superseded by current implementation"
archive_file "VISUAL_USER_GUIDE_IMPORT_FEATURE.md" "legacy_docs" "Superseded by current implementation"

# Archive old database and deployment files
echo "🗄️ Archiving old database files..."
archive_file "DATABASE_DESIGN.md" "legacy_docs" "Superseded by current implementation"
archive_file "DEPLOYMENT_PIPELINE.md" "legacy_docs" "Superseded by current implementation"

# Archive old tagging and analytics files
echo "🏷️ Archiving old tagging files..."
archive_file "TAGGING_ANALYTICS_GUIDE.md" "legacy_docs" "Superseded by current implementation"

# Archive old agent team files
echo "🤖 Archiving old agent team files..."
archive_file "AGENT_TEAM_ASSIGNMENTS.md" "legacy_docs" "Superseded by current implementation"
archive_file "AI_THEME_TEAM_ORG_CHART.md" "legacy_docs" "Superseded by current implementation"

# Archive old migration files
echo "🔄 Archiving old migration files..."
archive_file "ALPINE_MIGRATION_SUMMARY.md" "legacy_docs" "Migration completed - archived for reference"

# Archive old operational files
echo "📋 Archiving old operational files..."
archive_file "OPERATIONAL_RUNBOOK.md" "legacy_docs" "Superseded by current implementation"
archive_file "PRODUCTION_DEPLOYMENT_GUIDE.md" "legacy_docs" "Superseded by current implementation"
archive_file "PR_COMPLETE_APPLICATION_RECOVERY.md" "legacy_docs" "Superseded by current implementation"
archive_file "PR_DESCRIPTION.md" "legacy_docs" "Superseded by current implementation"
archive_file "PR_IMPORT_FEATURE_RELEASE.md" "legacy_docs" "Superseded by current implementation"

# Archive old multi-tenancy and security files
echo "🔐 Archiving old security files..."
archive_file "MULTI_TENANCY.md" "legacy_docs" "Superseded by current implementation"
archive_file "SECURITY.md" "legacy_docs" "Superseded by current implementation"
archive_file "SECURITY_MODEL.md" "legacy_docs" "Superseded by current implementation"

# Archive old demo files
echo "🎭 Archiving old demo files..."
archive_file "demo.py" "legacy_docs" "Demo file archived - functionality integrated into main app"
archive_file "demo_tagging.py" "legacy_docs" "Demo file archived - functionality integrated into main app"

# Archive old migration files
echo "📝 Archiving old migration files..."
archive_file "migrations.py" "legacy_docs" "Migration file archived - Django migrations used instead"

# Archive old validation files
echo "✅ Archiving old validation files..."
archive_file "validate_testing_framework.sh" "legacy_docs" "Validation script archived - CI/CD handles validation"
archive_file "validate_deployment_pipeline.sh" "legacy_docs" "Validation script archived - CI/CD handles validation"
archive_file "validate_feature.py" "legacy_docs" "Validation script archived - CI/CD handles validation"

# Archive old run scripts
echo "🏃 Archiving old run scripts..."
archive_file "run_containerized_tests.sh" "legacy_docs" "Run script archived - CI/CD handles testing"
archive_file "run_enhanced_tests.sh" "legacy_docs" "Run script archived - CI/CD handles testing"

# Archive old copilot instructions
echo "🤖 Archiving old copilot instructions..."
archive_file "copilot-instructions.md" "legacy_docs" "Copilot instructions archived - current setup documented"

echo "📋 Creating archive index..."

# Create archive index
cat > "${ARCHIVE_DIR}/ARCHIVE_INDEX.md" << 'EOF'
# Repository Cleanup Archive - Repository Cleanup

## Overview
This archive contains files that were moved during repository cleanup and modernization in Sprint 1.

## Archive Categories

### Sprint Documentation
- **SPRINT7_TEAM_KICKOFF.md**: Sprint completion - moved to archive
- **SPRINT_COMPLETION_SUMMARY.md**: Sprint completion - moved to archive  
- **SPRINT_EXECUTION_LOG.md**: Sprint completion - moved to archive

### Debug Reports
- **debug-report-20250901-215108.txt**: Debug session completed
- **debug-report-20250901-215149.txt**: Debug session completed

### Legacy Documentation
- **COMPREHENSIVE_TESTING_GUIDE.md**: Superseded by current implementation
- **COMPREHENSIVE_USER_GUIDE_WITH_VISUALS.md**: Superseded by current implementation
- **COMPREHENSIVE_IMPORT_ANALYSIS_SPRINT_PLAN.md**: Superseded by current implementation
- **COMPREHENSIVE_SECURITY_ANALYSIS_REPORT.md**: Superseded by current implementation
- **COMPREHENSIVE_SPRINT_PLAN.md**: Superseded by current implementation
- **COMPREHENSIVE_TESTING_GUIDE_FINAL.md**: Superseded by current implementation

### Team Assignments
- **TEAM_ALPHA_INFRASTRUCTURE_TASKS.md**: Team tasks completed - moved to archive
- **TEAM_BETA_ARCHITECTURE_TASKS.md**: Team tasks completed - moved to archive
- **TEAM_DELTA_SECURITY_TASKS.md**: Team tasks completed - moved to archive
- **TEAM_EPSILON_TESTING_TASKS.md**: Team tasks completed - moved to archive
- **TEAM_GAMMA_DATABASE_TASKS.md**: Team tasks completed - moved to archive
- **TEAM_ZETA_FRONTEND_TASKS.md**: Team tasks completed - moved to archive

### Old Releases
- **RELEASE_NOTES_v20250902_051242.md**: Release notes archived - current version maintained
- **FINAL_RELEASE_SUMMARY_v20250902_051242.md**: Release summary archived

### Feature Documentation
- **FEATURE_DEPLOYMENT_GUIDE.md**: Superseded by current implementation
- **IMPORT_FEATURE_EXECUTIVE_SUMMARY.md**: Superseded by current implementation
- **IMPORT_FEATURE_IMPLEMENTATION_ROADMAP.md**: Superseded by current implementation
- **IMPORT_FEATURE_TEAM_ASSIGNMENTS.md**: Superseded by current implementation
- **IMPORT_FEATURE_TECHNICAL_ARCHITECTURE.md**: Superseded by current implementation
- **IMPORT_WORKFLOW_VISUAL_GUIDE.md**: Superseded by current implementation

### Theme Documentation
- **THEME_IMPLEMENTATION_EXECUTIVE_SUMMARY.md**: Superseded by current implementation
- **THEME_SPRINT_TIMELINE.md**: Superseded by current implementation
- **CUSTOM_THEME_SPRINT_PLAN.md**: Superseded by current implementation

### Completion Reports
- **ULTIMATE_COMPLETION_REPORT.md**: Superseded by current implementation
- **COMPLETE_EXECUTION_REPORT.md**: Superseded by current implementation
- **FINAL_DEPLOYMENT_READY_STATUS.md**: Superseded by current implementation
- **FINAL_SPRINT_SUMMARY.md**: Superseded by current implementation
- **DEPLOYMENT_SUMMARY.md**: Superseded by current implementation
- **DEPLOYMENT_VALIDATION.md**: Superseded by current implementation
- **DOCUMENTATION_CODEBASE_REVIEW.md**: Superseded by current implementation
- **IMPLEMENTATION_SUMMARY.md**: Superseded by current implementation
- **GITHUB_ISSUES_CREATED.md**: Superseded by current implementation

### Analysis Files
- **WEBAPP_CRITICAL_ANALYSIS.md**: Superseded by current implementation
- **IMPORT_ANALYSIS_FEATURE_REQUIREMENTS.md**: Superseded by current implementation
- **WEB_GUI_INTEGRATION.md**: Superseded by current implementation

### Security Documentation
- **SECURITY_REMEDIATION_SPRINT_PLAN.md**: Superseded by current implementation
- **PENETRATION_TEST_SIMULATION_REPORT.md**: Superseded by current implementation
- **MULTI_TENANCY.md**: Superseded by current implementation
- **SECURITY.md**: Superseded by current implementation
- **SECURITY_MODEL.md**: Superseded by current implementation

### Configuration & Architecture
- **CONFIGURATION_SYSTEM.md**: Superseded by current implementation
- **ARCHITECTURE_ANALYSIS.md**: Superseded by current implementation
- **ARCHITECTURE_DECISION_RECORD.md**: Superseded by current implementation
- **BUG_FIXES.md**: Superseded by current implementation
- **CI_CD_PIPELINE.md**: Superseded by current implementation

### Testing & Documentation
- **TESTING_ARCHITECTURE.md**: Superseded by current implementation
- **VISUAL_DOCUMENTATION.md**: Superseded by current implementation
- **VISUAL_USER_GUIDE_IMPORT_FEATURE.md**: Superseded by current implementation

### Database & Deployment
- **DATABASE_DESIGN.md**: Superseded by current implementation
- **DEPLOYMENT_PIPELINE.md**: Superseded by current implementation

### Tagging & Analytics
- **TAGGING_ANALYTICS_GUIDE.md**: Superseded by current implementation

### Agent Team Files
- **AGENT_TEAM_ASSIGNMENTS.md**: Superseded by current implementation
- **AI_THEME_TEAM_ORG_CHART.md**: Superseded by current implementation

### Migration Files
- **ALPINE_MIGRATION_SUMMARY.md**: Migration completed - archived for reference
- **migrations.py**: Migration file archived - Django migrations used instead

### Operational Files
- **OPERATIONAL_RUNBOOK.md**: Superseded by current implementation
- **PRODUCTION_DEPLOYMENT_GUIDE.md**: Superseded by current implementation
- **PR_COMPLETE_APPLICATION_RECOVERY.md**: Superseded by current implementation
- **PR_DESCRIPTION.md**: Superseded by current implementation
- **PR_IMPORT_FEATURE_RELEASE.md**: Superseded by current implementation

### Demo Files
- **demo.py**: Demo file archived - functionality integrated into main app
- **demo_tagging.py**: Demo file archived - functionality integrated into main app

### Validation & Run Scripts
- **validate_testing_framework.sh**: Validation script archived - CI/CD handles validation
- **validate_deployment_pipeline.sh**: Validation script archived - CI/CD handles validation
- **validate_feature.py**: Validation script archived - CI/CD handles validation
- **run_containerized_tests.sh**: Run script archived - CI/CD handles testing
- **run_enhanced_tests.sh**: Run script archived - CI/CD handles testing

### Copilot Instructions
- **copilot-instructions.md**: Copilot instructions archived - current setup documented

## Access Instructions
- All files are preserved in their original format
- Use `git log` to view file history
- Files can be restored if needed by moving back from archive
- Archive is version controlled and searchable

## Restoration Process
To restore a file:
```bash
# Example: Restore a specific file
mv archive/${ARCHIVE_DATE}_repository_cleanup/sprint_docs/SPRINT7_TEAM_KICKOFF.md ./

# Example: Restore entire category
mv archive/${ARCHIVE_DATE}_repository_cleanup/sprint_docs/* ./
```

## Archive Metadata
- **Created**: Repository Cleanup
- **Reason**: Repository cleanup and modernization
- **Total Files**: $(find "${ARCHIVE_DIR}" -type f | wc -l)
- **Archive Size**: $(du -sh "${ARCHIVE_DIR}" | cut -f1)
EOF

echo "📋 Archive index created: ${ARCHIVE_DIR}/ARCHIVE_INDEX.md"

# Create archive README
cat > "${ARCHIVE_DIR}/README.md" << 'EOF'
# Repository Archive

This directory contains archived files from the repository cleanup process.

## Quick Access
- **ARCHIVE_INDEX.md**: Complete index of all archived files
- **ARCHIVE_LOG.txt**: Log of all archival operations

## Categories
- **sprint_docs/**: Sprint-related documentation
- **debug_reports/**: Debug and troubleshooting files
- **legacy_docs/**: Superseded documentation
- **duplicate_files/**: Identified duplicates
- **team_assignments/**: Team task files
- **old_releases/**: Previous release documentation

## Restoration
All files can be restored to their original location if needed.
EOF

echo "📋 Archive README created: ${ARCHIVE_DIR}/README.md"

echo "✅ Archive creation completed!"
echo "📁 Archive location: ${ARCHIVE_DIR}"
echo "📋 Archive index: ${ARCHIVE_DIR}/ARCHIVE_INDEX.md"
echo "📋 Archive log: ${ARCHIVE_DIR}/ARCHIVE_LOG.txt"
echo "📋 Archive README: ${ARCHIVE_DIR}/README.md"

# Show archive statistics
echo ""
echo "📊 Archive Statistics:"
echo "Total files archived: $(find "${ARCHIVE_DIR}" -type f | wc -l)"
echo "Archive size: $(du -sh "${ARCHIVE_DIR}" | cut -f1)"
echo "Categories created: $(ls -1 "${ARCHIVE_DIR}" | grep -v "\.md\|\.txt" | wc -l)"