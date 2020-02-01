function seasonsColumns() {
  return [
    {
      "title": "",
      "data": null,
      "searchable": false,
      "orderable": false,
      "className": "index right-border bold"
    },
    {
      "title": "ID",
      "data": "season.id",
      "visible": false
    },
    {
      "title": "League",
      "data": "league.name",
      "className": "serif left",
      "render": function(data, type, row, meta) {
        return leagueLink(row.league);
      }
    },
    {
      "title": "Name",
      "data": "season.name",
      "className": "serif left",
      "render": function(data, type, row, meta) {
        return seasonLink(row.league, row.season);
      }
    },
    {"title": "Position", "data": "position", "className": "index"},
    {
      "title": "Points",
      "data": "points",
      "className": "index",
      "orderSequence": ["desc", "asc"]
    },
    {"title": "Avg Start", "data": "avg_start", "className": "index"},
    {"title": "Avg Finish", "data": "avg_finish", "className": "index"},
    {
      "title": "Drivers",
      "data": "drivers",
      "className": "index",
      "orderSequence": ["desc", "asc"]
    },
    {
      "title": "Races",
      "data": "races",
      "className": "index",
      "orderSequence": ["desc", "asc"]
    },
    {
      "title": "Raced",
      "data": "raced",
      "className": "index",
      "orderSequence": ["desc", "asc"]
    },
    {
      "title": "Wins",
      "data": "wins",
      "className": "index",
      "orderSequence": ["desc", "asc"]
    },
    {
      "title": "Top 5",
      "data": "top5",
      "className": "index",
      "orderSequence": ["desc", "asc"]
    },
    {
      "title": "Top 10",
      "data": "top10",
      "className": "index",
      "orderSequence": ["desc", "asc"]
    },
    {
      "title": "Laps",
      "data": "laps",
      "className": "index",
      "orderSequence": ["desc", "asc"]
    },
    {"title": "Inc", "data": "incidents", "className": "index"},
    {
      "title": "CPI",
      "data": "cpi",
      "className": "index",
      "orderSequence": ["desc", "asc"]
    }
  ];
}

function leagueName(seasons, league) {
  for (var i = 0; i < seasons.length; i++) {
    if (seasons[i].league.id == league) {
      return seasons[i].league.name;
    }
  }
  return "N/A";
}

function seasonName(seasons, season) {
  for (var i = 0; i < seasons.length; i++) {
    if (seasons[i].season.id == season) {
      return seasons[i].season.name;
    }
  }
  return "N/A";
}

function resultsColumns(multiclass, seasons) {
  columns = [
    {
      "title": "",
      "data": null,
      "searchable": false,
      "orderable": false,
      "className": "index right-border bold"
    },
    {
      "title": "League",
      "data": "league.id",
      "className": "serif left",
      "render": function(data, type, row, meta) {
        return leagueLink(row.league) + "<br>" + seasonLink(row.league, row.season);
      }
    },
    {"title": "Date", "data": "date", "className": "serif left"},
    {
      "title": "Track",
      "data": "track",
      "className": "serif left",
      "render": function(data, type, row, meta) {
        var track = data;
        if (row.config != "N/A") {
          track += " ("  + row.config + ")";
        }
        return linked(raceLink(row.league.id, row.season.id, row.id), track);
      }
    },
    {"title": "Car", "data": "car", "className": "serif"},
    {
      "title": "",
      "searchable": false,
      "visible": false,
      "data": "interval_raw",
      "render": function(data, type, row, meta) {
        if (data <= 0) {
          var i = parseInt(row.interval);
          if (isNaN(i)) {
            i = 0;
          }
          return Number.MAX_SAFE_INTEGER - 1000 - i;
        }
        return data;
      }
    }
  ];

  if (multiclass) {
    columns.push(
      {
        "title": "Car Class",
        "data": "class.name",
        "className": "serif"
      },
      {
        "title": "",
        "visible": false,
        "searchable": false,
        "data": "class.interval_raw",
        "render": function(data, type, row, meta) {
          if (data <= 0) {
            var i = parseInt(row.class.interval);
            if (isNaN(i)) {
              i = 0;
            }
            return Number.MAX_SAFE_INTEGER - 1000 - i;
          }
          return data;
        }
      }
    );
  }

  columns.push(
    {"title": "Finish", "data": "finish", "className": "index"},
    {"title": "Start", "data": "start", "className": "index"}
  );

  if (multiclass) {
    columns.push({"title": "Class Finish", "data": "class.finish"});
  }

  columns.push({
    "title": "Interval",
    "data": "interval",
    "orderData": 5
  });

  if (multiclass) {
    columns.push({
      "title": "Class Interval",
      "data": "class.interval",
      "orderData": 7
    });
  }

  columns.push(
    {
      "title": "Laps",
      "data": "laps",
      "className": "index",
      "orderSequence": ["desc", "asc"]
    },
    {"title": "Inc", "data": "incidents", "className": "index"},
    {"title": "Points", "data": "points", "orderSequence": ["desc", "asc"]},
    {"title": "Drivers", "data": "drivers", "orderSequence": ["desc", "asc"]},
    {"title": "SOF", "data": "sof", "orderSequence": ["desc", "asc"]}
  );

  if (multiclass) {
    columns.push({
      "title": "Class Drivers",
      "data": "class.drivers",
      "orderSequence": ["desc", "asc"]
    });
  }

  return columns;
}

