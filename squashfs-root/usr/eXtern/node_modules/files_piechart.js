function generate_new_piechart()
{

$('#pieChart').remove(); // this is my <canvas> element
  $('#chart_properties').append('<canvas id="pieChart"><canvas>');
  //canvas = document.querySelector('#results-graph');
      
      
      
      var pieChartCanvas = $("#pieChart").get(0).getContext("2d");
        var pieChart = new Chart(pieChartCanvas);
        pieChart.canvas.width = 100;
        var PieData = [
          {
            value: 700,
            color: "rgba(0,0,0,0.1)",
            highlight: "#f56954",
            label: "Chrome"
          },
          {
            value: 500,
            color: "rgba(0,0,0,0.1)",/*"#00a65a",*/
            highlight: "#00a65a",
            label: "IE"
          },
          {
            value: 400,
            color: "rgba(0,0,0,0.1)",
            highlight: "#f39c12",
            label: "FireFox"
          },
          {
            value: 600,
            color: "rgba(0,154,255,1)",
            highlight: "#00c0ef",
            label: "Safari"
          },
          {
            value: 300,
            color: "rgba(0,0,0,0.1)",
            highlight: "#3c8dbc",
              showTooltip: true,
            label: "Opera"
          },
          {
            value: 100,
            color: "rgba(0,0,0,0.1)",
            highlight: "#d2d6de",
            label: "Navigator"
          }
        ];
        var pieOptions = {
          //Boolean - Whether we should show a stroke on each segment
          segmentShowStroke: true,
          //String - The colour of each segment stroke
          segmentStrokeColor: "rgba(255,255,255,0.3)",
          //Number - The width of each segment stroke
          segmentStrokeWidth: 2,
          //Number - The percentage of the chart that we cut out of the middle
          percentageInnerCutout: 50, // This is 0 for Pie charts
          //Number - Amount of animation steps
          animationSteps: 100,
          //String - Animation easing effect
          animationEasing: "easeInOutCirc",
          //Boolean - Whether we animate the rotation of the Doughnut
          animateRotate: true,
          //Boolean - Whether we animate scaling the Doughnut from the centre
          animateScale: false,
          //Boolean - whether to make the chart responsive to window resizing
          responsive: true,
          // Boolean - whether to maintain the starting aspect ratio or not when responsive, if set to false, will take up entire container
          maintainAspectRatio: true,
          
          tooltipTemplate: "<%= value %>",
        
        onAnimationComplete: function()
        {
            //this.showTooltip(this.segments, true);
        },
          //String - A legend template
          legendTemplate: "<ul class=\"<%=name.toLowerCase()%>-legend\"><% for (var i=0; i<segments.length; i++){%><li><span style=\"background-color:<%=segments[i].fillColor%>\"></span><%if(segments[i].label){%><%=segments[i].label%><%}%></li><%}%></ul>"
        };
        //Create pie or douhnut chart
        // You can switch between pie and douhnut using the method below.
        pieChart.Doughnut(PieData, pieOptions);
}