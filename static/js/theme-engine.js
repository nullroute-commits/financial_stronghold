/**
 * Theme Engine - Dynamic theme application system
 * Handles runtime theme switching and CSS variable management
 * 
 * Created by: Team Gamma (Gabriel & Grace)
 * Date: 2025-01-02
 */

class ThemeEngine {
    constructor() {
        this.currentTheme = null;
        this.themeStyleElement = null;
        this.apiBaseUrl = '/api/v1';
        this.csrfToken = this.getCsrfToken();
        this.init();
    }

    /**
     * Initialize the theme engine
     */
    init() {
        // Create style element for dynamic theme CSS
        this.themeStyleElement = document.createElement('style');
        this.themeStyleElement.id = 'dynamic-theme-variables';
        document.head.appendChild(this.themeStyleElement);

        // Load active theme on page load
        this.loadActiveTheme();

        // Add theme transition class to body
        document.body.classList.add('theme-transition');
    }

    /**
     * Get CSRF token from cookies
     */
    getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    /**
     * Load the active theme from the API
     */
    async loadActiveTheme() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/themes/active/`, {
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const theme = await response.json();
                this.applyTheme(theme);
            } else if (response.status === 404) {
                // No active theme, use defaults
                console.info('No active theme found, using defaults');
            } else {
                console.error('Failed to load active theme:', response.statusText);
            }
        } catch (error) {
            console.error('Error loading active theme:', error);
        }
    }

    /**
     * Apply a theme by updating CSS variables
     * @param {Object} theme - Compiled theme object with css_variables
     */
    applyTheme(theme) {
        if (!theme || !theme.css_variables) {
            console.error('Invalid theme data');
            return;
        }

        this.currentTheme = theme;

        // Build CSS variable declarations
        let cssText = ':root {\n';
        for (const [variable, value] of Object.entries(theme.css_variables)) {
            cssText += `    ${variable}: ${value};\n`;
        }
        cssText += '}';

        // Apply the CSS
        this.themeStyleElement.textContent = cssText;

        // Update data attributes
        document.documentElement.setAttribute('data-theme', theme.theme_data.category || 'custom');
        document.documentElement.setAttribute('data-theme-id', theme.id || 'default');

        // Dispatch theme change event
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: theme }));
    }

    /**
     * Switch to a different theme
     * @param {string} themeId - UUID of the theme to activate
     */
    async switchTheme(themeId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/themes/${themeId}/activate/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                await this.loadActiveTheme();
                return { success: true };
            } else {
                const error = await response.json();
                return { success: false, error: error.detail || 'Failed to switch theme' };
            }
        } catch (error) {
            console.error('Error switching theme:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Preview a theme without saving/activating
     * @param {Object} themeData - Theme data to preview
     */
    async previewTheme(themeData) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/themes/preview/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ theme_data: themeData })
            });

            if (response.ok) {
                const compiledTheme = await response.json();
                this.applyTheme(compiledTheme);
                return { success: true, theme: compiledTheme };
            } else {
                const error = await response.json();
                return { success: false, error: error.detail || 'Failed to preview theme' };
            }
        } catch (error) {
            console.error('Error previewing theme:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Reset to the active theme (cancel preview)
     */
    async resetToActiveTheme() {
        await this.loadActiveTheme();
    }

    /**
     * Get current theme data
     */
    getCurrentTheme() {
        return this.currentTheme;
    }

    /**
     * Export current theme as JSON
     */
    exportCurrentTheme() {
        if (!this.currentTheme) {
            return null;
        }

        return JSON.stringify({
            name: this.currentTheme.name || 'Exported Theme',
            version: '1.0',
            category: this.currentTheme.theme_data.category || 'custom',
            exported_at: new Date().toISOString(),
            theme_data: this.currentTheme.theme_data
        }, null, 2);
    }

    /**
     * Apply a single CSS variable
     * @param {string} variable - CSS variable name
     * @param {string} value - CSS value
     */
    updateVariable(variable, value) {
        document.documentElement.style.setProperty(variable, value);
    }

    /**
     * Apply multiple CSS variables
     * @param {Object} variables - Object with variable names and values
     */
    updateVariables(variables) {
        for (const [variable, value] of Object.entries(variables)) {
            this.updateVariable(variable, value);
        }
    }

    /**
     * Get computed value of a CSS variable
     * @param {string} variable - CSS variable name
     */
    getVariable(variable) {
        return getComputedStyle(document.documentElement).getPropertyValue(variable).trim();
    }

    /**
     * Check if user prefers dark mode
     */
    prefersDarkMode() {
        return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    }

    /**
     * Toggle between light and dark themes
     */
    async toggleDarkMode() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/themes/`, {
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const themes = await response.json();
                const currentCategory = this.currentTheme?.theme_data?.category || 'light';
                
                // Find opposite theme
                let targetTheme = null;
                if (currentCategory === 'dark') {
                    targetTheme = themes.find(t => t.category === 'light' && t.is_active === false);
                } else {
                    targetTheme = themes.find(t => t.category === 'dark');
                }

                if (targetTheme) {
                    await this.switchTheme(targetTheme.id);
                }
            }
        } catch (error) {
            console.error('Error toggling dark mode:', error);
        }
    }

    /**
     * Listen for system dark mode changes
     */
    watchSystemTheme() {
        if (window.matchMedia) {
            const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
            darkModeQuery.addEventListener('change', (e) => {
                window.dispatchEvent(new CustomEvent('systemThemeChanged', { 
                    detail: { prefersDark: e.matches } 
                }));
            });
        }
    }

    /**
     * Apply theme to iframe (for preview)
     * @param {HTMLIFrameElement} iframe - Target iframe
     * @param {Object} theme - Theme to apply
     */
    applyThemeToIframe(iframe, theme) {
        if (!iframe || !iframe.contentDocument) {
            console.error('Invalid iframe');
            return;
        }

        const iframeDoc = iframe.contentDocument;
        let styleElement = iframeDoc.getElementById('preview-theme-variables');
        
        if (!styleElement) {
            styleElement = iframeDoc.createElement('style');
            styleElement.id = 'preview-theme-variables';
            iframeDoc.head.appendChild(styleElement);
        }

        // Build CSS for iframe
        let cssText = ':root {\n';
        for (const [variable, value] of Object.entries(theme.css_variables)) {
            cssText += `    ${variable}: ${value};\n`;
        }
        cssText += '}';

        styleElement.textContent = cssText;
    }
}

