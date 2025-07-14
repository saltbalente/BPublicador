// Autopublicador Web Dashboard - JavaScript

// Configuration
const API_BASE_URL = 'http://localhost:8001/api/v1';
let authToken = localStorage.getItem('authToken');
let currentUser = null;

// DOM Elements
let loginModal;
let registerModal;
let loadingSpinner;
let createContentModal;

// Initialize App
document.addEventListener('DOMContentLoaded', function() {
    // Initialize DOM elements
    loadingSpinner = document.getElementById('loadingSpinner');
    loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
    registerModal = new bootstrap.Modal(document.getElementById('registerModal'));
    
    if (authToken) {
        checkAuthAndLoadUser();
    } else {
        showLoginModal();
    }
    
    setupEventListeners();
    
    // Setup Bootstrap tab event listeners
    const creadorTab = document.getElementById('creador-tab');
    if (creadorTab) {
        creadorTab.addEventListener('shown.bs.tab', function (e) {
            loadCreadorSection();
        });
    }
    
    const temasTab = document.getElementById('temas-tab');
    if (temasTab) {
        temasTab.addEventListener('shown.bs.tab', function (e) {
            loadThemesAndTemplates();
        });
    }
    
    // Restore active section from localStorage or URL hash
    restoreActiveSection();
});

// Event Listeners
function setupEventListeners() {
    // Helper function to safely add event listeners
    function safeAddEventListener(elementId, event, handler) {
        const element = document.getElementById(elementId);
        if (element) {
            element.addEventListener(event, handler);
        } else {
            console.warn(`Element with id '${elementId}' not found`);
        }
    }
    
    // Login Form
    safeAddEventListener('loginForm', 'submit', handleLogin);
    
    // Register Form
    safeAddEventListener('registerForm', 'submit', handleRegister);
    
    // Keyword Form
    safeAddEventListener('keywordForm', 'submit', handleAddKeyword);
    
    // Image tab functionality removed - only preserving image modal for content editor
    
    // Content Form
    safeAddEventListener('createContentForm', 'submit', function(e) {
        e.preventDefault();
        saveContent();
    });
    
    // Content Status Change
    safeAddEventListener('contentStatus', 'change', function() {
        const scheduledGroup = document.getElementById('scheduledDateGroup');
        if (scheduledGroup && this.value === 'scheduled') {
            scheduledGroup.style.display = 'block';
        } else if (scheduledGroup) {
            scheduledGroup.style.display = 'none';
        }
    });
    
    // Auto-generate slug from title
    safeAddEventListener('contentTitle', 'input', function() {
        const slugField = document.getElementById('contentSlug');
        if (slugField && (!slugField.value || slugField.value === generateSlug(slugField.dataset.originalTitle || ''))) {
            slugField.value = generateSlug(this.value);
            slugField.dataset.originalTitle = this.value;
        }
    });
}

// Authentication Functions
async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login-json`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            authToken = data.access_token;
            localStorage.setItem('authToken', authToken);
            
            console.log('Login successful - token saved:', authToken ? 'EXISTS' : 'NULL');
            console.log('Login successful - localStorage check:', localStorage.getItem('authToken') ? 'EXISTS' : 'NULL');
            
            loginModal.hide();
            await loadUserData();
            showAlert('Inicio de sesión exitoso', 'success');
        } else {
            const error = await response.json();
            showAlert(error.detail || 'Error al iniciar sesión', 'danger');
        }
    } catch (error) {
        showAlert('Error de conexión', 'danger');
        console.error('Login error:', error);
    } finally {
        showLoading(false);
    }
}

async function handleRegister(e) {
    e.preventDefault();
    
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    const username = document.getElementById('regFullName').value;
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                password: password,
                username: username
            })
        });
        
        if (response.ok) {
            registerModal.hide();
            showAlert('Registro exitoso. Por favor inicia sesión.', 'success');
            document.getElementById('email').value = email;
        } else {
            const error = await response.json();
            showAlert(error.detail || 'Error al registrarse', 'danger');
        }
    } catch (error) {
        showAlert('Error de conexión', 'danger');
        console.error('Register error:', error);
    } finally {
        showLoading(false);
    }
}

async function checkAuthAndLoadUser() {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            currentUser = await response.json();
            await loadUserData();
        } else {
            logout();
        }
    } catch (error) {
        logout();
    }
}

function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    showLoginModal();
}

function showLoginModal() {
    loginModal.show();
}

function showRegisterForm() {
    loginModal.hide();
    registerModal.show();
}

// Data Loading Functions
async function loadUserData() {
    if (currentUser) {
        document.getElementById('username').textContent = currentUser.username || currentUser.email;
    }
    
    await loadDashboardData();
    
    // Check if there's a saved active section, otherwise default to dashboard
    const savedSection = localStorage.getItem('activeSection') || 'dashboard';
    showSection(savedSection);
}

async function loadDashboardData() {
    showLoading(true);
    
    try {
        // Load dashboard stats
        const statsResponse = await apiRequest('/analytics/dashboard');
        if (statsResponse) {
            updateDashboardStats(statsResponse);
        }
        
        // Load keywords
        await loadKeywords();
        
        // Load scheduler status
        await loadSchedulerStatus();
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showAlert('Error cargando datos del dashboard', 'warning');
    } finally {
        showLoading(false);
    }
}

function updateDashboardStats(stats) {
    // Dashboard stats cards removed - only visual configuration remains
    console.log('Dashboard stats loaded:', stats);
}

// Keywords Functions
async function loadKeywords() {
    try {
        const keywords = await apiRequest('/keywords/');
        if (keywords) {
            displayKeywords(keywords);
        }
    } catch (error) {
        console.error('Error loading keywords:', error);
    }
}

function displayKeywords(keywords) {
    const tbody = document.getElementById('keywordsTable');
    tbody.innerHTML = '';
    
    if (!keywords || keywords.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">No hay keywords disponibles</td></tr>';
        return;
    }
    
    keywords.forEach(keyword => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${keyword.keyword}</strong></td>
            <td><span class="badge bg-${getStatusColor(keyword.status)}">${getStatusText(keyword.status)}</span></td>
            <td><span class="badge bg-${getPriorityColor(keyword.priority)}">${getPriorityText(keyword.priority)}</span></td>
            <td>${keyword.search_volume || 'N/A'}</td>
            <td>${keyword.difficulty ? keyword.difficulty.toFixed(1) : 'N/A'}</td>
            <td>${keyword.category || 'N/A'}</td>
            <td>${formatDate(keyword.created_at)}</td>
            <td>
                <button class="btn btn-sm btn-success me-1" onclick="generateContentFromKeyword(${keyword.id})" title="Generar Contenido con IA">
                    <i class="fas fa-magic"></i>
                </button>
                <button class="btn btn-sm btn-info me-1" onclick="analyzeKeyword(${keyword.id})" title="Analizar">
                    <i class="fas fa-chart-line"></i>
                </button>
                <button class="btn btn-sm btn-warning me-1" onclick="editKeyword(${keyword.id})" title="Editar">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteKeyword(${keyword.id})" title="Eliminar">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

async function handleAddKeyword(e) {
    e.preventDefault();
    
    const keywordText = document.getElementById('keywordText').value;
    const priority = document.getElementById('prioritySelect').value;
    const searchVolume = document.getElementById('searchVolumeInput').value;
    const difficulty = document.getElementById('difficultyInput').value;
    const category = document.getElementById('categoryInput').value;
    const notes = document.getElementById('notesInput').value;
    
    if (!keywordText.trim()) {
        showAlert('Por favor ingresa una palabra clave', 'warning');
        return;
    }
    
    showLoading(true);
    
    try {
        const keywordData = {
            keyword: keywordText.trim(),
            priority: priority,
            search_volume: searchVolume ? parseInt(searchVolume) : null,
            difficulty: difficulty ? parseFloat(difficulty) : null,
            category: category.trim() || null,
            notes: notes.trim() || null
        };
        
        const response = await apiRequest('/keywords/', {
            method: 'POST',
            body: JSON.stringify(keywordData)
        });
        
        if (response) {
            showAlert('Keyword agregada exitosamente', 'success');
            document.getElementById('keywordForm').reset();
            await loadKeywords();
        }
    } catch (error) {
        showAlert('Error al agregar keyword', 'danger');
        console.error('Error adding keyword:', error);
    } finally {
        showLoading(false);
    }
}

async function deleteKeyword(keywordId) {
    if (!confirm('¿Estás seguro de que quieres eliminar esta keyword?')) {
        return;
    }
    
    showLoading(true);
    
    try {
        await apiRequest(`/keywords/${keywordId}`, {
            method: 'DELETE'
        });
        
        showAlert('Keyword eliminada exitosamente', 'success');
        await loadKeywords();
    } catch (error) {
        showAlert('Error al eliminar keyword', 'danger');
        console.error('Error deleting keyword:', error);
    } finally {
        showLoading(false);
    }
}

async function analyzeKeyword(keywordId) {
    showLoading(true);
    
    try {
        const analysis = await apiRequest(`/keyword-analysis/analyze/${keywordId}`);
        if (analysis) {
            showAlert('Análisis completado', 'success');
            // You can display the analysis results in a modal or dedicated section
            console.log('Keyword analysis:', analysis);
        }
    } catch (error) {
        showAlert('Error al analizar keyword', 'danger');
        console.error('Error analyzing keyword:', error);
    } finally {
        showLoading(false);
    }
}

// Image tab functionality removed - only preserving image modal for content editor

// handleImageConfigForm removed - image tab functionality removed

// handleKeywordSelect and saveKeywordImageConfig removed - image tab functionality removed

// handleManualImageForm removed - image tab functionality removed

// loadImageConfiguration removed - image tab functionality removed

// populateImageConfigForm, toggleGeminiSettings, setupImageProviderListener removed - image tab functionality removed

// loadKeywordsForImageConfig, updateImageStats, handleGenerateImage, loadImageGallery, displayImageGallery removed - image tab functionality removed

// Scheduler Functions
async function loadSchedulerStatus() {
    try {
        const status = await apiRequest('/scheduler/status');
        if (status) {
            displaySchedulerStatus(status);
        }
        
        const stats = await apiRequest('/scheduler/statistics');
        if (stats) {
            displaySchedulerStats(stats);
        }
    } catch (error) {
        console.error('Error loading scheduler data:', error);
    }
}

function displaySchedulerStatus(status) {
    const statusDiv = document.getElementById('schedulerStatus');
    statusDiv.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
            <span>Estado:</span>
            <span class="status-badge ${status.is_running ? 'status-active' : 'status-inactive'}">
                ${status.is_running ? 'Activo' : 'Inactivo'}
            </span>
        </div>
        <div class="d-flex justify-content-between align-items-center mt-2">
            <span>Última ejecución:</span>
            <span>${status.last_run ? formatDate(status.last_run) : 'Nunca'}</span>
        </div>
        <div class="d-flex justify-content-between align-items-center mt-2">
            <span>Próxima ejecución:</span>
            <span>${status.next_run ? formatDate(status.next_run) : 'No programada'}</span>
        </div>
    `;
}

function displaySchedulerStats(stats) {
    const statsDiv = document.getElementById('schedulerStats');
    statsDiv.innerHTML = `
        <div class="row text-center">
            <div class="col-4">
                <h4 class="text-primary">${stats.total_executions || 0}</h4>
                <small>Total Ejecuciones</small>
            </div>
            <div class="col-4">
                <h4 class="text-success">${stats.successful_executions || 0}</h4>
                <small>Exitosas</small>
            </div>
            <div class="col-4">
                <h4 class="text-danger">${stats.failed_executions || 0}</h4>
                <small>Fallidas</small>
            </div>
        </div>
    `;
}

// Landings Functions
/**
 * Carga la sección de Landings
 * Inicializa las pestañas y prepara las funcionalidades futuras
 */
async function loadLandings() {
    try {
        console.log('Cargando sección de Landings...');
        // Placeholder para futuras funcionalidades
        // Aquí se cargarán los datos de landing pages cuando estén implementadas
        
        // Inicializar las pestañas de Bootstrap si es necesario
        initializeLandingsTabs();
        
    } catch (error) {
        console.error('Error loading landings:', error);
    }
}

/**
 * Inicializa las pestañas de la sección Landings
 */
function initializeLandingsTabs() {
    // Placeholder para inicialización de pestañas
    console.log('Inicializando pestañas de Landings...');
}

/**
 * Funciones placeholder para las diferentes secciones de Landings
 */

// ===== LANDING PAGES FUNCTIONALITY =====

// Creador de Landing Pages
function loadCreadorSection() {
    loadUserLandingPages();
}

// Optimización SEO
function loadSeoSection() {
    console.log('Cargando sección SEO...');
    loadSeoTools();
}

// Temas y Plantillas
function loadTemasSection() {
    loadThemesAndTemplates();
}

// ===== CREADOR FUNCTIONS =====

// Cargar landing pages del usuario
async function loadUserLandingPages() {
    try {
        console.log('=== EJECUTANDO loadUserLandingPages ===');
        showLoading(true);
        const response = await apiRequest('/landings/creador/landing-pages');
        console.log('Respuesta del API:', response);
        
        if (response && response.landing_pages) {
            displayUserLandingPages(response.landing_pages);
        } else {
            // Si la respuesta es exitosa pero no hay landing pages, mostrar lista vacía sin error
            displayUserLandingPages([]);
        }
    } catch (error) {
        console.error('Error loading user landing pages:', error);
        
        // Solo mostrar error si es un error real del servidor, no si simplemente no hay landing pages
        if (error.status && error.status !== 404) {
            showAlert('Error al cargar las landing pages', 'danger');
        }
        
        // Siempre mostrar la interfaz, aunque esté vacía
        displayUserLandingPages([]);
    } finally {
        showLoading(false);
    }
}

