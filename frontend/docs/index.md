# Azure Cost Summary

Welcome to your Azure Cost Dashboard.

<div id="login-container" style="display: none; text-align: center; margin-top: 50px;">
    <h2>Authentication Required</h2>
    <p>Please log in with your Entra ID (Azure AD) account to view costs.</p>
    <button onclick="login()" class="md-button md-button--primary">Sign In</button>
</div>

<div id="dashboard-container" class="dashboard-container" style="display: none;">
  <div style="grid-column: 1 / -1; margin-bottom: 5px;">
    <label for="subSelect" style="font-weight: 600; margin-right: 10px;">Filter by Subscription:</label>
    <select id="subSelect" style="padding: 8px 12px; border-radius: 6px; border: 1px solid #ccc; font-family: inherit; font-size: 14px; background: white; cursor: pointer; min-width: 200px;">
        <option value="">All Subscriptions</option>
    </select>
  </div>
  <div class="chart-card">
    <h3>Accumulated Cost</h3>
    <div class="canvas-wrapper"><canvas id="accumulatedChart"></canvas></div>
  </div>
  <div class="chart-card">
    <h3>Cost by Service</h3>
    <div class="canvas-wrapper"><canvas id="serviceChart"></canvas></div>
  </div>
  <div class="chart-card">
    <h3>Cost by Resource Group</h3>
    <div class="canvas-wrapper"><canvas id="rgChart"></canvas></div>
  </div>
  <div class="chart-card">
    <h3>Cost by Location</h3>
    <div class="canvas-wrapper"><canvas id="locationChart"></canvas></div>
  </div>
</div>

<script>
  // Wait for the DOM to be ready before calling JS functions
  document.addEventListener("DOMContentLoaded", async () => {
    
    // Slight delay to ensure scripts are completely injected by MkDocs
    setTimeout(async () => {
        const loginContainer = document.getElementById('login-container');
        const dashboardContainer = document.getElementById('dashboard-container');
        
        if (typeof initializeAuth === 'function') {
            const isLoggedIn = await initializeAuth();
            if (isLoggedIn) {
                // User is authenticated, load dashboard
                loginContainer.style.display = 'none';
                dashboardContainer.style.display = 'grid';
                loadDashboardData();
            } else {
                // User not authenticated
                loginContainer.style.display = 'block';
                dashboardContainer.style.display = 'none';
            }
        } else {
            console.error("Auth library not loaded. Ensure MSAL is configured.");
        }
    }, 200);
  });
</script>
