"""
Django management command for comprehensive health checks.
Validates all system components for production readiness.

Created by Team Alpha (Infrastructure & DevOps) for Sprint 6
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection
from django.core.cache import cache
import json
import time

from app.monitoring import health_check_service


class Command(BaseCommand):
    help = 'Run comprehensive health checks on all system components'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            choices=['text', 'json'],
            default='text',
            help='Output format for health check results',
        )
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Include detailed diagnostic information',
        )
        parser.add_argument(
            '--fail-on-warning',
            action='store_true',
            help='Exit with error code if any warnings are found',
        )
    
    def handle(self, *args, **options):
        """Execute health checks."""
        
        self.stdout.write('🏥 Running comprehensive health checks...')
        
        # Get health status
        health_data = health_check_service.get_health_status()
        
        if options['format'] == 'json':
            self.stdout.write(json.dumps(health_data, indent=2))
            return
        
        # Text format output
        self._display_health_results(health_data, options['detailed'])
        
        # Determine exit code
        if health_data['status'] == 'unhealthy':
            self.stderr.write(self.style.ERROR('❌ Health check failed'))
            exit(1)
        elif health_data['status'] == 'degraded':
            if options['fail_on_warning']:
                self.stderr.write(self.style.WARNING('⚠️  Health check found warnings'))
                exit(1)
            else:
                self.stdout.write(self.style.WARNING('⚠️  Health check passed with warnings'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ All health checks passed'))
    
    def _display_health_results(self, health_data, detailed=False):
        """Display health check results in text format."""
        
        # Overall status
        status_icon = {
            'healthy': '✅',
            'degraded': '⚠️ ',
            'unhealthy': '❌'
        }.get(health_data['status'], '❓')
        
        self.stdout.write(f"\n{status_icon} Overall Status: {health_data['status'].upper()}")
        self.stdout.write(f"🕐 Response Time: {health_data['response_time_ms']}ms")
        self.stdout.write(f"📅 Timestamp: {health_data['timestamp']}")
        self.stdout.write(f"🏷️  Version: {health_data['version']}")
        self.stdout.write(f"🔧 Framework: {health_data['framework']}")
        
        if 'uptime' in health_data:
            self.stdout.write(f"⏱️  Uptime: {health_data['uptime']}")
        
        # Component checks
        self.stdout.write("\n📋 Component Health Checks:")
        
        for check_name, check_result in health_data['checks'].items():
            status = check_result['status']
            icon = {
                'healthy': '✅',
                'warning': '⚠️ ',
                'unhealthy': '❌',
                'info': 'ℹ️ '
            }.get(status, '❓')
            
            self.stdout.write(f"  {icon} {check_name.title()}: {status}")
            
            if detailed:
                # Show detailed information
                for key, value in check_result.items():
                    if key not in ['status', 'timestamp']:
                        self.stdout.write(f"      {key}: {value}")
            
            if status in ['unhealthy', 'warning'] and 'error' in check_result:
                self.stdout.write(f"      Error: {check_result['error']}")
        
        # Recommendations
        if health_data['status'] != 'healthy':
            self.stdout.write("\n💡 Recommendations:")
            
            for check_name, check_result in health_data['checks'].items():
                if check_result['status'] == 'unhealthy':
                    self.stdout.write(f"  • Fix {check_name} connectivity issues")
                elif check_result['status'] == 'warning':
                    self.stdout.write(f"  • Monitor {check_name} performance")
        
        self.stdout.write("")