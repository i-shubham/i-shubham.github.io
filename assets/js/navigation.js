// Navigation Component - Reusable across all pages
class Navigation {
    constructor() {
        this.currentPage = this.getCurrentPage();
        this.init();
    }

    getCurrentPage() {
        const path = window.location.pathname;
        if (path.includes('/travel/pages/')) return 'travel';
        if (path.includes('/travel/')) return 'travel';
        if (path.includes('/tech/')) return 'tech';
        if (path.includes('/gpt/')) return 'gpt';
        if (path === '/' || path.endsWith('index.html')) return 'portfolio';
        return 'portfolio';
    }

    getNavItems() {
        const currentPage = this.currentPage;
        const basePath = this.getBasePath();
        const path = window.location.pathname;
        
        // Special handling for travel pages
        let travelUrl = `${basePath}travel/index.html`;
        if (path.includes('/travel/pages/') && path.split('/travel/pages/')[1].includes('/')) {
            travelUrl = '../../index.html'; // country subfolder -> travel/index.html
        } else if (path.includes('/travel/pages/')) {
            travelUrl = '../index.html'; // pages directory -> travel/index.html
        }
        
        return [
            { id: 'portfolio', text: 'Portfolio', url: `${basePath}index.html`, icon: 'fas fa-user' },
            { id: 'travel', text: 'Travel-Blog', url: travelUrl, icon: 'fas fa-plane' },
            { id: 'youtube', text: 'YouTube', url: 'https://www.youtube.com/@i-shubham-mallick', icon: 'fab fa-youtube', external: true },
            { id: 'tech', text: 'Tech-Blog', url: `${basePath}tech/tech-index.html`, icon: 'fas fa-code' },
            { id: 'gpt', text: 'Open-GPT', url: `${basePath}gpt/gpt-index.html`, icon: 'fas fa-robot', special: true }
        ];
    }

    getBasePath() {
        const path = window.location.pathname;
        if (path.includes('/travel/pages/') && path.split('/travel/pages/')[1].includes('/')) return '../../../';
        if (path.includes('/travel/pages/')) return '../../';
        if (path.includes('/travel/')) return '../../';
        if (path.includes('/tech/')) return '../../';
        if (path.includes('/gpt/')) return '../';
        return './';
    }

    getSocialLinks() {
        return [
            { url: 'https://www.linkedin.com/in/i-shubham/', icon: 'fab fa-linkedin', title: 'LinkedIn' },
            { url: 'https://www.youtube.com/@i-shubham-mallick', icon: 'fab fa-youtube', title: 'YouTube' },
            { url: 'https://www.instagram.com/i.shubham.01/', icon: 'fab fa-instagram', title: 'Instagram' },
            { url: '#', icon: 'fab fa-twitter', title: 'Twitter' }
        ];
    }

