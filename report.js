var data_loaded = 0;
var data_to_load = 0;
var tables = [];
var reportsUrl = ".";
var files = [];
var runs = [];
var selected_run = 0;



google.charts.load("current", {packages:["corechart"]});


function drawChart(data) {
    // Latency, time to first byte
    var options = {
        title: 'Time to first byte in seconds',
        legend: { position: 'none' },
    };

    var latency = new google.visualization.Histogram(document.getElementById('latency_div'));
    var latency_view = new google.visualization.DataView(data);
    latency_view.setColumns([5,9]);
    latency.draw(latency_view, options);

    // Speed
    var options = {
        title: 'Download speed (B/s)',
        legend: { position: 'none' },
    };

    var speed = new google.visualization.Histogram(document.getElementById('speed_div'));
    var speed_view = new google.visualization.DataView(data);
    speed_view.setColumns([8,9]);
    speed.draw(speed_view, options);

    // Size
    var options = {
        title: 'Size (B)',
        legend: { position: 'none' },
    };

    var size = new google.visualization.Histogram(document.getElementById('size_div'));
    var size_view = new google.visualization.DataView(data);
    size_view.setColumns([7,9]);
    size.draw(size_view, options);
}



function loadDataList() {
    return $.ajax({
        url: reportsUrl,
           dataType: 'xml',
           success: function(data) {
               $(data).find( "Key" ).each(
                   function () {
                       name = $(this).text();
                       if ( name.match('\.csv$') ) {
                           files.push(name)
                       }
                   });
               files.sort();
               last_end = 0;
               runcounter = -1;
               for (var i=0; i<files.length; i++) {
                   tags = files[i].split("-");
                   start = tags[0];
                   end   = tags[1];
                   var d = moment.unix(start)
                   d = d.format('YYYY-MM-DD HH:mm:ss')

                   if ( start <= last_end ) {
                       // This datafile started before the previous run ended.
                       // We assume it is part of the same run.
                       this_run = runs[runcounter];
                       if ( end > last_end ) {
                           last_end = end;
                       }
                       if ( end > this_run.end ){
                           this_run.end = end;
                       }
                       if ( end < this_run.firstend ){
                           this_run.firstend = end;
                       }
                       if ( start > this_run.laststart ){
                           this_run.laststart = start;
                       }
                       this_run.files.push(files[i]);
                   } else {
                       // This is a new run.
                       var this_run = {
                           tag:d,
                           start:start,
                           end:end,
                           laststart:start,
                           firstend:end,
                           files:[files[i]]
                       };
                       runcounter += 1;
                       runs[runcounter] = this_run;
                       last_end = end;
                   }
               }

               var $select = $("#selectRun");
               for (var i=0; i<runs.length; i++) {
                   var menuItemNo = $select.find("li").length;
                   $select.append('<li role="presentation"><a href="#">' + runs[i].tag + '</a></li>');
                   /* var el = document.createElement("option");
                   el.textContent = runs[i].tag;
                   el.value = i;
                   select.appendChild(el); */
               }

               $('#selectRun').change(function() {
                   // Load the data for this run.
                   this_run = runs[$(this).val()];
                   selected_run = $(this).val();
                   data_to_load = this_run.files.length;
                   tables = [];
                   for (var i=0; i<this_run.files.length; i++) {
                       $.get(this_run.files[i], function(csvString) {
                           var arrayData = $.csv.toArrays(csvString, {onParseValue: $.csv.hooks.castToScalar});
                           var data = new google.visualization.arrayToDataTable(arrayData);
                           tables.push(data);
                           data_loaded += 1;
                       }, dataType='text');
                   }

                   processData();
               });
           },
           error: function(data) {
               console.log('Error loading XML data');
           }
    });
}


function processData() {
    if ( data_loaded < data_to_load ) {
        setTimeout(processData, 100);
        return;
    }
  
    var data;
    for (var i=0; i<tables.length; i++) {
        if ( i == 0 ) {
            data = tables[i];
        } else {
            var json1 = JSON.parse(data.toJSON());
            var json2 = JSON.parse(tables[i].toJSON());
            var mergedRows = json1.rows.concat(json2.rows);
            json1.rows = mergedRows;
            data = new google.visualization.DataTable(json1);
        }
    }

    $('#teststart').text(runs[selected_run].tag);
    $('#results').show();

    d = moment.unix(runs[selected_run].laststart)
    $('#laststart').text(d.format('YYYY-MM-DD HH:mm:ss'));

    d = moment.unix(runs[selected_run].firstend)
    $('#firstend').text(d.format('YYYY-MM-DD HH:mm:ss'));

    testtime = runs[selected_run].firstend - runs[selected_run].laststart;
    $('#testtime').text(testtime);

    alldata = 0;
    for (i=0; i < data.getNumberOfRows(); i++)
        alldata = alldata + data.getValue(i,7);
    $('#alldata').text((alldata/1024/1024).toFixed());

    speed = alldata / testtime;
    $('#speed').text((speed/1024/1024).toFixed());

    gbps = alldata / testtime;
    $('#gbps').text(((speed*8)/1024/1024/1024).toFixed(3));

    data_loaded = 0;
    drawChart(data);
}

$( document ).ready( loadDataList() );

