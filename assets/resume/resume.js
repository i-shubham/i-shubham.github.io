// Function to detect if device is mobile
function isMobileDevice() {
    // Check for touch capability
    const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    
    // Check user agent for mobile indicators
    const mobileUserAgent = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    // Check screen size (mobile-like dimensions)
    const smallScreen = window.screen.width <= 768 || window.screen.height <= 768;
    
    // Check if orientation API is available (typically mobile)
    const hasOrientationAPI = typeof window.orientation !== 'undefined';
    
    return hasTouch || mobileUserAgent || (smallScreen && hasOrientationAPI);
}

// Function to detect if likely a tablet in landscape
function isTabletLandscape() {
    return window.screen.width > 768 && window.screen.width <= 1024 && 
           'ontouchstart' in window;
}

// Check device types
const isMobile = isMobileDevice();
const isTablet = isTabletLandscape();

// DevTools detection - runs ALWAYS (even with mobile emulation)
function showWarning() {
    document.body.innerHTML =  '<div style="text-align: center; padding: 50px; font-size: 24px; color: red; background: white; height: 100vh; display: flex; align-items: center; justify-content: center;">Developer tools detected. Access denied.</div>';
}

function checkDevTools() {
    const widthThreshold = 200;
    const heightThreshold = 200;
    
    const widthDiff = window.outerWidth - window.innerWidth;
    const heightDiff = window.outerHeight - window.innerHeight;
    
    // Account for normal browser chrome
    const normalChromeHeight = 100;
    const normalChromeWidth = 20;
    
    const suspiciousWidth = widthDiff > (normalChromeWidth + widthThreshold);
    const suspiciousHeight = heightDiff > (normalChromeHeight + heightThreshold);
    
    if (suspiciousWidth || suspiciousHeight) {
        showWarning();
    }
}

// Start DevTools detection immediately (works regardless of mobile emulation)
let devToolsCheckInterval;
window.addEventListener('load', () => {
    setTimeout(() => {
        devToolsCheckInterval = setInterval(checkDevTools, 1000);
    }, 2000);
});

// Apply other desktop restrictions only if not on mobile/tablet
if (!isMobile && !isTablet) {
    // Desktop-only restrictions (excluding DevTools detection which runs above)

    // Disable right-click context menu
    document.addEventListener('contextmenu', function(e) {
        e.preventDefault();
        return false;
    });

    // Disable keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Disable Ctrl+U (View Source)
        if (e.ctrlKey && e.key.toLowerCase() === 'u') {
            e.preventDefault();
            return false;
        }
        // Disable F12 (Developer Tools)
        if (e.key === 'F12') {
            e.preventDefault();
            return false;
        }
        // Disable Ctrl+Shift+I (Developer Tools)
        if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'i') {
            e.preventDefault();
            return false;
        }
        // Disable Ctrl+Shift+C (Developer Tools)
        if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'c') {
            e.preventDefault();
            return false;
        }
        // Disable Ctrl+Shift+J (Console)
        if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'j') {
            e.preventDefault();
            return false;
        }
        // Disable Ctrl+S (Save Page)
        if (e.ctrlKey && e.key.toLowerCase() === 's') {
            e.preventDefault();
            return false;
        }
        // Disable Ctrl+P (Print)
        if (e.ctrlKey && e.key.toLowerCase() === 'p') {
            e.preventDefault();
            return false;
        }
        // Disable Ctrl+A (Select All)
        if (e.ctrlKey && e.key.toLowerCase() === 'a') {
            e.preventDefault();
            return false;
        }
    });

    // Disable text selection
    document.addEventListener('selectstart', function(e) {
        e.preventDefault();
        return false;
    });

    // Disable copy
    document.addEventListener('copy', function(e) {
        e.preventDefault();
        return false;
    });

    // Disable cut
    document.addEventListener('cut', function(e) {
        e.preventDefault();
        return false;
    });

    // Disable paste
    document.addEventListener('paste', function(e) {
        e.preventDefault();
        return false;
    });

    // Disable drag and drop
    document.addEventListener('dragstart', function(e) {
        e.preventDefault();
        return false;
    });

    // Disable print screen
    document.addEventListener('keyup', function(e) {
        if (e.key === 'PrintScreen') {
            e.preventDefault();
            return false;
        }
    });

} else {
    // Mobile/Tablet - Only disable some features that make sense
    console.log('Mobile/Tablet device detected - Limited restrictions applied');
    
    // Still disable right-click context menu on tablets
    if (isTablet) {
        document.addEventListener('contextmenu', function(e) {
            e.preventDefault();
            return false;
        });
    }
}

// Disable view source via URL (applies to all devices)
if (window.location.href.includes('view-source:')) {
    window.location.href = window.location.href.replace('view-source:', '');
}

// Show device type and DevTools detection status for testing
document.addEventListener('DOMContentLoaded', function() {
    const deviceInfo = document.createElement('div');
    deviceInfo.style.cssText = 'position: fixed; bottom: 10px; right: 10px; background: rgba(0,0,0,0.7); color: white; padding: 10px; border-radius: 5px; font-size: 12px; z-index: 1000;';
    
    function updateDeviceInfo() {
        const widthDiff = window.outerWidth - window.innerWidth;
        const heightDiff = window.outerHeight - window.innerHeight;
        const devToolsOpen = widthDiff > 220 || heightDiff > 300;
        
        deviceInfo.innerHTML = `
            Device: ${isMobile ? 'Mobile' : isTablet ? 'Tablet' : 'Desktop'}<br>
            Screen: ${window.screen.width}x${window.screen.height}<br>
            Touch: ${('ontouchstart' in window) ? 'Yes' : 'No'}<br>
            DevTools: ${devToolsOpen ? '⚠️ DETECTED' : '✅ Clear'}<br>
            Dimensions: ${widthDiff}x${heightDiff} diff<br>
            Restrictions: ${(!isMobile && !isTablet) ? 'Active' : 'Limited'}<br>
            DevTools Check: Always Active
        `;
    }
    
    // Uncomment the lines below to show device info for testing
    // updateDeviceInfo();
    // setInterval(updateDeviceInfo, 1000);
    
    document.body.appendChild(deviceInfo);
});

