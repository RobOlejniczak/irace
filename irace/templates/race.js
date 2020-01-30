    $.fn.dataTable.moment("HH:mm:ss.SSSS", "en", false);
    $.fn.dataTable.moment("mm:ss.SSSS", "en", false);
    var t = $("#results").DataTable({
      "order": [[ 3, "asc" ]],
      "lengthMenu": [[25, -1], [25, "All"]],
      "columnDefs": [
        {"searchable": false, "orderable": false, "targets": 0},
        {"orderData": {% if race.multiclass %}4{% else %}3{% endif %}, "targets": {% if race.multiclass %}3{% else %}2{% endif %}}
      ],
      "aoColumns": [
        null,
        null,
        {%- if race.multiclass -%}null,{%- endif -%}
        null,
        null,
        {%- if race.multiclass -%}null,{%- endif -%}
        null,
        {"orderSequence": ["desc", "asc"]},
        {"orderSequence": ["desc", "asc"]},
        {"orderSequence": ["desc", "asc"]},
        null,
        null,
        {"orderSequence": ["desc", "asc"]}
      ]
    });
    t.on("order.dt search.dt", function() {
      t.column(
        0,
        {search: "applied", order: "applied"}
      ).nodes().each(function(cell, i) {
        cell.innerHTML = i + 1;
      });
    }).draw();
    $(".lapdata").DataTable({
      "lengthMenu": [[20, -1], [20, "All"]]
    });
    });
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