// Mostrar landing pages del usuario
function displayUserLandingPages(landingPages) {
    const container = document.getElementById('creador');
    
    const html = `
        <div class="container-fluid">
            <div class="row">
                <div class="col-12">
                    <div class="d-flex justify-content-between align-items-center mb-4">
                        <h5><i class="fas fa-magic me-2"></i>Creador de Landing Pages</h5>
                        <button class="btn btn-primary" onclick="showGenerateLandingModal()">
                            <i class="fas fa-plus me-1"></i>Crear Nueva Landing
                        </button>
                    </div>
                    
                    ${landingPages.length === 0 ? `
                        <div class="text-center py-5">
                            <i class="fas fa-magic fa-3x text-muted mb-3"></i>
                            <h4 class="text-muted">¡Crea tu primera Landing Page!</h4>
                            <p class="text-muted">Usa IA para generar landing pages ultra-optimizadas para SEO</p>
                            <button class="btn btn-primary btn-lg" onclick="showGenerateLandingModal()">
                                <i class="fas fa-magic me-2"></i>Crear Landing Page
                            </button>
                        </div>
                    ` : `
                        <div class="row">
                            ${landingPages.map(lp => `
                                <div class="col-md-6 col-lg-4 mb-4">
                                    <div class="card h-100 landing-card">
                                        <div class="card-body">
                                            <div class="d-flex justify-content-between align-items-start mb-2">
                                                <h6 class="card-title">${lp.title}</h6>
                                                <span class="badge ${lp.is_published ? 'bg-success' : 'bg-secondary'}">
                                                    ${lp.is_published ? 'Publicada' : 'Borrador'}
                                                </span>
                                            </div>
                                            <p class="card-text text-muted small">${lp.seo_description || 'Sin descripción'}</p>
                                            <div class="small text-muted mb-3">
                                                <i class="fas fa-calendar me-1"></i>
                                                ${new Date(lp.created_at).toLocaleDateString()}
                                            </div>
                                            ${lp.is_published ? `
                                                <div class="mb-2">
                                                    <small class="text-success">
                                                        <i class="fas fa-link me-1"></i>
                                                        <a href="${window.location.origin}/landing/${lp.slug}" target="_blank" class="text-success text-decoration-none">
                                                            ${window.location.origin}/landing/${lp.slug}
                                                        </a>
                                                    </small>
                                                </div>
                                            ` : ''}
                                            <div class="d-flex gap-2">
                                                <button class="btn btn-sm btn-outline-primary" onclick="viewLandingPage(${lp.id})" title="Ver">
                                                    <i class="fas fa-eye"></i>
                                                </button>
                                                <button class="btn btn-sm btn-outline-secondary" onclick="editLandingPage(${lp.id})" title="Editar">
                                                    <i class="fas fa-edit"></i>
                                                </button>
                                                ${lp.is_published ? `
                                                    <button class="btn btn-sm btn-outline-warning" onclick="unpublishLandingPage(${lp.id})" title="Despublicar">
                                                        <i class="fas fa-eye-slash"></i>
                                                    </button>
                                                ` : `
                                                    <button class="btn btn-sm btn-outline-success" onclick="publishLandingPage(${lp.id})" title="Publicar">
                                                        <i class="fas fa-globe"></i>
                                                    </button>
                                                `}
                                                <button class="btn btn-sm btn-outline-danger" onclick="deleteLandingPage(${lp.id})" title="Eliminar">
                                                    <i class="fas fa-trash"></i>
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    `}
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// Mostrar modal para generar landing page
function showGenerateLandingModal() {
    const modalHtml = `
        <div class="modal fade" id="generateLandingModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-magic me-2"></i>Generar Landing Page con IA
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="generateLandingForm">
                            <div class="mb-3">
                                <label for="landingKeywords" class="form-label">
                                    <i class="fas fa-key me-1"></i>Palabras Clave *
                                </label>
                                <input type="text" class="form-control" id="landingKeywords" 
                                       placeholder="Ej: consultoría empresarial, coaching ejecutivo" required>
                                <div class="form-text">Separa múltiples palabras clave con comas</div>
                            </div>
                            
                            <div class="mb-3">
                                <label for="landingPhone" class="form-label">
                                    <i class="fas fa-phone me-1"></i>Número de Teléfono *
                                </label>
                                <input type="tel" class="form-control" id="landingPhone" 
                                       placeholder="Ej: +34 600 123 456" required>
                                <div class="form-text">Se usará para el botón de WhatsApp</div>
                            </div>
                            
                            <div class="mb-3">
                                <label for="aiProvider" class="form-label">
                                    <i class="fas fa-robot me-1"></i>Proveedor de IA
                                </label>
                                <select class="form-select" id="aiProvider">
                                    <option value="openai">OpenAI (GPT-4)</option>
                                    <option value="deepseek">DeepSeek</option>
                                    <option value="gemini">Google Gemini</option>
                                </select>
                            </div>
                            
                            <div class="mb-3">
                                <label for="themeCategory" class="form-label">
                                    <i class="fas fa-palette me-1"></i>Categoría Temática
                                </label>
                                <select class="form-select" id="themeCategory">
                                    <option value="business">Negocios y Consultoría</option>
                                    <option value="health">Salud y Bienestar</option>
                                    <option value="esoteric">Esotérico y Espiritual</option>
                                    <option value="technology">Tecnología</option>
                                    <option value="education">Educación</option>
                                    <option value="finance">Finanzas</option>
                                    <option value="lifestyle">Estilo de Vida</option>
                                </select>
                            </div>
                            
                            <!-- Configuración Avanzada -->
                            <div class="card border-info mb-3">
                                <div class="card-header bg-info text-white">
                                    <h6 class="mb-0">
                                        <i class="fas fa-cogs me-2"></i>Configuración Avanzada (Opcional)
                                        <button type="button" class="btn btn-sm btn-outline-light float-end" onclick="toggleAdvancedConfig()">
                                            <i class="fas fa-chevron-down" id="advancedToggleIcon"></i>
                                        </button>
                                    </h6>
                                </div>
                                <div class="card-body" id="advancedConfigBody" style="display: none;">
                                    <div class="row">
                                        <div class="col-md-6">
                                            <div class="mb-3">
                                                <label for="additionalServices" class="form-label">
                                                    <i class="fas fa-plus me-1"></i>Servicios Adicionales
                                                </label>
                                                <textarea class="form-control" id="additionalServices" rows="3" 
                                                         placeholder="Ej: Consultoría personalizada, Auditorías, Formación..."></textarea>
                                                <div class="form-text">Separa cada servicio con una nueva línea</div>
                                            </div>
                                            
                                            <div class="mb-3">
                                                <label for="ctaCount" class="form-label">
                                                    <i class="fas fa-mouse-pointer me-1"></i>Cantidad de Call to Action
                                                </label>
                                                <select class="form-select" id="ctaCount">
                                                    <option value="1">1 CTA</option>
                                                    <option value="2" selected>2 CTAs</option>
                                                    <option value="3">3 CTAs</option>
                                                    <option value="4">4 CTAs</option>
                                                    <option value="5">5 CTAs</option>
                                                    <option value="6">6 CTAs</option>
                                                </select>
                                            </div>
                                            
                                            <div class="mb-3">
                                                <label for="paragraphCount" class="form-label">
                                                    <i class="fas fa-paragraph me-1"></i>Párrafos Informativos
                                                </label>
                                                <select class="form-select" id="paragraphCount">
                                                    <option value="1">1 Párrafo</option>
                                                    <option value="2">2 Párrafos</option>
                                                    <option value="3" selected>3 Párrafos</option>
                                                    <option value="4">4 Párrafos</option>
                                                    <option value="5">5 Párrafos</option>
                                                    <option value="6">6 Párrafos</option>
                                                </select>
                                            </div>
                                            
                                            <div class="mb-3">
                                                <label for="writingStyle" class="form-label">
                                                    <i class="fas fa-pen me-1"></i>Estilo de Redacción
                                                </label>
                                                <select class="form-select" id="writingStyle">
                                                    <option value="persuasiva" selected>Persuasiva</option>
                                                    <option value="tecnica">Técnica</option>
                                                    <option value="vendedora">Vendedora</option>
                                                    <option value="informativa">Informativa</option>
                                                    <option value="emocional">Emocional</option>
                                                    <option value="profesional">Profesional</option>
                                                </select>
                                            </div>
                                        </div>
                                        
                                        <div class="col-md-6">
                                            <div class="mb-3">
                                                <label for="landingLength" class="form-label">
                                                    <i class="fas fa-ruler me-1"></i>Longitud de Landing Page
                                                </label>
                                                <select class="form-select" id="landingLength">
                                                    <option value="corta">Corta (Concisa)</option>
                                                    <option value="mediana" selected>Mediana (Equilibrada)</option>
                                                    <option value="larga">Larga (Detallada)</option>
                                                </select>
                                            </div>
                                            
                                            <div class="mb-3">
                                                <label for="includeSliders" class="form-label">
                                                    <i class="fas fa-images me-1"></i>Sliders de Servicios
                                                </label>
                                                <select class="form-select" id="includeSliders">
                                                    <option value="no">No incluir</option>
                                                    <option value="si" selected>Sí incluir</option>
                                                </select>
                                                <div class="form-text">Sliders con categorías y descripciones de servicios</div>
                                            </div>
                                            
                                            <div class="mb-3">
                                                <label for="includeSeparators" class="form-label">
                                                    <i class="fas fa-minus me-1"></i>Separadores SVG
                                                </label>
                                                <select class="form-select" id="includeSeparators">
                                                    <option value="no">No incluir</option>
                                                    <option value="si" selected>Sí incluir</option>
                                                </select>
                                            </div>
                                            
                                            <div class="mb-3">
                                                <label for="separatorStyle" class="form-label">
                                                    <i class="fas fa-wave-square me-1"></i>Estilo de Separadores
                                                </label>
                                                <select class="form-select" id="separatorStyle">
                                                    <option value="lines">Líneas (_____)</option>
                                                    <option value="waves" selected>Ondas</option>
                                                    <option value="geometric">Geométrico</option>
                                                    <option value="organic">Orgánico</option>
                                                </select>
                                            </div>
                                            
                                            <div class="mb-3">
                                                <label for="responsiveMenu" class="form-label">
                                                    <i class="fas fa-bars me-1"></i>Menú Responsivo
                                                </label>
                                                <select class="form-select" id="responsiveMenu">
                                                    <option value="no">No incluir</option>
                                                    <option value="si" selected>Sí incluir</option>
                                                </select>
                                            </div>
                                            
                                            <div class="mb-3">
                                                <label for="testimonialLength" class="form-label">
                                                    <i class="fas fa-quote-left me-1"></i>Longitud de Testimonios
                                                </label>
                                                <select class="form-select" id="testimonialLength">
                                                    <option value="cortos">Cortos</option>
                                                    <option value="medianos" selected>Medianos</option>
                                                    <option value="largos">Largos</option>
                                                </select>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="alert alert-info">
                                <i class="fas fa-info-circle me-2"></i>
                                <strong>¿Qué se generará?</strong><br>
                                • HTML semántico ultra-optimizado para SEO<br>
                                • Contenido profesional centrado en tus keywords<br>
                                • Diseño responsive y de carga rápida<br>
                                • Botón de WhatsApp integrado<br>
                                • Meta tags y estructura H1/H2 optimizada
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                        <button type="button" class="btn btn-primary" onclick="generateLandingPage()">
                            <i class="fas fa-magic me-1"></i>Generar Landing Page
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('generateLandingModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('generateLandingModal'));
    modal.show();
}

// Función para mostrar/ocultar configuración avanzada
function toggleAdvancedConfig() {
    const body = document.getElementById('advancedConfigBody');
    const icon = document.getElementById('advancedToggleIcon');
    
    if (body.style.display === 'none') {
        body.style.display = 'block';
        icon.className = 'fas fa-chevron-up';
    } else {
        body.style.display = 'none';
        icon.className = 'fas fa-chevron-down';
    }
}

// Generar landing page con IA
async function generateLandingPage() {
    const keywords = document.getElementById('landingKeywords').value.trim();
    const phone = document.getElementById('landingPhone').value.trim();
    const aiProvider = document.getElementById('aiProvider').value;
    const themeCategory = document.getElementById('themeCategory').value;
    
    // Nuevos campos opcionales
    const additionalServices = document.getElementById('additionalServices')?.value || '';
    const ctaCount = document.getElementById('ctaCount')?.value || '2';
    const paragraphCount = document.getElementById('paragraphCount')?.value || '3';
    const writingStyle = document.getElementById('writingStyle')?.value || 'persuasiva';
    const landingLength = document.getElementById('landingLength')?.value || 'mediana';
    const includeSliders = document.getElementById('includeSliders')?.value || 'si';
    const includeSeparators = document.getElementById('includeSeparators')?.value || 'si';
    const separatorStyle = document.getElementById('separatorStyle')?.value || 'waves';
    const responsiveMenu = document.getElementById('responsiveMenu')?.value || 'si';
    const testimonialLength = document.getElementById('testimonialLength')?.value || 'medianos';
    
    if (!keywords || !phone) {
        showAlert('Por favor completa todos los campos obligatorios', 'warning');
        return;
    }
    
    // Validate phone format
    const phoneRegex = /^[+]?[0-9\s\-\(\)]{9,}$/;
    if (!phoneRegex.test(phone)) {
        showAlert('Por favor ingresa un número de teléfono válido', 'warning');
        return;
    }
    
    const generateBtn = document.querySelector('#generateLandingModal .btn-primary');
    const originalText = generateBtn.innerHTML;
    
    try {
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Generando con IA...';
        
        // Mostrar progreso detallado
        const progressContainer = document.createElement('div');
        progressContainer.id = 'aiProgressContainer';
        progressContainer.className = 'mt-3 p-3 bg-light rounded';
        progressContainer.innerHTML = `
            <div class="d-flex align-items-center mb-2">
                <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                <span id="progressText">Iniciando generación con IA...</span>
            </div>
            <div class="progress" style="height: 6px;">
                <div id="progressBar" class="progress-bar progress-bar-striped progress-bar-animated" 
                     role="progressbar" style="width: 0%"></div>
            </div>
        `;
        
        const modalBody = document.querySelector('#generateLandingModal .modal-body');
        modalBody.appendChild(progressContainer);
        
        // Simular progreso de IA
        const updateProgress = (percent, text) => {
            document.getElementById('progressBar').style.width = percent + '%';
            document.getElementById('progressText').textContent = text;
        };
        
        updateProgress(10, `Conectando con ${aiProvider.toUpperCase()}...`);
        await new Promise(resolve => setTimeout(resolve, 800));
        
        updateProgress(30, 'Analizando palabras clave...');
        await new Promise(resolve => setTimeout(resolve, 600));
        
        updateProgress(50, 'Generando contenido con IA...');
        
        // Preparar datos con campos opcionales
        const requestData = {
            keywords: keywords,
            phone_number: phone,
            ai_provider: aiProvider,
            theme_category: themeCategory
        };
        
        // Agregar campos opcionales
        if (additionalServices.trim()) {
            requestData.additional_services = additionalServices.split('\n').filter(s => s.trim());
        }
        
        requestData.cta_count = parseInt(ctaCount);
        requestData.paragraph_count = parseInt(paragraphCount);
        requestData.writing_style = writingStyle;
        requestData.landing_length = landingLength;
        requestData.include_sliders = includeSliders === 'si';
        requestData.include_separators = includeSeparators === 'si';
        requestData.separator_style = separatorStyle;
        requestData.responsive_menu = responsiveMenu === 'si';
        requestData.testimonial_length = testimonialLength;
        
        updateProgress(70, 'Procesando respuesta de IA...');
        
        const response = await apiRequest('/landings/creador/generate', {
            method: 'POST',
            body: JSON.stringify(requestData)
        });
        
        updateProgress(90, 'Construyendo landing page...');
        await new Promise(resolve => setTimeout(resolve, 500));
        
        if (response && response.success) {
            updateProgress(100, '¡Landing page generada con IA exitosamente!');
            await new Promise(resolve => setTimeout(resolve, 800));
            
            // Limpiar indicador de progreso
            const progressContainer = document.getElementById('aiProgressContainer');
            if (progressContainer) {
                progressContainer.remove();
            }
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('generateLandingModal'));
            modal.hide();
            
            showAlert('Landing page generada exitosamente con IA', 'success');
            
            // Reload landing pages
            loadUserLandingPages();
            
            // Show the generated landing in themes tab
            if (response.html_content) {
                showGeneratedLandingPreview(response.html_content, response.landing_page);
            }
        } else {
            throw new Error(response.message || 'Error al generar la landing page con IA');
        }
    } catch (error) {
        console.error('Error generating landing page:', error);
        showAlert(`Error al generar landing page con IA: ${error.message}`, 'danger');
    } finally {
        // Limpiar indicador de progreso si existe
        const progressContainer = document.getElementById('aiProgressContainer');
        if (progressContainer) {
            progressContainer.remove();
        }
        
        generateBtn.disabled = false;
        generateBtn.innerHTML = originalText;
    }
}

// Ver landing page
async function viewLandingPage(landingId) {
    try {
        const response = await apiRequest(`/landings/creador/landing-pages/${landingId}`);
        
        if (response && response.landing_page) {
            const lp = response.landing_page;
            
            // Show preview modal
            const modalHtml = `
                <div class="modal fade" id="viewLandingModal" tabindex="-1">
                    <div class="modal-dialog modal-xl">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">
                                    <i class="fas fa-eye me-2"></i>${lp.title}
                                </h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body p-0">
                                <iframe srcdoc="${lp.html_content.replace(/"/g, '&quot;')}" 
                                        style="width: 100%; height: 70vh; border: none;"></iframe>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                                ${lp.public_url ? `
                                    <a href="${lp.public_url}" target="_blank" class="btn btn-primary">
                                        <i class="fas fa-external-link-alt me-1"></i>Ver en Vivo
                                    </a>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Remove existing modal
            const existingModal = document.getElementById('viewLandingModal');
            if (existingModal) existingModal.remove();
            
            // Add and show modal
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            const modal = new bootstrap.Modal(document.getElementById('viewLandingModal'));
            modal.show();
        }
    } catch (error) {
        console.error('Error viewing landing page:', error);
        showAlert('Error al cargar la landing page', 'danger');
    }
}

// Editar landing page
async function editLandingPage(landingId) {
    try {
        showLoading(true);
        const response = await apiRequest(`/landings/creador/landing-pages/${landingId}`);
        
        if (response && response.landing_page) {
            const lp = response.landing_page;
            showEditLandingModal(lp);
        }
    } catch (error) {
        console.error('Error loading landing page for edit:', error);
        showAlert('Error al cargar la landing page para editar', 'danger');
    } finally {
        showLoading(false);
    }
}

// Mostrar modal de edición
function showEditLandingModal(landingPage) {
    const modalHtml = `
        <div class="modal fade" id="editLandingModal" tabindex="-1">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-edit me-2"></i>Editar Landing Page
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <!-- Pestañas de navegación -->
                        <ul class="nav nav-tabs" id="editLandingTabs" role="tablist">
                            <li class="nav-item" role="presentation">
                                <button class="nav-link active" id="basic-tab" data-bs-toggle="tab" data-bs-target="#basic-pane" type="button" role="tab">
                                    <i class="fas fa-cog me-1"></i>Configuración Básica
                                </button>
                            </li>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="css-tab" data-bs-toggle="tab" data-bs-target="#css-pane" type="button" role="tab">
                                    <i class="fab fa-css3-alt me-1"></i>CSS Personalizado
                                </button>
                            </li>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="html-tab" data-bs-toggle="tab" data-bs-target="#html-pane" type="button" role="tab">
                                    <i class="fab fa-html5 me-1"></i>HTML Personalizado
                                </button>
                            </li>
                        </ul>
                        
                        <!-- Contenido de las pestañas -->
                        <div class="tab-content" id="editLandingTabContent">
                            <!-- Pestaña de Configuración Básica -->
                            <div class="tab-pane fade show active" id="basic-pane" role="tabpanel">
                                <form id="editLandingForm" class="mt-3">
                                    <div class="mb-3">
                                        <label for="editTitle" class="form-label">
                                            <i class="fas fa-heading me-1"></i>Título *
                                        </label>
                                        <input type="text" class="form-control" id="editTitle" 
                                               value="${landingPage.title}" required maxlength="200">
                                        <div class="form-text d-flex justify-content-between">
                                            <span>Título principal de la landing page</span>
                                            <span id="titleCounter" class="text-muted">0/200</span>
                                        </div>
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label for="editDescription" class="form-label">
                                            <i class="fas fa-align-left me-1"></i>Descripción
                                        </label>
                                        <textarea class="form-control" id="editDescription" rows="3" maxlength="500">${landingPage.seo_description || ''}</textarea>
                                        <div class="form-text d-flex justify-content-between">
                                            <span>Descripción general de la landing page</span>
                                            <span id="descriptionCounter" class="text-muted">0/500</span>
                                        </div>
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label for="editSeoTitle" class="form-label">
                                            <i class="fas fa-search me-1"></i>Título SEO
                                        </label>
                                        <input type="text" class="form-control" id="editSeoTitle" 
                                               value="${landingPage.seo_title || ''}" maxlength="60">
                                        <div class="form-text d-flex justify-content-between">
                                            <span>Título optimizado para motores de búsqueda</span>
                                            <span id="seoTitleCounter" class="text-muted">0/60</span>
                                        </div>
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label for="editSeoKeywords" class="form-label">
                                            <i class="fas fa-key me-1"></i>Keywords SEO
                                        </label>
                                        <input type="text" class="form-control" id="editSeoKeywords" 
                                               value="${landingPage.seo_keywords || ''}" maxlength="500">
                                        <div class="form-text d-flex justify-content-between">
                                            <span>Separa múltiples keywords con comas</span>
                                            <span id="seoKeywordsCounter" class="text-muted">0/500</span>
                                        </div>
                                    </div>
                                    
                                    <div class="mb-3">
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" id="editIsActive" 
                                                   ${landingPage.is_active ? 'checked' : ''}>
                                            <label class="form-check-label" for="editIsActive">
                                                Landing page activa
                                            </label>
                                        </div>
                                    </div>
                                </form>
                            </div>
                            
                            <!-- Pestaña de CSS Personalizado -->
                            <div class="tab-pane fade" id="css-pane" role="tabpanel">
                                <div class="mt-3">
                                    <div class="d-flex justify-content-between align-items-center mb-2">
                                        <label for="editCustomCSS" class="form-label mb-0">
                                            <i class="fab fa-css3-alt me-1"></i>CSS Personalizado para esta Landing Page
                                        </label>
                                        <small class="text-muted">Este CSS se aplicará solo a esta landing page</small>
                                    </div>
                                    <textarea class="form-control font-monospace" id="editCustomCSS" rows="20" 
                                              placeholder="/* Escribe tu CSS personalizado aquí */\n/* Ejemplo: */\n.mi-clase-personalizada {\n    color: #ff6b6b;\n    font-size: 18px;\n}">${landingPage.css_content || ''}</textarea>
                                    <div class="form-text">
                                        <i class="fas fa-info-circle me-1"></i>
                                        Puedes usar cualquier CSS válido. Este código se aplicará únicamente a esta landing page.
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Pestaña de HTML Personalizado -->
                            <div class="tab-pane fade" id="html-pane" role="tabpanel">
                                <div class="mt-3">
                                    <div class="d-flex justify-content-between align-items-center mb-2">
                                        <label for="editCustomHTML" class="form-label mb-0">
                                            <i class="fab fa-html5 me-1"></i>HTML Personalizado para esta Landing Page
                                        </label>
                                        <small class="text-muted">Edita el HTML completo de esta landing page</small>
                                    </div>
                                    <div class="alert alert-warning" role="alert">
                                        <i class="fas fa-exclamation-triangle me-1"></i>
                                        <strong>¡Cuidado!</strong> Editar el HTML puede afectar el funcionamiento de la landing page. 
                                        Asegúrate de mantener una estructura HTML válida.
                                    </div>
                                    <textarea class="form-control font-monospace" id="editCustomHTML" rows="20" 
                                              placeholder="<!DOCTYPE html>\n<html lang='es'>\n<head>\n    <meta charset='UTF-8'>\n    <title>Mi Landing Page</title>\n</head>\n<body>\n    <!-- Tu contenido aquí -->\n</body>\n</html>">${landingPage.html_content || ''}</textarea>
                                    <div class="form-text">
                                        <i class="fas fa-info-circle me-1"></i>
                                        Si dejas este campo vacío, se usará el HTML generado automáticamente.
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                        <button type="button" class="btn btn-primary" onclick="updateLandingPage(${landingPage.id})">
                            <i class="fas fa-save me-1"></i>Guardar Cambios
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('editLandingModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('editLandingModal'));
    modal.show();
    
    // Setup character counters after modal is shown
    modal._element.addEventListener('shown.bs.modal', function() {
        setupCharacterCounters();
    });
}

// Setup character counters for form fields
function setupCharacterCounters() {
    const fields = [
        { id: 'editTitle', counterId: 'titleCounter', maxLength: 200 },
        { id: 'editDescription', counterId: 'descriptionCounter', maxLength: 500 },
        { id: 'editSeoTitle', counterId: 'seoTitleCounter', maxLength: 60 },
        { id: 'editSeoKeywords', counterId: 'seoKeywordsCounter', maxLength: 500 }
    ];
    
    fields.forEach(field => {
        const input = document.getElementById(field.id);
        const counter = document.getElementById(field.counterId);
        
        if (input && counter) {
            // Update counter initially
            updateCounter(input, counter, field.maxLength);
            
            // Add event listeners for real-time updates
            input.addEventListener('input', () => {
                updateCounter(input, counter, field.maxLength);
            });
            
            input.addEventListener('keyup', () => {
                updateCounter(input, counter, field.maxLength);
            });
        }
    });
}

// Update character counter
function updateCounter(input, counter, maxLength) {
    const currentLength = input.value.length;
    counter.textContent = `${currentLength}/${maxLength}`;
    
    // Change color based on usage
    if (currentLength > maxLength * 0.9) {
        counter.className = 'text-warning';
    } else if (currentLength >= maxLength) {
        counter.className = 'text-danger';
    } else {
        counter.className = 'text-muted';
    }
}

// Actualizar landing page
async function updateLandingPage(landingId) {
    const title = document.getElementById('editTitle').value.trim();
    const description = document.getElementById('editDescription').value.trim();
    const seoTitle = document.getElementById('editSeoTitle').value.trim();
    const seoKeywords = document.getElementById('editSeoKeywords').value.trim();
    const isActive = document.getElementById('editIsActive').checked;
    const customCSS = document.getElementById('editCustomCSS').value.trim();
    const customHTML = document.getElementById('editCustomHTML').value.trim();
    
    // Validaciones de campos requeridos y límites
    if (!title) {
        showAlert('El título es requerido', 'warning');
        return;
    }
    
    if (title.length > 200) {
        showAlert('El título no puede exceder 200 caracteres', 'warning');
        return;
    }
    
    if (description && description.length > 500) {
        showAlert('La descripción no puede exceder 500 caracteres', 'warning');
        return;
    }
    
    if (seoTitle && seoTitle.length > 60) {
        showAlert('El título SEO no puede exceder 60 caracteres', 'warning');
        return;
    }
    
    if (seoKeywords && seoKeywords.length > 500) {
        showAlert('Las keywords SEO no pueden exceder 500 caracteres', 'warning');
        return;
    }
    
    const updateBtn = document.querySelector('#editLandingModal .btn-primary');
    const originalText = updateBtn.innerHTML;
    
    try {
        // Debug: Check token status before making request
        const token = localStorage.getItem('authToken');
        console.log('updateLandingPage - Token check:', token ? 'EXISTS' : 'NULL');
        console.log('updateLandingPage - authToken variable:', authToken ? 'EXISTS' : 'NULL');
        
        if (!token) {
            showAlert('No hay token de autenticación. Por favor, inicia sesión nuevamente.', 'warning');
            logout();
            return;
        }
        
        updateBtn.disabled = true;
        updateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Guardando...';
        
        const requestData = {
            title: title,
            seo_description: description,
            seo_title: seoTitle,
            seo_keywords: seoKeywords,
            is_active: isActive,
            css_content: customCSS || null,
            html_content: customHTML || null
        };
        
        console.log('updateLandingPage - Request data:', requestData);
        
        const response = await apiRequest(`/landings/creador/landing-pages/${landingId}`, {
            method: 'PUT',
            body: JSON.stringify(requestData)
        });
        
        if (response && response.success) {
            showAlert('Landing page actualizada exitosamente', 'success');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('editLandingModal'));
            modal.hide();
            
            // Reload landing pages
            loadUserLandingPages();
        }
        
    } catch (error) {
        console.error('Error updating landing page:', error);
        showAlert('Error al actualizar la landing page', 'danger');
    } finally {
        updateBtn.disabled = false;
        updateBtn.innerHTML = originalText;
    }
}

// Publicar landing page
async function publishLandingPage(landingId) {
    if (!confirm('¿Estás seguro de que quieres publicar esta landing page?')) {
        return;
    }
    
    try {
        showLoading(true);
        const response = await apiRequest(`/landings/creador/landing-pages/${landingId}/publish`, {
            method: 'PUT'
        });
        
        if (response && response.success) {
            const landingPage = response.landing_page;
            const publicUrl = `${window.location.origin}/landing/${landingPage.slug}`;
            showAlert(`Landing page publicada exitosamente. URL: <a href="${publicUrl}" target="_blank" class="text-white">${publicUrl}</a>`, 'success');
            loadUserLandingPages();
        }
    } catch (error) {
        console.error('Error publishing landing page:', error);
        showAlert('Error al publicar la landing page', 'danger');
    } finally {
        showLoading(false);
    }
}

// Despublicar landing page
async function unpublishLandingPage(landingId) {
    if (!confirm('¿Estás seguro de que quieres despublicar esta landing page?')) {
        return;
    }
    
    try {
        showLoading(true);
        const response = await apiRequest(`/landings/creador/landing-pages/${landingId}/unpublish`, {
            method: 'PUT'
        });
        
        if (response && response.success) {
            showAlert('Landing page despublicada exitosamente', 'success');
            loadUserLandingPages();
        }
    } catch (error) {
        console.error('Error unpublishing landing page:', error);
        showAlert('Error al despublicar la landing page', 'danger');
    } finally {
        showLoading(false);
    }
}

// Eliminar landing page
async function deleteLandingPage(landingId) {
    if (!confirm('¿Estás seguro de que quieres eliminar esta landing page? Esta acción no se puede deshacer.')) {
        return;
    }
    
    try {
        showLoading(true);
        const response = await apiRequest(`/landings/creador/landing-pages/${landingId}`, {
            method: 'DELETE'
        });
        
        if (response && response.success) {
            showAlert('Landing page eliminada exitosamente', 'success');
            loadUserLandingPages();
        }
    } catch (error) {
        console.error('Error deleting landing page:', error);
        showAlert('Error al eliminar la landing page', 'danger');
    } finally {
        showLoading(false);
    }
}

// ===== SEO FUNCTIONS =====

function loadSeoTools() {
    const container = document.getElementById('seo');
    
    const html = `
        <div class="container-fluid">
            <div class="row">
                <div class="col-12">
                    <h5><i class="fas fa-search me-2"></i>Optimización SEO</h5>
                    <p class="text-muted">Herramientas para analizar y optimizar el SEO de tus landing pages.</p>
                    
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle me-2"></i>
                        <strong>Próximamente:</strong> Análisis SEO automático, sugerencias de keywords, y optimización de contenido.
                    </div>
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// ===== THEMES FUNCTIONS =====

async function loadThemesAndTemplates() {
    const container = document.getElementById('temas');
    
    try {
        // Load themes and landing pages
        const [themesResponse, landingsResponse] = await Promise.all([
            apiRequest('/themes'),
            apiRequest('/landings/creador/landing-pages')
        ]);
        
        // El API de temas devuelve directamente un array, no un objeto con propiedad themes
        const themes = Array.isArray(themesResponse) ? themesResponse : (themesResponse?.themes || []);
        const landingPages = landingsResponse?.landing_pages || [];
        
        const html = `
            <div class="container-fluid">
                <div class="row">
                    <div class="col-12">
                        <h5><i class="fas fa-palette me-2"></i>Temas Esotéricos</h5>
                        <p class="text-muted">Aplica temas místicos y esotéricos a tus landing pages.</p>
                        
                        <!-- Available Themes -->
                        <div class="card mb-4">
                            <div class="card-header">
                                <h6 class="mb-0"><i class="fas fa-magic me-2"></i>Temas Disponibles</h6>
                            </div>
                            <div class="card-body">
                                <div class="row" id="themesContainer">
                                    ${themes.map(theme => `
                                        <div class="col-md-6 mb-3">
                                            <div class="card theme-card ${theme.is_default ? 'border-primary' : ''}" data-theme-id="${theme.id}">
                                                <div class="card-body">
                                                    <div class="d-flex justify-content-between align-items-start mb-2">
                                                        <h6 class="card-title mb-0">${theme.display_name}</h6>
                                                        ${theme.is_default ? '<span class="badge bg-primary">Por Defecto</span>' : ''}
                                                    </div>
                                                    <p class="card-text text-muted small">${theme.description}</p>
                                                    <div class="mb-2">
                                                        <span class="badge bg-secondary">${theme.category}</span>
                                                    </div>
                                                    <button class="btn btn-sm btn-outline-primary" onclick="selectTheme(${theme.id}, '${theme.display_name}')">
                                                        <i class="fas fa-check me-1"></i>Seleccionar
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        </div>
                        
                        <!-- Theme Application -->
                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0"><i class="fas fa-wand-magic me-2"></i>Aplicar Tema</h6>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="selectedTheme" class="form-label">Tema Seleccionado</label>
                                            <input type="text" class="form-control" id="selectedTheme" readonly placeholder="Selecciona un tema">
                                            <input type="hidden" id="selectedThemeId">
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label for="targetLandingPage" class="form-label">Landing Page</label>
                                            <select class="form-select" id="targetLandingPage">
                                                <option value="">Selecciona una landing page</option>
                                                ${landingPages.map(lp => `
                                                    <option value="${lp.id}">${lp.title} ${lp.is_published ? '(Publicada)' : '(Borrador)'}</option>
                                                `).join('')}
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                <div class="d-flex gap-2">
                                    <button class="btn btn-primary" onclick="applyThemeToLandingPage()">
                                        <i class="fas fa-magic me-1"></i>Aplicar Tema
                                    </button>
                                    <button class="btn btn-outline-secondary" onclick="previewTheme()">
                                        <i class="fas fa-eye me-1"></i>Vista Previa
                                    </button>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Theme Info -->
                        <div class="card mt-4" id="themeInfoCard" style="display: none;">
                            <div class="card-header">
                                <h6 class="mb-0"><i class="fas fa-info-circle me-2"></i>Información del Tema</h6>
                            </div>
                            <div class="card-body" id="themeInfoContent">
                                <!-- Theme details will be loaded here -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
        
    } catch (error) {
        console.error('Error loading themes:', error);
        container.innerHTML = `
            <div class="container-fluid">
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Error al cargar los temas. Por favor, intenta de nuevo.
                </div>
            </div>
        `;
    }
}

// Select theme function
function selectTheme(themeId, themeName) {
    document.getElementById('selectedTheme').value = themeName;
    document.getElementById('selectedThemeId').value = themeId;
    
    // Update visual selection
    document.querySelectorAll('.theme-card').forEach(card => {
        card.classList.remove('border-success');
    });
    
    const selectedCard = document.querySelector(`[data-theme-id="${themeId}"]`);
    if (selectedCard) {
        selectedCard.classList.add('border-success');
    }
    
    // Load theme info
    loadThemeInfo(themeId);
}

// Load theme information
async function loadThemeInfo(themeId) {
    try {
        const response = await apiRequest(`/themes/${themeId}`);
        if (response && response.theme) {
            const theme = response.theme;
            const infoCard = document.getElementById('themeInfoCard');
            const infoContent = document.getElementById('themeInfoContent');
            
            infoContent.innerHTML = `
                <div class="row">
                    <div class="col-md-8">
                        <h6>${theme.display_name}</h6>
                        <p class="text-muted">${theme.description}</p>
                        <div class="mb-2">
                            <strong>Categoría:</strong> <span class="badge bg-secondary">${theme.category}</span>
                        </div>
                        ${theme.theme_variables ? `
                            <div class="mb-2">
                                <strong>Variables del tema:</strong>
                                <ul class="list-unstyled ms-3">
                                    ${Object.entries(JSON.parse(theme.theme_variables)).map(([key, value]) => `
                                        <li><code>${key}</code>: ${value}</li>
                                    `).join('')}
                                </ul>
                            </div>
                        ` : ''}
                    </div>
                    <div class="col-md-4">
                        <div class="text-end">
                            <small class="text-muted">Creado: ${new Date(theme.created_at).toLocaleDateString()}</small>
                        </div>
                    </div>
                </div>
            `;
            
            infoCard.style.display = 'block';
        }
    } catch (error) {
        console.error('Error loading theme info:', error);
    }
}

// Apply theme to landing page
async function applyThemeToLandingPage() {
    const themeId = document.getElementById('selectedThemeId').value;
    const landingPageId = document.getElementById('targetLandingPage').value;
    
    if (!themeId || !landingPageId) {
        showAlert('Por favor selecciona un tema y una landing page', 'warning');
        return;
    }
    
    try {
        const response = await apiRequest(`/themes/apply`, {
            method: 'POST',
            body: JSON.stringify({
                theme_id: parseInt(themeId),
                landing_page_id: parseInt(landingPageId)
            })
        });
        
        if (response && response.success) {
            showAlert('Tema aplicado exitosamente', 'success');
            // Refresh landing pages list
            loadLandings();
        } else {
            showAlert('Error al aplicar el tema', 'danger');
        }
    } catch (error) {
        console.error('Error applying theme:', error);
        showAlert('Error al aplicar el tema', 'danger');
    }
}

// Preview theme (placeholder for future implementation)
function previewTheme() {
    const themeId = document.getElementById('selectedThemeId').value;
    const landingPageId = document.getElementById('targetLandingPage').value;
    
    if (!themeId || !landingPageId) {
        showAlert('Por favor selecciona un tema y una landing page para la vista previa', 'warning');
        return;
    }
    
    showAlert('Vista previa del tema - Funcionalidad en desarrollo', 'info');
}

// Mostrar vista previa de landing generada
function showGeneratedLandingPreview(htmlContent, landingPageData) {
    // Switch to themes tab
    const temasTab = document.getElementById('temas-tab');
    if (temasTab) {
        temasTab.click();
    }
    
    setTimeout(() => {
        const container = document.getElementById('generatedLandingsContainer');
        
        const html = `
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">
                        <i class="fas fa-magic me-2"></i>Landing Page Generada: ${landingPageData.title}
                    </h6>
                    <div>
                        <button class="btn btn-sm btn-outline-primary me-2" onclick="downloadLandingHTML(${landingPageData.id})">
                            <i class="fas fa-download me-1"></i>Descargar HTML
                        </button>
                        <button class="btn btn-sm btn-primary" onclick="viewLandingPage(${landingPageData.id})">
                            <i class="fas fa-external-link-alt me-1"></i>Ver Completa
                        </button>
                    </div>
                </div>
                <div class="card-body p-0">
                    <iframe srcdoc="${htmlContent.replace(/"/g, '&quot;')}" 
                            style="width: 100%; height: 600px; border: none; border-radius: 0 0 0.375rem 0.375rem;"></iframe>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }, 500);
}

