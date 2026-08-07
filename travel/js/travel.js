(() => {
  "use strict";

  // Prefer extensionless URLs on GitHub Pages: /travel/ and /travel/pages/.../slug/
  // instead of .../index.html. Old .html destination paths keep a stub redirect file.
  if (/\/index\.html$/i.test(window.location.pathname)) {
    const clean = window.location.pathname.replace(/\/index\.html$/i, "/")
      + window.location.search
      + window.location.hash;
    window.location.replace(clean);
    return;
  }

  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  // Portrait photos should remain fully visible instead of being cropped to fill a
  // landscape carousel. Their own image becomes a soft, edge-to-edge backdrop while
  // the original stays sharp and uses its natural proportions in the foreground.
  const prepareSlideImage = (image) => {
    const slide = image.closest(".slide");
    if (!slide) return;

    const applyOrientation = () => {
      if (!image.naturalWidth || !image.naturalHeight) return;
      const isPortrait = image.naturalHeight > image.naturalWidth;
      slide.classList.toggle("is-portrait", isPortrait);

      if (isPortrait) {
        const source = image.currentSrc || image.src;
        const safeSource = source.replace(/["\\]/g, encodeURIComponent);
        slide.style.setProperty("--slide-background", `url("${safeSource}")`);
      } else {
        slide.style.removeProperty("--slide-background");
      }
    };

    if (image.complete) applyOrientation();
    else image.addEventListener("load", applyOrientation, { once: true });
  };

  document.querySelectorAll("[data-carousel] .slide img").forEach(prepareSlideImage);

  const menuButton = document.querySelector(".menu-toggle");
  const menu = document.querySelector(".site-nav");
  if (menuButton && menu) {
    menuButton.addEventListener("click", () => {
      const open = menu.classList.toggle("is-open");
      menuButton.setAttribute("aria-expanded", String(open));
    });
    menu.addEventListener("click", (event) => {
      if (event.target.closest("a")) {
        menu.classList.remove("is-open");
        menuButton.setAttribute("aria-expanded", "false");
      }
    });
  }

  const countryMenus = [...document.querySelectorAll(".nav-dropdown")];
  const closeCountryMenus = () => {
    countryMenus.forEach((countryMenu) => countryMenu.removeAttribute("open"));
  };

  countryMenus.forEach((countryMenu) => {
    countryMenu.addEventListener("toggle", () => {
      if (!countryMenu.open) return;
      countryMenus.forEach((otherMenu) => {
        if (otherMenu !== countryMenu) otherMenu.removeAttribute("open");
      });
    });
  });
  document.addEventListener("click", (event) => {
    if (!event.target.closest(".nav-dropdown")) closeCountryMenus();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeCountryMenus();
  });

  // On pointer devices a flyout should only stay open while the pointer is still over
  // the sidebar (or the flyout itself, which is a descendant of it). The short delay
  // covers the pointer travelling across the gap between the two.
  const sidebar = document.querySelector(".site-header");
  if (sidebar && window.matchMedia("(hover: hover)").matches) {
    let closeTimer = null;
    const cancelClose = () => {
      window.clearTimeout(closeTimer);
      closeTimer = null;
    };
    sidebar.addEventListener("mouseleave", () => {
      cancelClose();
      closeTimer = window.setTimeout(closeCountryMenus, 180);
    });
    sidebar.addEventListener("mouseenter", cancelClose);
  }

  class Carousel {
    constructor(element) {
      this.element = element;
      this.slides = [...element.querySelectorAll(".slide")];
      this.index = Math.max(0, this.slides.findIndex((slide) => slide.classList.contains("is-active")));
      this.interval = Number(element.dataset.interval) || 5500;
      this.timer = null;
      this.userPaused = false;
      this.status = element.querySelector(".carousel-status");
      this.dots = element.querySelector(".carousel-dots");
      this.previous = element.querySelector('[data-carousel-action="previous"]');
      this.next = element.querySelector('[data-carousel-action="next"]');
      this.pause = element.querySelector('[data-carousel-action="pause"]');

      if (this.slides.length < 2) return;
      this.buildDots();
      this.bind();
      this.show(this.index, false);
      this.start();
    }

    buildDots() {
      if (!this.dots) return;
      this.slides.forEach((slide, index) => {
        const dot = document.createElement("button");
        dot.className = "carousel-dot";
        dot.type = "button";
        dot.setAttribute("aria-label", `Show image ${index + 1} of ${this.slides.length}`);
        dot.addEventListener("click", () => {
          this.show(index);
          this.restart();
        });
        this.dots.append(dot);
      });
    }

    bind() {
      this.previous?.addEventListener("click", () => {
        this.show(this.index - 1);
        this.restart();
      });
      this.next?.addEventListener("click", () => {
        this.show(this.index + 1);
        this.restart();
      });
      this.pause?.addEventListener("click", () => {
        this.userPaused = !this.userPaused;
        this.pause.setAttribute("aria-pressed", String(this.userPaused));
        this.pause.setAttribute("aria-label", this.userPaused ? "Resume slideshow" : "Pause slideshow");
        this.pause.textContent = this.userPaused ? "▶" : "Ⅱ";
        this.userPaused ? this.stop() : this.start();
      });
      this.element.addEventListener("mouseenter", () => this.stop());
      this.element.addEventListener("mouseleave", () => {
        if (!this.userPaused) this.start();
      });
      this.element.addEventListener("focusin", () => this.stop());
      this.element.addEventListener("focusout", (event) => {
        if (!this.element.contains(event.relatedTarget) && !this.userPaused) this.start();
      });
      this.element.addEventListener("keydown", (event) => {
        if (event.key === "ArrowLeft") {
          event.preventDefault();
          this.show(this.index - 1);
          this.restart();
        }
        if (event.key === "ArrowRight") {
          event.preventDefault();
          this.show(this.index + 1);
          this.restart();
        }
        if (event.key === " ") {
          event.preventDefault();
          this.pause?.click();
        }
      });
      document.addEventListener("visibilitychange", () => {
        if (document.hidden) this.stop();
        else if (!this.userPaused) this.start();
      });
      reducedMotion.addEventListener?.("change", () => this.restart());
    }

    show(requested, announce = true) {
      this.index = (requested + this.slides.length) % this.slides.length;
      this.slides.forEach((slide, index) => {
        const active = index === this.index;
        slide.classList.toggle("is-active", active);
        slide.setAttribute("aria-hidden", String(!active));
        slide.querySelectorAll("a, button").forEach((item) => {
          item.tabIndex = active ? 0 : -1;
        });
      });
      [...(this.dots?.children || [])].forEach((dot, index) => {
        dot.setAttribute("aria-current", String(index === this.index));
      });
      if (announce && this.status) {
        this.status.textContent = `Image ${this.index + 1} of ${this.slides.length}`;
      }
    }

    start() {
      this.stop();
      if (reducedMotion.matches || this.userPaused || document.hidden) return;
      this.timer = window.setInterval(() => this.show(this.index + 1), this.interval);
    }

    stop() {
      if (this.timer) window.clearInterval(this.timer);
      this.timer = null;
    }

    restart() {
      if (!this.userPaused) this.start();
    }
  }

  document.querySelectorAll("[data-carousel]").forEach((carousel) => new Carousel(carousel));

  const audio = document.querySelector("[data-travel-audio]");
  const audioControl = document.querySelector("[data-audio-control]");
  const audioStatus = document.querySelector("[data-audio-status]");
  if (audio && audioControl) {
    audio.volume = 0.2;

    const renderAudio = (message) => {
      const playing = !audio.paused;
      audioControl.textContent = playing ? "Ⅱ" : "▶";
      audioControl.setAttribute("aria-label", playing ? "Pause ambient audio" : "Play ambient audio");
      audioControl.setAttribute("aria-pressed", String(playing));
      if (audioStatus && message) audioStatus.textContent = message;
    };

    audioControl.addEventListener("click", async () => {
      if (audio.paused) {
        try {
          await audio.play();
          renderAudio("Playing softly");
        } catch {
          renderAudio("Select play to listen");
        }
      } else {
        audio.pause();
        renderAudio("Paused");
      }
    });
    audio.addEventListener("play", () => renderAudio("Playing softly"));
    audio.addEventListener("pause", () => renderAudio("Paused"));
    audio.addEventListener("error", () => renderAudio("Audio unavailable"));

    window.addEventListener("load", async () => {
      try {
        await audio.play();
        renderAudio("Playing softly");
      } catch {
        renderAudio("Tap play for ambience");
      }
    }, { once: true });
  }

  const year = document.querySelector("[data-current-year]");
  if (year) year.textContent = new Date().getFullYear();

  // Ensure Google Translate mounts even if the CDN callback raced on first load
  const ensureTranslate = () => {
    const mount = document.getElementById("google_translate_element");
    if (!mount || mount.getAttribute("data-initialized") === "true") return;
    if (typeof window.googleTranslateElementInit === "function" && window.google?.translate?.TranslateElement) {
      window.googleTranslateElementInit();
    }
  };
  ensureTranslate();
  window.setTimeout(ensureTranslate, 600);
  window.setTimeout(ensureTranslate, 1500);

  // The visible language picker is ours, not Google's: the widget's own control is kept
  // off-screen and driven programmatically, so what the reader sees is always present and
  // styled no matter what markup the widget renders. The list below is Google's published
  // set of target languages, so every option is a code the translator accepts.
  const LANGUAGES = [
    ["ab", "Abkhaz"], ["ace", "Acehnese"], ["ach", "Acholi"], ["aa", "Afar"],
    ["af", "Afrikaans"], ["sq", "Albanian"], ["alz", "Alur"], ["am", "Amharic"],
    ["ar", "Arabic"], ["hy", "Armenian"], ["as", "Assamese"], ["av", "Avar"],
    ["awa", "Awadhi"], ["ay", "Aymara"], ["az", "Azerbaijani"], ["ban", "Balinese"],
    ["bal", "Baluchi"], ["bm", "Bambara"], ["bci", "Baoulé"], ["ba", "Bashkir"],
    ["eu", "Basque"], ["btx", "Batak Karo"], ["bts", "Batak Simalungun"],
    ["bbc", "Batak Toba"], ["be", "Belarusian"], ["bem", "Bemba"], ["bn", "Bengali"],
    ["bew", "Betawi"], ["bho", "Bhojpuri"], ["bik", "Bikol"], ["bs", "Bosnian"],
    ["br", "Breton"], ["bg", "Bulgarian"], ["bua", "Buryat"], ["yue", "Cantonese"],
    ["ca", "Catalan"], ["ceb", "Cebuano"], ["ch", "Chamorro"], ["ce", "Chechen"],
    ["ny", "Chichewa"], ["zh-CN", "Chinese (Simplified)"], ["zh-TW", "Chinese (Traditional)"],
    ["chk", "Chuukese"], ["cv", "Chuvash"], ["co", "Corsican"],
    ["crh", "Crimean Tatar (Cyrillic)"], ["crh-Latn", "Crimean Tatar (Latin)"],
    ["hr", "Croatian"], ["cs", "Czech"], ["da", "Danish"], ["fa-AF", "Dari"],
    ["dv", "Dhivehi"], ["din", "Dinka"], ["doi", "Dogri"], ["dov", "Dombe"], ["nl", "Dutch"],
    ["dyu", "Dyula"], ["dz", "Dzongkha"], ["en", "English"], ["eo", "Esperanto"],
    ["et", "Estonian"], ["ee", "Ewe"], ["fo", "Faroese"], ["fj", "Fijian"], ["tl", "Filipino"],
    ["fi", "Finnish"], ["fon", "Fon"], ["fr", "French"], ["fr-CA", "French (Canada)"],
    ["fy", "Frisian"], ["fur", "Friulian"], ["ff", "Fulani"], ["gaa", "Ga"],
    ["gl", "Galician"], ["ka", "Georgian"], ["de", "German"], ["el", "Greek"],
    ["gn", "Guarani"], ["gu", "Gujarati"], ["ht", "Haitian Creole"], ["cnh", "Hakha Chin"],
    ["ha", "Hausa"], ["haw", "Hawaiian"], ["iw", "Hebrew"], ["hil", "Hiligaynon"],
    ["hi", "Hindi"], ["hmn", "Hmong"], ["hu", "Hungarian"], ["hrx", "Hunsrik"],
    ["iba", "Iban"], ["is", "Icelandic"], ["ig", "Igbo"], ["ilo", "Ilocano"],
    ["id", "Indonesian"], ["iu-Latn", "Inuktut (Latin)"], ["iu", "Inuktut (Syllabics)"],
    ["ga", "Irish"], ["it", "Italian"], ["jam", "Jamaican Patois"], ["ja", "Japanese"],
    ["jw", "Javanese"], ["kac", "Jingpo"], ["kl", "Kalaallisut"], ["kn", "Kannada"],
    ["kr", "Kanuri"], ["pam", "Kapampangan"], ["kk", "Kazakh"], ["kha", "Khasi"],
    ["km", "Khmer"], ["cgg", "Kiga"], ["kg", "Kikongo"], ["rw", "Kinyarwanda"],
    ["ktu", "Kituba"], ["trp", "Kokborok"], ["kv", "Komi"], ["gom", "Konkani"],
    ["ko", "Korean"], ["kri", "Krio"], ["ku", "Kurdish (Kurmanji)"],
    ["ckb", "Kurdish (Sorani)"], ["ky", "Kyrgyz"], ["lo", "Lao"], ["ltg", "Latgalian"],
    ["la", "Latin"], ["lv", "Latvian"], ["lij", "Ligurian"], ["li", "Limburgish"],
    ["ln", "Lingala"], ["lt", "Lithuanian"], ["lmo", "Lombard"], ["lg", "Luganda"],
    ["luo", "Luo"], ["lb", "Luxembourgish"], ["mk", "Macedonian"], ["mad", "Madurese"],
    ["mai", "Maithili"], ["mak", "Makassar"], ["mg", "Malagasy"], ["ms", "Malay"],
    ["ms-Arab", "Malay (Jawi)"], ["ml", "Malayalam"], ["mt", "Maltese"], ["mam", "Mam"],
    ["gv", "Manx"], ["mi", "Maori"], ["mr", "Marathi"], ["mh", "Marshallese"],
    ["mwr", "Marwadi"], ["mfe", "Mauritian Creole"], ["chm", "Meadow Mari"],
    ["mni-Mtei", "Meiteilon (Manipuri)"], ["min", "Minang"], ["lus", "Mizo"],
    ["mn", "Mongolian"], ["my", "Myanmar (Burmese)"], ["bm-Nkoo", "NKo"],
    ["nhe", "Nahuatl (Eastern Huasteca)"], ["ndc-ZW", "Ndau"], ["nr", "Ndebele (South)"],
    ["new", "Nepalbhasa (Newari)"], ["ne", "Nepali"], ["no", "Norwegian"], ["nus", "Nuer"],
    ["oc", "Occitan"], ["or", "Odia (Oriya)"], ["om", "Oromo"], ["os", "Ossetian"],
    ["pag", "Pangasinan"], ["pap", "Papiamento"], ["ps", "Pashto"], ["fa", "Persian"],
    ["pl", "Polish"], ["pt", "Portuguese (Brazil)"], ["pt-PT", "Portuguese (Portugal)"],
    ["pa", "Punjabi (Gurmukhi)"], ["pa-Arab", "Punjabi (Shahmukhi)"], ["qu", "Quechua"],
    ["kek", "Qʼeqchiʼ"], ["rom", "Romani"], ["ro", "Romanian"], ["rn", "Rundi"],
    ["ru", "Russian"], ["se", "Sami (North)"], ["sm", "Samoan"], ["sg", "Sango"],
    ["sa", "Sanskrit"], ["sat-Latn", "Santali (Latin)"], ["sat", "Santali (Ol Chiki)"],
    ["gd", "Scots Gaelic"], ["nso", "Sepedi"], ["sr", "Serbian"], ["st", "Sesotho"],
    ["crs", "Seychellois Creole"], ["shn", "Shan"], ["sn", "Shona"], ["scn", "Sicilian"],
    ["szl", "Silesian"], ["sd", "Sindhi"], ["si", "Sinhala"], ["sk", "Slovak"],
    ["sl", "Slovenian"], ["so", "Somali"], ["es", "Spanish"], ["su", "Sundanese"],
    ["sus", "Susu"], ["sw", "Swahili"], ["ss", "Swati"], ["sv", "Swedish"], ["ty", "Tahitian"],
    ["tg", "Tajik"], ["ber-Latn", "Tamazight"], ["ber", "Tamazight (Tifinagh)"],
    ["ta", "Tamil"], ["tt", "Tatar"], ["te", "Telugu"], ["tet", "Tetum"], ["th", "Thai"],
    ["bo", "Tibetan"], ["ti", "Tigrinya"], ["tiv", "Tiv"], ["tpi", "Tok Pisin"],
    ["to", "Tongan"], ["lua", "Tshiluba"], ["ts", "Tsonga"], ["tn", "Tswana"], ["tcy", "Tulu"],
    ["tum", "Tumbuka"], ["tr", "Turkish"], ["tk", "Turkmen"], ["tyv", "Tuvan"], ["ak", "Twi"],
    ["udm", "Udmurt"], ["uk", "Ukrainian"], ["ur", "Urdu"], ["ug", "Uyghur"], ["uz", "Uzbek"],
    ["ve", "Venda"], ["vec", "Venetian"], ["vi", "Vietnamese"], ["war", "Waray"],
    ["cy", "Welsh"], ["wo", "Wolof"], ["xh", "Xhosa"], ["sah", "Yakut"], ["yi", "Yiddish"],
    ["yo", "Yoruba"], ["yua", "Yucatec Maya"], ["zap", "Zapotec"], ["zu", "Zulu"]
  ];

  const translateWrap = document.querySelector(".translate-wrap");
  if (translateWrap) {
    // Deliberately a constant rather than document.documentElement.lang: the widget
    // rewrites <html lang> to the language it translated into, so reading it back would
    // report the target language. It matches the pageLanguage passed to the widget in
    // every travel page.
    const SOURCE_LANGUAGE = "en";

    const picker = document.createElement("select");
    picker.className = "lang-select notranslate";
    picker.setAttribute("translate", "no");
    picker.setAttribute("aria-label", "Translate this page");
    LANGUAGES.forEach(([code, label]) => picker.append(new Option(label, code)));
    translateWrap.classList.add("notranslate");
    translateWrap.setAttribute("translate", "no");
    translateWrap.append(picker);

    // The notranslate hints above are not honoured for <option> text, so the canonical
    // labels are re-asserted whenever anything rewrites them. This keeps the picker in
    // English while the rest of the page is translated.
    const canonicalLabels = new Map(LANGUAGES);
    const restoreLabels = () => {
      [...picker.options].forEach((option) => {
        const label = canonicalLabels.get(option.value);
        if (label && option.textContent !== label) option.textContent = label;
      });
    };
    new MutationObserver(restoreLabels).observe(picker, {
      childList: true, subtree: true, characterData: true
    });

    // Always English on arrival — the choice is per page, and the inline head script has
    // already dropped the cookie the widget would otherwise translate from on start-up.
    picker.value = SOURCE_LANGUAGE;

    const applyToWidget = (code) => {
      const combo = document.querySelector(".goog-te-combo");
      if (!combo || !combo.options.length) return false;
      if (![...combo.options].some((option) => option.value === code)) return false;
      if (combo.value !== code) {
        combo.value = code;
        combo.dispatchEvent(new Event("change"));
      }
      restoreLabels();
      return true;
    };
    const whenWidgetReady = (callback) => {
      if (document.querySelector(".goog-te-combo")) {
        callback();
        return;
      }
      const observer = new MutationObserver(() => {
        if (!document.querySelector(".goog-te-combo")) return;
        observer.disconnect();
        callback();
      });
      observer.observe(document.body, { childList: true, subtree: true });
      window.setTimeout(() => observer.disconnect(), 15000);
    };

    picker.addEventListener("change", () => {
      const target = picker.value;
      // Back to English needs a reload — Google cannot un-translate a page it has already
      // rewritten in place — and a reload lands on English because no cookie is kept.
      if (target === SOURCE_LANGUAGE) {
        window.location.reload();
        return;
      }
      whenWidgetReady(() => applyToWidget(target));
    });
  }
})();