// Remove all CSS from skill icons at runtime
document.addEventListener('DOMContentLoaded', function() {
    const skillIcons = document.querySelectorAll('.skill-icon');
    skillIcons.forEach(function(icon) {
        // Remove all computed styles
        icon.style.cssText = '';
        // Force natural emoji display
        icon.style.color = '';
        icon.style.background = '';
        icon.style.webkitBackgroundClip = '';
        icon.style.webkitTextFillColor = '';
        icon.style.backgroundClip = '';
        icon.style.filter = '';
        icon.style.textShadow = '';
        icon.style.fontSize = '';
        icon.style.margin = '';
        icon.style.display = '';
        icon.style.verticalAlign = '';
    });
});

function downloadResume() {
    // Hide the download button temporarily
    const downloadBtn = document.querySelector('.download-btn');
    downloadBtn.style.display = 'none';
    
    // Get the resume container
    const element = document.querySelector('.container');
    
    // Temporarily fix gradient text elements for PDF
    const gradientElements = element.querySelectorAll('.company, .job-title, .degree, .grade, .award-title');
    const originalStyles = [];
    
    // Store original container styles
    const originalContainerStyles = {
        borderRadius: element.style.borderRadius,
        border: element.style.border,
        overflow: element.style.overflow
    };
    
    // Remove border radius from container for PDF
    element.style.borderRadius = '0';
    element.style.border = 'none';
    element.style.overflow = 'visible';
    
    gradientElements.forEach((el, index) => {
        originalStyles[index] = {
            background: el.style.background,
            webkitBackgroundClip: el.style.webkitBackgroundClip,
            webkitTextFillColor: el.style.webkitTextFillColor,
            backgroundClip: el.style.backgroundClip
        };
        
        // Force solid colors for PDF
        el.style.background = 'none';
        el.style.webkitBackgroundClip = 'unset';
        el.style.webkitTextFillColor = 'unset';
        el.style.backgroundClip = 'unset';
        el.style.textShadow = 'none';
        
        // Set appropriate solid colors
        if (el.classList.contains('company')) {
            el.style.color = '#3498db';
            el.style.fontWeight = '600';
            el.style.fontSize = '1.2em';
        } else if (el.classList.contains('job-title')) {
            el.style.color = '#704da6';
            el.style.fontWeight = '700';
            el.style.fontSize = '1em';
        } else if (el.classList.contains('degree')) {
            el.style.color = '#2c3e50';
            el.style.fontSize = '0.8em';
            el.style.lineHeight = '1.2';
        } else if (el.classList.contains('grade')) {
            el.style.color = '#27ae60';
            el.style.fontWeight = '600';
        } else if (el.classList.contains('award-title')) {
            el.style.color = '#e74c3c';
            el.style.fontWeight = '700';
        }
    });
    
    // PDF options - NO MARGINS with better color preservation
    const opt = {
        margin: [0, 0, 0, 0],
        filename: 'Shubham Mallick - Data and Application Architect.pdf',
        image: { type: 'jpeg', quality: 1.0, pixelRatio: 4, dpi: 900 },
        html2canvas: { 
            scale: 4,
            useCORS: true,
            allowTaint: true,
            backgroundColor: '#ffffff',
            scrollX: 0,
            scrollY: 0,
            windowWidth: document.documentElement.offsetWidth,
            windowHeight: document.documentElement.offsetHeight,
            logging: false,
            removeContainer: true
        },
        jsPDF: { 
            unit: 'mm', 
            format: 'a4', 
            orientation: 'portrait',
            compress: false
        }
    };
    
    // Generate and download PDF
    html2pdf().set(opt).from(element).save().then(() => {
        // Restore original styles
        gradientElements.forEach((el, index) => {
            if (originalStyles[index]) {
                el.style.background = originalStyles[index].background;
                el.style.webkitBackgroundClip = originalStyles[index].webkitBackgroundClip;
                el.style.webkitTextFillColor = originalStyles[index].webkitTextFillColor;
                el.style.backgroundClip = originalStyles[index].backgroundClip;
                el.style.color = '';
                el.style.fontWeight = '';
                el.style.textShadow = '';
            }
        });
        
        // Restore container styles
        element.style.borderRadius = originalContainerStyles.borderRadius;
        element.style.border = originalContainerStyles.border;
        element.style.overflow = originalContainerStyles.overflow;
        
        // Show the download button again
        downloadBtn.style.display = 'flex';
    }).catch(error => {
        console.error('PDF generation failed:', error);
        
        // Restore original styles on error too
        gradientElements.forEach((el, index) => {
            if (originalStyles[index]) {
                el.style.background = originalStyles[index].background;
                el.style.webkitBackgroundClip = originalStyles[index].webkitBackgroundClip;
                el.style.webkitTextFillColor = originalStyles[index].webkitTextFillColor;
                el.style.backgroundClip = originalStyles[index].backgroundClip;
                el.style.color = '';
                el.style.fontWeight = '';
                el.style.textShadow = '';
            }
        });
        
        // Restore container styles on error too
        element.style.borderRadius = originalContainerStyles.borderRadius;
        element.style.border = originalContainerStyles.border;
        element.style.overflow = originalContainerStyles.overflow;
        
        downloadBtn.style.display = 'flex';
    });
}
