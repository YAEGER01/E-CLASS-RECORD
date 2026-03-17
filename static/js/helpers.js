// helpers.js
    // Small reusable UI helpers used by main.js

    export function smoothScrollToHashLinks() {
      document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
          const href = this.getAttribute('href');
          if (!href || href === '#') return;
          const target = document.querySelector(href);
          if (!target) return;
          e.preventDefault();
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
      });
    }

    export function fadeInBodyOnLoad() {
      window.addEventListener('load', () => {
        document.body.style.opacity = '0';
        document.body.style.transition = 'opacity 0.6s ease-in-out';
        setTimeout(() => {
          document.body.style.opacity = '1';
        }, 120);
      });
    }

    export function applyParallax(selector = '.hero-graphic', intensity = 0.18) {
      window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        const heroGraphic = document.querySelector(selector);
        if (heroGraphic) {
          heroGraphic.style.transform = `translateY(${scrolled * intensity}px)`;
        }
      });
    }

    export function simpleTypeReveal(selector = '.hero-text h1') {
      setTimeout(() => {
        const el = document.querySelector(selector);
        if (!el) return;
        if (!el.classList.contains('typed')) {
          el.style.opacity = '0';
          setTimeout(() => {
            el.style.opacity = '1';
            el.classList.add('typed');
          }, 360);
        }
      }, 700);
    }
