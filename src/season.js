function standingsColumns() {
  return [
    {
      "title": "",
      "data": null,
      "searchable": false,
      "orderable": false,
      "className": "index right-border bold"
    },
    {
      "title": "Name",
      "data": "driver",
      "className": "serif left",
      "render": function(data, type, row, meta) {
        return '<a href="' + driverLink(row.driver_id) + '">' + data + "</a>";
      }
    },
    {"title": "Position", "data": "position", "className": "index"},
    {"title": "Points", "data": "points", "orderSequence": ["desc", "asc"]},
    {
      "title": "Races",
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
      "title": "Podiums",
      "data": "podiums",
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
    {"title": "Avg Start", "data": "avg_start", "className": "index"},
    {"title": "Avg Finish", "data": "avg_finish", "className": "index"},
    {"title": "Laps", "data": "laps", "orderSequence": ["desc", "asc"]},
    {"title": "Inc", "data": "incidents"},
    {"title": "CPI", "data": "cpi", "orderSequence": ["desc", "asc"]}
  ];
}

function racesColumns(league, season) {
  return [
    {
      "title": "Track",
      "data": "track",
      "className": "serif",
      "render": function(data, type, row, meta) {
        var track = row.track;
        if (row.config != "N/A") {
          track += " ("  + row.config + ")";
        }
        return '<a href="' + raceLink(league, season, row.id) + '">' +
          track + "</a>";
      }
    },
    {
      "title": "Winner",
      "data": "winner.name",
      "className": "serif",
      "render": function(data, type, row, meta) {
        return '<a href="' + driverLink(row.winner.id) + '">' + data + "</a>";
      }
    },
    {"title": "Drivers", "data": "drivers"},
    {"title": "Date", "data": "date", "className": "serif"}
  ]
}

function viewSeason(league, season) {
  if (isNaN(league)) {
    viewIndex();
    return;
  }

  if (isNaN(season)) {
    viewSeasons(league);
    return;
  }

  doInit();
  pushState({"league": league, "season": season});

  $.ajax({
    "url": "/" + league + "/" + season + ".json",
    "success": function(json) {

      setTitles(
        leagueLink(json.league),
        seasonLink(json.league, json.season),
        json.league.name + " - " + json.season.name
      );

      var content = $("#content")[0];

      content.appendChild(h2LeftLink(
        leagueSlug(league),
        "&#x2B11; All Seasons"
      ));

      var races = newDiv("races-container");
      races.appendChild(titleDiv("Races"));
      races.appendChild(contain(table("races", "display", "compact")));

      content.appendChild(races);

      var standings = newDiv("standings-container");
      standings.appendChild(titleDiv("Standings"));
      standings.appendChild(table("standings", "display", "compact"));

      content.appendChild(standings);

      $("#races").DataTable({
        "data": json.races,
        "searching": false,
        "ordering": false,
        "paging": false,
        "info": false,
        "columns": racesColumns(league, season)
      });

      var t = $("#standings").DataTable({
        "data": json.standings,
        "order": [[2, "asc"]],
        "lengthMenu": [[25, -1], [25, "All"]],
        "columns": standingsColumns()
      });

      t.on("order.dt search.dt", function() {
        t.column(
          0,
          {search: "applied", order: "applied"}
        ).nodes().each(function(cell, i) {
          cell.innerHTML = i + 1;
        });
      }).draw();

    },
    "error": function() {
      console.log("Something horrible happened");
      window.location = "/";
    },
    "dataType": "json"
  });
}
