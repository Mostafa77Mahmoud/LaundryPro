// Advanced Analytics Dashboard JavaScript
class AnalyticsDashboard {
    constructor() {
        this.charts = {};
        this.currentFilters = {
            startDate: null,
            endDate: null,
            period: 'week'
        };
        this.init();
    }

    init() {
        this.setupDateFilters();
        this.loadAllCharts();
        this.loadKPIs();
        this.setupEventListeners();
    }

    setupDateFilters() {
        // Set default date range to last 7 days
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(endDate.getDate() - 7);

        document.getElementById('startDate').value = startDate.toISOString().split('T')[0];
        document.getElementById('endDate').value = endDate.toISOString().split('T')[0];

        this.currentFilters.startDate = startDate;
        this.currentFilters.endDate = endDate;
    }

    setupEventListeners() {
        // Date filter change handlers
        document.getElementById('startDate').addEventListener('change', () => {
            this.updateFilters();
        });

        document.getElementById('endDate').addEventListener('change', () => {
            this.updateFilters();
        });

        // Auto-refresh every 2 minutes
        setInterval(() => {
            this.refreshAllData();
        }, 120000);
    }

    updateFilters() {
        const startDate = new Date(document.getElementById('startDate').value);
        const endDate = new Date(document.getElementById('endDate').value);

        if (startDate && endDate && startDate <= endDate) {
            this.currentFilters.startDate = startDate;
            this.currentFilters.endDate = endDate;
            this.loadAllCharts();
            this.loadKPIs();
        } else {
            this.showError('Invalid date range. Please check your selection.');
        }
    }

    // Chart Loading Functions
    async loadAllCharts() {
        try {
            await Promise.all([
                this.loadRevenueChart(),
                this.loadServicePopularityChart(),
                this.loadCommissionChart(),
                this.loadPaymentRevenueChart()
            ]);
        } catch (error) {
            console.error('Error loading charts:', error);
            this.showError('Failed to load analytics charts');
        }
    }

    async loadRevenueChart() {
        try {
            const days = Math.ceil((this.currentFilters.endDate - this.currentFilters.startDate) / (1000 * 60 * 60 * 24)) + 1;
            const response = await fetch(`/api/analytics/chart-data?type=daily_revenue&days=${days}`);
            
            if (!response.ok) throw new Error('Failed to fetch revenue data');
            
            const data = await response.json();
            this.createRevenueChart(data);
        } catch (error) {
            console.error('Error loading revenue chart:', error);
            this.showChartError('revenueChart', 'Failed to load revenue data');
        }
    }