// Descargar HTML de landing page
async function downloadLandingHTML(landingId) {
    try {
        const response = await apiRequest(`/landings/creador/landing-pages/${landingId}`);
        
        if (response && response.landing_page) {
            const lp = response.landing_page;
            const blob = new Blob([lp.html_content], { type: 'text/html' });
            const url = window.URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `${lp.slug || 'landing-page'}.html`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showAlert('HTML descargado exitosamente', 'success');
        }
    } catch (error) {
        console.error('Error downloading HTML:', error);
        showAlert('Error al descargar el HTML', 'danger');
    }
}

// Navigation Functions
function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.style.display = 'none';
    });
    
    // Show selected section
    document.getElementById(`${sectionName}-section`).style.display = 'block';
    
    // Update navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // Add active class to current section
    const currentLink = document.querySelector(`[onclick="showSection('${sectionName}')"]`);
    if (currentLink) {
        currentLink.classList.add('active');
    }
    
    // Load DALL-E gallery when content section is shown
    if (sectionName === 'content') {
        setTimeout(() => {
            if (typeof loadDalleGallery === 'function') {
                loadDalleGallery();
            }
        }, 100);
    }
    
    // Save current section to localStorage
    localStorage.setItem('activeSection', sectionName);
    
    // Load section-specific data
    switch(sectionName) {
        case 'keywords':
            loadKeywords();
            break;
        case 'content':
            loadContentList();
            break;
        case 'images':
            // Image tab functionality removed
            break;
        case 'scheduler':
            loadSchedulerStatus();
            break;
        case 'landings':
            loadLandings();
            break;
        case 'creador':
            loadCreadorSection();
            break;
        case 'temas':
            loadThemesAndTemplates();
            break;
        case 'settings':
            initializeApiSettings();
            break;
    }
}

