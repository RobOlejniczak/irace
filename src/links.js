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
