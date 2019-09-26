// Set new default font family and font color to mimic Bootstrap's default styling
Chart.defaults.global.defaultFontFamily = 'Nunito', '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
Chart.defaults.global.defaultFontColor = '#858796';

// Pie Chart Example
var ctx = document.getElementById("myPieChart");
var myPieChart = new Chart(ctx, {
  type: 'doughnut',
  data: {
    labels: ["Inloggen", "Lezen", "Beoordelingen",  '--'],
    datasets: [{
      data: [10, 30, 15, 5, 5, 35],
      backgroundColor: ['#e74a3b', '#f6c23e', '#4e73df',  '#1cc88a'],
      hoverBackgroundColor: ['#d52a1a', '#f4b30d', '#2653d4',  '#169b6b'],
      hoverBorderColor: "rgba(234, 236, 244, 1)",
    }],
  },
  options: {
    maintainAspectRatio: false,
    tooltips: {
      backgroundColor: "rgb(255,255,255)",
      bodyFontColor: "#858796",
      borderColor: '#dddfeb',
      borderWidth: 1,
      xPadding: 10,
      yPadding: 10,
	displayColors: false,
	caretPadding: 10,
    },
    legend: {
      display: false
    },
    cutoutPercentage: 40,
  },
});