// Function to restore active section on page load
function restoreActiveSection() {
    const savedSection = localStorage.getItem('activeSection');
    if (savedSection && authToken) {
        // Only restore if user is authenticated
        const sectionElement = document.getElementById(`${savedSection}-section`);
        if (sectionElement) {
            showSection(savedSection);
        }
    }
}

// Utility Functions
// Función para verificar si el token está próximo a expirar
function isTokenExpiringSoon(token) {
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const exp = payload.exp * 1000; // Convertir a milisegundos
        const now = Date.now();
        const timeUntilExpiry = exp - now;
        
        // Si expira en menos de 5 minutos (300000 ms), considerarlo próximo a expirar
        return timeUntilExpiry < 300000;
    } catch (error) {
        console.error('Error parsing token:', error);
        return true; // Si no se puede parsear, asumir que está expirado
    }
}

// Función para verificar la validez del token
async function verifyToken() {
    const token = localStorage.getItem('authToken');
    if (!token) return false;
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/verify-token`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        return response.ok;
    } catch (error) {
        console.error('Error verifying token:', error);
        return false;
    }
}

async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const token = localStorage.getItem('authToken');
    
    console.log('apiRequest - endpoint:', endpoint);
    console.log('apiRequest - token from localStorage:', token ? 'EXISTS' : 'NULL');
    console.log('apiRequest - authToken variable:', authToken ? 'EXISTS' : 'NULL');
    
    if (!token) {
        console.error('No auth token found, redirecting to login');
        console.log('localStorage contents:', localStorage);
        showAlert('Tu sesión ha expirado. Por favor, inicia sesión nuevamente.', 'warning');
        logout();
        return null;
    }
    
    // Verificar si el token está próximo a expirar
    if (isTokenExpiringSoon(token)) {
        console.warn('Token is expiring soon');
        const isValid = await verifyToken();
        if (!isValid) {
            showAlert('Tu sesión ha expirado. Por favor, inicia sesión nuevamente.', 'warning');
            logout();
            return null;
        }
    }
    
    // Update global authToken variable
    authToken = token;
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        }
    };
    
    // Merge headers properly to avoid overwriting Authorization
    const mergedHeaders = { ...defaultOptions.headers, ...(options.headers || {}) };
    const finalOptions = { ...defaultOptions, ...options, headers: mergedHeaders };
    
    console.log('apiRequest - final headers:', finalOptions.headers);
    
    try {
        const response = await fetch(url, finalOptions);
        
        if (response.status === 401) {
            showAlert('Tu sesión ha expirado. Por favor, inicia sesión nuevamente.', 'warning');
            logout();
            return null;
        }
        
        if (!response.ok) {
            // Manejar errores específicos
            if (response.status === 403) {
                showAlert('No tienes permisos para realizar esta acción.', 'danger');
            } else if (response.status >= 500) {
                showAlert('Error del servidor. Por favor, intenta nuevamente.', 'danger');
            } else {
                showAlert(`Error en la petición: ${response.status}`, 'danger');
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const contentType = response.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
            return await response.json();
        } else {
            return true; // Success, but no JSON response
        }
    } catch (error) {
        console.error('API request error:', error);
        if (error.message.includes('Failed to fetch')) {
            showAlert('Error de conexión. Verifica tu conexión a internet.', 'danger');
        }
        throw error;
    }
}

function showLoading(show) {
    if (show) {
        loadingSpinner.classList.remove('d-none');
    } else {
        loadingSpinner.classList.add('d-none');
    }
}

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getDifficultyColor(difficulty) {
    switch(difficulty) {
        case 'easy': return 'success';
        case 'medium': return 'warning';
        case 'hard': return 'danger';
        default: return 'secondary';
    }
}

function getPriorityColor(priority) {
    switch(priority) {
        case 'high': return 'danger';
        case 'medium': return 'warning';
        case 'low': return 'success';
        default: return 'secondary';
    }
}

function getPriorityText(priority) {
    switch(priority) {
        case 'high': return 'Alta';
        case 'medium': return 'Media';
        case 'low': return 'Baja';
        default: return 'N/A';
    }
}

function getStatusColor(status) {
    switch(status) {
        case 'pending': return 'secondary';
        case 'processing': return 'primary';
        case 'completed': return 'success';
        case 'failed': return 'danger';
        default: return 'secondary';
    }
}

function getStatusText(status) {
    switch(status) {
        case 'pending': return 'Pendiente';
        case 'processing': return 'Procesando';
        case 'completed': return 'Completado';
        case 'failed': return 'Fallido';
        default: return 'N/A';
    }
}

// Function to edit keyword
async function editKeyword(keywordId) {
    try {
        showLoading(true);
        const keyword = await apiRequest(`/keywords/${keywordId}`);
        if (keyword) {
            // Fill form with keyword data
            document.getElementById('keywordText').value = keyword.keyword || '';
            document.getElementById('prioritySelect').value = keyword.priority || 'medium';
            document.getElementById('searchVolumeInput').value = keyword.search_volume || '';
            document.getElementById('difficultyInput').value = keyword.difficulty || '';
            document.getElementById('categoryInput').value = keyword.category || '';
            document.getElementById('notesInput').value = keyword.notes || '';
            
            // Change form submit to update mode
            const form = document.getElementById('keywordForm');
            form.onsubmit = (e) => updateKeyword(e, keywordId);
            
            // Change button text
            const submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.textContent = 'Actualizar Keyword';
            
            // Add cancel button if not exists
            let cancelBtn = form.querySelector('.cancel-edit-btn');
            if (!cancelBtn) {
                cancelBtn = document.createElement('button');
                cancelBtn.type = 'button';
                cancelBtn.className = 'btn btn-secondary ms-2 cancel-edit-btn';
                cancelBtn.textContent = 'Cancelar';
                cancelBtn.onclick = cancelEditKeyword;
                submitBtn.parentNode.appendChild(cancelBtn);
            }
        }
    } catch (error) {
        console.error('Error loading keyword for edit:', error);
        showAlert('Error cargando keyword para editar', 'danger');
    } finally {
        showLoading(false);
    }
}

// Function to update keyword
async function updateKeyword(e, keywordId) {
    e.preventDefault();
    
    const keyword = document.getElementById('keywordText').value;
    const priority = document.getElementById('prioritySelect').value;
    const searchVolume = document.getElementById('searchVolumeInput').value;
    const difficulty = document.getElementById('difficultyInput').value;
    const category = document.getElementById('categoryInput').value;
    const notes = document.getElementById('notesInput').value;
    
    showLoading(true);
    
    try {
        const keywordData = {
            keyword: keyword.trim(),
            priority: priority,
            search_volume: searchVolume ? parseInt(searchVolume) : null,
            difficulty: difficulty ? parseFloat(difficulty) : null,
            category: category.trim() || null,
            notes: notes.trim() || null
        };
        
        const response = await apiRequest(`/keywords/${keywordId}`, {
            method: 'PUT',
            body: JSON.stringify(keywordData)
        });
        
        if (response) {
            showAlert('Keyword actualizada exitosamente', 'success');
            cancelEditKeyword();
            await loadKeywords();
        }
    } catch (error) {
        showAlert('Error al actualizar keyword', 'danger');
        console.error('Error updating keyword:', error);
    } finally {
        showLoading(false);
    }
}

// Function to cancel edit mode
function cancelEditKeyword() {
    const form = document.getElementById('keywordForm');
    form.reset();
    form.onsubmit = handleAddKeyword;
    
    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.textContent = 'Agregar Keyword';
    
    const cancelBtn = form.querySelector('.cancel-edit-btn');
    if (cancelBtn) {
        cancelBtn.remove();
    }
}

// Content Management Functions
function showCreateContentModal() {
    if (!createContentModal) {
        createContentModal = new bootstrap.Modal(document.getElementById('createContentModal'));
    }
    
    // Load categories, tags, templates, and keywords
    loadCategoriesForForm();
    loadTagsForForm();
    loadTemplatesForForm();
    loadKeywordsForGeneration();
    
    // Reset form
    document.getElementById('createContentForm').reset();
    document.getElementById('contentSlug').value = '';
    document.getElementById('scheduledDateGroup').style.display = 'none';
    
    // Show AI generation card and reset to AI mode
    document.getElementById('aiGenerationCard').style.display = 'block';
    
    // Reset save button to create mode
    const saveButton = document.querySelector('#createContentModal .btn-primary');
    saveButton.textContent = 'Guardar Contenido';
    saveButton.onclick = saveContent;
    
    createContentModal.show();
}

async function loadCategoriesForForm() {
    try {
        const response = await apiRequest('/categories/');
        if (response) {
            categories = response;
            const categoryDatalist = document.getElementById('categoryOptions');
            categoryDatalist.innerHTML = '';
            
            categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category.name;
                option.setAttribute('data-id', category.id);
                categoryDatalist.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

async function loadTagsForForm() {
    try {
        const response = await apiRequest('/tags/');
        if (response) {
            tags = response;
        }
    } catch (error) {
        console.error('Error loading tags:', error);
    }
}

async function loadTemplatesForForm() {
    try {
        const templates = await apiRequest('/templates/');
        const templateSelect = document.getElementById('templateTheme');
        if (templateSelect && templates) {
            templateSelect.innerHTML = '';
            templates.forEach(template => {
                const option = document.createElement('option');
                option.value = template.id;
                option.textContent = template.name;
                templateSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading templates:', error);
        // Set default options if API fails
        const templateSelect = document.getElementById('templateTheme');
        if (templateSelect) {
            templateSelect.innerHTML = `
                <option value="default">Default</option>
                <option value="dark">Dark - Oscuro Minimalista</option>
                <option value="light">Light - Claro Minimalista</option>
            `;
        }
    }
}

async function loadKeywordsForGeneration() {
    try {
        const response = await apiRequest('/keywords/');
        if (response) {
            const keywordSelect = document.getElementById('selectedKeywords');
            keywordSelect.innerHTML = '';
            
            response.forEach(keyword => {
                const option = document.createElement('option');
                option.value = keyword.id;
                option.textContent = `${keyword.keyword} (${getPriorityText(keyword.priority)} - Vol: ${keyword.search_volume || 'N/A'})`;
                keywordSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading keywords:', error);
        showAlert('Error cargando keywords', 'warning');
    }
}

function toggleManualMode() {
    const aiCard = document.getElementById('aiGenerationCard');
    const isHidden = aiCard.style.display === 'none';
    
    if (isHidden) {
        aiCard.style.display = 'block';
    } else {
        aiCard.style.display = 'none';
    }
}

async function generateContentWithAI() {
    const selectedKeywords = Array.from(document.getElementById('selectedKeywords').selectedOptions)
        .map(option => parseInt(option.value));
    
    if (selectedKeywords.length === 0) {
        showAlert('Debe seleccionar al menos una keyword', 'warning');
        return;
    }
    
    const provider = document.getElementById('aiProvider').value;
    const contentType = document.getElementById('contentType').value;
    
    showLoading(true);
    
    try {
        // For multiple keywords, we'll use the first one as primary and mention others in the prompt
        const primaryKeywordId = selectedKeywords[0];
        
        const response = await apiRequest(`/content/generate/${primaryKeywordId}`, {
            method: 'POST',
            body: JSON.stringify({
                provider: provider,
                content_type: contentType,
                additional_keywords: selectedKeywords.slice(1) // Send additional keywords if any
            })
        });
        
        if (response) {
            showAlert('Generación de contenido iniciada. El contenido se creará en segundo plano.', 'info');
            
            // Poll for the generated content
            pollForGeneratedContent(response.content_id);
        }
    } catch (error) {
        console.error('Error generating content:', error);
        showAlert('Error al generar contenido con IA', 'danger');
    } finally {
        showLoading(false);
    }
}

async function pollForGeneratedContent(contentId, attempts = 0) {
    const maxAttempts = 30; // 30 attempts = 5 minutes
    
    if (attempts >= maxAttempts) {
        showAlert('La generación de contenido está tomando más tiempo del esperado. Revisa la lista de contenido más tarde.', 'warning');
        return;
    }
    
    try {
        const content = await apiRequest(`/content/${contentId}`);
        
        if (content && content.content && content.content.trim() !== '') {
            // Content has been generated, fill the form
            document.getElementById('contentTitle').value = content.title || '';
            document.getElementById('contentSlug').value = content.slug || '';
            document.getElementById('contentExcerpt').value = content.excerpt || '';
            document.getElementById('contentBody').value = content.content || '';
            document.getElementById('contentMetaTitle').value = content.meta_title || '';
            document.getElementById('contentMetaDescription').value = content.meta_description || '';
            
            showAlert('¡Contenido generado exitosamente! Puedes editarlo antes de guardar.', 'success');
            
            // Hide AI generation card and show manual editing
            document.getElementById('aiGenerationCard').style.display = 'none';
        } else {
            // Content not ready yet, poll again in 10 seconds
            setTimeout(() => pollForGeneratedContent(contentId, attempts + 1), 10000);
        }
    } catch (error) {
        console.error('Error polling for content:', error);
        setTimeout(() => pollForGeneratedContent(contentId, attempts + 1), 10000);
    }
}

async function generateContentFromKeyword(keywordId) {
    if (!confirm('¿Deseas generar contenido automáticamente para esta keyword?')) {
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await apiRequest(`/content/generate/${keywordId}`, {
            method: 'POST',
            body: JSON.stringify({
                provider: 'openai',
                content_type: 'article',
                additional_keywords: []
            })
        });
        
        if (response && response.content_id) {
            showLoading(false);
            showAlert('Generación de contenido iniciada', 'info');
            
            // Mostrar ventana de progreso
            showGenerationProgress(response.content_id, keywordId);
        }
    } catch (error) {
        console.error('Error generating content:', error);
        showAlert('Error al generar contenido', 'danger');
        showLoading(false);
    }
}

async function saveContent() {
    const contentId = document.getElementById('contentId').value;
    const title = document.getElementById('contentTitle').value.trim();
    let body = document.getElementById('contentBody').value.trim();
    
    if (!title || !body) {
        showAlert('El título y el contenido son obligatorios', 'warning');
        return;
    }
    
    // Process content for semantic HTML if it doesn't already contain HTML tags
    body = processContentForDisplay(body);
    
    showLoading(true);
    
    try {
        // Handle category - can be existing or new
        const categoryInput = document.getElementById('contentCategory').value.trim();
        let categoryId = null;
        
        if (categoryInput) {
            // Check if it's an existing category
            const existingCategory = categories.find(cat => cat.name.toLowerCase() === categoryInput.toLowerCase());
            if (existingCategory) {
                categoryId = existingCategory.id;
            } else {
                // It's a new category, we'll send the name and let the backend create it
                categoryId = categoryInput; // Send the name for new categories
            }
        }
        
        const contentData = {
            title: title,
            slug: document.getElementById('contentSlug').value.trim() || generateSlug(title),
            excerpt: document.getElementById('contentExcerpt').value.trim(),
            content: body,
            status: document.getElementById('contentStatus').value,
            category_id: categoryId,
            meta_title: document.getElementById('contentMetaTitle').value.trim(),
            meta_description: document.getElementById('contentMetaDescription').value.trim(),
            template_theme: document.getElementById('templateTheme').value || 'default'
        };
        
        // Handle scheduled date
        if (contentData.status === 'scheduled') {
            const scheduledDate = document.getElementById('contentScheduledDate').value;
            if (scheduledDate) {
                contentData.scheduled_at = new Date(scheduledDate).toISOString();
            } else {
                showAlert('Debe especificar una fecha para contenido programado', 'warning');
                return;
            }
        }
        
        // Handle tags (for now, we'll skip tags as they need to be created first)
        const tagsInput = document.getElementById('contentTags').value.trim();
        if (tagsInput) {
            // For now, we'll just store as empty array since we need tag IDs
            contentData.tag_ids = [];
        }
        
        let response;
        if (contentId) {
            // Update existing content
            response = await apiRequest(`/content/${contentId}`, {
                method: 'PUT',
                body: JSON.stringify(contentData)
            });
        } else {
            // Create new content
            response = await apiRequest('/content/', {
                method: 'POST',
                body: JSON.stringify(contentData)
            });
        }
        
        if (response) {
            createContentModal.hide();
            showAlert(`Contenido ${contentId ? 'actualizado' : 'creado'} exitosamente`, 'success');
            
            // Reload content list separately to avoid showing error if this fails
            try {
                await loadContentList();
            } catch (listError) {
                console.error('Error reloading content list:', listError);
                // Don't show error to user since the save was successful
            }
        }
    } catch (error) {
        console.error(`Error ${contentId ? 'updating' : 'creating'} content:`, error);
        showAlert(`Error al ${contentId ? 'actualizar' : 'crear'} el contenido`, 'danger');
    } finally {
        showLoading(false);
    }
}

function generateSlug(title) {
    return title
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, '')
        .replace(/\s+/g, '-')
        .replace(/-+/g, '-')
        .trim('-');
}

async function loadContentList() {
    try {
        const response = await apiRequest('/content/');
        if (response) {
            displayContentList(response);
        }
    } catch (error) {
        console.error('Error loading content:', error);
        showAlert('Error cargando la lista de contenido', 'warning');
    }
}

function displayContentList(contentList) {
    const contentDiv = document.getElementById('contentList');
    
    if (!contentList || contentList.length === 0) {
        contentDiv.innerHTML = '<p class="text-muted">No hay contenido disponible. <a href="#" onclick="showCreateContentModal()">Crear el primero</a></p>';
        return;
    }
    
    let html = '<div class="row">';
    
    contentList.forEach(content => {
        const statusBadge = getStatusBadge(content.status);
        const categoryName = content.category ? content.category.name : 'Sin categoría';
        const excerpt = content.excerpt || (content.content ? content.content.substring(0, 150) + '...' : 'Sin contenido');
        
        // Add dynamic border class based on status
        const cardClass = content.status === 'published' ? 'card h-100 border-success' : 'card h-100';
        
        html += `
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="${cardClass}">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="card-title">${content.title}</h6>
                            ${statusBadge}
                        </div>
                        <p class="card-text text-muted small">${excerpt}</p>
                        <div class="mb-2">
                            <small class="text-muted">
                                <i class="fas fa-folder me-1"></i>${categoryName}
                            </small>
                        </div>
                        ${content.tags && content.tags.length > 0 ? `
                            <div class="mb-2">
                                ${content.tags.map(tag => `<span class="badge bg-secondary me-1">${tag.name}</span>`).join('')}
                            </div>
                        ` : ''}
                        <div class="d-flex justify-content-between align-items-center">
                            <small class="text-muted">${formatDate(content.created_at)}</small>
                            <div class="btn-group btn-group-sm">
                                ${content.status === 'published' ? `
                                    <button class="btn btn-outline-success" onclick="viewContent('${content.slug}')" title="Ver contenido">
                                        <i class="fas fa-eye"></i>
                                    </button>
                                ` : ''}
                                <button class="btn btn-outline-primary" onclick="editContent(${content.id})" title="Editar">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-outline-danger" onclick="deleteContent(${content.id})" title="Eliminar">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    contentDiv.innerHTML = html;
}

