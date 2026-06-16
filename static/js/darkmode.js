// ============================================
// DARK MODE TOGGLE
// ============================================

// Initialize dark mode on page load
document.addEventListener('DOMContentLoaded', function() {
    initDarkMode();
});

function initDarkMode() {
    // Check if user has saved preference
    const savedMode = localStorage.getItem('darkMode');
    
    // Check system preference
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Determine if dark mode should be on
    const isDarkMode = savedMode ? JSON.parse(savedMode) : prefersDark;
    
    // Apply the mode
    setDarkMode(isDarkMode);
    
    // Setup toggle button listener
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', toggleDarkMode);
    }
}

function setDarkMode(isDark) {
    const html = document.documentElement;
    
    if (isDark) {
        html.classList.add('dark-mode');
        localStorage.setItem('darkMode', 'true');
        updateToggleButton(true);
    } else {
        html.classList.remove('dark-mode');
        localStorage.setItem('darkMode', 'false');
        updateToggleButton(false);
    }
}

function toggleDarkMode() {
    const html = document.documentElement;
    const isDarkMode = html.classList.contains('dark-mode');
    setDarkMode(!isDarkMode);
}

function updateToggleButton(isDark) {
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        if (isDark) {
            darkModeToggle.innerHTML = '☀️';
            darkModeToggle.title = 'Switch to Light Mode';
        } else {
            darkModeToggle.innerHTML = '🌙';
            darkModeToggle.title = 'Switch to Dark Mode';
        }
    }
}
