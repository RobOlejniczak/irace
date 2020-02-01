function hideX() {
  var div = document.createElement("div");
  div.classList.add("hideX");
  var a = document.createElement("a");
  a.href = "javascript:hideLaps()";
  a.title = "Close";
  a.innerHTML = "x";
  div.appendChild(a);
  return div;
}

function driverLapsDiv(driver) {
  var div = document.createElement("div");
  div.id = "laps-" + driver.id;
  div.classList.add("laps");

  var p = document.createElement("p");
  p.innerHTML = driver.name + " laps driven";

  var table = document.createElement("table");
  table.id = driver.id + "-laps";
  table.classList.add("display");
  table.classList.add("compact");
  table.classList.add("lapdata");
  table.style.width = "100%";

  div.appendChild(p);
  div.appendChild(hideX());
  div.appendChild(table);

  return div;
}

function getColumns(multiclass) {
  var columns = [
    {
      "title": "",
      "data": null,
      "searchable": false,
      "orderable": false,
      "className": "index right-border bold"
    },
    {
      "title": "Name",
      "data": "driver.name",
      "className": "serif left",
      "render": function(data, type, row, meta) {
        return '<a href="' + driverLink(row.driver.id) + '">' + data + "</a>";
      }
    }
  ];

  if (multiclass) {
    columns.push({
      "title": "Class",
      "data": "class.name",
      "className": "serif"
    });
  }

  columns.push({
    "title": "Interval",
    "data": "interval",
    "orderData": multiclass ? 4 : 3
  });
  columns.push({
    "title": "Finish",
    "data": "finish",
    "className": "index"
  });

  if (multiclass) {
    columns.push({
      "title": "Class Finish",
      "data": "class.finish",
      "className": "index"
    });
  }

  columns.push({
    "title": "Start",
    "data": "start",
    "className": "index"
  });
  columns.push({
    "title": "Result",
    "data": "out",
    "className": "serif"
  });
  columns.push({
    "title": "Laps",
    "data": "num_laps",
    "orderSequence": ["desc", "asc"],
    "render": function(data, type, row, meta) {
      return '<a href="javascript:showLaps(' + row.driver.id + ')">' +
        data + "</a>";
    }
  });
  columns.push({"title": "Fastest Lap", "data": "fastest_lap"});
  columns.push({
    "title": "Fast Lap",
    "data": "fast_lap",
    "orderSequence": ["desc", "asc"],
    "className": "index"
  });
  columns.push({"title": "Average Lap", "data": "average_lap"});
  columns.push({
    "title": "Inc",
    "data": "incidents",
    "className": "index"
  });
  columns.push({
    "title": "Points",
    "data": "points",
    "orderSequence": ["desc", "asc"],
    "className": "index"
  });

  return columns;
}

function lapColumns() {
  return [
    {"title": "Lap", "data": "lap", "className": "index"},
    {"title": "Time", "data": "time"},
    {
      "title": "Incidents",
      "data": "flags",
      "className": "serif",
      "render": function(data, type, row, meta) {
        if (data != null) {
          return data.join(", ");
        }
        return "";
      }
    }
  ]
}

function makeLapsChart(race) {
  var datasets = [];
  var bgColor = currentBackgroundColor();

  for (var i = 0; i < race.results.length; i++) {
    if (race.results[i].laps.length > 1) {
      var lapData = []
      for (var l = 1; l < race.results[i].laps.length; l++) {
        lapData = lapData.concat({
          "x": race.results[i].laps[l].lap,
          "y": race.results[i].laps[l].time
        });
      }
      datasets = datasets.concat({
        "label": race.results[i].driver.name,
        "order": race.results[i].finish,
        "hidden": true,
        "fill": false,
        "lineTension": 0.1,
        "borderColor": contrastingColor(bgColor),
        "data": lapData
      });
    }
  }

  var labels = [];
  for (var i = 0; i < race.laps; i++) {
    labels = labels.concat(i + 1);
  }

  var raceChart = new Chart($('#lapTimesChart'), {
    "type": "line",
    "data": {
      "labels": labels,
      "datasets": datasets
    },
    "options": {
      "scales": {
        "yAxes": [{
          "scaleLabel": {
            "display": true,
            "labelString": "Lap Time",
            "fontFamily": "Roboto"
          },
          "type": "time",
          "distribution": "series",
          "time": {
            "parser": "mm:ss.SSSS",
            "unit": "millisecond",
            "displayFormats": {"millisecond": "mm:ss.SSSS"}
          },
          "ticks": {
            "stepSize": 100000,
            "beginAtZero": false,
            "fontFamily": "Roboto"
          }
        }],
        "xAxes": [{
          "scaleLabel": {
            "display": true,
            "labelString": "Lap",
            "fontFamily": "Roboto"
          },
          "bounds": "data",
          "ticks": {
            "min": 1,
            "beginAtZero": false,
            "fontFamily": "Roboto"
          }
        }]
      },
      "legend": {"fontFamily": "Roboto"}
    }
  });
}