    createNavHTML() {
        const navItems = this.getNavItems();
        const socialLinks = this.getSocialLinks();
        
        let navItemsHTML = '';
        navItems.forEach(item => {
            const isActive = item.id === this.currentPage ? 'active' : '';
            const ariaCurrent = item.id === this.currentPage ? ' aria-current="page"' : '';
            const target = item.external ? ' target="_blank" rel="noopener noreferrer"' : '';
            const specialClass = item.special ? 'gpt-nav-item' : '';
            
            if (item.special) {
                navItemsHTML += `
                    <li class="nav-item">
                        <a class="nav-link ${isActive} ${specialClass}" href="${item.url}"${target}${ariaCurrent}>
                            <span class="gpt-icon">🤖</span>
                            <span class="gpt-text">${item.text}</span>
                        </a>
                    </li>
                `;
            } else {
                navItemsHTML += `
                    <li class="nav-item">
                        <a class="nav-link ${isActive}" href="${item.url}"${target}${ariaCurrent}>
                            <i class="${item.icon}"></i> ${item.text}
                        </a>
                    </li>
                `;
            }
        });

        let socialHTML = '';
        socialLinks.forEach(link => {
            const target = link.url !== '#' ? ' target="_blank"' : '';
            socialHTML += `
                <a href="${link.url}"${target} class="btn btn-outline-primary me-2" title="${link.title}">
                    <i class="${link.icon}"></i>
                </a>
            `;
        });

        return `
            <nav id="mainNavBar" class="navbar navbar-expand-lg navbar-light bg-light">
                <div class="container-fluid" id="mainDivNavBar">
                    <img id="navbarImg" src="${this.getProfileImagePath()}" alt="" class="img-fluid rounded-circle" onerror="this.onerror=null;this.src='${this.getBasePath()}assets/img/profile-img.jpg';">
                    <!-- Brand/Logo -->
                    <a class="navbar-brand" href="${this.getBasePath()}index.html">
                        &nbsp;&nbsp;&nbsp;&nbsp;Shubham Mallick
                    </a>

                    <!-- Toggle Button for Mobile -->
                    <button id="navBarExpandBtn" class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                        <span class="navbar-toggler-icon"></span>
                    </button>

                    <!-- Navbar Content -->
                    <div class="collapse navbar-collapse" id="navbarNav">
                        <!-- Centered Menu -->
                        <ul class="navbar-nav">
                            ${navItemsHTML}
                        </ul>
                        <!-- Social Media Icons -->
                        <div class="d-flex">
                            ${socialHTML}
                        </div>
                    </div>
                </div>
            </nav>
        `;
    }

    getProfileImagePath() {
        const path = window.location.pathname;
        if (path.includes('/travel/pages/') && path.split('/travel/pages/')[1].includes('/')) return '../../../assets/img/profile-img.jpg';
        if (path.includes('/travel/pages/')) return '../../assets/img/profile-img.jpg';
        if (path.includes('/travel/')) return '../../assets/img/profile-img.jpg';
        if (path.includes('/tech/')) return '../../assets/img/profile-img.jpg';
        if (path.includes('/gpt/')) return '../assets/img/profile-img.jpg';
        return 'assets/img/profile-img.jpg';
    }

    loadFonts() {
        // Nunito must be loaded on every page, otherwise the nav falls back to a
        // generic sans-serif and renders at a different weight/metrics per page.
        if (document.querySelector('#nav-fonts')) return;
        const preconnect = document.createElement('link');
        preconnect.rel = 'preconnect';
        preconnect.href = 'https://fonts.gstatic.com';
        preconnect.crossOrigin = 'anonymous';
        document.head.appendChild(preconnect);

        const font = document.createElement('link');
        font.id = 'nav-fonts';
        font.rel = 'stylesheet';
        font.href = 'https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap';
        document.head.appendChild(font);
    }

