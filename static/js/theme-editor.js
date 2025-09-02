/**
 * Theme Editor - UI components for theme customization
 * Provides interactive controls for creating and editing themes
 * 
 * Created by: Team Gamma (Gabriel & Grace)
 * Date: 2025-01-02
 */

class ThemeEditor {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.currentThemeData = null;
        this.isPreviewMode = false;
        this.originalTheme = null;
        this.apiBaseUrl = '/api/v1';
        this.csrfToken = this.getCsrfToken();
        
        if (this.container) {
            this.init();
        }
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
     * Initialize the theme editor
     */
    init() {
        this.render();
        this.attachEventListeners();
        this.loadCurrentTheme();
    }

    /**
     * Render the theme editor UI
     */
    render() {
        this.container.innerHTML = `
            <div class="theme-editor-wrapper">
                <div class="theme-editor-header">
                    <h3>Theme Customization</h3>
                    <div class="theme-actions">
                        <button class="btn btn-sm btn-secondary" id="theme-reset">Reset</button>
                        <button class="btn btn-sm btn-primary" id="theme-save">Save Theme</button>
                    </div>
                </div>

                <div class="theme-editor-tabs">
                    <ul class="nav nav-tabs" role="tablist">
                        <li class="nav-item">
                            <a class="nav-link active" data-bs-toggle="tab" href="#colors-tab">Colors</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" data-bs-toggle="tab" href="#typography-tab">Typography</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" data-bs-toggle="tab" href="#spacing-tab">Spacing</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" data-bs-toggle="tab" href="#components-tab">Components</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" data-bs-toggle="tab" href="#presets-tab">Presets</a>
                        </li>
                    </ul>
                </div>

                <div class="tab-content theme-editor-content">
                    <div class="tab-pane fade show active" id="colors-tab">
                        ${this.renderColorsTab()}
                    </div>
                    <div class="tab-pane fade" id="typography-tab">
                        ${this.renderTypographyTab()}
                    </div>
                    <div class="tab-pane fade" id="spacing-tab">
                        ${this.renderSpacingTab()}
                    </div>
                    <div class="tab-pane fade" id="components-tab">
                        ${this.renderComponentsTab()}
                    </div>
                    <div class="tab-pane fade" id="presets-tab">
                        ${this.renderPresetsTab()}
                    </div>
                </div>

                <div class="theme-editor-footer">
                    <div class="preview-toggle">
                        <label class="form-check-label">
                            <input type="checkbox" class="form-check-input" id="preview-mode">
                            Live Preview
                        </label>
                    </div>
                    <div class="theme-info">
                        <small class="text-muted">Changes are applied in real-time when preview is enabled</small>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Render colors tab
     */
    renderColorsTab() {
        return `
            <div class="color-groups">
                <div class="color-group">
                    <h5>Primary Colors</h5>
                    <div class="color-controls">
                        ${this.renderColorInput('primary', 'Primary', '#0d6efd')}
                        ${this.renderColorInput('secondary', 'Secondary', '#6c757d')}
                        ${this.renderColorInput('success', 'Success', '#198754')}
                        ${this.renderColorInput('danger', 'Danger', '#dc3545')}
                        ${this.renderColorInput('warning', 'Warning', '#ffc107')}
                        ${this.renderColorInput('info', 'Info', '#0dcaf0')}
                    </div>
                </div>

                <div class="color-group">
                    <h5>Neutral Colors</h5>
                    <div class="color-controls">
                        ${this.renderColorInput('light', 'Light', '#f8f9fa')}
                        ${this.renderColorInput('dark', 'Dark', '#212529')}
                        ${this.renderColorInput('background', 'Background', '#ffffff')}
                        ${this.renderColorInput('surface', 'Surface', '#f5f5f5')}
                        ${this.renderColorInput('border', 'Border', '#dee2e6')}
                    </div>
                </div>

                <div class="color-group">
                    <h5>Text Colors</h5>
                    <div class="color-controls">
                        ${this.renderColorInput('text-primary', 'Primary Text', '#212529')}
                        ${this.renderColorInput('text-secondary', 'Secondary Text', '#6c757d')}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Render a color input control
     */
    renderColorInput(id, label, defaultValue) {
        return `
            <div class="color-control">
                <label for="color-${id}">${label}</label>
                <div class="color-input-group">
                    <input type="color" 
                           class="form-control form-control-color" 
                           id="color-${id}" 
                           data-color-key="${id}"
                           value="${defaultValue}">
                    <input type="text" 
                           class="form-control form-control-sm color-hex" 
                           id="color-${id}-hex" 
                           data-color-key="${id}"
                           value="${defaultValue}">
                </div>
            </div>
        `;
    }

    /**
     * Render typography tab
     */
    renderTypographyTab() {
        return `
            <div class="typography-controls">
                <div class="form-group">
                    <label for="font-family-base">Base Font Family</label>
                    <select class="form-control" id="font-family-base" data-typography-key="font-family-base">
                        <option value="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif">System Default</option>
                        <option value="'Inter', sans-serif">Inter</option>
                        <option value="'Roboto', sans-serif">Roboto</option>
                        <option value="'Open Sans', sans-serif">Open Sans</option>
                        <option value="'Lato', sans-serif">Lato</option>
                        <option value="'Poppins', sans-serif">Poppins</option>
                        <option value="'Montserrat', sans-serif">Montserrat</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="font-size-base">Base Font Size</label>
                    <div class="input-group">
                        <input type="number" 
                               class="form-control" 
                               id="font-size-base" 
                               data-typography-key="font-size-base"
                               min="12" max="24" step="1" value="16">
                        <span class="input-group-text">px</span>
                    </div>
                </div>

                <div class="form-group">
                    <label for="line-height-base">Line Height</label>
                    <input type="number" 
                           class="form-control" 
                           id="line-height-base" 
                           data-typography-key="line-height-base"
                           min="1" max="2" step="0.1" value="1.5">
                </div>

                <div class="form-group">
                    <label for="headings-font-family">Headings Font Family</label>
                    <select class="form-control" id="headings-font-family" data-typography-key="headings-font-family">
                        <option value="inherit">Same as body</option>
                        <option value="'Poppins', sans-serif">Poppins</option>
                        <option value="'Playfair Display', serif">Playfair Display</option>
                        <option value="'Montserrat', sans-serif">Montserrat</option>
                        <option value="'Raleway', sans-serif">Raleway</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="headings-font-weight">Headings Font Weight</label>
                    <select class="form-control" id="headings-font-weight" data-typography-key="headings-font-weight">
                        <option value="300">Light (300)</option>
                        <option value="400">Regular (400)</option>
                        <option value="500" selected>Medium (500)</option>
                        <option value="600">Semi Bold (600)</option>
                        <option value="700">Bold (700)</option>
                    </select>
                </div>
            </div>
        `;
    }

    /**
     * Render spacing tab
     */
    renderSpacingTab() {
        return `
            <div class="spacing-controls">
                <div class="form-group">
                    <label for="spacer">Base Spacer</label>
                    <div class="input-group">
                        <input type="number" 
                               class="form-control" 
                               id="spacer" 
                               data-spacing-key="spacer"
                               min="0.5" max="2" step="0.25" value="1">
                        <span class="input-group-text">rem</span>
                    </div>
                    <small class="form-text text-muted">All spacing values are multiplied by this base value</small>
                </div>

                <div class="form-group">
                    <label for="container-padding">Container Padding</label>
                    <div class="input-group">
                        <input type="number" 
                               class="form-control" 
                               id="container-padding" 
                               data-spacing-key="container-padding"
                               min="0.5" max="3" step="0.25" value="1.5">
                        <span class="input-group-text">rem</span>
                    </div>
                </div>

                <div class="form-group">
                    <label for="grid-gutter">Grid Gutter Width</label>
                    <div class="input-group">
                        <input type="number" 
                               class="form-control" 
                               id="grid-gutter" 
                               data-spacing-key="grid-gutter"
                               min="0.5" max="3" step="0.25" value="1.5">
                        <span class="input-group-text">rem</span>
                    </div>
                </div>

                <div class="border-controls mt-4">
                    <h5>Borders</h5>
                    <div class="form-group">
                        <label for="border-radius">Border Radius</label>
                        <div class="input-group">
                            <input type="number" 
                                   class="form-control" 
                                   id="border-radius" 
                                   data-border-key="radius"
                                   min="0" max="2" step="0.125" value="0.375">
                            <span class="input-group-text">rem</span>
                        </div>
                    </div>

                    <div class="form-group">
                        <label for="border-width">Border Width</label>
                        <div class="input-group">
                            <input type="number" 
                                   class="form-control" 
                                   id="border-width" 
                                   data-border-key="width"
                                   min="0" max="5" step="1" value="1">
                            <span class="input-group-text">px</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Render components tab
     */
    renderComponentsTab() {
        return `
            <div class="component-controls">
                <div class="component-group">
                    <h5>Cards</h5>
                    <div class="form-group">
                        <label for="card-bg">Background Color</label>
                        <input type="color" 
                               class="form-control form-control-color" 
                               id="card-bg" 
                               data-component="card"
                               data-component-key="bg"
                               value="#ffffff">
                    </div>
                    <div class="form-group">
                        <label for="card-border-radius">Border Radius</label>
                        <div class="input-group">
                            <input type="number" 
                                   class="form-control" 
                                   id="card-border-radius" 
                                   data-component="card"
                                   data-component-key="border-radius"
                                   min="0" max="2" step="0.125" value="0.375">
                            <span class="input-group-text">rem</span>
                        </div>
                    </div>
                </div>

                <div class="component-group">
                    <h5>Buttons</h5>
                    <div class="form-group">
                        <label for="button-padding-x">Horizontal Padding</label>
                        <div class="input-group">
                            <input type="number" 
                                   class="form-control" 
                                   id="button-padding-x" 
                                   data-component="button"
                                   data-component-key="padding-x"
                                   min="0.25" max="2" step="0.125" value="0.75">
                            <span class="input-group-text">rem</span>
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="button-padding-y">Vertical Padding</label>
                        <div class="input-group">
                            <input type="number" 
                                   class="form-control" 
                                   id="button-padding-y" 
                                   data-component="button"
                                   data-component-key="padding-y"
                                   min="0.25" max="1" step="0.125" value="0.375">
                            <span class="input-group-text">rem</span>
                        </div>
                    </div>
                </div>

                <div class="component-group">
                    <h5>Forms</h5>
                    <div class="form-group">
                        <label for="input-border-radius">Input Border Radius</label>
                        <div class="input-group">
                            <input type="number" 
                                   class="form-control" 
                                   id="input-border-radius" 
                                   data-component="input"
                                   data-component-key="border-radius"
                                   min="0" max="2" step="0.125" value="0.375">
                            <span class="input-group-text">rem</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Render presets tab
     */
    renderPresetsTab() {
        return `
            <div class="theme-presets">
                <div class="preset-grid" id="preset-grid">
                    <div class="text-center p-4">
                        <div class="spinner-border" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Color inputs
        this.container.querySelectorAll('input[type="color"]').forEach(input => {
            input.addEventListener('change', (e) => this.handleColorChange(e));
        });

        // Color hex inputs
        this.container.querySelectorAll('.color-hex').forEach(input => {
            input.addEventListener('change', (e) => this.handleColorHexChange(e));
        });

        // Typography controls
        this.container.querySelectorAll('[data-typography-key]').forEach(input => {
            input.addEventListener('change', (e) => this.handleTypographyChange(e));
        });

        // Spacing controls
        this.container.querySelectorAll('[data-spacing-key]').forEach(input => {
            input.addEventListener('change', (e) => this.handleSpacingChange(e));
        });

        // Border controls
        this.container.querySelectorAll('[data-border-key]').forEach(input => {
            input.addEventListener('change', (e) => this.handleBorderChange(e));
        });

        // Component controls
        this.container.querySelectorAll('[data-component]').forEach(input => {
            input.addEventListener('change', (e) => this.handleComponentChange(e));
        });

        // Preview toggle
        const previewToggle = this.container.querySelector('#preview-mode');
        if (previewToggle) {
            previewToggle.addEventListener('change', (e) => this.togglePreview(e.target.checked));
        }

        // Save button
        const saveButton = this.container.querySelector('#theme-save');
        if (saveButton) {
            saveButton.addEventListener('click', () => this.saveTheme());
        }

        // Reset button
        const resetButton = this.container.querySelector('#theme-reset');
        if (resetButton) {
            resetButton.addEventListener('click', () => this.resetTheme());
        }

        // Load presets when tab is shown
        const presetsTab = this.container.querySelector('a[href="#presets-tab"]');
        if (presetsTab) {
            presetsTab.addEventListener('shown.bs.tab', () => this.loadPresets());
        }
    }

    /**
     * Handle color change
     */
    handleColorChange(event) {
        const colorKey = event.target.dataset.colorKey;
        const value = event.target.value;

        // Update hex input
        const hexInput = this.container.querySelector(`#color-${colorKey}-hex`);
        if (hexInput) {
            hexInput.value = value;
        }

        this.updateThemeData('colors', colorKey, value);
    }

    /**
     * Handle color hex input change
     */
    handleColorHexChange(event) {
        const colorKey = event.target.dataset.colorKey;
        let value = event.target.value;

        // Validate hex color
        if (!/^#[0-9A-F]{6}$/i.test(value)) {
            if (!/^#/.test(value)) {
                value = '#' + value;
            }
            if (!/^#[0-9A-F]{6}$/i.test(value)) {
                event.target.classList.add('is-invalid');
                return;
            }
        }

        event.target.classList.remove('is-invalid');

        // Update color picker
        const colorPicker = this.container.querySelector(`#color-${colorKey}`);
        if (colorPicker) {
            colorPicker.value = value;
        }

        this.updateThemeData('colors', colorKey, value);
    }

    /**
     * Handle typography change
     */
    handleTypographyChange(event) {
        const key = event.target.dataset.typographyKey;
        let value = event.target.value;

        if (event.target.id === 'font-size-base') {
            value = value + 'px';
        }

        this.updateThemeData('typography', key, value);
    }

    /**
     * Handle spacing change
     */
    handleSpacingChange(event) {
        const key = event.target.dataset.spacingKey;
        const value = event.target.value + 'rem';

        this.updateThemeData('spacing', key, value);
    }

    /**
     * Handle border change
     */
    handleBorderChange(event) {
        const key = event.target.dataset.borderKey;
        let value = event.target.value;

        if (key === 'radius') {
            value = value + 'rem';
        } else if (key === 'width') {
            value = value + 'px';
        }

        this.updateThemeData('borders', key, value);
    }

    /**
     * Handle component change
     */
    handleComponentChange(event) {
        const component = event.target.dataset.component;
        const key = event.target.dataset.componentKey;
        let value = event.target.value;

        if (key.includes('padding') || key.includes('radius')) {
            value = value + 'rem';
        }

        if (!this.currentThemeData.components) {
            this.currentThemeData.components = {};
        }
        if (!this.currentThemeData.components[component]) {
            this.currentThemeData.components[component] = {};
        }

        this.currentThemeData.components[component][key] = value;

        if (this.isPreviewMode) {
            this.applyPreview();
        }
    }

    /**
     * Update theme data
     */
    updateThemeData(section, key, value) {
        if (!this.currentThemeData) {
            this.currentThemeData = this.getDefaultThemeData();
        }

        if (!this.currentThemeData[section]) {
            this.currentThemeData[section] = {};
        }

        this.currentThemeData[section][key] = value;

        if (this.isPreviewMode) {
            this.applyPreview();
        }
    }

    /**
     * Get default theme data structure
     */
    getDefaultThemeData() {
        return {
            colors: {},
            typography: {},
            spacing: {},
            borders: {},
            shadows: {},
            components: {}
        };
    }

    /**
     * Toggle preview mode
     */
    togglePreview(enabled) {
        this.isPreviewMode = enabled;

        if (enabled) {
            if (!this.originalTheme) {
                this.originalTheme = window.themeEngine.getCurrentTheme();
            }
            this.applyPreview();
        } else {
            // Restore original theme
            if (this.originalTheme) {
                window.themeEngine.applyTheme(this.originalTheme);
            }
        }
    }

    /**
     * Apply preview
     */
    async applyPreview() {
        if (!this.currentThemeData) return;

        const result = await window.themeEngine.previewTheme(this.currentThemeData);
        if (!result.success) {
            this.showError(result.error);
        }
    }

    /**
     * Load current theme
     */
    async loadCurrentTheme() {
        try {
            const theme = window.themeEngine.getCurrentTheme();
            if (theme && theme.theme_data) {
                this.currentThemeData = theme.theme_data;
                this.populateControls();
            } else {
                this.currentThemeData = this.getDefaultThemeData();
            }
        } catch (error) {
            console.error('Error loading current theme:', error);
        }
    }

    /**
     * Populate controls with current theme data
     */
    populateControls() {
        if (!this.currentThemeData) return;

        // Colors
        if (this.currentThemeData.colors) {
            Object.entries(this.currentThemeData.colors).forEach(([key, value]) => {
                const colorInput = this.container.querySelector(`#color-${key}`);
                const hexInput = this.container.querySelector(`#color-${key}-hex`);
                if (colorInput) colorInput.value = value;
                if (hexInput) hexInput.value = value;
            });
        }

        // Typography
        if (this.currentThemeData.typography) {
            Object.entries(this.currentThemeData.typography).forEach(([key, value]) => {
                const input = this.container.querySelector(`[data-typography-key="${key}"]`);
                if (input) {
                    if (key === 'font-size-base') {
                        input.value = parseInt(value);
                    } else {
                        input.value = value;
                    }
                }
            });
        }

        // Add similar population for spacing, borders, and components
    }

    /**
     * Save theme
     */
    async saveTheme() {
        const themeName = prompt('Enter a name for your theme:');
        if (!themeName) return;

        try {
            const response = await fetch(`${this.apiBaseUrl}/themes/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: themeName,
                    theme_data: this.currentThemeData,
                    category: 'custom'
                })
            });

            if (response.ok) {
                const theme = await response.json();
                this.showSuccess('Theme saved successfully!');
                
                // Activate the new theme
                await window.themeEngine.switchTheme(theme.id);
            } else {
                const error = await response.json();
                this.showError(error.detail || 'Failed to save theme');
            }
        } catch (error) {
            console.error('Error saving theme:', error);
            this.showError('Error saving theme');
        }
    }

    /**
     * Reset theme
     */
    resetTheme() {
        if (confirm('Are you sure you want to reset all changes?')) {
            this.loadCurrentTheme();
            if (this.isPreviewMode && this.originalTheme) {
                window.themeEngine.applyTheme(this.originalTheme);
            }
        }
    }

    /**
     * Load theme presets
     */
    async loadPresets() {
        const presetGrid = this.container.querySelector('#preset-grid');
        if (!presetGrid) return;

        try {
            const response = await fetch(`${this.apiBaseUrl}/theme-templates/`, {
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const templates = await response.json();
                presetGrid.innerHTML = templates.map(template => `
                    <div class="preset-card" data-template-id="${template.id}">
                        <div class="preset-preview" style="background: linear-gradient(135deg, ${template.theme_data.colors?.primary || '#0d6efd'}, ${template.theme_data.colors?.secondary || '#6c757d'})">
                            <div class="preset-colors">
                                ${Object.entries(template.theme_data.colors || {}).slice(0, 6).map(([key, color]) => 
                                    `<span class="color-swatch" style="background-color: ${color}" title="${key}"></span>`
                                ).join('')}
                            </div>
                        </div>
                        <div class="preset-info">
                            <h6>${template.name}</h6>
                            <p class="text-muted small mb-2">${template.description}</p>
                            <button class="btn btn-sm btn-primary use-preset" data-template-id="${template.id}">
                                Use This Theme
                            </button>
                        </div>
                    </div>
                `).join('');

                // Attach preset click handlers
                presetGrid.querySelectorAll('.use-preset').forEach(btn => {
                    btn.addEventListener('click', (e) => this.usePreset(e.target.dataset.templateId));
                });
            }
        } catch (error) {
            console.error('Error loading presets:', error);
            presetGrid.innerHTML = '<p class="text-danger">Error loading theme presets</p>';
        }
    }

    /**
     * Use a preset template
     */
    async usePreset(templateId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/theme-templates/${templateId}/use_template/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: prompt('Enter a name for your theme:', 'My Custom Theme')
                })
            });

            if (response.ok) {
                const theme = await response.json();
                this.showSuccess('Theme created from template!');
                
                // Load and activate the new theme
                await window.themeEngine.switchTheme(theme.id);
                this.loadCurrentTheme();
            } else {
                const error = await response.json();
                this.showError(error.detail || 'Failed to create theme from template');
            }
        } catch (error) {
            console.error('Error using preset:', error);
            this.showError('Error creating theme from template');
        }
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        // You can implement a toast notification here
        alert(message);
    }

    /**
     * Show error message
     */
    showError(message) {
        // You can implement a toast notification here
        alert('Error: ' + message);
    }
}

// Initialize theme editor when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('theme-editor')) {
        window.themeEditor = new ThemeEditor('theme-editor');
    }
});