    createRevenueChart(data) {
        const ctx = document.getElementById('revenueChart').getContext('2d');
        
        if (this.charts.revenue) {
            this.charts.revenue.destroy();
        }

        this.charts.revenue = new Chart(ctx, {
            type: 'line',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Revenue Trends Over Time'
                    },
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + context.parsed.y.toFixed(2) + ' LE';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Amount (LE)'
                        },
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value.toFixed(2) + ' LE';
                            }
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    }

    async loadServicePopularityChart() {
        try {
            const response = await fetch('/api/analytics/chart-data?type=service_popularity');
            
            if (!response.ok) throw new Error('Failed to fetch service data');
            
            const data = await response.json();
            this.createServicePopularityChart(data);
            this.updateTopServicesList(data);
        } catch (error) {
            console.error('Error loading service popularity chart:', error);
            this.showChartError('servicePopularityChart', 'Failed to load service data');
        }
    }

    createServicePopularityChart(data) {
        const ctx = document.getElementById('servicePopularityChart').getContext('2d');
        
        if (this.charts.servicePopularity) {
            this.charts.servicePopularity.destroy();
        }

        this.charts.servicePopularity = new Chart(ctx, {
            type: 'bar',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Most Popular Services'
                    },
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Quantity: ' + context.parsed.y;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Services'
                        },
                        ticks: {
                            maxRotation: 45,
                            minRotation: 0
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Quantity Ordered'
                        },
                        beginAtZero: true
                    }
                }
            }
        });
    }

    updateTopServicesList(data) {
        const container = document.getElementById('topServicesList');
        if (!container) return;

        // Clear container safely
        while (container.firstChild) {
            container.removeChild(container.firstChild);
        }

        if (!data.labels || data.labels.length === 0) {
            const noDataMsg = document.createElement('p');
            noDataMsg.className = 'text-muted';
            noDataMsg.textContent = 'No service data available';
            container.appendChild(noDataMsg);
            return;
        }

        data.labels.slice(0, 5).forEach((service, index) => {
            const quantity = data.datasets[0].data[index];
            const revenue = data.revenue_data ? data.revenue_data[index] : 0;
            
            const serviceItem = document.createElement('div');
            serviceItem.className = 'd-flex justify-content-between align-items-center py-2 border-bottom';
            
            const serviceInfo = document.createElement('div');
            const serviceName = document.createElement('strong');
            serviceName.textContent = service;
            const serviceRevenue = document.createElement('small');
            serviceRevenue.className = 'text-muted d-block';
            serviceRevenue.textContent = `${revenue.toFixed(2)} LE revenue`;
            
            serviceInfo.appendChild(serviceName);
            serviceInfo.appendChild(serviceRevenue);
            
            const quantityBadge = document.createElement('span');
            quantityBadge.className = 'badge bg-primary';
            quantityBadge.textContent = quantity;
            
            serviceItem.appendChild(serviceInfo);
            serviceItem.appendChild(quantityBadge);
            container.appendChild(serviceItem);
        });
    }

    async loadCommissionChart() {
        try {
            const days = Math.ceil((this.currentFilters.endDate - this.currentFilters.startDate) / (1000 * 60 * 60 * 24)) + 1;
            const response = await fetch(`/api/analytics/chart-data?type=daily_revenue&days=${days}`);
            
            if (!response.ok) throw new Error('Failed to fetch commission data');
            
            const data = await response.json();
            this.createCommissionChart(data);
        } catch (error) {
            console.error('Error loading commission chart:', error);
            this.showChartError('commissionChart', 'Failed to load commission data');
        }
    }

    createCommissionChart(data) {
        const ctx = document.getElementById('commissionChart').getContext('2d');
        
        if (this.charts.commission) {
            this.charts.commission.destroy();
        }

        // Extract commission and shop revenue data
        const commissionData = data.datasets.find(d => d.label === 'Commission');
        const shopData = data.datasets.find(d => d.label === 'Shop Revenue');

        this.charts.commission = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Commission (15%)', 'Shop Revenue (85%)'],
                datasets: [{
                    data: [
                        commissionData ? commissionData.data.reduce((a, b) => a + b, 0) : 0,
                        shopData ? shopData.data.reduce((a, b) => a + b, 0) : 0
                    ],
                    backgroundColor: ['#dc3545', '#28a745'],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Revenue Distribution'
                    },
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return context.label + ': ' + context.parsed.toFixed(2) + ' LE (' + percentage + '%)';
                            }
                        }
                    }
                }
            }
        });
    }

    async loadPaymentRevenueChart() {
        try {
            const response = await fetch('/api/analytics/chart-data?type=payment_methods');
            
            if (!response.ok) throw new Error('Failed to fetch payment data');
            
            const data = await response.json();
            this.createPaymentRevenueChart(data);
        } catch (error) {
            console.error('Error loading payment revenue chart:', error);
            this.showChartError('paymentRevenueChart', 'Failed to load payment data');
        }
    }

    createPaymentRevenueChart(data) {
        const ctx = document.getElementById('paymentRevenueChart').getContext('2d');
        
        if (this.charts.paymentRevenue) {
            this.charts.paymentRevenue.destroy();
        }

        // Create revenue-based chart instead of count-based
        const revenueData = data.revenue_data || data.datasets[0].data;

        this.charts.paymentRevenue = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels.map(label => label.replace('_', ' ').toUpperCase()),
                datasets: [{
                    label: 'Revenue by Payment Method',
                    data: revenueData,
                    backgroundColor: [
                        '#28a745', // Cash - Green
                        '#007bff', // Card - Blue
                        '#17a2b8', // Mobile - Teal
                        '#ffc107', // Other - Yellow
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Revenue by Payment Method'
                    },
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Revenue: ' + context.parsed.y.toFixed(2) + ' LE';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Payment Method'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Revenue (LE)'
                        },
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value.toFixed(2) + ' LE';
                            }
                        }
                    }
                }
            }
        });
    }

    // KPI Loading
    async loadKPIs() {
        try {
            const response = await fetch('/api/analytics/summary');
            
            if (!response.ok) throw new Error('Failed to fetch KPI data');
            
            const data = await response.json();
            this.updateKPICards(data);
        } catch (error) {
            console.error('Error loading KPIs:', error);
            this.showError('Failed to load key performance indicators');
        }
    }

    updateKPICards(data) {
        const container = document.getElementById('kpiCards');
        if (!container) return;

        // Clear container safely
        while (container.firstChild) {
            container.removeChild(container.firstChild);
        }

        // Calculate additional KPIs
        const avgOrderValue = data.total_orders > 0 ? data.total_revenue / data.total_orders : 0;
        const commissionRate = data.total_revenue > 0 ? (data.total_commission / data.total_revenue) * 100 : 15;

        const kpis = [
            {
                title: 'Average Order Value',
                value: avgOrderValue.toFixed(2) + ' LE',
                icon: 'fas fa-calculator',
                color: 'primary'
            },
            {
                title: 'Commission Rate',
                value: commissionRate.toFixed(1) + '%',
                icon: 'fas fa-percentage',
                color: 'info'
            },
            {
                title: 'Active Orders',
                value: Object.keys(data.status_breakdown).reduce((sum, status) => 
                    status !== 'delivered' ? sum + (data.status_breakdown[status] || 0) : sum, 0),
                icon: 'fas fa-hourglass-half',
                color: 'warning'
            },
            {
                title: 'Completed Orders',
                value: data.status_breakdown.delivered || 0,
                icon: 'fas fa-check-circle',
                color: 'success'
            }
        ];

        kpis.forEach(kpi => {
            const colDiv = document.createElement('div');
            colDiv.className = 'col-md-3 mb-3';
            
            const cardDiv = document.createElement('div');
            cardDiv.className = `card border-left-${kpi.color} shadow h-100 py-2`;
            
            const cardBody = document.createElement('div');
            cardBody.className = 'card-body';
            
            const rowDiv = document.createElement('div');
            rowDiv.className = 'row no-gutters align-items-center';
            
            const colMr2 = document.createElement('div');
            colMr2.className = 'col mr-2';
            
            const titleDiv = document.createElement('div');
            titleDiv.className = `text-xs font-weight-bold text-${kpi.color} text-uppercase mb-1`;
            titleDiv.textContent = kpi.title;
            
            const valueDiv = document.createElement('div');
            valueDiv.className = 'h5 mb-0 font-weight-bold text-gray-800';
            valueDiv.textContent = kpi.value;
            
            const colAuto = document.createElement('div');
            colAuto.className = 'col-auto';
            
            const icon = document.createElement('i');
            icon.className = `${kpi.icon} fa-2x text-gray-300`;
            
            colMr2.appendChild(titleDiv);
            colMr2.appendChild(valueDiv);
            colAuto.appendChild(icon);
            rowDiv.appendChild(colMr2);
            rowDiv.appendChild(colAuto);
            cardBody.appendChild(rowDiv);
            cardDiv.appendChild(cardBody);
            colDiv.appendChild(cardDiv);
            container.appendChild(colDiv);
        });
    }

    // Utility Functions
    async refreshAllData() {
        try {
            await this.loadAllCharts();
            await this.loadKPIs();
        } catch (error) {
            console.error('Error refreshing analytics data:', error);
        }
    }

    showChartError(chartId, message) {
        const canvas = document.getElementById(chartId);
        if (canvas) {
            const container = canvas.parentElement;
            
            // Clear container safely
            while (container.firstChild) {
                container.removeChild(container.firstChild);
            }
            
            const errorContainer = document.createElement('div');
            errorContainer.className = 'd-flex align-items-center justify-content-center h-100';
            
            const errorContent = document.createElement('div');
            errorContent.className = 'text-center text-muted';
            
            const icon = document.createElement('i');
            icon.className = 'fas fa-exclamation-triangle fa-3x mb-3';
            
            const messageP = document.createElement('p');
            messageP.textContent = message;
            
            const retryBtn = document.createElement('button');
            retryBtn.className = 'btn btn-outline-primary btn-sm';
            retryBtn.onclick = () => location.reload();
            
            const retryIcon = document.createElement('i');
            retryIcon.className = 'fas fa-sync-alt me-1';
            
            retryBtn.appendChild(retryIcon);
            retryBtn.appendChild(document.createTextNode('Retry'));
            
            errorContent.appendChild(icon);
            errorContent.appendChild(messageP);
            errorContent.appendChild(retryBtn);
            errorContainer.appendChild(errorContent);
            container.appendChild(errorContainer);
        }
    }

    showError(message) {
        this.showToast(message, 'error');
    }

    showSuccess(message) {
        this.showToast(message, 'success');
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'error' ? 'danger' : 'success'} alert-dismissible fade show position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        
        const icon = document.createElement('i');
        icon.className = `fas fa-${type === 'error' ? 'exclamation-triangle' : 'check-circle'} me-2`;
        
        const messageText = document.createTextNode(message);
        
        const closeBtn = document.createElement('button');
        closeBtn.type = 'button';
        closeBtn.className = 'btn-close';
        closeBtn.setAttribute('data-bs-dismiss', 'alert');
        
        toast.appendChild(icon);
        toast.appendChild(messageText);
        toast.appendChild(closeBtn);
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 5000);
    }
}

// Quick date range functions
function setDateRange(days) {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - days);

    document.getElementById('startDate').value = startDate.toISOString().split('T')[0];
    document.getElementById('endDate').value = endDate.toISOString().split('T')[0];

    // Trigger update if analytics dashboard exists
    if (window.analyticsDashboard) {
        window.analyticsDashboard.updateFilters();
    }
}

// Update charts function for template
function updateCharts() {
    if (window.analyticsDashboard) {
        window.analyticsDashboard.updateFilters();
    }
}

// Initialize analytics dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.analyticsDashboard = new AnalyticsDashboard();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AnalyticsDashboard };
}
