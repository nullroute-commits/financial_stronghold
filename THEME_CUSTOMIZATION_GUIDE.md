# Theme Customization Guide

**Version**: 1.0  
**Last Updated**: January 2, 2025  
**Created by**: Documentation Team

---

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Theme Editor Interface](#theme-editor-interface)
4. [Creating Custom Themes](#creating-custom-themes)
5. [Theme Structure](#theme-structure)
6. [API Reference](#api-reference)
7. [Advanced Customization](#advanced-customization)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The Financial Stronghold theme system allows users to personalize their interface with custom colors, typography, spacing, and component styles. Themes are applied in real-time using CSS variables, ensuring optimal performance and instant visual feedback.

### Key Features

- **Live Preview**: See changes instantly as you customize
- **Theme Templates**: Start with pre-designed themes
- **Import/Export**: Share themes with other users
- **Multiple Themes**: Create and manage multiple themes
- **Accessibility**: Built-in high contrast options
- **Performance**: Zero impact on application speed

---

## Getting Started

### Accessing the Theme Editor

1. Navigate to **Settings** → **Appearance** → **Themes**
2. Click the **"Customize Theme"** button
3. The theme editor will open in a modal or side panel

### Quick Start

1. **Choose a Template**: Select from pre-designed themes
2. **Customize**: Adjust colors, fonts, and spacing
3. **Preview**: Toggle live preview to see changes
4. **Save**: Name your theme and save it
5. **Activate**: Set as your active theme

---

## Theme Editor Interface

### Editor Tabs

#### 1. Colors Tab
Customize all color aspects of your theme:

- **Primary Colors**: Main brand colors (primary, secondary, success, danger, warning, info)
- **Neutral Colors**: Background, surface, and border colors
- **Text Colors**: Primary and secondary text colors

#### 2. Typography Tab
Control fonts and text styling:

- **Font Family**: Choose from system fonts or web fonts
- **Font Sizes**: Base size and scale
- **Line Height**: Text spacing
- **Font Weights**: Regular, medium, bold options

#### 3. Spacing Tab
Adjust layout spacing:

- **Base Spacer**: Core spacing unit
- **Container Padding**: Page margins
- **Grid Gutters**: Column spacing
- **Border Radius**: Corner rounding

#### 4. Components Tab
Fine-tune individual components:

- **Cards**: Background, borders, shadows
- **Buttons**: Padding, borders, hover states
- **Forms**: Input styling and focus states
- **Navigation**: Header and sidebar styling

#### 5. Presets Tab
Browse and use theme templates:

- **Light Themes**: Professional light backgrounds
- **Dark Themes**: Eye-friendly dark modes
- **High Contrast**: Accessibility-focused themes
- **Colorful**: Vibrant, personality-rich themes

---

## Creating Custom Themes

### Step-by-Step Guide

#### 1. Start from Scratch
```javascript
// Click "Create New Theme"
// Default structure is provided:
{
  "name": "My Custom Theme",
  "colors": {
    "primary": "#0d6efd",
    "background": "#ffffff",
    "text-primary": "#212529"
  },
  "typography": {...},
  "spacing": {...},
  "borders": {...}
}
```

#### 2. Modify Colors
- Use the color picker for visual selection
- Enter hex codes directly for precision
- Preview changes in real-time

#### 3. Adjust Typography
```javascript
"typography": {
  "font-family-base": "'Inter', sans-serif",
  "font-size-base": "16px",
  "line-height-base": "1.5",
  "headings-font-family": "'Poppins', sans-serif",
  "headings-font-weight": "600"
}
```

#### 4. Set Spacing
```javascript
"spacing": {
  "spacer": "1rem",        // Base unit
  "container-padding": "1.5rem",
  "grid-gutter": "1.5rem"
}
```

#### 5. Configure Borders
```javascript
"borders": {
  "radius": "0.375rem",    // Default border radius
  "width": "1px",          // Default border width
  "style": "solid"         // Border style
}
```

### Using Theme Templates

1. **Browse Templates**: Go to the Presets tab
2. **Preview**: Hover over templates to see color schemes
3. **Use Template**: Click "Use This Theme"
4. **Customize**: Modify the template to your liking
5. **Save As New**: Save with a custom name

---

## Theme Structure

### Complete Theme Schema

```json
{
  "name": "Theme Name",
  "version": "1.0",
  "category": "light|dark|custom",
  "colors": {
    "primary": "#0d6efd",
    "secondary": "#6c757d",
    "success": "#198754",
    "danger": "#dc3545",
    "warning": "#ffc107",
    "info": "#0dcaf0",
    "light": "#f8f9fa",
    "dark": "#212529",
    "background": "#ffffff",
    "surface": "#f5f5f5",
    "text-primary": "#212529",
    "text-secondary": "#6c757d",
    "border": "#dee2e6",
    "shadow": "rgba(0, 0, 0, 0.1)"
  },
  "typography": {
    "font-family-base": "system-ui, -apple-system, sans-serif",
    "font-family-monospace": "monospace",
    "font-size-base": "1rem",
    "font-size-sm": "0.875rem",
    "font-size-lg": "1.125rem",
    "font-weight-light": "300",
    "font-weight-normal": "400",
    "font-weight-bold": "700",
    "line-height-base": "1.5",
    "headings-font-family": "inherit",
    "headings-font-weight": "500",
    "headings-line-height": "1.2"
  },
  "spacing": {
    "spacer": "1rem",
    "spacers": {
      "0": "0",
      "1": "0.25rem",
      "2": "0.5rem",
      "3": "1rem",
      "4": "1.5rem",
      "5": "3rem"
    },
    "container-padding": "1.5rem",
    "grid-gutter": "1.5rem"
  },
  "borders": {
    "width": "1px",
    "style": "solid",
    "radius": "0.375rem",
    "radius-sm": "0.25rem",
    "radius-lg": "0.5rem",
    "radius-pill": "50rem"
  },
  "shadows": {
    "sm": "0 0.125rem 0.25rem rgba(0, 0, 0, 0.075)",
    "default": "0 0.5rem 1rem rgba(0, 0, 0, 0.15)",
    "lg": "0 1rem 3rem rgba(0, 0, 0, 0.175)",
    "inset": "inset 0 1px 2px rgba(0, 0, 0, 0.075)"
  },
  "components": {
    "card": {
      "bg": "#ffffff",
      "border-radius": "0.375rem",
      "box-shadow": "0 0.125rem 0.25rem rgba(0, 0, 0, 0.075)"
    },
    "button": {
      "border-radius": "0.375rem",
      "padding-x": "0.75rem",
      "padding-y": "0.375rem"
    }
  }
}
```

### CSS Variable Mapping

Theme properties are automatically converted to CSS variables:

| Theme Property | CSS Variable |
|----------------|--------------|
| `colors.primary` | `--theme-color-primary` |
| `typography.font-size-base` | `--theme-font-size-base` |
| `spacing.spacer` | `--theme-spacing-spacer` |
| `borders.radius` | `--theme-border-radius` |

---

## API Reference

### REST API Endpoints

#### List User Themes
```http
GET /api/v1/themes/
Authorization: Bearer {token}

Response:
[
  {
    "id": "uuid",
    "name": "My Theme",
    "category": "custom",
    "is_active": true,
    "theme_data": {...}
  }
]
```

#### Get Active Theme
```http
GET /api/v1/themes/active/
Authorization: Bearer {token}

Response:
{
  "id": "uuid",
  "name": "Active Theme",
  "css_variables": {
    "--theme-color-primary": "#0d6efd",
    ...
  },
  "theme_data": {...}
}
```

#### Create Theme
```http
POST /api/v1/themes/
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "New Theme",
  "theme_data": {
    "colors": {...},
    "typography": {...},
    "spacing": {...},
    "borders": {...}
  }
}
```

#### Update Theme
```http
PUT /api/v1/themes/{theme_id}/
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Updated Name",
  "theme_data": {...}
}
```

#### Activate Theme
```http
POST /api/v1/themes/{theme_id}/activate/
Authorization: Bearer {token}
```

#### Delete Theme
```http
DELETE /api/v1/themes/{theme_id}/
Authorization: Bearer {token}
```

#### Preview Theme
```http
POST /api/v1/themes/preview/
Authorization: Bearer {token}
Content-Type: application/json

{
  "theme_data": {...}
}
```

#### Import Theme
```http
POST /api/v1/themes/import/
Authorization: Bearer {token}
Content-Type: application/json

{
  "theme_json": "{...}",
  "name": "Imported Theme"
}
```

#### Export Theme
```http
GET /api/v1/themes/{theme_id}/export/
Authorization: Bearer {token}

Response:
{
  "theme_json": "{...}",
  "filename": "theme_name.json"
}
```

### JavaScript API

#### Theme Engine
```javascript
// Get current theme
const currentTheme = window.themeEngine.getCurrentTheme();

// Switch theme
await window.themeEngine.switchTheme(themeId);

// Preview theme without saving
await window.themeEngine.previewTheme(themeData);

// Reset to active theme
await window.themeEngine.resetToActiveTheme();

// Update single variable
window.themeEngine.updateVariable('--theme-color-primary', '#ff0000');

// Update multiple variables
window.themeEngine.updateVariables({
  '--theme-color-primary': '#ff0000',
  '--theme-color-secondary': '#00ff00'
});

// Export current theme
const exportJson = window.themeEngine.exportCurrentTheme();

// Toggle dark mode
await window.themeEngine.toggleDarkMode();
```

#### Theme Editor
```javascript
// Initialize theme editor
const editor = new ThemeEditor('theme-editor-container');

// Load current theme
await editor.loadCurrentTheme();

// Save theme
await editor.saveTheme();

// Preview changes
editor.togglePreview(true);

// Reset changes
editor.resetTheme();
```

---

## Advanced Customization

### Custom Color Schemes

#### Creating a Monochromatic Theme
```json
{
  "colors": {
    "primary": "#2563eb",
    "secondary": "#3b82f6",
    "success": "#10b981",
    "danger": "#ef4444",
    "warning": "#f59e0b",
    "info": "#06b6d4",
    "light": "#e0e7ff",
    "dark": "#1e3a8a",
    "background": "#f0f4ff",
    "surface": "#dbeafe",
    "text-primary": "#1e3a8a",
    "text-secondary": "#3730a3"
  }
}
```

#### High Contrast Theme
```json
{
  "colors": {
    "primary": "#0000ff",
    "secondary": "#800080",
    "background": "#ffffff",
    "text-primary": "#000000",
    "border": "#000000"
  },
  "borders": {
    "width": "2px"
  }
}
```

### Custom Fonts

#### Using Google Fonts
```json
{
  "typography": {
    "font-family-base": "'Roboto', sans-serif",
    "headings-font-family": "'Roboto Slab', serif"
  }
}
```

#### System Font Stack
```json
{
  "typography": {
    "font-family-base": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Fira Sans', 'Droid Sans', 'Helvetica Neue', Arial, sans-serif"
  }
}
```

### Component-Specific Styling

#### Custom Card Styles
```json
{
  "components": {
    "card": {
      "bg": "#f8fafc",
      "border-width": "0",
      "border-radius": "1rem",
      "box-shadow": "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
      "header-bg": "transparent",
      "header-border-color": "transparent"
    }
  }
}
```

#### Custom Button Styles
```json
{
  "components": {
    "button": {
      "border-radius": "9999px",
      "padding-x": "1.5rem",
      "padding-y": "0.5rem",
      "font-weight": "600",
      "transition": "all 0.2s ease-in-out"
    }
  }
}
```

---

## Best Practices

### 1. Color Selection
- **Contrast**: Ensure sufficient contrast between text and background (WCAG AA: 4.5:1)
- **Consistency**: Use a limited color palette (5-7 colors max)
- **Meaning**: Use colors consistently (e.g., red for errors, green for success)

### 2. Typography
- **Readability**: Choose fonts with good legibility
- **Hierarchy**: Use font sizes to create clear visual hierarchy
- **Line Length**: Keep line lengths between 45-75 characters

### 3. Spacing
- **Consistency**: Use multiples of your base spacer
- **Breathing Room**: Don't crowd elements
- **Alignment**: Maintain consistent alignment

### 4. Performance
- **Limit Themes**: Keep under 10 themes per user
- **Optimize Images**: Use optimized preview images
- **Cache Themes**: Active themes are cached automatically

### 5. Accessibility
- **Test Contrast**: Use contrast checking tools
- **Focus States**: Ensure visible focus indicators
- **Color Blind**: Test with color blind simulators

---

## Troubleshooting

### Common Issues

#### Theme Not Applying
1. **Clear Cache**: Try refreshing the page
2. **Check Console**: Look for JavaScript errors
3. **Verify Active**: Ensure theme is set as active
4. **Browser Support**: Check CSS variable support

#### Colors Look Wrong
1. **Valid Format**: Use valid hex colors (#RRGGBB)
2. **Color Space**: Check monitor color profile
3. **Preview Mode**: Ensure preview is enabled

#### Can't Save Theme
1. **Theme Limit**: Check if at maximum (10 themes)
2. **Name Conflict**: Try a different name
3. **Validation**: Check for validation errors
4. **Permissions**: Ensure you're logged in

#### Import Fails
1. **JSON Format**: Validate JSON syntax
2. **Required Fields**: Ensure all required fields present
3. **File Size**: Keep under 100KB
4. **Version**: Check theme version compatibility

### Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "Maximum theme limit reached" | 10 theme limit | Delete unused themes |
| "Invalid color format" | Bad hex color | Use format #RRGGBB |
| "Theme name already exists" | Duplicate name | Choose unique name |
| "Cannot delete active theme" | Trying to delete active | Activate another first |
| "Theme data too large" | >100KB theme | Simplify theme data |

### Getting Help

1. **Documentation**: Check this guide first
2. **Support**: Contact support@financialstronghold.com
3. **Community**: Join our Discord server
4. **Issues**: Report bugs on GitHub

---

## Appendix

### Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Save Theme | `Ctrl/Cmd + S` |
| Toggle Preview | `Ctrl/Cmd + P` |
| Reset Changes | `Ctrl/Cmd + R` |
| Close Editor | `Esc` |

### Browser Support

| Feature | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| CSS Variables | ✅ 49+ | ✅ 31+ | ✅ 9.1+ | ✅ 15+ |
| Color Picker | ✅ | ✅ | ✅ | ✅ |
| Import/Export | ✅ | ✅ | ✅ | ✅ |

### Theme Limits

- **Themes per user**: 10
- **Theme size**: 100KB
- **Name length**: 100 characters
- **Description**: 500 characters
- **Color values**: Valid CSS colors only

---

*For technical support or feature requests, please contact our support team or visit the [GitHub repository](https://github.com/financialstronghold/themes).*