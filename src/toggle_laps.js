var lastOpened;

function showLaps(driver) {
  hideLaps();
  $("#laps-" + driver).slideDown(100, function() {
    lastOpened = driver;
  });
}

function hideLaps() {
  if (lastOpened != null) {
    $("#laps-" + lastOpened).slideUp(100);
    lastOpened = null;
  }
}

var lapsOpen = false;

function toggleLaps() {
  if (lapsOpen) {
    $("#lapTimeChart").slideUp(100, function() {
      lapsOpen = false;
      $("#toggleLapsState")[0].innerHTML = "show";
    });
  } else {
    $("#lapTimeChart").slideDown(100, function() {
      lapsOpen = true;
      $("#toggleLapsState")[0].innerHTML = "hide";
    });
  }
}

$(document).click(function(event) {
  ele = event.target;
  if (ele == null) {
    hideLaps();
    return;
  }
  if (ele.getElementsByClassName("laps").length) {
    return;
  }
  while (ele != null && !ele.classList.contains("laps")) {
    if (ele.tagName == "BODY") {
      hideLaps();
      break;
    }
    ele = ele.parentElement;
  }
});