function getStatusBadge(status) {
    const badges = {
        'draft': '<span class="badge bg-secondary">Borrador</span>',
        'published': '<span class="badge bg-success">Publicado</span>',
        'scheduled': '<span class="badge bg-warning">Programado</span>'
    };
    return badges[status] || '<span class="badge bg-secondary">Desconocido</span>';
}

async function editContent(contentId) {
    try {
        showLoading(true);
        const content = await apiRequest(`/content/${contentId}`);
        if (content) {
            // Load categories, tags and templates first
            await loadCategoriesForForm();
            await loadTagsForForm();
            await loadTemplatesForForm();
            
            // Reset form first
            document.getElementById('createContentForm').reset();
            
            // Fill form with content data
            document.getElementById('contentId').value = content.id; // Add this line
            document.getElementById('contentTitle').value = content.title || '';
            document.getElementById('contentSlug').value = content.slug || '';
            document.getElementById('contentExcerpt').value = content.excerpt || '';
            document.getElementById('contentBody').value = content.content || '';
            document.getElementById('contentStatus').value = content.status || 'draft';
            document.getElementById('contentCategory').value = content.category ? content.category.name : '';
            document.getElementById('contentMetaTitle').value = content.meta_title || '';
            document.getElementById('contentMetaDescription').value = content.meta_description || '';
            document.getElementById('templateTheme').value = content.template_theme || 'default';
            
            // Handle tags
            if (content.tags && content.tags.length > 0) {
                document.getElementById('contentTags').value = content.tags.map(tag => tag.name).join(', ');
            } else {
                document.getElementById('contentTags').value = '';
            }
            
            // Handle scheduled date
            if (content.status === 'scheduled' && content.scheduled_at) {
                const scheduledDate = new Date(content.scheduled_at);
                // Format date for datetime-local input
                const formattedDate = scheduledDate.toISOString().slice(0, 16);
                document.getElementById('contentScheduledDate').value = formattedDate;
                document.getElementById('scheduledDateGroup').style.display = 'block';
            } else {
                document.getElementById('contentScheduledDate').value = '';
                document.getElementById('scheduledDateGroup').style.display = 'none';
            }
            
            // Show the modal
            if (!createContentModal) {
                createContentModal = new bootstrap.Modal(document.getElementById('createContentModal'));
            }
            createContentModal.show();
        }
    } catch (error) {
        console.error('Error editing content:', error);
        showAlert('Error cargando el contenido para editar', 'danger');
    } finally {
        showLoading(false);
    }
}

