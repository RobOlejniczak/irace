var t = $("#standings").DataTable({
       "order": [[ 1, "asc" ]],
       "lengthMenu": [[25, -1], [25, "All"]],
       "columnDefs": [{
          "searchable": false,
          "orderable": false,
          "targets": 0
        }]
     });
     t.on("order.dt search.dt", function() {
       t.column(
         0,
         {search: "applied", order: "applied"}
       ).nodes().each(function(cell, i) {
         cell.innerHTML = i + 1;
       });
     }).draw();
     function ajaxGetSet(url, ele) {
       $.ajax({
         url: url,
         success: function(response) {
           $(ele)[0].innerText = response;
         },
         error: function(XMLHttpRequest, textStatus, errorThrown) {
           $(ele)[0].innerText = textStatus;
         }
       })
     }
     function healthCheck() {
       ajaxGetSet("/health", "#health");
       $("#time")[0].innerText = new Date().toISOString().split('.')[0];
     }
     healthCheck();
     setInterval(healthCheck, 30000);
     function getStates() {
       $("#states").DataTable({
         "order": [[ 1, "asc" ]],
         "lengthMenu": [[25, -1], [25, "All"]],
         "ajax": {
           "url": "/state",
           "dataSrc": ""
         },
         "columns": [
           {"data": "l"},
           {"data": "t"}
         ],
         "destroy": true
       });
     }
     getStates();
     var socket = io.connect("/");
     socket.on("state", getStates);
     socket.on("sync", function(message) {
       $("#sync")[0].innerText = message;
     });
