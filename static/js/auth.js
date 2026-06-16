// ============================================
// AUTHENTICATION WITH DATABASE BACKEND
// ============================================

const API_BASE = '/api';

// Check if user is authenticated on page load
document.addEventListener('DOMContentLoaded', function() {
    checkAuthentication();
    setupAuthForms();
});

// ============================================
// AUTHENTICATION CHECK
// ============================================

async function checkAuthentication() {
    try {
        const response = await fetch(`${API_BASE}/auth/check`);
        const data = await response.json();
        
        if (data.authenticated) {
            // User is logged in
            const currentPage = window.location.pathname;
            if (currentPage === '/login' || currentPage === '/register') {
                // Redirect to home if already logged in
                window.location.href = '/';
            }
        } else {
            // User is not logged in
            const currentPage = window.location.pathname;
            if (currentPage === '/') {
                // Uncomment to force login redirect
                // window.location.href = '/login';
            }
        }
    } catch (error) {
        console.log('Auth check error:', error);
    }
}

// ============================================
// FORM SETUP
// ============================================

function setupAuthForms() {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
        
        const regPassword = document.getElementById('regPassword');
        if (regPassword) {
            regPassword.addEventListener('input', updatePasswordStrength);
        }
    }
}

// ============================================
// LOGIN
// ============================================

async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const errorMsg = document.getElementById('errorMsg');
    
    if (!username || !password) {
        showError('Please enter username and password', errorMsg);
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Store user info in localStorage (optional, for UI state)
            localStorage.setItem('user', JSON.stringify(data.user));
            
            // Redirect to home
            window.location.href = '/';
        } else {
            showError(data.error || 'Login failed', errorMsg);
        }
    } catch (error) {
        showError(`Error: ${error.message}`, errorMsg);
    }
}

// ============================================
// REGISTER
// ============================================

async function handleRegister(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('regPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const terms = document.querySelector('input[name="terms"]').checked;
    const errorMsg = document.getElementById('errorMsg');
    
    // Validation
    if (!username || !email || !password) {
        showError('Please fill in all fields', errorMsg);
        return;
    }
    
    if (username.length < 3) {
        showError('Username must be at least 3 characters', errorMsg);
        return;
    }
    
    if (password.length < 6) {
        showError('Password must be at least 6 characters', errorMsg);
        return;
    }
    
    if (password !== confirmPassword) {
        showError('Passwords do not match', errorMsg);
        return;
    }
    
    if (!terms) {
        showError('You must accept the terms and conditions', errorMsg);
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                email: email,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Show success message
            showSuccess('Account created! Redirecting to login...', errorMsg);
            
            // Redirect to login after 2 seconds
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
        } else {
            showError(data.error || 'Registration failed', errorMsg);
        }
    } catch (error) {
        showError(`Error: ${error.message}`, errorMsg);
    }
}

// ============================================
// LOGOUT
// ============================================

async function logoutFunc() {
    try {
        const response = await fetch(`${API_BASE}/auth/logout`, {
            method: 'POST'
        });
        
        if (response.ok) {
            // Clear localStorage
            localStorage.removeItem('user');
            
            // Redirect to login
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Logout error:', error);
        // Force logout anyway
        localStorage.removeItem('user');
        window.location.href = '/login';
    }
}

// ============================================
// PASSWORD STRENGTH
// ============================================

function updatePasswordStrength() {
    const password = document.getElementById('regPassword').value;
    const strengthBar = document.getElementById('strengthBar');
    const strengthText = document.getElementById('strengthText');
    
    if (!strengthBar || !strengthText) return;
    
    let strength = 0;
    let text = '';
    
    if (password.length >= 6) strength += 20;
    if (password.length >= 10) strength += 20;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength += 20;
    if (/\d/.test(password)) strength += 20;
    if (/[^a-zA-Z0-9]/.test(password)) strength += 20;
    
    if (strength < 20) {
        text = 'Weak password';
        strengthBar.style.width = '20%';
        strengthBar.style.backgroundColor = '#dc2626';
    } else if (strength < 40) {
        text = 'Fair password';
        strengthBar.style.width = '40%';
        strengthBar.style.backgroundColor = '#f59e0b';
    } else if (strength < 60) {
        text = 'Good password';
        strengthBar.style.width = '60%';
        strengthBar.style.backgroundColor = '#eab308';
    } else if (strength < 80) {
        text = 'Strong password';
        strengthBar.style.width = '80%';
        strengthBar.style.backgroundColor = '#84cc16';
    } else {
        text = 'Very strong password';
        strengthBar.style.width = '100%';
        strengthBar.style.backgroundColor = '#22c55e';
    }
    
    strengthText.textContent = text;
}

// ============================================
// ERROR/SUCCESS MESSAGES
// ============================================

function showError(message, element) {
    if (!element) {
        element = document.getElementById('errorMsg');
    }
    
    if (element) {
        element.textContent = message;
        element.classList.remove('hidden');
        element.className = 'error-message';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            element.classList.add('hidden');
        }, 5000);
    }
}

function showSuccess(message, element) {
    if (!element) {
        element = document.getElementById('errorMsg');
    }
    
    if (element) {
        element.textContent = message;
        element.classList.remove('hidden');
        element.className = 'success-message';
    }
}