function mergeLeagueSeasonInfo(json) {
  function _pull_info(key, _id) {
    for (var i = 0; i < json.seasons.length; i++) {
      if (json.seasons[i][key].id == _id) {
        return json.seasons[i][key];
      }
    }
    return {"id": _id, "name": "N/A"};
  }
  for (var i = 0; i < json.results.length; i++) {
    json.results[i].season = _pull_info("season", json.results[i].season);
    json.results[i].league = _pull_info("league", json.results[i].league);
  }
}

function viewDriver(driver) {
  if (isNaN(driver)) {
    viewIndex();
    return;
  }

  doInit();
  pushState({"driver": driver});

  $.ajax({
    "url": "/drivers/" + driver + ".json",
    "success": function(json) {

      setTitles(
        json.driver.name,
        "iRace Driver Overview",
        json.driver.name,
        "small"
      );

      mergeLeagueSeasonInfo(json);

      var content = $("#content")[0];

      var seasons = newDiv("seasons-container");
      seasons.appendChild(titleDiv("Seasons"));
      seasons.appendChild(table("seasons", "display", "compact", "small"));

      content.appendChild(seasons);

      var races = newDiv("races-container");
      races.appendChild(titleDiv("Races"));
      races.appendChild(table("races", "display", "compact", "small"));

      content.appendChild(races);

      var seasonsDT = $("#seasons").DataTable({
        "data": json.seasons,
        "columns": seasonsColumns()
      });

      seasonsDT.on("order.dt search.dt", function() {
        seasonsDT.column(
          0,
          {search: "applied", order: "applied"}
        ).nodes().each(function(cell, i) {
          cell.innerHTML = i + 1;
        });
      }).draw();

      if (json.results != null && json.results.length > 0) {
        var multiclass = false;
        for (var i = 0; i < json.results.length; i++) {
          if (json.results[i].class != null) {
            multiclass = true;
            break;
          }
        }
        if (multiclass) {
          for (var i = 0; i < json.results.length; i++) {
            if (json.results[i].class == null) {
              json.results[i].class = {
                "name": json.results[i].car,
                "drivers": json.results[i].drivers,
                "finish": json.results[i].finish,
                "laps": json.results[i].laps,
                "interval": json.results[i].interval,
                "interval_raw": json.results[i].interval_raw
              }
            }
          }
        }

        var racesDT = $("#races").DataTable({
          "data": json.results,
          "order": [[2, "desc"]],
          "lengthMenu": [[25, -1], [25, "All"]],
          "columns": resultsColumns(multiclass, json.seasons)
        });

        racesDT.on("order.dt search.dt", function() {
          racesDT.column(
            0,
            {search: "applied", order: "applied"}
          ).nodes().each(function(cell, i) {
            cell.innerHTML = i + 1;
          });
        }).draw();
      }

    },
    "error": function() {
      console.log("Something horrible happened");
      window.location = "/";
    },
    "dataType": "json"
  });
}
