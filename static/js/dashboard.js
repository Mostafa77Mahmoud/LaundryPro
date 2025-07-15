// Dashboard JavaScript functionality
class Dashboard {
    constructor() {
        this.init();
    }

    init() {
        this.setupThemeToggle();
        this.setupLanguageToggle();
        this.setupEventListeners();
        this.loadInitialData();
    }

    // Theme Management
    setupThemeToggle() {
        const themeToggle = document.getElementById('themeToggle');
        const themeIcon = document.getElementById('themeIcon');
        
        // Load saved theme or default to light
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        this.updateThemeIcon(savedTheme);

        themeToggle.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            this.updateThemeIcon(newTheme);
        });
    }

    updateThemeIcon(theme) {
        const themeIcon = document.getElementById('themeIcon');
        if (themeIcon) {
            themeIcon.className = theme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
        }
    }

    // Language Management
    setupLanguageToggle() {
        const langToggle = document.getElementById('langToggle');
        const langText = document.getElementById('langText');
        
        // Load saved language or default to English
        const savedLang = localStorage.getItem('language') || 'en';
        this.setLanguage(savedLang);

        langToggle.addEventListener('click', () => {
            const currentLang = localStorage.getItem('language') || 'en';
            const newLang = currentLang === 'en' ? 'ar' : 'en';
            this.setLanguage(newLang);
        });
    }

    setLanguage(lang) {
        localStorage.setItem('language', lang);
        const langText = document.getElementById('langText');
        
        if (lang === 'ar') {
            document.documentElement.setAttribute('dir', 'rtl');
            document.documentElement.setAttribute('lang', 'ar');
            if (langText) langText.textContent = 'English';
        } else {
            document.documentElement.setAttribute('dir', 'ltr');
            document.documentElement.setAttribute('lang', 'en');
            if (langText) langText.textContent = 'عربي';
        }

        // Update page content based on language
        this.updateLanguageContent(lang);
    }

    updateLanguageContent(lang) {
        const translations = {
            en: {
                dashboard: 'Dashboard',
                orders: 'Orders',
                categories: 'Categories',
                analytics: 'Analytics',
                reports: 'Reports',
                totalOrders: 'Total Orders',
                totalRevenue: 'Total Revenue',
                appCommission: 'App Commission',
                shopRevenue: 'Shop Revenue',
                addCategory: 'Add Category',
                editCategory: 'Edit Category',
                deleteCategory: 'Delete Category',
                changeImage: 'Change Image',
                servicesAndPrices: 'Services & Prices',
                noCategoriesFound: 'No Categories Found',
                startByAdding: 'Start by adding your first service category.',
                search: 'Search...',
                filter: 'Filter',
                all: 'All',
                pending: 'Pending',
                inProgress: 'In Progress',
                completed: 'Completed',
                cancelled: 'Cancelled',
                orderManagement: 'Order Management',
                allOrders: 'All Orders',
                filterByStatus: 'Filter by Status',
                filterByPayment: 'Filter by Payment',
                searchOrders: 'Search Orders',
                filterByDate: 'Filter by Date',
                allStatuses: 'All Statuses',
                allPaymentMethods: 'All Payment Methods',
                orderIdOrCustomer: 'Order ID or Customer',
                refresh: 'Refresh'
            },
            ar: {
                dashboard: 'لوحة التحكم',
                orders: 'الطلبات',
                categories: 'الفئات',
                analytics: 'التحليلات',
                reports: 'التقارير',
                totalOrders: 'إجمالي الطلبات',
                totalRevenue: 'إجمالي الإيرادات',
                appCommission: 'عمولة التطبيق',
                shopRevenue: 'إيرادات المتجر',
                addCategory: 'إضافة فئة',
                editCategory: 'تحرير الفئة',
                deleteCategory: 'حذف الفئة',
                changeImage: 'تغيير الصورة',
                servicesAndPrices: 'الخدمات والأسعار',
                noCategoriesFound: 'لم يتم العثور على فئات',
                startByAdding: 'ابدأ بإضافة فئة الخدمة الأولى.',
                search: 'بحث...',
                filter: 'تصفية',
                all: 'الكل',
                pending: 'قيد الانتظار',
                inProgress: 'قيد التنفيذ',
                completed: 'مكتمل',
                cancelled: 'ملغي',
                orderManagement: 'إدارة الطلبات',
                allOrders: 'جميع الطلبات',
                filterByStatus: 'تصفية حسب الحالة',
                filterByPayment: 'تصفية حسب الدفع',
                searchOrders: 'البحث في الطلبات',
                filterByDate: 'تصفية حسب التاريخ',
                allStatuses: 'جميع الحالات',
                allPaymentMethods: 'جميع طرق الدفع',
                orderIdOrCustomer: 'رقم الطلب أو العميل',
                refresh: 'تحديث'
            }
        };

        // Update navigation labels
        const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
        navLinks.forEach((link, index) => {
            const keys = ['dashboard', 'orders', 'categories', 'analytics', 'reports'];
            if (keys[index]) {
                const iconHtml = link.querySelector('i').outerHTML;
                link.innerHTML = iconHtml + ' ' + translations[lang][keys[index]];
            }
        });

        // Update metric card titles
        const metricTitles = document.querySelectorAll('.text-uppercase');
        const metricKeys = ['totalOrders', 'totalRevenue', 'appCommission', 'shopRevenue'];
        metricTitles.forEach((title, index) => {
            if (metricKeys[index]) {
                title.textContent = translations[lang][metricKeys[index]];
            }
        });

        // Update category content based on language
        if (lang === 'ar') {
            // Show Arabic content, hide English
            document.querySelectorAll('.category-name-en, .category-desc-en, .item-name-en').forEach(el => {
                el.classList.add('d-none');
            });
            document.querySelectorAll('.category-name-ar, .category-desc-ar, .item-name-ar').forEach(el => {
                el.classList.remove('d-none');
            });
        } else {
            // Show English content, hide Arabic
            document.querySelectorAll('.category-name-ar, .category-desc-ar, .item-name-ar').forEach(el => {
                el.classList.add('d-none');
            });
            document.querySelectorAll('.category-name-en, .category-desc-en, .item-name-en').forEach(el => {
                el.classList.remove('d-none');
            });
        }

        // Update button texts and UI elements
        const uiElements = {
            '.btn-add-category': translations[lang].addCategory,
            '[data-translate="services-prices"]': translations[lang].servicesAndPrices,
            '[data-translate="no-categories"]': translations[lang].noCategoriesFound,
            '[data-translate="start-adding"]': translations[lang].startByAdding,
            'input[placeholder*="Search"], input[placeholder*="بحث"]': translations[lang].search,
        };

        Object.entries(uiElements).forEach(([selector, text]) => {
            document.querySelectorAll(selector).forEach(el => {
                if (el.tagName === 'INPUT') {
                    el.placeholder = text;
                } else {
                    el.textContent = text;
                }
            });
        });
    }

    // Event Listeners
    setupEventListeners() {
        // Auto-refresh data every 30 seconds
        setInterval(() => {
            this.refreshDashboardData();
        }, 30000);

        // Handle window resize for responsive charts
        window.addEventListener('resize', () => {
            this.handleWindowResize();
        });

        // Handle visibility change for performance
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                this.refreshDashboardData();
            }
        });
    }

    // Data Loading
    async loadInitialData() {
        try {
            await this.loadDashboardMetrics();
            await this.loadRecentOrders();
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    async loadDashboardMetrics() {
        try {
            const response = await fetch('/api/analytics/summary');
            if (!response.ok) throw new Error('Failed to fetch metrics');
            
            const data = await response.json();
            this.updateMetricCards(data);
        } catch (error) {
            console.error('Error loading metrics:', error);
            this.showError('Failed to load metrics');
        }
    }

    updateMetricCards(data) {
        // Update metric values with animation
        this.animateNumber('total-orders', data.total_orders || 0);
        this.animateNumber('total-revenue', data.total_revenue || 0, true);
        this.animateNumber('total-commission', data.total_commission || 0, true);
        this.animateNumber('shop-revenue', data.shop_revenue || 0, true);
    }

    animateNumber(elementClass, targetValue, isCurrency = false) {
        const elements = document.querySelectorAll(`.${elementClass}`);
        elements.forEach(element => {
            const startValue = parseFloat(element.textContent.replace(/[^\d.-]/g, '')) || 0;
            const increment = (targetValue - startValue) / 20;
            let currentValue = startValue;
            
            const timer = setInterval(() => {
                currentValue += increment;
                if ((increment > 0 && currentValue >= targetValue) || 
                    (increment < 0 && currentValue <= targetValue)) {
                    currentValue = targetValue;
                    clearInterval(timer);
                }
                
                element.textContent = isCurrency ? 
                    `${currentValue.toFixed(2)} LE` : 
                    Math.round(currentValue).toString();
            }, 50);
        });
    }

    async loadRecentOrders() {
        try {
            // This would typically fetch recent orders from API
            // For now, show loading state then empty state
            const tbody = document.getElementById('recentOrdersBody');
            if (!tbody) return;

            tbody.innerHTML = '<tr><td colspan="7" class="text-center">Loading orders...</td></tr>';
            
            // Simulate API call
            setTimeout(() => {
                tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No recent orders</td></tr>';
            }, 1000);
        } catch (error) {
            console.error('Error loading recent orders:', error);
        }
    }

    // Data Refresh
    async refreshDashboardData() {
        try {
            await this.loadDashboardMetrics();
            await this.loadRecentOrders();
        } catch (error) {
            console.error('Error refreshing data:', error);
        }
    }

    // Utility Functions
    handleWindowResize() {
        // Trigger chart resize if charts exist
        if (window.Chart) {
            Chart.helpers.each(Chart.instances, (instance) => {
                instance.resize();
            });
        }
    }

    showError(message) {
        this.showToast(message, 'error');
    }

    showSuccess(message) {
        this.showToast(message, 'success');
    }

    showToast(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'error' ? 'danger' : 'success'} alert-dismissible fade show position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        toast.innerHTML = `
            <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : 'check-circle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 5000);
    }

    // Chart Helpers
    getChartColors() {
        return {
            primary: '#007bff',
            success: '#28a745',
            danger: '#dc3545',
            warning: '#ffc107',
            info: '#17a2b8',
            secondary: '#6c757d'
        };
    }

    // Format currency for display
    formatCurrency(amount) {
        return `${amount.toFixed(2)} LE`;
    }

    // Format date for display
    formatDate(date) {
        const currentLang = localStorage.getItem('language') || 'en';
        return new Intl.DateTimeFormat(currentLang === 'ar' ? 'ar-SA' : 'en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(date));
    }
}

// Real-time updates using WebSocket (if available)
class RealTimeUpdates {
    constructor(dashboard) {
        this.dashboard = dashboard;
        this.setupWebSocket();
    }

    setupWebSocket() {
        // Use polling instead of WebSocket to avoid connection errors
        this.fallbackToPolling();
    }

    fallbackToPolling() {
        // Poll for updates every 10 seconds
        setInterval(() => {
            this.dashboard.refreshDashboardData();
        }, 10000);
    }

    handleRealtimeUpdate(data) {
        switch (data.type) {
            case 'new_order':
                this.dashboard.showSuccess('New order received!');
                this.dashboard.refreshDashboardData();
                break;
            case 'order_status_update':
                this.dashboard.refreshDashboardData();
                break;
            case 'metrics_update':
                this.dashboard.updateMetricCards(data.metrics);
                break;
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const dashboard = new Dashboard();
    const realTimeUpdates = new RealTimeUpdates(dashboard);
    
    // Make dashboard globally available for debugging
    window.dashboard = dashboard;
});

// Notification helper functions
function showNotification(title, body, icon = '/static/images/logo.png') {
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, { body, icon });
    } else if ('Notification' in window && Notification.permission !== 'denied') {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                new Notification(title, { body, icon });
            }
        });
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { Dashboard, RealTimeUpdates };
}
