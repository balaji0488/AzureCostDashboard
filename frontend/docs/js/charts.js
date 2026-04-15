let chartInstances = {};

async function loadDashboardData() {
    // 1. Setup Dropdown
    const subs = await fetchSubscriptions();
    const subSelect = document.getElementById('subSelect');
    if (subSelect && subSelect.options.length === 1) { // Populate only once
        subs.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s.id || s;
            opt.textContent = s.name || s;
            subSelect.appendChild(opt);
        });
        
        // Listen for user changes
        subSelect.addEventListener('change', async (e) => {
            await refreshCharts(e.target.value);
        });
    }
    
    // 2. Load initial charts with 'All subscriptions' (empty ID)
    await refreshCharts('');
}

async function refreshCharts(subscriptionId) {
    const data = await fetchCosts(subscriptionId);
    if (!data) {
        console.error("No data received for charts.");
        return;
    }
    
    const currency = data.currency || 'USD';
    renderAccumulatedChart(data.monthly, currency);
    renderServiceChart(data.service, currency);
    renderRgChart(data.resourceGroup, currency);
    renderLocationChart(data.location, currency);
}

const currencyFormatter = (currency) => {
    return (value) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(value);
    };
};

const commonOptions = (currency) => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: 'bottom',
        },
        tooltip: {
            callbacks: {
                label: function(context) {
                    const fmt = currencyFormatter(currency);
                    return `${context.dataset.label || context.label}: ${fmt(context.parsed.y || context.parsed || context.raw)}`;
                }
            }
        }
    }
});

function renderAccumulatedChart(monthlyData, currency) {
    const ctx = document.getElementById('accumulatedChart');
    if (!ctx) return;
    
    if (chartInstances.accumulated) chartInstances.accumulated.destroy();
    
    // Calculate cumulative sum
    let total = 0;
    const accumulated = monthlyData.map(d => {
        total += d.cost;
        return total;
    });
    
    const fmt = currencyFormatter(currency);

    chartInstances.accumulated = new Chart(ctx, {
        type: 'line',
        data: {
            labels: monthlyData.map(d => {
                const [y, m] = d.month.split('-');
                return new Date(y, m - 1).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
            }),
            datasets: [{
                label: `Accumulated Cost (${currency})`,
                data: accumulated,
                borderColor: 'rgba(59, 130, 246, 1)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            ...commonOptions(currency),
            scales: {
                y: {
                    ticks: { callback: fmt }
                }
            }
        }
    });
}

function renderServiceChart(serviceData, currency) {
    const ctx = document.getElementById('serviceChart');
    if (!ctx) return;

    if (chartInstances.service) chartInstances.service.destroy();
    
    const fmt = currencyFormatter(currency);

    chartInstances.service = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: serviceData.map(d => d.service),
            datasets: [{
                data: serviceData.map(d => d.cost),
                backgroundColor: [
                    '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#94a3b8'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { boxWidth: 14, padding: 12 }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.label}: ${fmt(context.raw)}`;
                        }
                    }
                }
            }
        }
    });
}

function renderRgChart(rgData, currency) {
    const ctx = document.getElementById('rgChart');
    if (!ctx) return;

    if (chartInstances.rg) chartInstances.rg.destroy();
    
    const fmt = currencyFormatter(currency);

    chartInstances.rg = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: rgData.map(d => d.resourceGroup),
            datasets: [{
                label: `Cost by Resource Group (${currency})`,
                data: rgData.map(d => d.cost),
                backgroundColor: 'rgba(16, 185, 129, 0.8)',
            }]
        },
        options: {
            ...commonOptions(currency),
            indexAxis: 'y',
            scales: {
                x: { ticks: { callback: fmt } }
            }
        }
    });
}

function renderLocationChart(locData, currency) {
    const ctx = document.getElementById('locationChart');
    if (!ctx) return;

    if (chartInstances.location) chartInstances.location.destroy();
    
    const fmt = currencyFormatter(currency);

    chartInstances.location = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: locData.map(d => d.location),
            datasets: [{
                label: `Cost by Location (${currency})`,
                data: locData.map(d => d.cost),
                backgroundColor: 'rgba(139, 92, 246, 0.8)',
            }]
        },
        options: {
            ...commonOptions(currency),
            scales: {
                y: { ticks: { callback: fmt } }
            }
        }
    });
}
