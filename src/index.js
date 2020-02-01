function viewIndex() {
  doInit();
  pushState();

  $.ajax({
    "url": "/leagues.json",
    "success": function(json) {

      setTitles(
        '<a href="https://github.com/a-tal/irace">iRace</a> Tracked Leagues',
        "",
        "Leagues"
      );

      var content = $("#content")[0];
      content.appendChild(contain(table("leagues", "display", "large")));

      $("#leagues").DataTable({
        "data": json,
        "order": [[0, "asc"]],
        // "lengthMenu": [[25, -1], [25, "All"]],
        "info": false,
        "searching": false,
        "paging": false,
        "columns": [
          {
            "title": "ID",
            "data": "id",
            "visible": false,
          },
          {
            "title": "",
            "data": "name",
            "className": "serif large",
            "render": function(data, type, row, meta) {
              return leagueLink(row);
            }
          }
        ]
      });

    },
    "error": function() {
      console.log("something horrible happened");
    },
    "dataType": "json"
  });
}
