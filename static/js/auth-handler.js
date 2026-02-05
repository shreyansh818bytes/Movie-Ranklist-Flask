/**
 * Auth Handler - Client-side authentication state management
 */

const AuthHandler = {
    user: null,

    async checkAuthStatus() {
        try {
            const response = await fetch('/api/auth/status');
            const data = await response.json();
            this.user = data.authenticated ? data.user : null;
            this.updateUI();

            // Load watchlist IDs if user is logged in, then refresh movie cards
            if (this.user && typeof WatchlistStorage !== 'undefined') {
                await WatchlistStorage.loadIds();
                // Re-render movies to show correct watchlist button states
                if (typeof MovieRenderer !== 'undefined') {
                    MovieRenderer.renderAll();
                }
            }

            return data;
        } catch (error) {
            console.error('Failed to check auth status:', error);
            this.user = null;
            this.updateUI();
            return { authenticated: false };
        }
    },

    async logout() {
        try {
            const response = await fetch('/api/auth/logout', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();
            if (data.success) {
                // Show success toast and reload to reset state
                if (typeof showToast === 'function') {
                    showToast('Logged out successfully', 'success');
                }
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
            return data;
        } catch (error) {
            console.error('Failed to logout:', error);
            return { success: false, error: 'Logout failed' };
        }
    },

    updateUI() {
        const authNav = document.getElementById('auth-nav');
        if (!authNav) return;

        if (this.user) {
            const displayName = this.user.username || this.user.email.split('@')[0];
            authNav.innerHTML = `
                <div class="dropdown">
                    <button class="btn btn-outline-light dropdown-toggle" type="button" id="userDropdown" data-bs-toggle="dropdown" aria-expanded="false">
                        <i class="fa fa-user"></i> ${this.escapeHtml(displayName)}
                    </button>
                    <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="userDropdown">
                        <li><a class="dropdown-item" href="#" onclick="AuthHandler.logout(); return false;">Logout</a></li>
                    </ul>
                </div>
            `;
        } else {
            authNav.innerHTML = `
                <a href="/login" class="btn btn-outline-light">Login</a>
            `;
        }
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

document.addEventListener('DOMContentLoaded', () => {
    AuthHandler.checkAuthStatus();
});