    addStyles() {
        const styles = `
            <style>
                /* Center navigation menu */
                .navbar-nav {
                    margin-left: auto;
                    margin-right: auto;
                }
                #navbarImg {
                    height: 50px;
                    padding-left: 10px;
                }
                #navbarNav {
                    padding-left: 10px;
                    padding-top: 0;
                    padding-bottom: 0;
                }

                /* Pin the navbar's own metrics so per-page stylesheets and body
                   typography cannot change its height. These styles are injected last,
                   so they win over page CSS at equal specificity. (The tech and GPT
                   pages load travel/css/style_travel.css, which sets a 55px height and
                   extra padding here; height:auto + min-height keeps the bar at the
                   avatar's 50px on desktop while still expanding on mobile.) */
                #mainDivNavBar {
                    height: auto;
                    min-height: 50px;
                    padding-top: 0;
                    padding-bottom: 0;
                }
                #navBarExpandBtn {
                    padding-top: 0;
                }
                #mainDivNavBar,
                #mainDivNavBar .navbar-nav .nav-link,
                #mainDivNavBar .navbar-brand {
                    line-height: 1.5;
                }
                /* The inner container is a centered flex child, so it is shorter than
                   the nav's padding box. Painting the same colour on the nav itself
                   prevents Bootstrap's bg-light showing as strips above/below. */
                #mainNavBar {
                    background: #d1d82f;
                    padding-top: 0;
                    padding-bottom: 0;
                }
                #mainDivNavBar .navbar-brand {
                    font-family: 'Nunito', sans-serif;
                    font-size: 1.25rem;
                    font-weight: 600;
                    margin: 0;
                    padding: 0;
                }
                
                /* Match travel blog navbar look */
                .navbar-light .navbar-nav .nav-link {
                    font-family: 'Nunito', sans-serif;
                    position: relative;
                    margin-right: 25px;
                    color: #FFFFFF !important;
                    font-size: 18px;
                    font-weight: 600;
                    outline: none;
                    transition: .5s;
                }
                .navbar-light .navbar-nav .nav-link:hover,
                .navbar-light .navbar-nav .nav-link.active {
                    color: #86B817 !important;
                }
                #mainDivNavBar {
                    background: #d1d82f;
                }
                /* Underline effect for active and hovered nav links */
                .navbar-light .navbar-nav .nav-link {
                    position: relative;
                }
                .navbar-light .navbar-nav .nav-link::before {
                    position: absolute;
                    content: "";
                    width: 0;
                    height: 2px;
                    bottom: -2px;
                    left: 50%;
                    background: #86B817;
                    transition: .5s;
                }
                .navbar-light .navbar-nav .nav-link:hover::before,
                .navbar-light .navbar-nav .nav-link.active::before {
                    width: calc(100% - 2px);
                    left: 1px;
                }
                
                /* GPT Navigation Animation */
                .gpt-nav-item .gpt-icon {
                    display: inline-block;
                    animation: pulse-gpt 2s infinite;
                    margin-right: 5px;
                    font-size: 1.1em;
                }
                
                .gpt-nav-item .gpt-text {
                    background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4);
                    background-size: 300% 300%;
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    animation: gradient-shift 3s ease-in-out infinite;
                    font-weight: 600;
                }
                
                @keyframes pulse-gpt {
                    0%, 100% {
                        transform: scale(1);
                        opacity: 1;
                    }
                    50% {
                        transform: scale(1.1);
                        opacity: 0.8;
                    }
                }
                
                @keyframes gradient-shift {
                    0%, 100% {
                        background-position: 0% 50%;
                    }
                    50% {
                        background-position: 100% 50%;
                    }
                }
                
                /* Hover effects */
                .nav-link:hover .gpt-icon {
                    animation: bounce-gpt 0.6s ease-in-out;
                }
                
                .nav-link:hover .gpt-text {
                    animation: gradient-shift 1s ease-in-out infinite;
                }
                
                @keyframes bounce-gpt {
                    0%, 20%, 50%, 80%, 100% {
                        transform: translateY(0) scale(1);
                    }
                    40% {
                        transform: translateY(-3px) scale(1.1);
                    }
                    60% {
                        transform: translateY(-1px) scale(1.05);
                    }
                }
            </style>
        `;
        
        // Add styles to head if not already present
        if (!document.querySelector('#nav-styles')) {
            const styleElement = document.createElement('div');
            styleElement.innerHTML = styles;
            styleElement.id = 'nav-styles';
            document.head.appendChild(styleElement);
        }
    }

    init() {
        // Load webfonts, then styles
        this.loadFonts();
        this.addStyles();
        
        // Find the navigation placeholder or create one
        let navContainer = document.querySelector('#nav-placeholder');
        if (!navContainer) {
            // Create a placeholder at the beginning of body
            navContainer = document.createElement('div');
            navContainer.id = 'nav-placeholder';
            document.body.insertBefore(navContainer, document.body.firstChild);
        }
        
        // Insert navigation HTML
        navContainer.innerHTML = this.createNavHTML();
    }
}

// Initialize navigation when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new Navigation();
}); 