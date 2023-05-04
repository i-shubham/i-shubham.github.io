
(function () {
  "use strict";

  /**
   * Easy selector helper function
   */
  const select = (el, all = false) => {
    el = el.trim()
    if (all) {
      return [...document.querySelectorAll(el)]
    } else {
      return document.querySelector(el)
    }
  }

  /**
   * Easy event listener function
   */
  const on = (type, el, listener, all = false) => {
    let selectEl = select(el, all)
    if (selectEl) {
      if (all) {
        selectEl.forEach(e => e.addEventListener(type, listener))
      } else {
        selectEl.addEventListener(type, listener)
      }
    }
  }

  /**
   * Easy on scroll event listener 
   */
  const onscroll = (el, listener) => {
    el.addEventListener('scroll', listener)
  }

  /**
   * Navbar links active state on scroll
   */
  let navbarlinks = select('#navbar .scrollto', true)
  const navbarlinksActive = () => {
    let position = window.scrollY + 200
    navbarlinks.forEach(navbarlink => {
      if (!navbarlink.hash) return
      let section = select(navbarlink.hash)
      if (!section) return
      if (position >= section.offsetTop && position <= (section.offsetTop + section.offsetHeight)) {
        navbarlink.classList.add('active')
      } else {
        navbarlink.classList.remove('active')
      }
    })
  }
  window.addEventListener('load', navbarlinksActive)
  onscroll(document, navbarlinksActive)

  /**
   * Scrolls to an element with header offset
   */
  const scrollto = (el) => {
    let elementPos = select(el).offsetTop
    window.scrollTo({
      top: elementPos,
      behavior: 'smooth'
    })
  }

  /**
   * Back to top button
   */
  let backtotop = select('.back-to-top')
  if (backtotop) {
    const toggleBacktotop = () => {
      if (window.scrollY > 100) {
        backtotop.classList.add('active')
      } else {
        backtotop.classList.remove('active')
      }
    }
    window.addEventListener('load', toggleBacktotop)
    onscroll(document, toggleBacktotop)
  }

  /**
   * Mobile nav toggle
   */
  on('click', '.mobile-nav-toggle', function (e) {
    select('body').classList.toggle('mobile-nav-active')
    this.classList.toggle('bi-list')
    this.classList.toggle('bi-x')
  })

  /**
   * Scrool with ofset on links with a class name .scrollto
   */
  on('click', '.scrollto', function (e) {
    if (select(this.hash)) {
      e.preventDefault()

      let body = select('body')
      if (body.classList.contains('mobile-nav-active')) {
        body.classList.remove('mobile-nav-active')
        let navbarToggle = select('.mobile-nav-toggle')
        navbarToggle.classList.toggle('bi-list')
        navbarToggle.classList.toggle('bi-x')
      }
      scrollto(this.hash)
    }
  }, true)

  /**
   * Scroll with ofset on page load with hash links in the url
   */
  window.addEventListener('load', () => {
    if (window.location.hash) {
      if (select(window.location.hash)) {
        scrollto(window.location.hash)
      }
    }
  });

  /**
   * Home Type effect
   */
  const typed = select('.typed')
  if (typed) {
    let typed_strings = typed.getAttribute('data-typed-items')
    typed_strings = typed_strings.split(',')
    new Typed('.typed', {
      strings: typed_strings,
      loop: true,
      typeSpeed: 100,
      backSpeed: 50,
      backDelay: 2000,
      cursorChar: '.',
    });
  }

  /**
   * Skills animation
   */
  let skilsContent = select('.skills-content');
  if (skilsContent) {
    new Waypoint({
      element: skilsContent,
      offset: '80%',
      handler: function (direction) {
        let progress = select('.progress .progress-bar', true);
        progress.forEach((el) => {
          el.style.width = el.getAttribute('aria-valuenow') + '%'
        });
      }
    })
  }

  /**
   * Porfolio isotope and filter
   */
  window.addEventListener('load', () => {
    let portfolioContainer = select('.portfolio-container');
    if (portfolioContainer) {
      let portfolioIsotope = new Isotope(portfolioContainer, {
        itemSelector: '.portfolio-item'
      });

      let portfolioFilters = select('#portfolio-flters li', true);

      on('click', '#portfolio-flters li', function (e) {
        e.preventDefault();
        portfolioFilters.forEach(function (el) {
          el.classList.remove('filter-active');
        });
        this.classList.add('filter-active');

        portfolioIsotope.arrange({
          filter: this.getAttribute('data-filter')
        });
        portfolioIsotope.on('arrangeComplete', function () {
          AOS.refresh()
        });
      }, true);
    }

  });

  /**
   * Initiate portfolio lightbox 
   */
  const portfolioLightbox = GLightbox({
    selector: '.portfolio-lightbox'
  });

  /**
   * Portfolio details slider
   */
  new Swiper('.portfolio-details-slider', {
    speed: 400,
    loop: true,
    autoplay: {
      delay: 5000,
      disableOnInteraction: false
    },
    pagination: {
      el: '.swiper-pagination',
      type: 'bullets',
      clickable: true
    }
  });

  /**
   * Testimonials slider
   */
  new Swiper('.testimonials-slider', {
    speed: 600,
    loop: true,
    autoplay: {
      delay: 5000,
      disableOnInteraction: false
    },
    slidesPerView: 'auto',
    pagination: {
      el: '.swiper-pagination',
      type: 'bullets',
      clickable: true
    },
    breakpoints: {
      320: {
        slidesPerView: 1,
        spaceBetween: 20
      },

      1200: {
        slidesPerView: 3,
        spaceBetween: 20
      }
    }
  });

  /**
   * Animation on scroll
   */
  window.addEventListener('load', () => {
    AOS.init({
      duration: 1000,
      easing: 'ease-in-out',
      once: true,
      mirror: false
    })
  });

  /**
   * Initiate Pure Counter 
   */
  new PureCounter();

})()