// Function to view published content
function viewContent(slug) {
    // Open content in new tab/window
    const contentUrl = `${window.location.origin}/content/${slug}`;
    window.open(contentUrl, '_blank');
}

async function updateContent(contentId) {
    const title = document.getElementById('contentTitle').value.trim();
    let body = document.getElementById('contentBody').value.trim();
    
    if (!title || !body) {
        showAlert('El título y el contenido son obligatorios', 'warning');
        return;
    }
    
    // Process content for semantic HTML if it doesn't already contain HTML tags
    body = processContentForDisplay(body);
    
    showLoading(true);
    
    try {
        const contentData = {
            title: title,
            slug: document.getElementById('contentSlug').value.trim() || generateSlug(title),
            excerpt: document.getElementById('contentExcerpt').value.trim(),
            content: body,
            status: document.getElementById('contentStatus').value,
            category_id: document.getElementById('contentCategory').value || null,
            meta_title: document.getElementById('contentMetaTitle').value.trim(),
            meta_description: document.getElementById('contentMetaDescription').value.trim(),
            template_theme: document.getElementById('templateTheme').value || 'default'
        };
        
        // Handle scheduled date
        if (contentData.status === 'scheduled') {
            const scheduledDate = document.getElementById('contentScheduledDate').value;
            if (scheduledDate) {
                contentData.scheduled_at = new Date(scheduledDate).toISOString();
            } else {
                showAlert('Debe especificar una fecha para contenido programado', 'warning');
                return;
            }
        }
        
        // Handle tags (for now, we'll skip tags as they need to be created first)
        const tagsInput = document.getElementById('contentTags').value.trim();
        if (tagsInput) {
            // For now, we'll just store as empty array since we need tag IDs
            contentData.tag_ids = [];
        }
        
        const response = await apiRequest(`/content/${contentId}`, {
            method: 'PUT',
            body: JSON.stringify(contentData)
        });
        
        if (response) {
            createContentModal.hide();
            showAlert('Contenido actualizado exitosamente', 'success');
            
            // Reset save button
            const saveButton = document.querySelector('#createContentModal .btn-primary');
            saveButton.textContent = 'Guardar Contenido';
            saveButton.onclick = saveContent;
            
            // Reload content list separately to avoid showing error if this fails
            try {
                await loadContentList();
            } catch (listError) {
                console.error('Error reloading content list:', listError);
                // Don't show error to user since the update was successful
            }
        }
    } catch (error) {
        console.error('Error updating content:', error);
        showAlert('Error al actualizar el contenido', 'danger');
    } finally {
        showLoading(false);
    }
}

async function deleteContent(contentId) {
    if (!confirm('¿Estás seguro de que quieres eliminar este contenido?')) {
        return;
    }
    
    showLoading(true);
    
    try {
        await apiRequest(`/content/${contentId}`, {
            method: 'DELETE'
        });
        
        showAlert('Contenido eliminado exitosamente', 'success');
        
        // Reload content list separately to avoid showing error if this fails
        try {
            await loadContentList();
        } catch (listError) {
            console.error('Error reloading content list:', listError);
            // Don't show error to user since the deletion was successful
        }
    } catch (error) {
        console.error('Error deleting content:', error);
        showAlert('Error al eliminar el contenido', 'danger');
    } finally {
        showLoading(false);
    }
}

// Content Editor Functions
function insertTag(tag) {
    const textarea = document.getElementById('contentBody');
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = textarea.value.substring(start, end);
    
    let replacement;
    if (selectedText) {
        replacement = `<${tag}>${selectedText}</${tag}>`;
    } else {
        replacement = `<${tag}></${tag}>`;
    }
    
    textarea.value = textarea.value.substring(0, start) + replacement + textarea.value.substring(end);
    
    // Position cursor inside the tag if no text was selected
    if (!selectedText) {
        textarea.setSelectionRange(start + tag.length + 2, start + tag.length + 2);
    } else {
        textarea.setSelectionRange(start + replacement.length, start + replacement.length);
    }
    
    textarea.focus();
}

function insertList(listType) {
    const textarea = document.getElementById('contentBody');
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = textarea.value.substring(start, end);
    
    let replacement;
    if (selectedText) {
        const lines = selectedText.split('\n').filter(line => line.trim());
        const listItems = lines.map(line => `  <li>${line.trim()}</li>`).join('\n');
        replacement = `<${listType}>\n${listItems}\n</${listType}>`;
    } else {
        replacement = `<${listType}>\n  <li></li>\n</${listType}>`;
    }
    
    textarea.value = textarea.value.substring(0, start) + replacement + textarea.value.substring(end);
    
    // Position cursor inside the first li tag
    const newPosition = start + replacement.indexOf('<li>') + 4;
    textarea.setSelectionRange(newPosition, newPosition);
    textarea.focus();
}

function formatParagraphs() {
    const textarea = document.getElementById('contentBody');
    let content = textarea.value;
    
    // Remove existing <p> tags to avoid duplication
    content = content.replace(/<\/?p>/g, '');
    
    // Split by double line breaks and create paragraphs
    const paragraphs = content.split(/\n\s*\n/)
        .map(p => p.trim())
        .filter(p => p.length > 0)
        .map(p => {
            // Don't wrap if it's already an HTML tag
            if (p.match(/^<(h[1-6]|blockquote|ul|ol|div)/i)) {
                return p;
            }
            return `<p>${p}</p>`;
        });
    
    textarea.value = paragraphs.join('\n\n');
    
    showAlert('Párrafos formateados automáticamente', 'success');
}

function processContentForDisplay(content) {
    if (!content) return '';
    
    // If content doesn't have HTML tags, auto-format paragraphs
    if (!content.includes('<') && !content.includes('>')) {
        const paragraphs = content.split(/\n\s*\n/)
            .map(p => p.trim())
            .filter(p => p.length > 0)
            .map(p => `<p>${p}</p>`);
        return paragraphs.join('\n');
    }
    
    return content;
}

// API Settings Functions
async function loadApiStatus() {
    try {
        const response = await apiRequest('/users/api-status');
        if (response) {
            updateApiStatusDisplay(response);
        }
    } catch (error) {
        console.error('Error loading API status:', error);
        showAlert('Error al cargar el estado de las APIs', 'danger');
    }
}

function updateApiStatusDisplay(status) {
    // Update OpenAI status
    const openaiStatusBadge = document.getElementById('openaiStatusBadge');
    const openaiApiKeyInput = document.getElementById('openaiApiKey');
    
    if (status.openai.configured) {
        openaiStatusBadge.textContent = 'Configurado';
        openaiStatusBadge.className = 'badge bg-success';
        openaiApiKeyInput.placeholder = status.openai.key_preview || 'API Key configurada';
    } else {
        openaiStatusBadge.textContent = 'No configurado';
        openaiStatusBadge.className = 'badge bg-secondary';
        openaiApiKeyInput.placeholder = 'sk-...';
    }
    
    // Update DeepSeek status
    const deepseekStatusBadge = document.getElementById('deepseekStatusBadge');
    const deepseekApiKeyInput = document.getElementById('deepseekApiKey');
    
    if (status.deepseek.configured) {
        deepseekStatusBadge.textContent = 'Configurado';
        deepseekStatusBadge.className = 'badge bg-success';
        deepseekApiKeyInput.placeholder = status.deepseek.key_preview || 'API Key configurada';
    } else {
        deepseekStatusBadge.textContent = 'No configurado';
        deepseekStatusBadge.className = 'badge bg-secondary';
        deepseekApiKeyInput.placeholder = 'sk-...';
    }
}

function togglePasswordVisibility(inputId) {
    const input = document.getElementById(inputId);
    const button = input.nextElementSibling;
    const icon = button.querySelector('i');
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.className = 'fas fa-eye-slash';
    } else {
        input.type = 'password';
        icon.className = 'fas fa-eye';
    }
}

async function testApiConnection(provider) {
    const apiKeyInput = document.getElementById(`${provider}ApiKey`);
    const statusDiv = document.getElementById(`${provider}Status`);
    const apiKey = apiKeyInput.value.trim();
    
    if (!apiKey) {
        showAlert(`Por favor ingresa la API key de ${provider}`, 'warning');
        return;
    }
    
    // Show loading state
    statusDiv.innerHTML = '<div class="alert alert-info mb-0"><i class="fas fa-spinner fa-spin me-1"></i>Probando conexión...</div>';
    
    try {
        const response = await apiRequest('/users/test-api-connection', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: new URLSearchParams({
                provider: provider,
                api_key: apiKey
            })
        });
        
        if (response.success) {
            statusDiv.innerHTML = `
                <div class="alert alert-success mb-0">
                    <i class="fas fa-check-circle me-1"></i>${response.message}
                    ${response.model ? `<br><small>Modelo: ${response.model}</small>` : ''}
                    ${response.usage ? `<br><small>Tokens usados: ${response.usage.total_tokens || 'N/A'}</small>` : ''}
                </div>
            `;
        } else {
            statusDiv.innerHTML = `
                <div class="alert alert-danger mb-0">
                    <i class="fas fa-exclamation-circle me-1"></i>${response.message}
                </div>
            `;
        }
    } catch (error) {
        console.error('Error testing API connection:', error);
        statusDiv.innerHTML = `
            <div class="alert alert-danger mb-0">
                <i class="fas fa-exclamation-circle me-1"></i>Error al probar la conexión
            </div>
        `;
    }
}

async function saveApiKey(provider) {
    const apiKeyInput = document.getElementById(`${provider}ApiKey`);
    const statusDiv = document.getElementById(`${provider}Status`);
    const apiKey = apiKeyInput.value.trim();
    
    if (!apiKey) {
        showAlert(`Por favor ingresa la API key de ${provider}`, 'warning');
        return;
    }
    
    // Show loading state
    statusDiv.innerHTML = '<div class="alert alert-info mb-0"><i class="fas fa-spinner fa-spin me-1"></i>Guardando...</div>';
    
    try {
        const updateData = {};
        updateData[`api_key_${provider}`] = apiKey;
        
        const response = await apiRequest('/users/profile', {
            method: 'PUT',
            body: JSON.stringify(updateData)
        });
        
        if (response) {
            statusDiv.innerHTML = `
                <div class="alert alert-success mb-0">
                    <i class="fas fa-check-circle me-1"></i>API key guardada exitosamente
                </div>
            `;
            
            // Clear the input for security
            apiKeyInput.value = '';
            
            // Update status display
            loadApiStatus();
            
            showAlert(`API key de ${provider} guardada exitosamente`, 'success');
        }
    } catch (error) {
        console.error('Error saving API key:', error);
        statusDiv.innerHTML = `
            <div class="alert alert-danger mb-0">
                <i class="fas fa-exclamation-circle me-1"></i>Error al guardar la API key
            </div>
        `;
        showAlert('Error al guardar la API key', 'danger');
    }
}

// Initialize API settings when settings section is shown
function initializeApiSettings() {
    loadApiStatus();
}

// Content Generation Progress Functions
function showGenerationProgress(contentId, keywordId) {
    // Create progress modal
    const progressModal = document.createElement('div');
    progressModal.className = 'modal fade';
    progressModal.id = 'generationProgressModal';
    progressModal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">
                        <i class="fas fa-magic me-2"></i>Generando Contenido con IA
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="text-center mb-4">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Generando...</span>
                        </div>
                        <p class="mt-3 mb-0" id="progressMessage">Iniciando generación de contenido...</p>
                        <small class="text-muted" id="progressDetails">Esto puede tomar entre 30 segundos y 2 minutos</small>
                    </div>
                    
                    <div class="progress mb-3">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                             role="progressbar" style="width: 25%" id="progressBar">
                            25%
                        </div>
                    </div>
                    
                    <div id="generationStatus" class="alert alert-info">
                        <i class="fas fa-info-circle me-2"></i>
                        Conectando con la IA para generar contenido optimizado...
                    </div>
                    
                    <div id="contentPreview" class="d-none">
                        <h6>Vista Previa del Contenido Generado:</h6>
                        <div class="border rounded p-3 bg-light">
                            <h6 id="previewTitle" class="text-primary"></h6>
                            <p id="previewContent" class="text-muted"></p>
                            <div class="d-flex justify-content-between text-sm">
                                <span id="previewWordCount"></span>
                                <span id="previewReadingTime"></span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer" id="progressFooter">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                    <button type="button" class="btn btn-primary d-none" id="editContentBtn" onclick="editGeneratedContent()">Editar Contenido</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(progressModal);
    const modal = new bootstrap.Modal(progressModal);
    modal.show();
    
    // Start polling for progress
    pollGenerationProgress(contentId, modal, 0);
    
    // Store content ID for later use
    window.currentGeneratingContentId = contentId;
    
    // Clean up modal when closed
    progressModal.addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(progressModal);
        window.currentGeneratingContentId = null;
    });
}