// Create global theme engine instance
window.themeEngine = new ThemeEngine();

// Utility functions for theme management
window.ThemeUtils = {
    /**
     * Convert hex color to RGB
     */
    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    },

    /**
     * Convert RGB to hex
     */
    rgbToHex(r, g, b) {
        return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
    },

    /**
     * Lighten a color
     */
    lightenColor(color, percent) {
        const rgb = this.hexToRgb(color);
        if (!rgb) return color;

        const factor = percent / 100;
        const r = Math.round(rgb.r + (255 - rgb.r) * factor);
        const g = Math.round(rgb.g + (255 - rgb.g) * factor);
        const b = Math.round(rgb.b + (255 - rgb.b) * factor);

        return this.rgbToHex(r, g, b);
    },

    /**
     * Darken a color
     */
    darkenColor(color, percent) {
        const rgb = this.hexToRgb(color);
        if (!rgb) return color;

        const factor = percent / 100;
        const r = Math.round(rgb.r * (1 - factor));
        const g = Math.round(rgb.g * (1 - factor));
        const b = Math.round(rgb.b * (1 - factor));

        return this.rgbToHex(r, g, b);
    },

    /**
     * Check if color is light or dark
     */
    isColorLight(color) {
        const rgb = this.hexToRgb(color);
        if (!rgb) return true;

        // Calculate luminance
        const luminance = (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b) / 255;
        return luminance > 0.5;
    },

    /**
     * Get contrasting text color
     */
    getContrastColor(backgroundColor) {
        return this.isColorLight(backgroundColor) ? '#000000' : '#ffffff';
    }
};