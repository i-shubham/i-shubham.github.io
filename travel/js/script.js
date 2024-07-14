$(document).ready(function () {
  var w = window.innerWidth;

  if (w > 767) {
    $("#menu-jk").scrollToFixed();
    $("#floating-white-wrapper").scrollToFixed();
  } else {
    // $('#menu-jk').scrollToFixed();
  }
});

$(document).ready(function () {
  $(".owl-carousel").owlCarousel({
    loop: true,
    margin: 0,
    nav: true,
    autoplay: true,
    dots: true,
    autoplayTimeout: 5000,
    navText: [
      '<i class="fa fa-angle-left"></i>',
      '<i class="fa fa-angle-right"></i>',
    ],
    responsive: {
      0: {
        items: 1,
      },
      600: {
        items: 1,
      },
      1000: {
        items: 1,
      },
    },
  });

  var urlPath = window.location.pathname;
  var currentPage = urlPath.split("/").pop();
  if (currentPage.includes("html")) {
    console.log("Current Page:" + currentPage);
    var newLink = currentPage.split('.html')[0];
    window.history.replaceState(null, null, newLink);
    window.location(newLink).focus();
  }

});

function openPopup(imageElement) {
  const imageSrc = imageElement.src;
  const imageAlt = imageElement.alt;

  document.getElementById("popup").style.display = "flex";
  document.getElementById("popupImage").src = imageSrc;
  document.getElementById("popupAltText").innerText = imageAlt;
  document.getElementById("mainContainer").classList.add("blurred");
}

function closePopup() {
  document.getElementById("popup").style.display = "none";
  document.getElementById("popupImage").src = "";
  document.getElementById("popupAltText").innerText = "";
  document.getElementById("mainContainer").classList.remove("blurred");
}
