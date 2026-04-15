const msalConfig = {
    auth: {
        // REPLACE WITH YOUR FRONTEND APP REGISTRATION CLIENT ID
        clientId: "b13cf0fa-9928-42aa-8de9-bca20155ef54",
        
        // REPLACE WITH YOUR TENANT ID
        authority: "https://login.microsoftonline.com/0e979c79-b015-47ab-b27a-8a0b0924d271",
        
        redirectUri: "https://localhost:8000"
    },
    cache: {
        cacheLocation: "sessionStorage",
        storeAuthStateInCookie: false,
    }
};

const msalInstance = new msal.PublicClientApplication(msalConfig);

// Initialize MSAL instance (required for MSAL.js v3)
let isMsalInitialized = false;

// API scopes requested
const tokenRequest = {
    // We are just requesting basic sign-in for now. 
    // Later, when you deploy the backend, we can add: "api://YOUR_BACKEND_CLIENT_ID_HERE/access_as_user"
    scopes: ["User.Read"]
};

// Check if user is already logged in
async function initializeAuth() {
    await msalInstance.initialize();
    isMsalInitialized = true;
    
    // Handle redirect flow if we just came back from login page
    await msalInstance.handleRedirectPromise();

    const accounts = msalInstance.getAllAccounts();
    if (accounts.length > 0) {
        msalInstance.setActiveAccount(accounts[0]);
        console.log("User logged in:", accounts[0].username);
        return true;
    }
    return false;
}

// Perform login
async function login() {
    if (!isMsalInitialized) await msalInstance.initialize();
    try {
        await msalInstance.loginPopup(tokenRequest);
        const accounts = msalInstance.getAllAccounts();
        if (accounts.length > 0) {
            msalInstance.setActiveAccount(accounts[0]);
            location.reload(); // Reload to refresh dashboard view
        }
    } catch (err) {
        console.error("Login failed:", err);
    }
}

// Perform logout
async function logout() {
    await msalInstance.logoutPopup();
    location.reload();
}

// Get Access Token for API calls
async function getAccessToken() {
    if (!msalInstance.getActiveAccount() && msalInstance.getAllAccounts().length > 0) {
        msalInstance.setActiveAccount(msalInstance.getAllAccounts()[0]);
    }

    const account = msalInstance.getActiveAccount();
    if (!account) return null;

    try {
        const response = await msalInstance.acquireTokenSilent({
            ...tokenRequest,
            account: account
        });
        return response.accessToken;
    } catch (err) {
        if (err instanceof msal.InteractionRequiredAuthError) {
            console.warn("Silent token acquisition failed. Acquiring token using popup");
            return msalInstance.acquireTokenPopup(tokenRequest).then(res => res.accessToken).catch(e => null);
        }
        console.error("Token acquisition error:", err);
        return null;
    }
}