async function pollGenerationProgress(contentId, modal, attempts) {
    const maxAttempts = 60; // 3 minutos máximo (60 * 3 segundos) - aumentado para incluir imágenes
    
    if (attempts >= maxAttempts) {
        updateProgressStatus('timeout', {
            message: 'Tiempo de espera agotado. La generación puede continuar en segundo plano.',
            details: 'Revisa la lista de contenido en unos minutos.'
        });
        return;
    }
    
    try {
        const response = await apiRequest(`/content/generation-status/${contentId}`);
        
        if (response) {
            // Calcular progreso basado en las fases
            let progress = 10; // Inicio
            
            if (response.progress.text_generating) {
                progress = Math.min(10 + (attempts * 2), 50); // Texto: 10-50%
                updateProgressMessage('Generando contenido de texto...');
            } else if (response.progress.image_generating) {
                progress = Math.min(50 + (attempts * 2), 90); // Imágenes: 50-90%
                updateProgressMessage('Generando imágenes con IA...');
                updateImageProgress(response.images);
            } else if (response.progress.completed) {
                progress = 100;
                updateProgressBar(100);
                updateProgressStatus('completed', {
                    title: response.title,
                    content: response.content_preview,
                    word_count: response.word_count,
                    reading_time: response.reading_time,
                    images: response.images
                });
                showContentPreview(response);
                return;
            } else if (response.progress.failed) {
                updateProgressStatus('failed', {
                    message: 'Error en la generación de contenido',
                    details: 'Por favor, intenta nuevamente o contacta soporte.'
                });
                return;
            }
            
            updateProgressBar(progress);
            
            // Mensajes específicos para cada fase
            if (response.progress.text_generating) {
                const textMessages = [
                    'Analizando la palabra clave...',
                    'Investigando el tema...',
                    'Estructurando el contenido...',
                    'Generando texto optimizado...',
                    'Aplicando técnicas SEO...'
                ];
                const messageIndex = Math.min(Math.floor(attempts / 4), textMessages.length - 1);
                updateProgressMessage(textMessages[messageIndex]);
            } else if (response.progress.image_generating) {
                const imageMessages = [
                    'Generando imágenes con IA...',
                    'Creando imagen destacada...',
                    'Optimizando imágenes...',
                    'Finalizando contenido visual...'
                ];
                const messageIndex = Math.min(Math.floor((attempts - 15) / 3), imageMessages.length - 1);
                updateProgressMessage(imageMessages[messageIndex]);
            }
        }
        
        // Continue polling
        setTimeout(() => {
            pollGenerationProgress(contentId, modal, attempts + 1);
        }, 3000);
        
    } catch (error) {
        console.error('Error checking generation status:', error);
        updateProgressStatus('error', {
            message: 'Error verificando el estado',
            details: 'Revisa la lista de contenido manualmente.'
        });
    }
}

function updateProgressBar(percentage) {
    const progressBar = document.getElementById('progressBar');
    if (progressBar) {
        progressBar.style.width = percentage + '%';
        progressBar.textContent = Math.round(percentage) + '%';
    }
}

function updateProgressMessage(message) {
    const messageElement = document.getElementById('progressMessage');
    if (messageElement) {
        messageElement.textContent = message;
    }
}

function updateProgressStatus(status, data) {
    const statusElement = document.getElementById('generationStatus');
    const progressElement = document.querySelector('.spinner-border');
    
    if (status === 'completed') {
        if (progressElement) progressElement.style.display = 'none';
        if (statusElement) {
            statusElement.className = 'alert alert-success';
            let imageInfo = '';
            if (data.images && data.images.count > 0) {
                imageInfo = ` y ${data.images.count} imagen(es)`;
            }
            statusElement.innerHTML = `<i class="fas fa-check-circle me-2"></i>¡Contenido${imageInfo} generado exitosamente!`;
        }
        updateProgressMessage('Contenido generado y listo para editar');
        
        // Show edit button
        const editBtn = document.getElementById('editContentBtn');
        if (editBtn) editBtn.classList.remove('d-none');
        
    } else if (status === 'failed' || status === 'error') {
        if (progressElement) progressElement.style.display = 'none';
        if (statusElement) {
            statusElement.className = 'alert alert-danger';
            statusElement.innerHTML = `<i class="fas fa-exclamation-circle me-2"></i>${data.message}`;
        }
        updateProgressMessage('Error en la generación');
        document.getElementById('progressDetails').textContent = data.details;
        
    } else if (status === 'timeout') {
        if (progressElement) progressElement.style.display = 'none';
        if (statusElement) {
            statusElement.className = 'alert alert-warning';
            statusElement.innerHTML = `<i class="fas fa-clock me-2"></i>${data.message}`;
        }
        updateProgressMessage('Tiempo de espera agotado');
        document.getElementById('progressDetails').textContent = data.details;
    }
}

function updateImageProgress(imageData) {
    // Agregar información sobre el progreso de las imágenes
    const statusElement = document.getElementById('generationStatus');
    if (statusElement && imageData) {
        let imageStatusText = '';
        
        switch (imageData.status) {
            case 'generating':
                imageStatusText = '<i class="fas fa-image me-2"></i>Generando imágenes con IA...';
                break;
            case 'completed':
                imageStatusText = `<i class="fas fa-check-circle me-2"></i>Imágenes generadas: ${imageData.count} imagen(es)`;
                break;
            case 'none':
                imageStatusText = '<i class="fas fa-info-circle me-2"></i>Contenido generado sin imágenes';
                break;
            case 'failed':
                imageStatusText = '<i class="fas fa-exclamation-triangle me-2"></i>Error generando imágenes';
                break;
            default:
                imageStatusText = '<i class="fas fa-clock me-2"></i>Preparando generación de imágenes...';
        }
        
        statusElement.innerHTML = imageStatusText;
    }
}

function showContentPreview(contentData) {
    const previewDiv = document.getElementById('contentPreview');
    if (previewDiv) {
        previewDiv.classList.remove('d-none');
        
        document.getElementById('previewTitle').textContent = contentData.title;
        document.getElementById('previewContent').textContent = contentData.content_preview;
        
        // Información del contenido
        let statsHtml = `${contentData.word_count || 0} palabras • ${contentData.reading_time || 1} min de lectura`;
        
        // Agregar información de imágenes si están disponibles
        if (contentData.images && contentData.images.count > 0) {
            statsHtml += ` • ${contentData.images.count} imagen(es)`;
            if (contentData.images.featured_count > 0) {
                statsHtml += ` (${contentData.images.featured_count} destacada)`;
            }
        }
        
        document.getElementById('previewWordCount').textContent = statsHtml;
        document.getElementById('previewReadingTime').textContent = '';
    }
}

async function editGeneratedContent() {
    if (!window.currentGeneratingContentId) {
        showAlert('Error: No se encontró el ID del contenido', 'danger');
        return;
    }
    
    try {
        // Close progress modal
        const progressModal = bootstrap.Modal.getInstance(document.getElementById('generationProgressModal'));
        if (progressModal) progressModal.hide();
        
        // Switch to content section
        showSection('content');
        
        // Wait a moment for the section to load
        setTimeout(async () => {
            try {
                // Load and edit the generated content
                await editContent(window.currentGeneratingContentId);
                
                // Show success message
                showAlert('Contenido cargado en el editor. ¡Puedes revisarlo y editarlo antes de publicar!', 'success');
            } catch (error) {
                console.error('Error loading generated content:', error);
                showAlert('Error al cargar el contenido generado', 'danger');
            }
        }, 300);
        
    } catch (error) {
        console.error('Error switching to content section:', error);
        showAlert('Error al cambiar a la sección de contenido', 'danger');
    }
}

// Global functions for onclick handlers
window.showSection = showSection;
window.logout = logout;
window.showRegisterForm = showRegisterForm;
window.deleteKeyword = deleteKeyword;
window.analyzeKeyword = analyzeKeyword;
window.editKeyword = editKeyword;
window.cancelEditKeyword = cancelEditKeyword;
window.showCreateContentModal = showCreateContentModal;
window.saveContent = saveContent;
window.editContent = editContent;
window.viewContent = viewContent;
window.deleteContent = deleteContent;
window.insertTag = insertTag;
window.insertList = insertList;
window.formatParagraphs = formatParagraphs;
window.togglePasswordVisibility = togglePasswordVisibility;
window.testApiConnection = testApiConnection;
window.saveApiKey = saveApiKey;
window.loadApiStatus = loadApiStatus;
window.showGenerationProgress = showGenerationProgress;
window.editGeneratedContent = editGeneratedContent;
window.generateContentFromKeyword = generateContentFromKeyword;

// Image Upload Functions
function triggerImageUpload() {
    const imageInput = document.getElementById('imageUploadInput');
    imageInput.click();
}

function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
        showAlert('Por favor selecciona un archivo de imagen válido (JPG, PNG, GIF, WebP)', 'warning');
        return;
    }
    
    // Validate file size (max 5MB)
    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
        showAlert('La imagen es demasiado grande. El tamaño máximo es 5MB', 'warning');
        return;
    }
    
    // Show loading state
    const loadingHtml = `
        <div class="text-center my-3" id="imageUploadLoading">
            <div class="spinner-border text-primary" role="status">
            </div>
        </div>
    `;
    
    // Insert loading indicator at cursor position
    insertAtCursor('contentBody', loadingHtml);
    
    // Create FormData for upload
    const formData = new FormData();
    formData.append('file', file);
    
    // Upload image
    uploadImageToServer(formData, file.name);
}

async function uploadImageToServer(formData, fileName) {
    try {
        console.log('Uploading image to: /api/v1/image-generation/upload-manual');
        console.log('Token:', localStorage.getItem('authToken') ? 'Present' : 'Missing');
        
        const response = await fetch('/api/v1/image-generation/upload-manual', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Error ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // Remove loading indicator
        const loadingElement = document.getElementById('imageUploadLoading');
        if (loadingElement) {
            loadingElement.remove();
        }
        
        // Create image HTML for textarea (will be converted to proper HTML when content is saved/displayed)
        // Extract filename from the full path and construct the correct URL
        const filename = result.image_path.split('/').pop();
        
        // Get article title for automatic alt and title generation
        const fullTitle = document.getElementById('contentTitle')?.value || 'Artículo';
        
        // Extract key concepts from title (remove common words and limit length)
        const extractKeyWords = (title) => {
            const commonWords = ['el', 'la', 'los', 'las', 'un', 'una', 'de', 'del', 'en', 'con', 'por', 'para', 'que', 'como', 'y', 'o', 'pero', 'si', 'no', 'es', 'son', 'está', 'están', 'tiene', 'tienen', 'hace', 'hacen', 'puede', 'pueden', 'debe', 'deben', 'será', 'serán', 'fue', 'fueron', 'ha', 'han', 'había', 'habían', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must'];
            
            return title
                .toLowerCase()
                .split(' ')
                .filter(word => word.length > 2 && !commonWords.includes(word))
                .slice(0, 4) // Take only first 4 key words
                .join(' ');
        };
        
        const keyWords = extractKeyWords(fullTitle);
        const shortTitle = keyWords || fullTitle.substring(0, 30) + (fullTitle.length > 30 ? '...' : '');
        
        const imageAlt = `Imagen sobre ${shortTitle}`;
        const imageTitle = `Ilustración: ${shortTitle}`;
        
        const imageHtml = `\n\n<img src="/images/manual/${filename}" alt="${imageAlt}" title="${imageTitle}" class="content-image">\n\n`;
        
        // Insert image at cursor position
        insertAtCursor('contentBody', imageHtml);
        
        showAlert('Imagen subida exitosamente', 'success');
        
    } catch (error) {
        console.error('Error uploading image:', error);
        
        // Remove loading indicator
        const loadingElement = document.getElementById('imageUploadLoading');
        if (loadingElement) {
            loadingElement.remove();
        }
        
        showAlert('Error al subir la imagen. Inténtalo de nuevo.', 'danger');
    }
}

function insertAtCursor(textareaId, text) {
    const textarea = document.getElementById(textareaId);
    if (!textarea) return;
    
    const startPos = textarea.selectionStart;
    const endPos = textarea.selectionEnd;
    const beforeText = textarea.value.substring(0, startPos);
    const afterText = textarea.value.substring(endPos, textarea.value.length);
    
    textarea.value = beforeText + text + afterText;
    
    // Set cursor position after inserted text
    const newPos = startPos + text.length;
    textarea.setSelectionRange(newPos, newPos);
    textarea.focus();
}

// Make functions globally available
window.triggerImageUpload = triggerImageUpload;
window.handleImageUpload = handleImageUpload;

// Image Gallery Modal Functions
let currentGalleryImages = [];
let selectedImageData = null;
let currentPage = 1;
const imagesPerPage = 12;

function openImageGalleryModal() {
    const modal = new bootstrap.Modal(document.getElementById('imageGalleryModal'));
    modal.show();
    
    // Load images when modal opens
    loadGalleryImages();
    
    // Setup search functionality
    setupImageSearch();
}

function setupImageSearch() {
    const searchInput = document.getElementById('imageSearchInput');
    const filterSelect = document.getElementById('imageFilterType');
    
    // Debounce search input
    let searchTimeout;
    searchInput.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            currentPage = 1;
            loadGalleryImages();
        }, 300);
    });
    
    // Filter change
    filterSelect.addEventListener('change', () => {
        currentPage = 1;
        loadGalleryImages();
    });
}

async function loadGalleryImages() {
    const galleryContainer = document.getElementById('modalImageGallery');
    const searchTerm = document.getElementById('imageSearchInput').value.toLowerCase();
    const filterType = document.getElementById('imageFilterType').value;
    
    // Show loading
    galleryContainer.innerHTML = `
        <div class="col-12 text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando imágenes...</span>
            </div>
        </div>
    `;
    
    try {
        // Load all images from the unified endpoint
        const response = await fetch('/api/v1/image-generation/images', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            }
        });
        
        let allImages = [];
        
        if (response.ok) {
            const data = await response.json();
            console.log('Raw image data from API:', data); // Debug log
            
            allImages = data.images.map(img => {
                console.log(`Processing image: ${img.id}, Type: ${img.type}, Path: ${img.image_path}, File exists: ${img.file_exists}`); // Debug log
                
                // Extract filename from image_path
                const filename = img.image_path ? img.image_path.split('/').pop() : 'unknown.png';
                
                // Construct URL based on image type and path
                let url;
                
                if (img.type === 'content') {
                    // Content images are served from static directory
                    if (img.image_path && img.image_path.startsWith('static/')) {
                        url = `/${img.image_path}`;
                    } else if (img.image_path && img.image_path.startsWith('images/generated/')) {
                        url = `/static/${img.image_path}`;
                    } else {
                        // Default for content images
                        url = `/static/images/generated/${filename}`;
                    }
                } else if (img.type === 'manual') {
                    // Manual images are always served through the API endpoint
                    url = `/api/v1/image-generation/manual-images/${filename}`;
                } else {
                    // Fallback for unknown types
                    url = `/api/v1/image-generation/manual-images/${filename}`;
                }
                
                console.log(`Final URL for ${img.id}: ${url}`); // Debug log
                
                return {
                    ...img,
                    url: url,
                    filename: filename,
                    displayName: img.prompt_used ? img.prompt_used.substring(0, 30) + '...' : (img.alt_text || filename),
                    displayType: img.type // Keep original type for display
                };
            });
        }
        
        // Filter images
        let filteredImages = allImages;
        
        if (filterType !== 'all') {
            filteredImages = allImages.filter(img => {
                if (filterType === 'generated') {
                    return img.displayType === 'manual' || img.displayType === 'content';
                } else if (filterType === 'manual') {
                    return img.displayType === 'uploaded';
                }
                return img.displayType === filterType;
            });
        }
        
        if (searchTerm) {
            filteredImages = filteredImages.filter(img => 
                img.displayName.toLowerCase().includes(searchTerm) ||
                (img.prompt && img.prompt.toLowerCase().includes(searchTerm))
            );
        }
        
        currentGalleryImages = filteredImages;
        
        // Paginate
        const startIndex = (currentPage - 1) * imagesPerPage;
        const endIndex = startIndex + imagesPerPage;
        const paginatedImages = filteredImages.slice(startIndex, endIndex);
        
        displayGalleryImages(paginatedImages);
        setupPagination(filteredImages.length);
        
    } catch (error) {
        console.error('Error loading gallery images:', error);
        galleryContainer.innerHTML = `
            <div class="col-12">
                <div class="gallery-empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h5>Error al cargar imágenes</h5>
                    <p>No se pudieron cargar las imágenes. Inténtalo de nuevo.</p>
                </div>
            </div>
        `;
    }
}