function showPortfolioDetails(src) {
  portfolio_data = {
    "sfdc_cop_hackathon": {
      "project_image": "assets/img/portfolio/sfdc_cop_hackathon.png",
      "project_category": "AI/ML",
      "project_client": "Hackathon Competition",
      "project_date": "Oct-2022",
      "project_description": "This is a 96 hours coding challenge based on different categories like: AI/ML, Front-End, Back-End, Data Engineering etc. We're the winner in AI/ML category."
    },
    "apple_recognition": {
      "project_image": "assets/img/portfolio/apple_award.jpeg",
      "project_category": "Big-Data [Supply-Chain]",
      "project_client": "Apple",
      "project_date": "Sep-2021",
      "project_description": "The project was on Apple's Supply Chain domain based on Big-Data ecosystems. The application was built from scratch and breaking couple of monolith applications into microservices based architecture. This was recognised for significant contribution to the success."
    },
    "qualcomm_innovation_maestro": {
      "project_image": "assets/img/portfolio/qcom_innovation_maestro.jpeg",
      "project_category": "Innovation Maestro",
      "project_client": "Qualcomm",
      "project_date": "Jan-2019",
      "project_description": "This was awarded for couple of innovations ideas & prototyping. And, projects were based on Computer Vision / Image Processing."
    },
    "qualcomm_super_qualstar": {
      "project_image": "assets/img/portfolio/qcom_super_qualstar.png",
      "project_category": "Super Qualstar",
      "project_client": "Qualcomm",
      "project_date": "Feb-2019",
      "project_description": "This was awarded for couple of innovations ideas & prototyping, and winning of Innovation Maestro. And, projects were based on Computer Vision / Image Processing."
    },
    "qualcomm_hackathon": {
      "project_image": "assets/img/portfolio/qcom_hackathon.jpeg",
      "project_category": "Qualcomm HaQkathon",
      "project_client": "Qualcomm",
      "project_date": "Nov-2018",
      "project_description": "Qualcomm HaQkathon was an event of 48 hours coding challenges, where participants had to submit innovative ideas along with MVP on the idea. Here, I was declared as winner of the event where projects were based on computer-vision / image-processing."
    },
    "qualcomm_qbuzz": {
      "project_image": "assets/img/portfolio/qcom_qbuzz.jpeg",
      "project_category": "Qualcomm QBuzz",
      "project_client": "Qualcomm",
      "project_date": "2019",
      "project_description": "Qualcomm QBuzz is a platform where all participants project their innovative ideas to the larger & bigger audiences. I was one of the finalists."
    },
    "qualcomm_innovation_maestro_certificate": {
      "project_image": "assets/img/portfolio/qcom_innovation_maestro_certificate.jpeg",
      "project_category": "Qualcomm Innovation Maestro Certificate",
      "project_client": "Qualcomm",
      "project_date": "Jan-2019",
      "project_description": "Certificate for winning the title of Qualcomm Innovation Maestro."
    },
    "qualcomm_qualstar": {
      "project_image": "assets/img/portfolio/qcom_qualstar.png",
      "project_category": "Qualcomm Qualstar",
      "project_client": "Qualcomm",
      "project_date": "Nov-2018",
      "project_description": "Qualstar Certificate for rapid prototyping & execution on AI/ML category."
    },
    "pwc_star_performer": {
      "project_image": "assets/img/portfolio/pwc_star_performer.jpeg",
      "project_category": "PwC Star Performer",
      "project_client": "PwC",
      "project_date": "2015",
      "project_description": "I was awarded as Star performer in the year for successful deliverable of the project."
    },
    "pwc_kudos": {
      "project_image": "assets/img/portfolio/pwc_kudos.jpeg",
      "project_category": "PwC Kudos",
      "project_client": "PwC",
      "project_date": "2016",
      "project_description": "Awarded Kudos for successful deliverables."
    },
    "pwc_appreciation": {
      "project_image": "assets/img/portfolio/pwc_award.jpeg",
      "project_category": "PwC Appreciation",
      "project_client": "PwC",
      "project_date": "Aug-2015",
      "project_description": "Appreciated for successful deliverables."
    },
  }
  var project_image = portfolio_data[src]['project_image'];
  var project_category = portfolio_data[src]['project_category'];
  var project_client = portfolio_data[src]['project_client'];
  var project_date = portfolio_data[src]['project_date'];
  var project_description = portfolio_data[src]['project_description'];
  localStorage["project_image"] = project_image;
  localStorage["project_category"] = project_category;
  localStorage["project_client"] = project_client;
  localStorage["project_date"] = project_date;
  localStorage["project_description"] = project_description;
  window.open('portfolio_details.html', '_blank').focus();

  //    $.ajax({
  //    url: "assets/docs/portfolio_info.json", //the path of the file is replaced by File.json
  //    dataType: "json",
  //    crossOrigin: null,
  //    success:
  //        function (response) {
  //            var project_image = response[src]['project_image'];
  //            var project_category = response[src]['project_category'];
  //            var project_client = response[src]['project_client'];
  //            var project_date = response[src]['project_date'];
  //            var project_description = response[src]['project_description'];
  //            localStorage["project_image"] = project_image;
  //            localStorage["project_category"] = project_category;
  //            localStorage["project_client"] = project_client;
  //            localStorage["project_date"] = project_date;
  //            localStorage["project_description"] = project_description;
  //            window.open('portfolio_details.html', '_blank').focus();
  //        }
  //    });


};
