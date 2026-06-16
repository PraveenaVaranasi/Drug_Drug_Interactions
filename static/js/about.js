// ============================================
// ABOUT PAGE INTERACTIONS
// ============================================

const API_BASE = '/api';

// Logout Function
async function logoutFunc() {
    try {
        const response = await fetch(`${API_BASE}/auth/logout`, {
            method: 'POST'
        });
        
        // Clear localStorage and redirect regardless of response
        localStorage.removeItem('user');
        window.location.href = '/login';
    } catch (error) {
        console.error('Logout error:', error);
        localStorage.removeItem('user');
        window.location.href = '/login';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    setupFAQ();
    setupScrollAnimations();
});

function setupFAQ() {
    const faqItems = document.querySelectorAll('.faq-item');
    
    faqItems.forEach(item => {
        const heading = item.querySelector('h4');
        heading.addEventListener('click', function() {
            item.classList.toggle('active');
        });
    });
}

function setupScrollAnimations() {
    // Animate cards on scroll
    const cards = document.querySelectorAll('.about-card, .team-member, .tech-item');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animation = 'slideIn 0.5s ease-out';
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1
    });

    cards.forEach(card => observer.observe(card));
}

// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
