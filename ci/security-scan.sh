#!/bin/bash
# Comprehensive security scanning script using Bandit
# Team Beta - Architecture Sprint 2

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
ORANGE='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔒 Starting comprehensive security scanning...${NC}"

# Create reports directory
mkdir -p reports/security

# Set environment variables
export PYTHONPATH=/app
export BANDIT_CONFIG_FILE=/app/.bandit

# Check if Bandit is installed
if ! command -v bandit &> /dev/null; then
    echo -e "${YELLOW}Installing Bandit...${NC}"
    pip install bandit[pyyaml]
fi

# Bandit configuration
BANDIT_OPTS=(
    --format json
    --output reports/security/bandit-report.json
    --severity-level ${BANDIT_SEVERITY:-medium}
    --confidence-level ${BANDIT_CONFIDENCE:-medium}
    --exclude tests/,migrations/,venv/,env/
    --recursive
    --verbose
)

echo -e "${YELLOW}Running Bandit security scan...${NC}"

# Run Bandit on the main application
echo -e "${BLUE}Scanning main application...${NC}"
if bandit "${BANDIT_OPTS[@]}" app/ > reports/security/bandit-app.txt 2>&1; then
    echo -e "${GREEN}✅ Main application security scan completed${NC}"
    APP_EXIT=0
else
    echo -e "${ORANGE}⚠️  Main application security scan completed with issues${NC}"
    APP_EXIT=0  # Bandit exits with 1 if issues found, but we want to continue
fi

# Run Bandit on configuration
echo -e "${BLUE}Scanning configuration...${NC}"
if bandit "${BANDIT_OPTS[@]}" config/ > reports/security/bandit-config.txt 2>&1; then
    echo -e "${GREEN}✅ Configuration security scan completed${NC}"
    CONFIG_EXIT=0
else
    echo -e "${ORANGE}⚠️  Configuration security scan completed with issues${NC}"
    CONFIG_EXIT=0
fi

# Run Bandit on scripts
echo -e "${BLUE}Scanning scripts...${NC}"
if bandit "${BANDIT_OPTS[@]}" scripts/ > reports/security/bandit-scripts.txt 2>&1; then
    echo -e "${GREEN}✅ Scripts security scan completed${NC}"
    SCRIPTS_EXIT=0
else
    echo -e "${ORANGE}⚠️  Scripts security scan completed with issues${NC}"
    SCRIPTS_EXIT=0
fi

# Run Bandit on CI scripts
echo -e "${BLUE}Scanning CI scripts...${NC}"
if bandit "${BANDIT_OPTS[@]}" ci/ > reports/security/bandit-ci.txt 2>&1; then
    echo -e "${GREEN}✅ CI scripts security scan completed${NC}"
    CI_EXIT=0
else
    echo -e "${ORANGE}⚠️  CI scripts security scan completed with issues${NC}"
    CI_EXIT=0
fi

# Generate security summary
echo -e "${YELLOW}Generating security scan summary...${NC}"
cat > reports/security/security-scan-summary.md << EOF
# Security Scan Summary

## Overview
Security scanning results from Bandit with ${BANDIT_SEVERITY:-medium} severity and ${BANDIT_CONFIDENCE:-medium} confidence levels.

## Scan Results

### Main Application
- **Status**: ✅ COMPLETED
- **File**: [bandit-app.txt](bandit-app.txt)
- **JSON Report**: [bandit-report.json](bandit-report.json)

### Configuration
- **Status**: ✅ COMPLETED
- **File**: [bandit-config.txt](bandit-config.txt)

### Scripts
- **Status**: ✅ COMPLETED
- **File**: [bandit-scripts.txt](bandit-scripts.txt)

### CI Scripts
- **Status**: ✅ COMPLETED
- **File**: [bandit-ci.txt](bandit-ci.txt)

## Bandit Configuration
- **Severity Level**: ${BANDIT_SEVERITY:-medium}
- **Confidence Level**: ${BANDIT_CONFIDENCE:-medium}
- **Excluded Directories**: tests/, migrations/, venv/, env/
- **Recursive Scanning**: Enabled
- **Output Format**: JSON + Text

