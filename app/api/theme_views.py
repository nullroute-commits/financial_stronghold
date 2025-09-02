"""
Theme API endpoints using Django REST Framework.
Provides RESTful API for theme management.

Created by: Team Beta (Blake & Bella)
Date: 2025-01-02
"""

import json
import logging
from typing import Dict, Any

from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django_filters import rest_framework as filters

from ..models.theme_models import (
    UserThemePreference,
    ThemeTemplate,
    ThemeCategory,
    ThemeAuditLog
)
from ..serializers.theme_serializers import (
    UserThemePreferenceSerializer,
    ThemeTemplateSerializer,
    ThemeCreateSerializer,
    ThemeUpdateSerializer,
    ThemeImportSerializer,
    ThemePreviewSerializer,
    CompiledThemeSerializer
)
from ..services.theme_service import theme_service, ThemeValidationError

logger = logging.getLogger(__name__)


class ThemeFilter(filters.FilterSet):
    """Filter for theme queries."""
    category = filters.ChoiceFilter(choices=ThemeCategory.choices)
    is_active = filters.BooleanFilter()
    
    class Meta:
        model = UserThemePreference
        fields = ['category', 'is_active']


class ThemeTemplateFilter(filters.FilterSet):
    """Filter for theme templates."""
    category = filters.ChoiceFilter(choices=ThemeCategory.choices)
    is_featured = filters.BooleanFilter()
    is_public = filters.BooleanFilter()
    
    class Meta:
        model = ThemeTemplate
        fields = ['category', 'is_featured', 'is_public']


class UserThemeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user theme preferences.
    Provides CRUD operations and theme management actions.
    """
    serializer_class = UserThemePreferenceSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = ThemeFilter
    
    def get_queryset(self):
        """Filter themes to current user only."""
        return UserThemePreference.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return ThemeCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ThemeUpdateSerializer
        elif self.action == 'import_theme':
            return ThemeImportSerializer
        elif self.action == 'preview':
            return ThemePreviewSerializer
        return self.serializer_class
    
    def create(self, request, *args, **kwargs):
        """Create a new theme."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            theme_pref = theme_service.create_theme(
                user=request.user,
                name=serializer.validated_data['name'],
                theme_data=serializer.validated_data['theme_data'],
                base_template_id=serializer.validated_data.get('base_template_id'),
                request_meta=request.META
            )
            
            # Update optional fields
            if 'description' in serializer.validated_data:
                theme_pref.description = serializer.validated_data['description']
            if 'category' in serializer.validated_data:
                theme_pref.category = serializer.validated_data['category']
            theme_pref.save()
            
            response_serializer = UserThemePreferenceSerializer(theme_pref)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except ThemeValidationError as e:
            raise ValidationError(str(e))
        except Exception as e:
            logger.error(f"Error creating theme: {str(e)}")
            raise ValidationError("Error creating theme")
    
    def update(self, request, *args, **kwargs):
        """Update a theme."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        try:
            theme_pref = theme_service.update_theme(
                user=request.user,
                theme_id=str(instance.id),
                name=serializer.validated_data.get('name'),
                theme_data=serializer.validated_data.get('theme_data'),
                request_meta=request.META
            )
            
            # Update optional fields
            if 'description' in serializer.validated_data:
                theme_pref.description = serializer.validated_data['description']
                theme_pref.save()
            
            response_serializer = UserThemePreferenceSerializer(theme_pref)
            return Response(response_serializer.data)
            
        except ThemeValidationError as e:
            raise ValidationError(str(e))
        except Exception as e:
            logger.error(f"Error updating theme: {str(e)}")
            raise ValidationError("Error updating theme")
    
    def destroy(self, request, *args, **kwargs):
        """Delete a theme."""
        instance = self.get_object()
        
        try:
            theme_service.delete_theme(
                user=request.user,
                theme_id=str(instance.id),
                request_meta=request.META
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except ThemeValidationError as e:
            raise ValidationError(str(e))
        except Exception as e:
            logger.error(f"Error deleting theme: {str(e)}")
            raise ValidationError("Error deleting theme")
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get the currently active theme."""
        try:
            active_theme = theme_service.get_active_theme(request.user)
            serializer = CompiledThemeSerializer(active_theme)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error getting active theme: {str(e)}")
            raise ValidationError("Error retrieving active theme")
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a theme."""
        instance = self.get_object()
        
        try:
            theme_pref = theme_service.activate_theme(
                user=request.user,
                theme_id=str(instance.id),
                request_meta=request.META
            )
            
            serializer = UserThemePreferenceSerializer(theme_pref)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error activating theme: {str(e)}")
            raise ValidationError("Error activating theme")
    
    @action(detail=False, methods=['post'])
    def preview(self, request):
        """Preview a theme without saving."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            compiled_theme = theme_service.preview_theme(
                serializer.validated_data['theme_data']
            )
            response_serializer = CompiledThemeSerializer(compiled_theme)
            return Response(response_serializer.data)
            
        except ThemeValidationError as e:
            raise ValidationError(str(e))
        except Exception as e:
            logger.error(f"Error previewing theme: {str(e)}")
            raise ValidationError("Error previewing theme")
    
    @action(detail=False, methods=['post'])
    def import_theme(self, request):
        """Import a theme from JSON."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            theme_pref = theme_service.import_theme(
                user=request.user,
                theme_json=serializer.validated_data['theme_json'],
                request_meta=request.META
            )
            
            if 'name' in serializer.validated_data:
                theme_pref.name = serializer.validated_data['name']
                theme_pref.save()
            
            response_serializer = UserThemePreferenceSerializer(theme_pref)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except ThemeValidationError as e:
            raise ValidationError(str(e))
        except Exception as e:
            logger.error(f"Error importing theme: {str(e)}")
            raise ValidationError("Error importing theme")
    
    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        """Export a theme to JSON."""
        instance = self.get_object()
        
        try:
            theme_json = theme_service.export_theme(
                user=request.user,
                theme_id=str(instance.id),
                request_meta=request.META
            )
            
            return Response({
                'theme_json': theme_json,
                'filename': f'theme_{instance.name.lower().replace(" ", "_")}.json'
            })
            
        except Exception as e:
            logger.error(f"Error exporting theme: {str(e)}")
            raise ValidationError("Error exporting theme")


class ThemeTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for theme templates.
    Read-only access to pre-defined templates.
    """
    serializer_class = ThemeTemplateSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = ThemeTemplateFilter
    
    def get_queryset(self):
        """Return only public templates."""
        return ThemeTemplate.objects.filter(is_public=True)
    
    @action(detail=True, methods=['post'])
    def use_template(self, request, pk=None):
        """Create a user theme from a template."""
        template = self.get_object()
        
        try:
            # Get name from request or use default
            name = request.data.get('name', f"{template.name} (Copy)")
            
            theme_pref = template.create_user_preference(request.user, name)
            
            serializer = UserThemePreferenceSerializer(theme_pref)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error using template: {str(e)}")
            raise ValidationError("Error creating theme from template")


class ThemeAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for theme audit logs.
    Read-only access to audit history.
    """
    serializer_class = None  # Would need to create ThemeAuditLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return audit logs for current user."""
        return ThemeAuditLog.objects.filter(user=self.request.user)