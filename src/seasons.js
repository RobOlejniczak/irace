function viewSeasons(league) {
  if (isNaN(league)) {
    viewIndex();
    return;
  }
  pushState({"league": league}, "iRace - Seasons");
}

function loadSeasons(league) {
  $.ajax({
    "url": "/" + league + ".json",
    "success": function(json) {

      setTitles(
        json.league.name,
        "",
        json.league.name + " - Seasons",
        {"league": json.league.id}
      );

      var content = $("#content")[0];
      content.appendChild(h2LeftLink(
        indexSlug(),
        "&#x2B11; All Leagues"
      ));
      content.appendChild(contain(table("seasons", "display")));

      $("#seasons").DataTable({
        "data": json.seasons,
        "searching": false,
        "ordering": false,
        "paging": false,
        "info": false,
        "columns": [
          {
            "title": "Seasons",
            "data": "name",
            "className": "serif large",
            "render": function(data, type, row, meta) {
              return seasonLink(json.league, row);
            }
          }
        ]
      });

    },
    "error": function() {
      console.log("Something horrible happened");
      window.location = "/";
    },
    "dataType": "json"
  });
}