function displayGalleryImages(images) {
    const galleryContainer = document.getElementById('modalImageGallery');
    
    if (images.length === 0) {
        galleryContainer.innerHTML = `
            <div class="col-12">
                <div class="gallery-empty-state">
                    <i class="fas fa-images"></i>
                    <h5>No se encontraron imágenes</h5>
                    <p>No hay imágenes que coincidan con tu búsqueda.</p>
                </div>
            </div>
        `;
        return;
    }
    
    galleryContainer.innerHTML = `
        <div class="image-gallery-grid">
            ${images.map(img => `
                <div class="gallery-image-item" onclick="selectGalleryImage('${img.url}', '${img.displayName}', '${img.displayType}')">
                    <img src="${img.url}" alt="${img.displayName}" loading="lazy">
                    <div class="gallery-image-overlay">
                        <div class="gallery-image-info">
                            <div class="gallery-image-name">${img.displayName}</div>
                            <div class="gallery-image-type">${img.style === 'uploaded' ? 'Imagen subida' : (img.displayType === 'manual' ? 'Generada por IA' : 'Imagen de contenido')}</div>
                        </div>
                    </div>
                    <div class="gallery-image-actions">
                        <button class="gallery-action-btn preview" onclick="event.stopPropagation(); previewImage('${img.url}', '${img.displayName}')" title="Vista previa">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="gallery-action-btn delete" onclick="event.stopPropagation(); confirmDeleteImage('${img.url}', '${img.filename}', '${img.displayType}')" title="Eliminar">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

function setupPagination(totalImages) {
    const paginationContainer = document.getElementById('imagePagination');
    const totalPages = Math.ceil(totalImages / imagesPerPage);
    
    if (totalPages <= 1) {
        paginationContainer.style.display = 'none';
        return;
    }
    
    paginationContainer.style.display = 'block';
    
    let paginationHtml = '';
    
    // Previous button
    paginationHtml += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage - 1})">
                <i class="fas fa-chevron-left"></i>
            </a>
        </li>
    `;
    
    // Page numbers
    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
            paginationHtml += `
                <li class="page-item ${i === currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="changePage(${i})">${i}</a>
                </li>
            `;
        } else if (i === currentPage - 3 || i === currentPage + 3) {
            paginationHtml += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    // Next button
    paginationHtml += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage + 1})">
                <i class="fas fa-chevron-right"></i>
            </a>
        </li>
    `;
    
    paginationContainer.querySelector('.pagination').innerHTML = paginationHtml;
}

function changePage(page) {
    const totalPages = Math.ceil(currentGalleryImages.length / imagesPerPage);
    if (page < 1 || page > totalPages) return;
    
    currentPage = page;
    
    const startIndex = (currentPage - 1) * imagesPerPage;
    const endIndex = startIndex + imagesPerPage;
    const paginatedImages = currentGalleryImages.slice(startIndex, endIndex);
    
    displayGalleryImages(paginatedImages);
    setupPagination(currentGalleryImages.length);
}

function selectGalleryImage(imageUrl, imageName, imageType) {
    // Get article title for automatic alt and title generation
    const fullTitle = document.getElementById('contentTitle')?.value || 'Artículo';
    
    // Extract key concepts from title
    const extractKeyWords = (title) => {
        const commonWords = ['el', 'la', 'los', 'las', 'un', 'una', 'de', 'del', 'en', 'con', 'por', 'para', 'que', 'como', 'y', 'o', 'pero', 'si', 'no', 'es', 'son', 'está', 'están', 'tiene', 'tienen', 'hace', 'hacen', 'puede', 'pueden', 'debe', 'deben', 'será', 'serán', 'fue', 'fueron', 'ha', 'han', 'había', 'habían', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must'];
        
        return title
            .toLowerCase()
            .split(' ')
            .filter(word => word.length > 2 && !commonWords.includes(word))
            .slice(0, 4)
            .join(' ');
    };
    
    const keyWords = extractKeyWords(fullTitle);
    const shortTitle = keyWords || fullTitle.substring(0, 30) + (fullTitle.length > 30 ? '...' : '');
    
    const imageAlt = `Imagen sobre ${shortTitle}`;
    const imageTitle = `Ilustración: ${shortTitle}`;
    
    const imageHtml = `\n\n<img src="${imageUrl}" alt="${imageAlt}" title="${imageTitle}" class="content-image">\n\n`;
    
    // Insert image at cursor position
    insertAtCursor('contentBody', imageHtml);
    
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('imageGalleryModal'));
    modal.hide();
    
    showAlert('Imagen insertada exitosamente', 'success');
}

function triggerNewImageUpload() {
    const modalImageInput = document.getElementById('modalImageUploadInput');
    modalImageInput.click();
}

function handleModalImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
        showAlert('Por favor selecciona un archivo de imagen válido (JPG, PNG, GIF, WebP)', 'warning');
        return;
    }
    
    // Validate file size (max 5MB)
    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
        showAlert('La imagen es demasiado grande. El tamaño máximo es 5MB', 'warning');
        return;
    }
    
    // Show upload progress
    const progressContainer = document.getElementById('uploadProgressContainer');
    const progressBar = document.getElementById('uploadProgressBar');
    progressContainer.style.display = 'block';
    progressBar.style.width = '0%';
    
    // Create FormData for upload
    const formData = new FormData();
    formData.append('file', file);
    
    // Upload image with progress
    uploadImageWithProgress(formData, file.name);
}

async function uploadImageWithProgress(formData, fileName) {
    try {
        const progressBar = document.getElementById('uploadProgressBar');
        const progressContainer = document.getElementById('uploadProgressContainer');
        
        // Simulate progress (since we can't track real progress with fetch)
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 30;
            if (progress > 90) progress = 90;
            progressBar.style.width = progress + '%';
        }, 200);
        
        const response = await fetch('/api/v1/image-generation/upload-manual', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: formData
        });
        
        clearInterval(progressInterval);
        progressBar.style.width = '100%';
        
        if (!response.ok) {
            throw new Error(`Error ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // Hide progress
        setTimeout(() => {
            progressContainer.style.display = 'none';
        }, 500);
        
        // Reload gallery
        loadGalleryImages();
        
        showAlert('Imagen subida exitosamente', 'success');
        
    } catch (error) {
        console.error('Error uploading image:', error);
        
        const progressContainer = document.getElementById('uploadProgressContainer');
        progressContainer.style.display = 'none';
        
        showAlert('Error al subir la imagen. Inténtalo de nuevo.', 'danger');
    }
}

function previewImage(imageUrl, imageName) {
    const previewModal = new bootstrap.Modal(document.getElementById('imagePreviewModal'));
    const previewImg = document.getElementById('previewImage');
    const previewDescription = document.getElementById('previewImageDescription');
    
    previewImg.src = imageUrl;
    previewImg.alt = imageName;
    previewDescription.textContent = imageName;
    
    selectedImageData = { url: imageUrl, name: imageName };
    
    previewModal.show();
}

function selectPreviewedImage() {
    if (!selectedImageData) return;
    
    selectGalleryImage(selectedImageData.url, selectedImageData.name, 'preview');
    
    // Close preview modal
    const previewModal = bootstrap.Modal.getInstance(document.getElementById('imagePreviewModal'));
    previewModal.hide();
}

function confirmDeleteImage(imageUrl, filename, imageType) {
    if (confirm('¿Estás seguro de que quieres eliminar esta imagen? Esta acción no se puede deshacer.')) {
        deleteImage(filename, imageType);
    }
}

async function deleteImage(filename, imageType) {
    try {
        const endpoint = imageType === 'manual' 
            ? `/api/v1/image-generation/manual-images/${filename}`
            : `/api/v1/image-generation/images/${filename}`;
        
        const response = await fetch(endpoint, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`Error ${response.status}: ${response.statusText}`);
        }
        
        // Reload gallery
        loadGalleryImages();
        
        showAlert('Imagen eliminada exitosamente', 'success');
        
    } catch (error) {
        console.error('Error deleting image:', error);
        showAlert('Error al eliminar la imagen', 'danger');
    }
}

// Make gallery functions globally available
window.openImageGalleryModal = openImageGalleryModal;
window.selectGalleryImage = selectGalleryImage;
window.triggerNewImageUpload = triggerNewImageUpload;
window.handleModalImageUpload = handleModalImageUpload;
window.previewImage = previewImage;
window.selectPreviewedImage = selectPreviewedImage;
window.confirmDeleteImage = confirmDeleteImage;
window.changePage = changePage;

// DALL-E Image Generation Functions
async function generateDalleImage() {
    const prompt = document.getElementById('eblagalPrompt').value.trim();
    
    if (!prompt) {
        showAlert('Por favor ingresa un prompt para generar la imagen', 'warning');
        return;
    }
    
    const generateBtn = event.target;
    const statusDiv = document.getElementById('eblagalGenerationStatus');
    const previewDiv = document.getElementById('eblagalPreview');
    
    // Update UI to show loading state
    generateBtn.disabled = true;
    generateBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generando...';
    statusDiv.innerHTML = '<div class="alert alert-info">Generando imagen con DALL-E...</div>';
    previewDiv.innerHTML = '';
    
    try {
        const response = await fetch('/api/v1/image-generation/dalle-generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: JSON.stringify({
                prompt: prompt,
                size: '1024x1024',
                quality: 'standard'
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `Error ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // Show success status
        statusDiv.innerHTML = '<div class="alert alert-success">¡Imagen generada exitosamente!</div>';
        
        // Show preview
        previewDiv.innerHTML = `
            <div class="text-center">
                <img src="${result.image_url}" alt="Generated image" class="img-fluid rounded" style="max-height: 200px;">
                <div class="mt-2">
                    <button class="btn btn-primary btn-sm" onclick="insertDalleImage('${result.image_url}', '${prompt}')">
                        <i class="fas fa-plus"></i> Insertar en contenido
                    </button>
                </div>
            </div>
        `;
        
        // Reload gallery to show new image
        loadDalleGallery();
        
        // Clear prompt
        document.getElementById('eblagalPrompt').value = '';
        
    } catch (error) {
        console.error('Error generating DALL-E image:', error);
        statusDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
    } finally {
        // Reset button
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<i class="fas fa-magic"></i> Generar Imagen';
    }
}

function insertDalleImage(imageUrl, prompt) {
    const imageAlt = `Imagen generada: ${prompt.substring(0, 50)}${prompt.length > 50 ? '...' : ''}`;
    const imageTitle = `Imagen DALL-E: ${prompt}`;
    
    const imageHtml = `\n\n<img src="${imageUrl}" alt="${imageAlt}" title="${imageTitle}" class="content-image">\n\n`;
    
    // Insert image at cursor position
    insertAtCursor('contentBody', imageHtml);
    
    showAlert('Imagen insertada exitosamente en el contenido', 'success');
}

async function loadDalleGallery() {
    try {
        const response = await fetch('/api/v1/image-generation/dalle-gallery', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`Error ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('DALL-E gallery response:', data);
        
        // Handle different response formats
        let images = [];
        if (Array.isArray(data)) {
            images = data;
        } else if (data && Array.isArray(data.images)) {
            images = data.images;
        } else if (data && data.message) {
            console.log('Gallery message:', data.message);
            images = [];
        }
        
        displayDalleGallery(images);
        
    } catch (error) {
        console.error('Error loading DALL-E gallery:', error);
        const galleryContainer = document.getElementById('eblagalGallery');
        galleryContainer.innerHTML = '<div class="alert alert-warning">Error al cargar la galería de imágenes</div>';
    }
}

function displayDalleGallery(images) {
    const galleryContainer = document.getElementById('eblagalGallery');
    
    if (!images || !Array.isArray(images) || images.length === 0) {
        galleryContainer.innerHTML = '<div class="text-muted text-center py-4">No hay imágenes generadas aún</div>';
        return;
    }
    
    const galleryHtml = images.map(image => `
        <div class="col-md-4 col-lg-3">
            <div class="eblagal-gallery-item">
                <div class="eblagal-image-container">
                    <img src="${image.url}" alt="Generated image" class="eblagal-image" onclick="previewDalleImage('${image.url}', '${image.filename}')">
                </div>
                <div class="eblagal-info">
                    <div class="eblagal-url" title="${image.url}">${image.url}</div>
                    <div class="eblagal-date">${new Date(image.created_at).toLocaleDateString()}</div>
                    <div class="eblagal-actions">
                        <button class="eblagal-copy-btn" onclick="copyToClipboard('${image.url}')" title="Copiar URL">
                            <i class="fas fa-copy"></i>
                        </button>
                        <button class="btn btn-sm btn-primary" onclick="insertDalleImage('${image.url}', 'Imagen generada')" title="Insertar en contenido">
                            <i class="fas fa-plus"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteDalleImage('${image.filename}')" title="Eliminar imagen">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
    
    galleryContainer.innerHTML = galleryHtml;
}

function previewDalleImage(imageUrl, filename) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Vista previa de imagen</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body text-center">
                    <img src="${imageUrl}" alt="Preview" class="img-fluid" style="max-height: 70vh;">
                    <div class="mt-3">
                        <small class="text-muted">${filename}</small>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                    <button type="button" class="btn btn-primary" onclick="insertDalleImage('${imageUrl}', 'Imagen generada'); bootstrap.Modal.getInstance(this.closest('.modal')).hide();">Insertar en contenido</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Remove modal from DOM when hidden
    modal.addEventListener('hidden.bs.modal', () => {
        document.body.removeChild(modal);
    });
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showAlert('URL copiada al portapapeles', 'success');
    }).catch(err => {
        console.error('Error copying to clipboard:', err);
        showAlert('Error al copiar URL', 'danger');
    });
}

async function deleteDalleImage(filename) {
    if (!confirm('¿Estás seguro de que quieres eliminar esta imagen? Esta acción no se puede deshacer.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/v1/image-generation/dalle-delete/${encodeURIComponent(filename)}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `Error ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        showAlert('Imagen eliminada exitosamente', 'success');
        
        // Reload gallery to reflect changes
        loadDalleGallery();
        
    } catch (error) {
        console.error('Error deleting DALL-E image:', error);
        showAlert(`Error al eliminar imagen: ${error.message}`, 'danger');
    }
}

// Make DALL-E functions globally available
window.generateDalleImage = generateDalleImage;
window.insertDalleImage = insertDalleImage;
window.loadDalleGallery = loadDalleGallery;
window.previewDalleImage = previewDalleImage;
window.copyToClipboard = copyToClipboard;
window.deleteDalleImage = deleteDalleImage;

// Load DALL-E gallery when content section is shown
document.addEventListener('DOMContentLoaded', function() {
    // Add event listener for when content section becomes active
    const contentTab = document.querySelector('[data-section="content"]');
    if (contentTab) {
        contentTab.addEventListener('click', function() {
            setTimeout(() => {
                loadDalleGallery();
            }, 100);
        });
    }
});