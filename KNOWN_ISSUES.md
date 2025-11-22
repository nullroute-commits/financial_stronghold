# Known Issues and Workarounds

**Last Updated:** 2025-11-22

## Critical Issues

### 1. Model Import Circular Dependency (In Progress)

**Status:** ⚠️ In Progress  
**Severity:** High  
**Impact:** Django system checks fail, models cannot be imported

**Description:**
The application has a complex model structure with both:
- `app/models.py` (imports from django_models.py and models/import_models.py)
- `app/models/` directory (contains import_models.py)

This creates a circular import dependency where:
1. `import_models.py` used `get_user_model()` at module level
2. Django admin tries to load before User model is fully registered
3. Results in `LookupError: App 'app' doesn't have a 'User' model`

**Workaround Applied:**
- Changed `from django.contrib.auth import get_user_model()` to `from django.conf import settings`
- Changed `ForeignKey(User, ...)` to `ForeignKey(settings.AUTH_USER_MODEL, ...)`
- This uses Django's lazy reference system instead of eager model loading

**Status:** Partially fixed, needs testing with full app initialization

**Next Steps:**
1. Test with database migrations
2. Verify admin interface loads correctly
3. Consider refactoring model structure to be more conventional

---

## Medium Priority Issues

### 2. Production Dependencies Incompatible with Python 3.12

**Status:** ⚠️ Known Limitation  
**Severity:** Medium  
**Impact:** Production deployment uses alternatives

**Description:**
The following packages are not compatible with Python 3.12.3:
- `pylibmc==1.6.3` - Memcached client for Python
- `uwsgi==2.0.28` - Application server

**Workaround:**
- Using `python-memcached==1.59` instead (already in requirements)
- Using `gunicorn==23.0.0` instead of uwsgi
- Both alternatives are production-ready and widely used

**Documentation:** Noted in `requirements/production.txt` and `VERSION_COMPATIBILITY_MATRIX.md`

**Future:** Monitor upstream projects for Python 3.12 support

---

### 3. Logs Directory Not Created by Default

**Status:** ✅ Fixed  
**Severity:** Low  
**Impact:** Django system checks fail on fresh clone

**Description:**
The `logs/` directory is required by logging configuration but not created by default.

**Workaround:**
```bash
mkdir -p logs
```

**Permanent Fix:** Add logs directory creation to:
- Docker entrypoint scripts
- Development setup scripts
- Documentation

---

## Low Priority Issues

### 4. Docker Compose Command Name Change

**Status:** ℹ️ Informational  
**Severity:** Low  
**Impact:** Documentation may show `docker-compose` (hyphenated)

**Description:**
Modern Docker uses `docker compose` (space) instead of `docker-compose` (hyphen).

**Workaround:**
Both commands work on most systems, but `docker compose` is preferred.

**Update Required:**
- Update all documentation to use `docker compose`
- Update all scripts to use `docker compose`

---

### 5. Multiple README Files

**Status:** ⏳ To Be Addressed  
**Severity:** Low  
**Impact:** Documentation duplication and potential inconsistency

**Description:**
Repository has multiple README files:
- `README.md` - Main README
- `README_MODERNIZED.md` - Updated version with sprint information

**Recommendation:**
Consolidate into single authoritative `README.md` and archive the other.

---

## Fixed Issues

### ✅ NumPy Version Incompatibility

**Status:** ✅ Fixed in Sprint 1  
**Resolution:** Upgraded from 1.24.4 to 1.26.4

### ✅ scikit-learn Version Incompatibility

**Status:** ✅ Fixed in Sprint 1  
**Resolution:** Upgraded from 1.3.2 to 1.4.2

### ✅ Black Version Mismatch

**Status:** ✅ Fixed in Sprint 1  
**Resolution:** Standardized to 24.3.0 across all files

### ✅ Documentation Version Mismatches

**Status:** ✅ Fixed in Sprint 1 & 2  
**Resolution:** All versions updated to match actual codebase

### ✅ Repository Name References

**Status:** ✅ Fixed in Sprint 1  
**Resolution:** Changed all references from "Test" to "financial_stronghold"

---

## Reporting New Issues

If you encounter a new issue:

1. Check this document first
2. Check existing GitHub issues
3. Create a new issue with:
   - Clear description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (Python version, OS, etc.)

---

## Testing Status

| Component | Status | Notes |
|-----------|--------|-------|
| Dependency Installation | ✅ | All packages install successfully |
| Version Compatibility | ✅ | All versions compatible with Python 3.12.3 |
| Docker Compose Config | ✅ | Configuration validates successfully |
| Model Imports | ⚠️ | In progress - circular dependency fix |
| Django System Checks | ⏳ | Pending model import fix |
| Test Suite | ⏳ | Pending full dependency validation |
| CI/CD Pipeline | ⏳ | Pending validation |

---

**Note:** This document is actively maintained. Please update it when issues are discovered or resolved.