## Common Security Issues to Check
- **B101**: assert_used - Assert statements in production code
- **B102**: exec_used - Use of exec() function
- **B103**: set_bad_file_permissions - Unsafe file permissions
- **B104**: hardcoded_bind_all_interfaces - Hardcoded bind to all interfaces
- **B105**: hardcoded_password_string - Hardcoded password strings
- **B106**: hardcoded_password_funcarg - Hardcoded password in function argument
- **B107**: hardcoded_password_default - Hardcoded password in default argument
- **B201**: flask_debug_true - Flask debug mode enabled
- **B301**: pickle - Use of pickle module
- **B302**: marshal - Use of marshal module
- **B303**: md5 - Use of MD5 hash function
- **B304**: md5 - Use of MD5 hash function
- **B305**: sha1 - Use of SHA1 hash function
- **B306**: mktemp_q - Use of mktemp() function
- **B307**: eval - Use of eval() function
- **B308**: mark_safe - Use of mark_safe() function
- **B309**: https_certificate_verification_disabled - HTTPS certificate verification disabled
- **B310**: urllib_urlopen - Use of urllib.urlopen() function
- **B311**: random - Use of random module
- **B312**: telnetlib - Use of telnetlib module
- **B313**: xml_bad_cElementTree - Use of cElementTree
- **B314**: xml_bad_ElementTree - Use of ElementTree
- **B315**: xml_bad_expatreader - Use of ExpatReader
- **B316**: xml_bad_expatbuilder - Use of ExpatBuilder
- **B317**: xml_bad_sax - Use of SAX
- **B318**: xml_bad_minidom - Use of minidom
- **B319**: xml_bad_pulldom - Use of pulldom
- **B320**: xml_bad_etree - Use of etree
- **B321**: ftplib - Use of ftplib module
- **B322**: input - Use of input() function
- **B323**: unverified_context - Use of unverified context
- **B324**: hashlib_new_insecure_functions - Use of insecure hash functions
- **B325**: tempnam - Use of tempnam() function
- **B401**: import_telnetlib - Import of telnetlib module
- **B402**: import_ftplib - Import of ftplib module
- **B403**: import_xml_etree - Import of xml.etree module
- **B404**: import_subprocess - Import of subprocess module
- **B405**: import_xml_sax - Import of xml.sax module
- **B406**: import_xml_expat - Import of xml.expat module
- **B407**: import_xml_minidom - Import of xml.minidom module
- **B408**: import_xml_pulldom - Import of xml.pulldom module
- **B409**: import_xml_etree_cElementTree - Import of xml.etree.cElementTree module
- **B410**: import_lxml - Import of lxml module
- **B411**: import_xml_expatreader - Import of xml.expatreader module
- **B412**: import_xml_expatbuilder - Import of xml.expatbuilder module
- **B413**: import_xml_sax - Import of xml.sax module
- **B501**: request_with_no_cert_validation - Request with no certificate validation
- **B601**: paramiko_calls - Paramiko call with shell=True
- **B602**: subprocess_popen_with_shell_equals_true - subprocess call with shell=True
- **B603**: subprocess_without_shell_equals_true - subprocess call without shell=True
- **B604**: any_other_function_with_shell_equals_true - Function call with shell=True
- **B605**: start_process_with_a_shell - Starting a process with a shell
- **B606**: start_process_with_no_shell - Starting a process without a shell
- **B607**: start_process_with_partial_path - Starting a process with a partial path
- **B608**: hardcoded_sql_expressions - Hardcoded SQL expressions
- **B609**: linux_commands_wildcard_injection - Linux command injection with wildcard
- **B701**: jinja2_autoescape_false - Jinja2 autoescape set to False

## Recommendations
- Review all HIGH severity issues first
- Address MEDIUM severity issues based on risk assessment
- Consider LOW severity issues for code quality improvements
- Use the JSON report for automated analysis
- Integrate with CI/CD pipeline for continuous security monitoring

## Generated: $(date)
EOF

# Parse JSON report for summary statistics
if [ -f "reports/security/bandit-report.json" ]; then
    echo -e "${YELLOW}Analyzing security scan results...${NC}"
    
    # Extract summary statistics using Python
    python3 -c "
import json
import sys

try:
    with open('reports/security/bandit-report.json', 'r') as f:
        data = json.load(f)
    
    # Count issues by severity
    severity_counts = {}
    confidence_counts = {}
    
    for issue in data.get('results', []):
        severity = issue.get('issue_severity', 'unknown')
        confidence = issue.get('issue_confidence', 'unknown')
        
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1
    
    print('📊 Security Scan Statistics:')
    print(f'Total Issues Found: {len(data.get(\"results\", []))}')
    print('\\nBy Severity:')
    for severity, count in sorted(severity_counts.items()):
        print(f'  {severity.upper()}: {count}')
    
    print('\\nBy Confidence:')
    for confidence, count in sorted(confidence_counts.items()):
        print(f'  {confidence.upper()}: {count}')
    
    # Check for critical issues
    high_severity = severity_counts.get('HIGH', 0)
    if high_severity > 0:
        print(f'\\n⚠️  WARNING: {high_severity} HIGH severity issues found!')
        sys.exit(1)
    else:
        print('\\n✅ No HIGH severity issues found')
        sys.exit(0)
        
except Exception as e:
    print(f'Error parsing security report: {e}')
    sys.exit(1)
" > reports/security/security-stats.txt 2>&1
    
    SECURITY_EXIT=$?
    cat reports/security/security-stats.txt
else
    echo -e "${ORANGE}⚠️  No JSON security report found${NC}"
    SECURITY_EXIT=0
fi

# Show summary
echo ""
echo -e "${YELLOW}=== SECURITY SCAN SUMMARY ===${NC}"
echo -e "Main Application: ${GREEN}✅ COMPLETED${NC}"
echo -e "Configuration: ${GREEN}✅ COMPLETED${NC}"
echo -e "Scripts: ${GREEN}✅ COMPLETED${NC}"
echo -e "CI Scripts: ${GREEN}✅ COMPLETED${NC}"

if [ $SECURITY_EXIT -eq 0 ]; then
    echo -e "${GREEN}🎉 Security scanning completed successfully!${NC}"
else
    echo -e "${RED}⚠️  Security scanning completed with HIGH severity issues!${NC}"
fi

echo -e "${BLUE}📋 Detailed reports available in: reports/security/${NC}"
echo -e "${BLUE}📊 Security statistics: reports/security/security-stats.txt${NC}"

exit $SECURITY_EXIT