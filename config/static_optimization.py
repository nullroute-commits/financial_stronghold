"""
Static File Optimization Configuration
Team Delta - Security Sprint 4
"""

from django.conf import settings
from django.contrib.staticfiles.storage import StaticFilesStorage
from django.core.files.storage import FileSystemStorage
import os
import hashlib

class StaticFileOptimizer:
    """Static file optimization and CDN integration"""
    
    def __init__(self):
        self.cdn_enabled = getattr(settings, 'CDN_ENABLED', False)
        self.cdn_url = getattr(settings, 'CDN_URL', '')
        self.compression_enabled = getattr(settings, 'STATIC_COMPRESSION', True)
        self.cache_busting_enabled = getattr(settings, 'STATIC_CACHE_BUSTING', True)
    
    def get_optimized_static_url(self, path):
        """Get optimized static file URL with CDN and cache busting"""
        if self.cdn_enabled and self.cdn_url:
            base_url = self.cdn_url
        else:
            base_url = settings.STATIC_URL
        
        if self.cache_busting_enabled:
            # Add cache busting hash
            hash_suffix = self.get_file_hash(path)
            if hash_suffix:
                path = f"{path}?v={hash_suffix}"
        
        return f"{base_url}{path}"
    
    def get_file_hash(self, path):
        """Get file hash for cache busting"""
        try:
            file_path = os.path.join(settings.STATIC_ROOT, path)
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    content = f.read()
                    return hashlib.md5(content).hexdigest()[:8]
        except Exception:
            pass
        return None
    
    def optimize_static_files(self):
        """Optimize static files for production"""
        if not self.compression_enabled:
            return
        
        # This would integrate with build tools like Webpack or Gulp
        # to minify and compress static files
        pass

# Static file optimization settings
STATIC_OPTIMIZATION_SETTINGS = {
    'COMPRESSION': {
        'enabled': True,
        'min_size': 1024,  # 1KB
        'algorithms': ['gzip', 'brotli'],
    },
    'MINIFICATION': {
        'enabled': True,
        'css': True,
        'javascript': True,
        'html': True,
    },
    'BUNDLING': {
        'enabled': True,
        'css_bundles': ['main', 'admin', 'auth'],
        'js_bundles': ['main', 'admin', 'auth'],
    },
    'CDN': {
        'enabled': False,
        'url': '',
        'fallback': True,
    }
}

# Global static file optimizer instance
static_optimizer = StaticFileOptimizer()
