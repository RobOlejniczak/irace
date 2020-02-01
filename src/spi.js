var initialized = false;

function doInit() {
  if (!initialized) {
    $.fn.dataTable.moment("HH:mm:ss.SSSS", "en", false);
    $.fn.dataTable.moment("mm:ss.SSSS", "en", false);

    $("#js-required").remove();
    console.log($("#js-required"));

    initialized = true;
  }
  setLoading();
}


function setLoading() {
  setTitles("Loading...", "Just one second", null, "small");

  var content = $("#content")[0];
  while (content.firstChild) {
    content.removeChild(content.firstChild);
  }
}

function init() {
  var params = new URLSearchParams(location.search);

  var driver = parseInt(params.get("d"));

  if (!isNaN(driver)) {
    viewDriver(driver);
    return;
  }

  var league = parseInt(params.get("l"));
  var season = parseInt(params.get("s"));
  var race = parseInt(params.get("r"));

  if (isNaN(league)) {
    viewIndex();
    return;
  }

  if (isNaN(season)) {
    viewSeasons(league);
    return;
  }

  if (isNaN(race)) {
    viewSeason(league, season);
    return;
  }

  viewRace(league, season, race);
}
