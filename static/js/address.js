// Suggests Cyprus street addresses from Google Places as the customer types, then fills the
// address and town fields. Without a key or network the field stays a plain text input.
(function () {
  var script = document.currentScript;
  var input = document.getElementById("address");
  var town = document.getElementById("town");
  var list = document.getElementById("address-suggest");
  if (!script || !input || !list) return;
  var key = script.dataset.key;
  var lang = script.dataset.lang || "en";
  if (!key) return;

  var places = null;
  var token = null;
  var items = [];
  var active = -1;
  var timer = null;
  var latest = 0;

  function loadGoogle() {
    return new Promise(function (resolve, reject) {
      window.vittorioMapsReady = resolve;
      var tag = document.createElement("script");
      tag.src = "https://maps.googleapis.com/maps/api/js?key=" + encodeURIComponent(key) +
        "&loading=async&libraries=places&region=CY&language=" + lang + "&callback=vittorioMapsReady";
      tag.async = true;
      tag.onerror = reject;
      document.head.appendChild(tag);
    }).then(function () {
      return google.maps.importLibrary("places");
    });
  }

  function ready() {
    if (!places) {
      places = loadGoogle().catch(function () { places = null; return null; });
    }
    return places;
  }

  function close() {
    list.hidden = true;
    list.innerHTML = "";
    items = [];
    active = -1;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
  }

  function highlight(index) {
    var options = list.querySelectorAll("[role=option]");
    options.forEach(function (option, i) { option.setAttribute("aria-selected", i === index ? "true" : "false"); });
    active = index;
    if (options[index]) input.setAttribute("aria-activedescendant", options[index].id);
  }

  function render(suggestions) {
    list.innerHTML = "";
    items = suggestions;
    suggestions.forEach(function (suggestion, i) {
      var option = document.createElement("li");
      option.id = "address-option-" + i;
      option.setAttribute("role", "option");
      option.textContent = suggestion.placePrediction.text.toString();
      option.addEventListener("mousedown", function (event) {
        event.preventDefault();
        choose(i);
      });
      list.appendChild(option);
    });
    var credit = document.createElement("li");
    credit.className = "address-credit";
    credit.setAttribute("aria-hidden", "true");
    credit.textContent = "Powered by Google";
    list.appendChild(credit);
    list.hidden = suggestions.length === 0;
    input.setAttribute("aria-expanded", suggestions.length ? "true" : "false");
    active = -1;
  }

  function lookup() {
    var text = input.value.trim();
    if (text.length < 3) return close();
    var request = ++latest;
    ready().then(function (lib) {
      if (!lib) return;
      token = token || new lib.AutocompleteSessionToken();
      return lib.AutocompleteSuggestion.fetchAutocompleteSuggestions({
        input: text,
        includedRegionCodes: ["cy"],
        language: lang,
        sessionToken: token
      }).then(function (result) {
        if (request !== latest) return;
        render((result.suggestions || []).filter(function (s) { return s.placePrediction; }).slice(0, 5));
      });
    }).catch(close);
  }

  function part(components, type, short) {
    var found = (components || []).find(function (c) { return c.types.indexOf(type) !== -1; });
    return found ? (short ? found.shortText : found.longText) : "";
  }

  function choose(index) {
    var suggestion = items[index];
    if (!suggestion) return;
    var fallback = suggestion.placePrediction.text.toString();
    close();
    input.value = fallback;
    var place = suggestion.placePrediction.toPlace();
    place.fetchFields({ fields: ["addressComponents", "formattedAddress"] }).then(function () {
      var c = place.addressComponents;
      var street = [part(c, "route"), part(c, "street_number")].filter(Boolean).join(" ");
      var building = part(c, "premise");
      var city = part(c, "locality") || part(c, "postal_town") || part(c, "administrative_area_level_1");
      var postcode = part(c, "postal_code");
      var line = [building, street, postcode].filter(Boolean).join(", ");
      input.value = line || (place.formattedAddress || fallback).replace(/,\s*(Cyprus|Κύπρος)$/, "");
      if (town && city) town.value = city;
    }).catch(function () {}).then(function () {
      token = null;  // a selection ends the billing session
      input.focus();
    });
  }

  input.setAttribute("role", "combobox");
  input.setAttribute("aria-autocomplete", "list");
  input.setAttribute("aria-controls", list.id);
  input.setAttribute("aria-expanded", "false");
  input.setAttribute("autocomplete", "off");

  input.addEventListener("input", function () {
    clearTimeout(timer);
    timer = setTimeout(lookup, 250);
  });
  input.addEventListener("keydown", function (event) {
    if (list.hidden || !items.length) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      highlight((active + 1) % items.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      highlight((active - 1 + items.length) % items.length);
    } else if (event.key === "Enter" && active >= 0) {
      event.preventDefault();
      choose(active);
    } else if (event.key === "Escape") {
      close();
    }
  });
  input.addEventListener("blur", function () { setTimeout(close, 150); });
})();
