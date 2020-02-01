function indexSlug() {
  return "javascript:viewIndex()";
}

function leagueSlug(league) {
  return "javascript:viewSeasons(" + league + ")";
}

function leagueLink(league) {
  return '<a href="' + leagueSlug(league.id) + '">' + league.name + '</a>';
}

function seasonSlug(league, season) {
  return "javascript:viewSeason(" + league + "," + season + ")";
}

function seasonLink(league, season) {
  return '<a href="' + seasonSlug(league.id, season.id) + '">' + season.name + '</a>';
}

function driverLink(driver) {
  return "javascript:viewDriver(" + driver + ")";
}

function raceLink(league, season, race) {
  return "javascript:viewRace(" + league + "," + season + "," + race + ")";
}

function pushState(state) {
  if (state == null) {
    history.pushState(null, "", "/");
    return;
  }
  if (state.driver != null) {
    history.pushState(null, "", "/?d=" + state.driver);
    return;
  }
  if (state.league != null && state.season != null && state.race != null) {
    history.pushState(null, "", "/?l=" + state.league + "&s=" + state.season +
      "&r=" + state.race);
    return;
  }
  if (state.league != null && state.season != null) {
    history.pushState(null, "",  "/?l=" + state.league + "&s=" + state.season);
    return;
  }
  if (state.league != null) {
    history.pushState(null, "",  "/?l=" + state.league);
    return;
  }
  history.pushState(null, "", "/");
}
