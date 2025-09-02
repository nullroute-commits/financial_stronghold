// Minimal theme helper for guest users and client-side toggle without FOUC
(function () {
    var THEME_KEY = 'ui_theme';
    function getStoredTheme() {
        try {
            var t = localStorage.getItem(THEME_KEY);
            if (t === 'light' || t === 'dark' || t === 'system' || t === 'high-contrast') return t;
        } catch (e) {}
        var cookie = document.cookie.split('; ').find(function (row) { return row.startsWith(THEME_KEY + '='); });
        if (cookie) {
            var v = cookie.split('=')[1];
            if (v === 'light' || v === 'dark' || v === 'system' || v === 'high-contrast') return v;
        }
        return null;
    }
    var theme = getStoredTheme();
    if (theme) {
        document.documentElement.setAttribute('data-theme', theme);
    }
})();

// Expose a minimal API for theme switching without dependencies
window.Theme = window.Theme || {
    set: function(theme){
        if(['light','dark','system','high-contrast'].indexOf(theme)===-1) return;
        try { localStorage.setItem('ui_theme', theme); } catch(e) {}
        document.cookie = 'ui_theme=' + theme + '; path=/; SameSite=Lax';
        document.documentElement.setAttribute('data-theme', theme);
    }
};

