/**
 * Local Storage Manager
 */
const StorageManager = {
    // Save data
    save: (key, data) => {
        try {
            localStorage.setItem(key, JSON.stringify(data));
        } catch (error) {
            console.error('Error saving to localStorage:', error);
        }
    },
    
    // Get data
    get: (key) => {
        try {
            const data = localStorage.getItem(key);
            return data ? JSON.parse(data) : null;
        } catch (error) {
            console.error('Error reading from localStorage:', error);
            return null;
        }
    },
    
    // Remove data
    remove: (key) => {
        try {
            localStorage.removeItem(key);
        } catch (error) {
            console.error('Error removing from localStorage:', error);
        }
    },
    
    // Clear all
    clear: () => {
        try {
            localStorage.clear();
        } catch (error) {
            console.error('Error clearing localStorage:', error);
        }
    }
};

/**
 * API Manager
 */
const APIManager = {
    baseURL: '/api',
    
    // GET request
    get: async (endpoint) => {
        try {
            const response = await fetch(`${APIManager.baseURL}${endpoint}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('GET request error:', error);
            throw error;
        }
    },
    
    // POST request
    post: async (endpoint, data) => {
        try {
            const response = await fetch(`${APIManager.baseURL}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('POST request error:', error);
            throw error;
        }
    }
};

/**
 * Logger
 */
const Logger = {
    log: (message, data = null) => {
        console.log(`[LOG] ${message}`, data || '');
    },
    
    error: (message, error = null) => {
        console.error(`[ERROR] ${message}`, error || '');
    },
    
    warn: (message, data = null) => {
        console.warn(`[WARN] ${message}`, data || '');
    }
};

/**
 * String utilities
 */
const StringUtils = {
    // Truncate string
    truncate: (str, length = 100) => {
        return str.length > length ? str.substring(0, length) + '...' : str;
    },
    
    // Capitalize first letter
    capitalize: (str) => {
        return str.charAt(0).toUpperCase() + str.slice(1);
    },
    
    // Convert to title case
    toTitleCase: (str) => {
        return str.replace(/\b\w/g, char => char.toUpperCase());
    },
    
    // Remove extra spaces
    trimSpaces: (str) => {
        return str.replace(/\s+/g, ' ').trim();
    },
    
    // Escape HTML
    escapeHtml: (str) => {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
};

/**
 * Date utilities
 */
const DateUtils = {
    // Format date
    format: (date, format = 'MM/DD/YYYY') => {
        const d = new Date(date);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const hours = String(d.getHours()).padStart(2, '0');
        const minutes = String(d.getMinutes()).padStart(2, '0');
        
        return format
            .replace('YYYY', year)
            .replace('MM', month)
            .replace('DD', day)
            .replace('HH', hours)
            .replace('mm', minutes);
    },
    
    // Get relative time
    getRelativeTime: (date) => {
        const now = new Date();
        const diff = now - new Date(date);
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);
        
        if (seconds < 60) return `${seconds}s ago`;
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        
        return DateUtils.format(date);
    }
};

/**
 * Number utilities
 */
const NumberUtils = {
    // Format number with commas
    formatNumber: (num) => {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },
    
    // Round to decimal places
    round: (num, decimals = 2) => {
        return Math.round(num * Math.pow(10, decimals)) / Math.pow(10, decimals);
    },
    
    // Get percentage
    percentage: (value, total) => {
        return NumberUtils.round((value / total) * 100, 2);
    }
};

/**
 * Notification Manager
 */
const NotificationManager = {
    show: (message, type = 'info', duration = 3000) => {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            background: ${type === 'error' ? '#ff6b6b' : type === 'success' ? '#51cf66' : '#4ecdc4'};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, duration);
    },
    
    success: (message) => NotificationManager.show(message, 'success'),
    error: (message) => NotificationManager.show(message, 'error'),
    info: (message) => NotificationManager.show(message, 'info')
};

/**
 * Form utilities
 */
const FormUtils = {
    // Get form data
    getFormData: (form) => {
        const formData = new FormData(form);
        const data = {};
        formData.forEach((value, key) => {
            data[key] = value;
        });
        return data;
    },
    
    // Reset form
    resetForm: (form) => {
        form.reset();
    },
    
    // Disable form
    disableForm: (form) => {
        const inputs = form.querySelectorAll('input, textarea, button, select');
        inputs.forEach(input => input.disabled = true);
    },
    
    // Enable form
    enableForm: (form) => {
        const inputs = form.querySelectorAll('input, textarea, button, select');
        inputs.forEach(input => input.disabled = false);
    }
};

/**
 * Array utilities
 */
const ArrayUtils = {
    // Remove duplicates
    unique: (arr) => [...new Set(arr)],
    
    // Group by property
    groupBy: (arr, key) => {
        return arr.reduce((result, item) => {
            const group = item[key];
            if (!result[group]) result[group] = [];
            result[group].push(item);
            return result;
        }, {});
    },
    
    // Chunk array
    chunk: (arr, size) => {
        const chunks = [];
        for (let i = 0; i < arr.length; i += size) {
            chunks.push(arr.slice(i, i + size));
        }
        return chunks;
    }
};

// Add CSS animations to document
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
