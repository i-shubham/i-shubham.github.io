// Resume Protection Script
(function() {
    'use strict';
    
    // Store original page content
    let originalContent = null;
    let isProtected = false;
    
    // Function to remove HTML elements from the page
    function removeHtmlElements() {
        if (isProtected) return; // Already protected
        
        // Store original content before clearing
        originalContent = document.documentElement.innerHTML;
        isProtected = true;
        
        // Completely clear the entire document
        document.documentElement.innerHTML = '';
        
        // Create a new body with protection message
        const newBody = document.createElement('body');
        newBody.style.cssText = `
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: Arial, sans-serif;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        // Create protection message
        const message = document.createElement('div');
        message.style.cssText = `
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            text-align: center;
            max-width: 500px;
            margin: 20px;
        `;
        message.innerHTML = `
            <div style="font-size: 48px; margin-bottom: 20px;">🛡️</div>
            <h2 style="color: #2c3e50; margin-bottom: 15px; font-size: 24px;">Access Restricted</h2>
            <p style="color: #7f8c8d; margin-bottom: 20px; line-height: 1.5;">
                Developer tools detected. This content is protected for security reasons.
            </p>
            <div style="color: #e74c3c; font-size: 14px; font-weight: bold;">
                HTML content has been removed
            </div>
        `;
        
        newBody.appendChild(message);
        document.documentElement.appendChild(newBody);
    }
    
    // Function to restore original page content
    function restoreOriginalContent() {
        if (!isProtected || !originalContent) return;
        
        // Restore original content
        document.documentElement.innerHTML = originalContent;
        isProtected = false;
        
        // Re-initialize protection after restoration
        setTimeout(() => {
            disableBrowserFeatures();
            detectDevTools();
            disableViewSource();
            addProtectionOverlay();
        }, 100);
    }
    
    // Function to detect developer tools
    function detectDevTools() {
        let devtools = {open: false, orientation: null};
        
        // Multiple detection methods
        function checkDevTools() {
            const threshold = 160;
            const widthThreshold = window.outerWidth - window.innerWidth > threshold;
            const heightThreshold = window.outerHeight - window.innerHeight > threshold;
            
            // Additional detection methods
            const consoleCheck = window.console && (window.console.firebug || window.console.exception);
            const performanceCheck = window.performance && window.performance.timing && window.performance.timing.loadEventEnd > 0;
            
            if (widthThreshold || heightThreshold || consoleCheck) {
                if (!devtools.open) {
                    devtools.open = true;
                    devtools.orientation = widthThreshold ? 'vertical' : 'horizontal';
                    removeHtmlElements();
                }
            } else {
                if (devtools.open) {
                    devtools.open = false;
                    devtools.orientation = null;
                    // Restore content when dev tools are closed
                    setTimeout(restoreOriginalContent, 500);
                }
            }
        }
        
        // Check immediately
        checkDevTools();
        
        // Check periodically
        setInterval(checkDevTools, 100);
        
        // Additional protection: monitor console usage
        const originalConsole = window.console;
        window.console = {
            log: function() { removeHtmlElements(); },
            warn: function() { removeHtmlElements(); },
            error: function() { removeHtmlElements(); },
            info: function() { removeHtmlElements(); },
            debug: function() { removeHtmlElements(); },
            clear: function() { removeHtmlElements(); },
            dir: function() { removeHtmlElements(); },
            dirxml: function() { removeHtmlElements(); },
            table: function() { removeHtmlElements(); },
            trace: function() { removeHtmlElements(); },
            group: function() { removeHtmlElements(); },
            groupCollapsed: function() { removeHtmlElements(); },
            groupEnd: function() { removeHtmlElements(); },
            time: function() { removeHtmlElements(); },
            timeEnd: function() { removeHtmlElements(); },
            timeLog: function() { removeHtmlElements(); },
            profile: function() { removeHtmlElements(); },
            profileEnd: function() { removeHtmlElements(); },
            count: function() { removeHtmlElements(); },
            countReset: function() { removeHtmlElements(); },
            assert: function() { removeHtmlElements(); },
            markTimeline: function() { removeHtmlElements(); },
            timeline: function() { removeHtmlElements(); },
            timelineEnd: function() { removeHtmlElements(); },
            timeStamp: function() { removeHtmlElements(); },
            memory: originalConsole.memory,
            firebug: originalConsole.firebug,
            exception: originalConsole.exception
        };
    }
    
    // Function to disable various browser features
    function disableBrowserFeatures() {
        // Disable right-click context menu
        document.addEventListener('contextmenu', function(e) {
            e.preventDefault();
            return false;
        });
        
        // Disable keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            // Disable Ctrl+U (View Source)
            if (e.ctrlKey && e.key === 'u') {
                e.preventDefault();
                removeHtmlElements();
                return false;
            }
            // Disable F12 (Developer Tools)
            if (e.key === 'F12') {
                e.preventDefault();
                removeHtmlElements();
                return false;
            }
            // Disable Ctrl+Shift+I (Developer Tools)
            if (e.ctrlKey && e.shiftKey && e.key === 'I') {
                e.preventDefault();
                removeHtmlElements();
                return false;
            }
            // Disable Ctrl+Shift+C (Developer Tools)
            if (e.ctrlKey && e.shiftKey && e.key === 'C') {
                e.preventDefault();
                removeHtmlElements();
                return false;
            }
            // Disable Ctrl+S (Save Page)
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                return false;
            }
            // Disable Ctrl+P (Print) - Allow printing for resume
            if (e.ctrlKey && e.key === 'p') {
                // Allow printing but remove HTML after
                setTimeout(removeHtmlElements, 1000);
            }
            // Disable Ctrl+A (Select All)
            if (e.ctrlKey && e.key === 'a') {
                e.preventDefault();
                return false;
            }
        });
        
        // Disable drag and drop
        document.addEventListener('dragstart', function(e) {
            e.preventDefault();
            return false;
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
        
        // Disable print screen
        document.addEventListener('keyup', function(e) {
            if (e.key === 'PrintScreen') {
                e.preventDefault();
                removeHtmlElements();
                return false;
            }
        });
        
        // Disable save as
        document.addEventListener('beforeunload', function(e) {
            e.preventDefault();
            e.returnValue = '';
        });
    }
    
    // Function to disable view source via URL
    function disableViewSource() {
        if (window.location.href.includes('view-source:')) {
            window.location.href = window.location.href.replace('view-source:', '');
        }
    }
    
    // Function to add protection overlay
    function addProtectionOverlay() {
        const overlay = document.createElement('div');
        overlay.id = 'protection-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: transparent;
            z-index: 9999;
            pointer-events: none;
        `;
        document.body.appendChild(overlay);
        
        // Add additional protection methods
        addMutationObserver();
        addDebuggerProtection();
    }
    
    // Function to monitor DOM changes
    function addMutationObserver() {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    // Check if any added nodes are suspicious
                    for (let i = 0; i < mutation.addedNodes.length; i++) {
                        const node = mutation.addedNodes[i];
                        if (node.nodeType === 1 && (node.tagName === 'SCRIPT' || node.tagName === 'IFRAME')) {
                            removeHtmlElements();
                            break;
                        }
                    }
                }
            });
        });
        
        observer.observe(document.documentElement, {
            childList: true,
            subtree: true
        });
    }
    
    // Function to add debugger protection
    function addDebuggerProtection() {
        setInterval(function() {
            debugger;
        }, 100);
    }
    
    // Initialize protection when DOM is loaded
    function initProtection() {
        // Wait for DOM to be fully loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                disableBrowserFeatures();
                detectDevTools();
                disableViewSource();
                addProtectionOverlay();
            });
        } else {
            disableBrowserFeatures();
            detectDevTools();
            disableViewSource();
            addProtectionOverlay();
        }
    }
    
    // Start protection
    initProtection();
    
    // Export functions for external use if needed
    window.ResumeProtection = {
        removeHtmlElements: removeHtmlElements,
        restoreOriginalContent: restoreOriginalContent,
        detectDevTools: detectDevTools,
        disableBrowserFeatures: disableBrowserFeatures
    };
    
})(); 