function raceDetails(race) {
  var h2 = document.createElement("h2");

  var p = document.createElement("p");
  p.classList.add("small");

  var dateSpan = document.createElement("span");
  dateSpan.id = "date";
  dateSpan.innerHTML = race.date;

  var infoSpan = document.createElement("span");
  infoSpan.id = "info";
  infoSpan.innerHTML = "Sim: " + race.sim_time + " | Weather " + race.temp;

  p.appendChild(dateSpan);
  p.appendChild(document.createElement("br"));
  p.appendChild(infoSpan);

  h2.appendChild(p);

  return h2;
}

function lapToggleDiv() {
  var div = newDiv("toggleLaps", "center", "large");
  div.hidden = true;
  var a = document.createElement("a");
  a.classList.add("gray");
  a.href = "javascript:toggleLaps()";
  a.innerHTML = 'Lap Times Chart (click to <span id="toggleLapsState">show</span>)';
  div.appendChild(a);
  return div;
}

function lapTimesDiv() {
  var div = newDiv("lapTimeChart", "chartContainer");
  div.hidden = true;
  var canv = document.createElement("canvas");
  canv.id = "lapTimesChart";
  canv.width = "400";
  canv.height = "400";
  div.appendChild(canv);
  return div;
}

function viewRace(league, season, race) {
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

  doInit();
  pushState({"league": league, "season": season, "race": race});

  $.ajax({
    "url": "/" + league + "/" + season + "/" + race + ".json",
    "success": function(json) {

      var trackName = (json.race.config == "N/A") ?
        json.race.track :
        json.race.track + " ("  + json.race.config + ")";

      setTitles(
        leagueLink(json.league) + " " + seasonLink(json.league, json.season),
        trackName,
        json.league.name + " - " + json.season.name + " - " + trackName
      );

      var content = $("#content")[0];
      content.appendChild(raceDetails(json.race));
      content.appendChild(table("results", "display", "compact"));
      content.appendChild(newDiv("laps"));
      content.appendChild(lapToggleDiv());
      content.appendChild(lapTimesDiv());

      var multiclass = json.race.classes != null && json.race.classes.length > 1;

      var t = $("#results").DataTable({
        "data": json.race.results,
        "columns": getColumns(multiclass),
        "order": [[multiclass ? 4 : 3, "asc"]],
        "lengthMenu": [[25, -1], [25, "All"]]
      });

      t.on("order.dt search.dt", function() {
        t.column(
          0,
          {search: "applied", order: "applied"}
        ).nodes().each(function(cell, i) {
          cell.innerHTML = i + 1;
        });
      }).draw();

      if (json.race.results != null) {
        var laps = $("#laps");
        laps.empty();

        // add all laps divs
        for (var i = 0; i < json.race.results.length; i++) {
          laps.append(driverLapsDiv(json.race.results[i].driver))
        }

        // init all lap div datatables
        var lapCols = lapColumns();
        for (var i = 0; i < json.race.results.length; i++) {
         var driver = json.race.results[i];
          $("#" + driver.driver.id + "-laps").DataTable({
            "data": driver.laps,
            "columns": lapCols,
            "lengthMenu": [[20, -1], [20, "All"]]
          });
        }

        makeLapsChart(json.race);
        $("#toggleLaps")[0].hidden = false;
      }
    },
    "error": function() {
      console.log("Something horrible happened");
      window.location = "/";
    },
    "dataType": "json"
  });
}
