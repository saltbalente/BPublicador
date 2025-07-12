// Frontend Configuration
// This file handles environment-specific configurations

class Config {
    constructor() {
        this.environment = this.detectEnvironment();
        this.config = this.getConfig();
    }

    detectEnvironment() {
        const hostname = window.location.hostname;
        const port = window.location.port;
        
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'development';
        } else if (hostname.includes('staging')) {
            return 'staging';
        } else {
            return 'production';
        }
    }

    getConfig() {
        const configs = {
            development: {
                API_BASE_URL: 'http://localhost:8001/api/v1',
                WS_URL: 'ws://localhost:8001/ws',
                DEBUG: true,
                LOG_LEVEL: 'debug',
                ENABLE_ANALYTICS: false,
                CACHE_DURATION: 5 * 60 * 1000, // 5 minutes
                REQUEST_TIMEOUT: 30000, // 30 seconds
                RETRY_ATTEMPTS: 3,
                ENABLE_SERVICE_WORKER: false
            },
            staging: {
                API_BASE_URL: 'https://staging-api.autopublicador.com/api/v1',
                WS_URL: 'wss://staging-api.autopublicador.com/ws',
                DEBUG: true,
                LOG_LEVEL: 'info',
                ENABLE_ANALYTICS: true,
                CACHE_DURATION: 15 * 60 * 1000, // 15 minutes
                REQUEST_TIMEOUT: 30000,
                RETRY_ATTEMPTS: 3,
                ENABLE_SERVICE_WORKER: true
            },
            production: {
                API_BASE_URL: 'https://api.autopublicador.com/api/v1',
                WS_URL: 'wss://api.autopublicador.com/ws',
                DEBUG: false,
                LOG_LEVEL: 'error',
                ENABLE_ANALYTICS: true,
                CACHE_DURATION: 30 * 60 * 1000, // 30 minutes
                REQUEST_TIMEOUT: 30000,
                RETRY_ATTEMPTS: 5,
                ENABLE_SERVICE_WORKER: true
            }
        };

        return configs[this.environment];
    }

    get(key) {
        return this.config[key];
    }

    getAll() {
        return { ...this.config, environment: this.environment };
    }

    isDevelopment() {
        return this.environment === 'development';
    }

    isProduction() {
        return this.environment === 'production';
    }

    isStaging() {
        return this.environment === 'staging';
    }
}

// Export singleton instance
const config = new Config();

// Make it globally available
window.AppConfig = config;

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = config;
}