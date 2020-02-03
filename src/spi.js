var initialized = false;
var lastState = null;

function oneTime() {
  if (!initialized) {
    $.fn.dataTable.moment("HH:mm:ss.SSSS", "en", false);
    $.fn.dataTable.moment("mm:ss.SSSS", "en", false);

    function equalStates(s1, s2) {
      if (s1 == null || s2 == null) {
        return s1 == s2;
      }
      if (s1.driver != null || s2.driver != null) {
        return s1.driver == s2.driver;
      }
      if (s1.race != null || s2.race != null) {
        return s1.race == s2.race &&
          s1.season == s2.season &&
          s1.league == s2.league;
      }
      if (s1.season != null || s2.season != null) {
        return s1.season == s2.season &&
          s1.league == s2.league;
      }
      if (s1.league != null || s2.league != null) {
        return s1.league == s2.league;
      }
      return true;
    }

    History.Adapter.bind(window, "statechange", function() {
      var state = History.getState();
      if (state.data != null && !equalStates(state.data, lastState)) {
        lastState = state.data;
        loadState(state.data);
      }
    });

    $("#js-required").remove();

    initialized = true;
  }
}

function doInit() {
  oneTime();
  setTitles("Loading...", "Just one second", null, false, "small");
  var content = $("#content")[0];
  while (content.firstChild) {
    content.removeChild(content.firstChild);
  }
}

function pushState(state, title) {
  History.pushState(state, title, getSlug(state));
}

function updateState(state, title) {
  lastState = state;
  History.replaceState(state, title, getSlug(state));
}

function getSlug(state) {
  if (state == null) {
    return "?";
  }

  if (state.driver != null && !isNaN(state.driver)) {
    return "?d=" + state.driver;
  }

  if (state.league == null || isNaN(state.league)) {
    return "?";
  }

  if (state.season == null || isNaN(state.season)) {
    return "?l=" + state.league;
  }

  if (state.race == null || isNaN(state.race)) {
    return "?l=" + state.league + "&s=" + state.season;
  }

  return "?l=" + state.league + "&s=" + state.season + "&r=" + state.race;
}

function readState() {
  var params = new URLSearchParams(location.search);
  var state = {
    "driver": parseInt(params.get("d")),
    "league": parseInt(params.get("l")),
    "season": parseInt(params.get("s")),
    "race": parseInt(params.get("r"))
  };
  return state;
}

function loadState(state) {
  doInit();

  if (state.driver != null && !isNaN(state.driver)) {
    loadDriver(state.driver);
    return;
  }

  if (state.league == null || isNaN(state.league)) {
    loadIndex();
    return;
  }

  if (state.season == null || isNaN(state.season)) {
    loadSeasons(state.league);
    return;
  }

  if (state.race == null || isNaN(state.race)) {
    loadSeason(state.league, state.season);
    return;
  }

  loadRace(state.league, state.season, state.race);
}

function init() {
  lastState = readState();
  loadState(lastState);
}
