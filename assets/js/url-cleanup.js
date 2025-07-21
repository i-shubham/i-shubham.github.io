// Minimal script to hide .html extension from URL
(function() {
    'use strict';
    
    // Check if current page has .html extension
    var urlPath = window.location.pathname;
    var currentPage = urlPath.split("/").pop();
    
    if (currentPage && currentPage.includes(".html")) {
        console.log("Current Page: " + currentPage);
        var newLink = currentPage.split('.html')[0];
        var newPath = urlPath.replace(currentPage, newLink);
        window.history.replaceState(null, null, newPath);
    }
})(); 