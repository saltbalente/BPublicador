// ===== AUTOPUBLICADOR WEB - MAIN JAVASCRIPT =====

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    initScrollToTop();
    initReadingProgress();
    initMobileMenu();
    initSearch();
    initSmoothScrolling();
    initLazyLoading();
    initTooltips();
    initAnimations();
});

// ===== SCROLL TO TOP =====
function initScrollToTop() {
    const scrollToTopBtn = document.getElementById('scrollToTop');
    
    if (!scrollToTopBtn) return;
    
    // Mostrar/ocultar botón según scroll
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            scrollToTopBtn.classList.add('visible');
        } else {
            scrollToTopBtn.classList.remove('visible');
        }
    });
    
    // Funcionalidad del botón
    scrollToTopBtn.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// ===== BARRA DE PROGRESO DE LECTURA =====
function initReadingProgress() {
    const progressBar = document.getElementById('readingProgress');
    
    if (!progressBar) return;
    
    window.addEventListener('scroll', function() {
        const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
        const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        const scrolled = (winScroll / height) * 100;
        
        progressBar.style.width = scrolled + '%';
    });
}

// ===== MENÚ MÓVIL =====
function initMobileMenu() {
    const mobileToggle = document.querySelector('.mobile-menu-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (!mobileToggle || !navMenu) return;
    
    mobileToggle.addEventListener('click', function() {
        navMenu.classList.toggle('active');
        mobileToggle.classList.toggle('active');
        
        // Cambiar icono
        const icon = mobileToggle.querySelector('svg');
        if (navMenu.classList.contains('active')) {
            icon.innerHTML = '<path d="M6 18L18 6M6 6l12 12"/>';
        } else {
            icon.innerHTML = '<path d="M3 12h18M3 6h18M3 18h18"/>';
        }
    });
    
    // Cerrar menú al hacer clic en un enlace
    const navLinks = navMenu.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            navMenu.classList.remove('active');
            mobileToggle.classList.remove('active');
        });
    });
}

// ===== FUNCIONALIDAD DE BÚSQUEDA =====
function initSearch() {
    const searchForm = document.querySelector('.search-form');
    const searchInput = document.querySelector('.search-input');
    const searchButton = document.querySelector('.search-button');
    
    if (!searchForm || !searchInput) return;
    
    // Envío del formulario
    searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const query = searchInput.value.trim();
        
        if (query) {
            window.location.href = `/buscar?q=${encodeURIComponent(query)}`;
        }
    });
    
    // Búsqueda con Enter
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            searchForm.dispatchEvent(new Event('submit'));
        }
    });
    
    // Autocompletado simple (opcional)
    let searchTimeout;
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (query.length >= 2) {
            searchTimeout = setTimeout(() => {
                // Aquí se podría implementar autocompletado
                // fetchSearchSuggestions(query);
            }, 300);
        }
    });
}

// ===== SCROLL SUAVE =====
function initSmoothScrolling() {
    // Enlaces internos con scroll suave
    const internalLinks = document.querySelectorAll('a[href^="#"]');
    
    internalLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            
            if (href === '#') {
                e.preventDefault();
                window.scrollTo({ top: 0, behavior: 'smooth' });
                return;
            }
            
            const target = document.querySelector(href);
            if (target) {
                e.preventDefault();
                const offsetTop = target.offsetTop - 80; // Ajuste para header fijo
                
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// ===== LAZY LOADING DE IMÁGENES =====
function initLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    
    if (!images.length) return;
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                img.classList.add('loaded');
                observer.unobserve(img);
            }
        });
    });
    
    images.forEach(img => {
        img.classList.add('lazy');
        imageObserver.observe(img);
    });
}

// ===== TOOLTIPS =====
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(e) {
    const text = e.target.getAttribute('data-tooltip');
    if (!text) return;
    
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = text;
    
    document.body.appendChild(tooltip);
    
    const rect = e.target.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';
    
    setTimeout(() => tooltip.classList.add('visible'), 10);
}

function hideTooltip() {
    const tooltip = document.querySelector('.tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// ===== ANIMACIONES =====
function initAnimations() {
    // Animaciones al hacer scroll
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    
    if (!animatedElements.length) return;
    
    const animationObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    animatedElements.forEach(element => {
        animationObserver.observe(element);
    });
}

// ===== UTILIDADES =====

// Debounce function
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

// Throttle function
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Formatear fecha
function formatDate(date, format = 'dd/mm/yyyy') {
    const d = new Date(date);
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    
    switch (format) {
        case 'dd/mm/yyyy':
            return `${day}/${month}/${year}`;
        case 'mm/dd/yyyy':
            return `${month}/${day}/${year}`;
        case 'yyyy-mm-dd':
            return `${year}-${month}-${day}`;
        default:
            return `${day}/${month}/${year}`;
    }
}

// Truncar texto
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substr(0, maxLength) + '...';
}

// Escapar HTML
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

// Validar email
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Mostrar notificación
function showNotification(message, type = 'info', duration = 3000) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('visible');
    }, 10);
    
    setTimeout(() => {
        notification.classList.remove('visible');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, duration);
}

// ===== FUNCIONES ESPECÍFICAS PARA PÁGINAS =====

