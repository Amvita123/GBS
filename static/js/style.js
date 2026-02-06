$(document).ready(function(){
    $("#toggleBtn").click(function(){
        $(".side-navbar").toggleClass("side-width");
        $(".main-wrapper").toggleClass("main-width");
    });
    
    $(".profile-link").click(function(){
        $(".profile-nav").toggleClass("slide-in");
    });

    $("#optBtn").click(function(){
        $(".side-navbar").toggleClass("side-hide");
        $(".main-wrapper").toggleClass("main-width");
    });
    $(".closeBtn").click(function(){
        $(".side-navbar").toggleClass("side-hide");
        $(".main-wrapper").toggleClass("main-width");
    });
});      



/* canvas js start */

window.onload = function () {
	var chart = new CanvasJS.Chart("chartContainer", {	
	axisY:{
		tickColor: "#C24642",
		labelFontColor: "#000",
		includeZero: true
	},
	toolTip: {
		shared: true
	},
	legend: {
		cursor: "pointer",
		itemclick: toggleDataSeries
	},
	data: [{
		type: "line",
		color: "#369EAD",
		axisYIndex: 1,
		dataPoints: [
			{ x: new Date(2017, 00, 7), y: 85.4 }, 
			{ x: new Date(2017, 00, 14), y: 92.7 },
			{ x: new Date(2017, 00, 21), y: 64.9 },
			{ x: new Date(2017, 00, 28), y: 58.0 },
			{ x: new Date(2017, 01, 4), y: 63.4 },
			{ x: new Date(2017, 01, 11), y: 69.9 },
			{ x: new Date(2017, 01, 18), y: 88.9 },
			{ x: new Date(2017, 01, 25), y: 66.3 },
			{ x: new Date(2017, 02, 4), y: 82.7 },
			{ x: new Date(2017, 02, 11), y: 60.2 },
			{ x: new Date(2017, 02, 18), y: 87.3 },
			{ x: new Date(2017, 02, 25), y: 98.5 }
		]
	},
	{
		type: "line",
		color: "#C24642",
		axisYIndex: 0,
		dataPoints: [
			{ x: new Date(2017, 00, 7), y: 32.3 }, 
			{ x: new Date(2017, 00, 14), y: 33.9 },
			{ x: new Date(2017, 00, 21), y: 26.0 },
			{ x: new Date(2017, 00, 28), y: 15.8 },
			{ x: new Date(2017, 01, 4), y: 18.6 },
			{ x: new Date(2017, 01, 11), y: 34.6 },
			{ x: new Date(2017, 01, 18), y: 37.7 },
			{ x: new Date(2017, 01, 25), y: 24.7 },
			{ x: new Date(2017, 02, 4), y: 35.9 },
			{ x: new Date(2017, 02, 11), y: 12.8 },
			{ x: new Date(2017, 02, 18), y: 38.1 },
			{ x: new Date(2017, 02, 25), y: 42.4 }
		]
	}]
});
chart.render();

function toggleDataSeries(e) {
        if (typeof (e.dataSeries.visible) === "undefined" || e.dataSeries.visible) {
            e.dataSeries.visible = false;
        } else {
            e.dataSeries.visible = true;
        }
        e.chart.render();
    }
}

/* canvas js end */

/* Date picker start */

$( function() {
	$( "#datepicker, #datepicker2" ).datepicker({
		dateFormat: "dd-mm-yy"
		,	duration: "fast"
	});
} );

/* Date picker end */



// Password show/hide


function passwordEye() {
	var x = document.getElementById("password");
	if (x.type === "password") {
		x.type = "text";
	} else {
		x.type = "password";
	}
	
	var eyeicon = document.getElementById("eyeIcon");
	eyeicon.classList.toggle('fa-eye-slash');
	eyeicon.classList.toggle('fa-eye');
	
}
		
function oldpswEye() {
	var x = document.getElementById("oldPassword");
	if (x.type === "password") {
		x.type = "text";
	} else {
		x.type = "password";
	}
	
	var eyeicon = document.getElementById("eyeIcon1");
	eyeicon.classList.toggle('fa-eye-slash');
	eyeicon.classList.toggle('fa-eye');
	
}
function newpswEye() {
	var x = document.getElementById("newPassword");
	if (x.type === "password") {
		x.type = "text";
	} else {
		x.type = "password";
	}
	
	var eyeicon = document.getElementById("eyeIcon2");
	eyeicon.classList.toggle('fa-eye-slash');
	eyeicon.classList.toggle('fa-eye');
	
}
function confirmpswEye() {
	var x = document.getElementById("confirmPassword");
	if (x.type === "password") {
		x.type = "text";
	} else {
		x.type = "password";
	}
	
	var eyeicon = document.getElementById("eyeIcon3");
	eyeicon.classList.toggle('fa-eye-slash');
	eyeicon.classList.toggle('fa-eye');
	
}

