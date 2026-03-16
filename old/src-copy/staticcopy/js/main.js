// main.js
    import { smoothScrollToHashLinks, fadeInBodyOnLoad, applyParallax, simpleTypeReveal } from './helpers.js';

    // Initialize UI helpers
    smoothScrollToHashLinks();
    fadeInBodyOnLoad();
    applyParallax('.hero-graphic', 0.18);
    simpleTypeReveal('.hero-text h1');

    // Feature card hover polish
    document.querySelectorAll('.feature-card').forEach(card => {
      card.addEventListener('mouseenter', function () {
        this.style.transform = 'translateY(-12px) scale(1.02)';
        this.style.transition = 'transform 220ms ease';
      });
      card.addEventListener('mouseleave', function () {
        this.style.transform = 'translateY(0) scale(1)';
      });
    });

    // Login form validation and mock auth flow
    const loginForm = document.querySelector('.login-form');
    if (loginForm) {
      loginForm.addEventListener('submit', function (e) {
        e.preventDefault();

        const userType = document.getElementById('userType').value.trim();
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;

        if (!userType || !username || !password) {
          window.alert('Please fill in all required fields.');
          return;
        }
        if (username.length < 3) {
          window.alert('Username must be at least 3 characters long.');
          return;
        }
        if (password.length < 6) {
          window.alert('Password must be at least 6 characters long.');
          return;
        }

        const btn = loginForm.querySelector('.login-btn');
        const originalText = btn.textContent;
        btn.textContent = 'Authenticating...';
        btn.disabled = true;

        // Simulate server validation
        setTimeout(() => {
          window.alert('Login successful. Redirecting to dashboard...');
          btn.textContent = originalText;
          btn.disabled = false;
          // In a real app, replace below with a real navigation:
          // window.location.href = '/dashboard';
        }, 1200);
      });
    }
