$(document).ready(function() {
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
      var raceChart = new Chart($('#lapTimesChart'), {
        "type": "line",
        "data": {
          "labels": [
            {%- for lapNum in range(1, race.race["eventlapscomplete"] + 1) -%}
            {{ lapNum }}
            {%- if loop.index != loop.length %},{% endif -%}
            {%- endfor -%}
          ],
          "datasets": [
            {%- for laps in race.laps -%}
            {%- if laps.laps|length > 1 %}
            {"label":"{{ laps.driver }}","order":{{ race.summary(laps.driver_id)["finish"] }},"hidden":true,"fill":false,"lineTension":0.1,"borderColor":"{{ random_color() }}","data":[
              {%- for lap in laps.laps %}
              {%- if lap.lap != 0 and lap.time.total_seconds() > 0 %}{x:{{ lap.lap }},y:"{{ time_string(lap.time) }}"}
              {%- if loop.index != loop.length %},{% endif %}
              {%- endif %}
              {%- endfor -%}
            ]}{% if loop.index != loop.length %},{% endif %}
            {%- endif %}
            {%- endfor -%}
          ]
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
    });
