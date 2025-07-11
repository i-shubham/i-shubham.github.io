function includeHTML(id, file, callback) {
  fetch(file)
    .then(response => response.text())
    .then(data => {
      document.getElementById(id).innerHTML = data;
      if (callback) callback();
    });
}
document.addEventListener('DOMContentLoaded', function() {
  includeHTML('header-include', 'header.html');
  includeHTML('navbar-include', 'navbar.html', setActiveNav);
  includeHTML('footer-include', 'footer.html');
});

function setActiveNav() {
  var path = window.location.pathname;
  if (path === "/" || path.endsWith("/index.html")) {
    path = "/index.html";
  }
  var navLinks = document.querySelectorAll('#navbar-include .nav-link');
  navLinks.forEach(function(link) {
    link.classList.remove('active');
    var href = link.getAttribute('href');
    if (href && (path.endsWith(href) || path === href)) {
      link.classList.add('active');
    }
  });
} 