// Funcionalidad para página de archivo
function initArchivePage() {
    const viewToggle = document.querySelectorAll('.view-toggle');
    const postContainer = document.querySelector('.posts-container');
    
    if (!viewToggle.length || !postContainer) return;
    
    viewToggle.forEach(button => {
        button.addEventListener('click', function() {
            const view = this.dataset.view;
            
            // Actualizar botones activos
            viewToggle.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Cambiar vista
            postContainer.className = `posts-container posts-${view}`;
        });
    });
}

// Funcionalidad para página de búsqueda
function initSearchPage() {
    const searchForm = document.querySelector('.advanced-search-form');
    const sortSelect = document.querySelector('#sort');
    const categorySelect = document.querySelector('#category');
    
    if (!searchForm) return;
    
    // Auto-submit en cambios de filtros
    [sortSelect, categorySelect].forEach(select => {
        if (select) {
            select.addEventListener('change', function() {
                searchForm.submit();
            });
        }
    });
    
    // Limpiar filtros
    const clearFilters = document.querySelector('.clear-filters');
    if (clearFilters) {
        clearFilters.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Limpiar todos los campos
            searchForm.querySelectorAll('input, select').forEach(field => {
                if (field.type === 'text' || field.type === 'date') {
                    field.value = '';
                } else if (field.type === 'select-one') {
                    field.selectedIndex = 0;
                }
            });
            
            // Enviar formulario
            searchForm.submit();
        });
    }
}

// Funcionalidad para página 404
function init404Page() {
    // Efecto de escritura para el título
    const title = document.querySelector('.error-title');
    if (title) {
        const text = title.textContent;
        title.textContent = '';
        
        let i = 0;
        const typeWriter = () => {
            if (i < text.length) {
                title.textContent += text.charAt(i);
                i++;
                setTimeout(typeWriter, 100);
            }
        };
        
        setTimeout(typeWriter, 500);
    }
    
    // Animación de partículas de fondo (opcional)
    createParticles();
}

function createParticles() {
    const particlesContainer = document.querySelector('.particles-container');
    if (!particlesContainer) return;
    
    for (let i = 0; i < 50; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 2 + 's';
        particle.style.animationDuration = (Math.random() * 3 + 2) + 's';
        particlesContainer.appendChild(particle);
    }
}

// ===== EXPORTAR FUNCIONES GLOBALES =====
window.AutopublicadorWeb = {
    initArchivePage,
    initSearchPage,
    init404Page,
    showNotification,
    formatDate,
    truncateText,
    isValidEmail,
    debounce,
    throttle
};

// ===== CSS ADICIONAL PARA JAVASCRIPT =====
const additionalCSS = `
/* Estilos para lazy loading */
.lazy {
    opacity: 0;
    transition: opacity 0.3s;
}

.loaded {
    opacity: 1;
}

/* Estilos para tooltips */
.tooltip {
    position: absolute;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
    white-space: nowrap;
    opacity: 0;
    transition: opacity 0.3s;
    z-index: 1000;
    pointer-events: none;
}

.tooltip.visible {
    opacity: 1;
}

.tooltip::after {
    content: '';
    position: absolute;
    top: 100%;
    left: 50%;
    margin-left: -5px;
    border-width: 5px;
    border-style: solid;
    border-color: rgba(0, 0, 0, 0.8) transparent transparent transparent;
}

/* Estilos para notificaciones */
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    color: white;
    font-weight: 500;
    z-index: 1000;
    opacity: 0;
    transform: translateX(100%);
    transition: all 0.3s ease;
    max-width: 300px;
}

.notification.visible {
    opacity: 1;
    transform: translateX(0);
}

.notification-info {
    background: #3b82f6;
}

.notification-success {
    background: #10b981;
}

.notification-warning {
    background: #f59e0b;
}

.notification-error {
    background: #ef4444;
}

/* Animaciones */
.animate-on-scroll {
    opacity: 0;
    transform: translateY(20px);
    transition: all 0.6s ease;
}

.animate-on-scroll.animated {
    opacity: 1;
    transform: translateY(0);
}

/* Partículas para 404 */
.particles-container {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: -1;
}

.particle {
    position: absolute;
    width: 4px;
    height: 4px;
    background: rgba(107, 70, 193, 0.3);
    border-radius: 50%;
    animation: float 3s infinite ease-in-out;
}

@keyframes float {
    0%, 100% {
        transform: translateY(0) rotate(0deg);
        opacity: 1;
    }
    50% {
        transform: translateY(-20px) rotate(180deg);
        opacity: 0.5;
    }
}

/* Menú móvil activo */
@media (max-width: 768px) {
    .nav-menu {
        display: none;
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: white;
        border: 1px solid var(--border-color);
        border-top: none;
        box-shadow: var(--shadow-lg);
        padding: 1rem;
    }
    
    .nav-menu.active {
        display: flex;
    }
    
    .mobile-menu-toggle.active svg {
        transform: rotate(90deg);
    }
}
`;

// Inyectar CSS adicional
const style = document.createElement('style');
style.textContent = additionalCSS;
document.head.appendChild(style);

console.log('🚀 Autopublicador Web - JavaScript cargado correctamente');