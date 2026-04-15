// Function API Base URL (routed through our local HTTPS proxy)
const API_BASE_URL = "https://localhost:8000/api";

async function fetchCosts(subscriptionId = '') {
    try {
        let url = `${API_BASE_URL}/costs`;
        if (subscriptionId) {
            url += `?subscriptionId=${encodeURIComponent(subscriptionId)}`;
        }
        
        // Fetch token from MSAL
        const token = typeof getAccessToken === 'function' ? await getAccessToken() : null;
        
        const headers = {};
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        } else {
            console.warn("No authentication token found. Making anonymous request.");
        }

        const response = await fetch(url, { headers });
        if (!response.ok) {
            if (response.status === 401) {
                console.error("Unauthorized: Please login.");
                throw new Error("Unauthorized");
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Failed to fetch cost data:", error);
        
        // Mock data fallback if backend is not running yet
        console.warn("Using mock data because backend request failed.");
        return {
            currency: "USD",
            monthly: [
                {month: "2025-11", cost: 120.5},
                {month: "2025-12", cost: 135.2},
                {month: "2026-01", cost: 140.0},
                {month: "2026-02", cost: 110.8},
                {month: "2026-03", cost: 150.3}
            ],
            service: [
                {service: "Virtual Machines", cost: 400.0},
                {service: "Storage", cost: 150.0},
                {service: "Azure SQL", cost: 250.0},
                {service: "App Service", cost: 120.0},
                {service: "Others", cost: 80.0}
            ],
            resourceGroup: [
                {resourceGroup: "rg-prod-01", cost: 500.0},
                {resourceGroup: "rg-dev-01", cost: 300.0},
                {resourceGroup: "rg-test-01", cost: 120.0}
            ],
            location: [
                {location: "East US", cost: 600.0},
                {location: "West Europe", cost: 320.0}
            ]
        };
    }
}

async function fetchSubscriptions() {
    try {
        const token = typeof getAccessToken === 'function' ? await getAccessToken() : null;
        const headers = {};
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const response = await fetch(`${API_BASE_URL}/subscriptions`, { headers });
        if (!response.ok) throw new Error("Failed to load subscriptions");
        return await response.json();
    } catch (e) {
        console.warn("Using mock subscriptions because API failed.");
        return [
            {id: "mock-sub-01", name: "Production"},
            {id: "mock-sub-02", name: "Development"},
            {id: "mock-sub-03", name: "Testing"}
        ];
    }
}
