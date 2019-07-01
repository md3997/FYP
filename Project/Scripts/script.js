var shouldUpdate = 0;
var data = undefined;
var wdata = undefined;
var airport_names=undefined;
var renderAtOnce = 50;
var renderNewAtOnce = 20;
var currRow = undefined;
var st = undefined;
var lockScrolling = false;
var currStatus = 'All';
var nextTO = 120;
var timeOutId = undefined

var getServerTime = function() {
	date = new Date($.ajax({
		async:false,
		cache:false,
	}).getResponseHeader('Date'));
	
	return date;
};


var updateServerTime = function () {			
	strGMT = st.toGMTString();
	document.getElementById("topDiv").innerHTML =  strGMT.substring(0,strGMT.match(/20\d\d/).index + 4);
	document.getElementById("bottomDiv").innerHTML = strGMT.substring(strGMT.match(/20\d\d/).index + 4, strGMT.length - 3) + " UTC";
	
	if(shouldUpdate < 5) {
		shouldUpdate++;
	} else {
		st = getServerTime();
		shouldUpdate = 0;
	}
	
	st.setSeconds(st.getSeconds() + 1);
	
	setTimeout(function(){
		updateServerTime();
	}, 1000);
};

var createNode = function(obj) {
	var tempPDG = undefined;
	
	if(obj.PredictedDepartureGMT == "NA") {
		tempPDG = "<img src = 'Images/plane.png' class = 'plane'/>";
	} else {
		tempPDG = obj.PredictedDepartureGMT;
	}
	
	return $('<tr>').attr("id",obj.FlightIdentifier)
	.append($("<td>").append(obj.ScheduledDate).append($("</td>")))
	.append($("<td>").append(obj.OriginAirport).append($("</td>")))
	.append($("<td>").append(obj.DestinationAirport).append($("</td>")))
	.append($("<td>").append(obj.Airline+obj.FlightNumber).append($("</td>")))
	.append($("<td>").append(obj.TailNumber).append($("</td>")))
	.append($("<td>").append(obj.ScheduledTime).append($("</td>")))
	.append($("<td>").append(obj.ScheduledDepartureGMT).append($("</td>")).attr("title",obj.ScheduledDepartureLocal))
	.append($("<td>").append(obj.ScheduledArrivalGMT).append($("</td>")).attr("title",obj.ScheduledArrivalLocal))
	.append($("<td>").attr("class","predDep").append(tempPDG).append($("</td>")))
	.append($("<td>").attr("class","predArr").append(obj.PredictedArrivalGMT).append($("</td>")).attr("title",obj.PredictedArrivalLocal))
	.append($("<td>").attr("class","level"+obj.Level+" status").append(obj.Status).append($("</td>")));
}

var appendRow = function(posInData, nodeBeforeId) {
	if (nodeBeforeId == undefined){
		$("#table_content").append(createNode(data[posInData]));
	} else {
		$('#' + nodeBeforeId).after(createNode(data[posInData]));
	}
	
	if(data[posInData].Status == "Not Yet Departed") {
		$("#"+ data[posInData].FlightIdentifier + " > .predDep").attr("title",data[posInData].PredictedDepartureLocal);
	} else {
		$("#"+ data[posInData].FlightIdentifier + " > .status").attr("title",data[posInData].ActualDepartureLocal);
	}
	if(data[posInData].Wrong == 1) {
		$("#"+ data[posInData].FlightIdentifier + " > .predDep").attr("style","color:red");
		$("#"+ data[posInData].FlightIdentifier + " > .predArr").attr("style","color:red");
	}
}

var scrollFurther = function() {
	if(lockScrolling == false) {
		if($(window).scrollTop() + window.innerHeight + 100 >= document.body.scrollHeight) {
			for(i = currRow; i < currRow + renderNewAtOnce; i++) {
				if (i < data.length) {
					appendRow(i)
				}
			}
			
			currRow = currRow + renderNewAtOnce;
			
			if(currRow > data.length) {
				currRow = data.length;
			}
		}
	}
}

var removeNode = function(id) {
	var retVal = 0;
	
	if (document.getElementById(id) != null) {
		$("#" + id).remove();
		retVal = 1;
	}
	
	data.splice(data.findIndex(function(obj){
		return obj.FlightIdentifier === id;
	}), 1);
	
	return retVal;
}

var changeNode = function(obj) {
	
	var fi = obj.FlightIdentifier;
	
	var index = data.findIndex(x => x.FlightIdentifier == fi);
	
	if (document.getElementById(fi) != null) {
		node = document.getElementById(fi);
		predDepNode = node.getElementsByClassName('predDep')[0];
		statusNode = node.getElementsByClassName('status')[0];
		if(obj.PredictedDepartureGMT == 'NA') {
			predDepNode.innerHTML = "<img src = 'Images/plane.png' class = 'plane'/>";
			predDepNode.removeAttribute("title");
			statusNode.title = obj.ActualDepartureLocal;
		} else {
			predDepNode.innerHTML = obj.PredictedDepartureGMT;
			predDepNode.title = obj.PredictedDepartureLocal;
		}
		
		predArrNode = node.getElementsByClassName('predArr')[0];
		predArrNode.innerHTML = obj.PredictedArrivalGMT;
		predArrNode.title = obj.PredictedArrivalLocal;
		
		statusNode.innerHTML = obj.Status;
		statusNode.classList.remove('level' + data[index].Level);
		statusNode.classList.add('level' + obj.Level);
		
		if(obj.Wrong == 1) {
			$("#"+ obj.FlightIdentifier + " > .predDep").attr("style","color:red");
			$("#"+ obj.FlightIdentifier + " > .predArr").attr("style","color:red");
		} else {
			$("#"+ obj.FlightIdentifier + " > .predDep").attr("style","");
			$("#"+ obj.FlightIdentifier + " > .predArr").attr("style","");
		}
	}
	
	data[index].LastUpdateEpoch = obj.LastUpdateEpoch;
	data[index].PredictedDepartureGMT = obj.PredictedDepartureGMT;
	data[index].PredictedDepartureLocal = obj.PredictedDepartureLocal;
	data[index].PredictedArrivalGMT = obj.PredictedArrivalGMT;
	data[index].PredictedArrivalLocal = obj.PredictedArrivalLocal;
	data[index].ActualDepartureGMT = obj.ActualDepartureGMT;
	data[index].ActualDepartureLocal = obj.ActualDepartureLocal;
	data[index].Level = obj.Level;
	data[index].Status = obj.Status;
	data[index].Weather = obj.Weather;
	data[index].PrevFlight = obj.PrevFlight;
	data[index].Wrong = obj.Wrong;
	data[index].DepartureDelay = obj.DepartureDelay;
	data[index].ArrivalDelay = obj.ArrivalDelay;
}

var addNode = function(obj) {
	for(var i = 0; i < data.length; i++) {
		if ( obj["SchDepEpoch"] < data[i]["SchDepEpoch"])
			break;
	}
	
	data.splice(i, 0, obj);
	
	if(i != 0) {
		var prevNodeId = data[i-1]["FlightIdentifier"];	
		
		if (document.getElementById(prevNodeId) != null) {
			appendRow(i, prevNodeId);
			currRow = currRow + 1;
		}
	} else {
		$("#table_content").prepend(createNode(data[i]));
		currRow = currRow + 1;		
	}
}

var updateFlights = function() {
	lockScrolling = true;
	var sendData = {};
	
	data.forEach(function(flight) {
		sendData[flight.FlightIdentifier] = flight.LastUpdateEpoch;
	});
	
	var sendString = JSON.stringify(sendData);
	
	$.post('API/update.php', {'timeStamps':sendString, 'status': currStatus}, function(receivedData) {
		totalRemovedFromDOM = 0;
		
		receivedData.flightsDeleted.forEach(function(currentValue) {
			totalRemovedFromDOM = totalRemovedFromDOM + removeNode(currentValue);
		});
		
		currRow = currRow - totalRemovedFromDOM;
		
		if(currRow < renderAtOnce) {
			var render = data.length < renderAtOnce ? data.length : renderAtOnce;
		
			for (var i = currRow; i < render; i++) {
				appendRow(i);
			}
		
			currRow = render;
		}
		
		receivedData.flightsChanged.forEach(function(currentObj) {
			changeNode(currentObj);
		});
		
		receivedData.flightsAdded.forEach(function(currentObj) {
			addNode(currentObj);
		});
	});
	
	ut = getServerTime();
	nextTO = 120 - ut.getSeconds();
	strUtGMT = ut.toGMTString();
	
	document.getElementById("topDivUpdate").innerHTML =  "Last Updated";
	document.getElementById("bottomDivUpdate").innerHTML = "At: " + strUtGMT.substring(strUtGMT.match(/20\d\d/).index + 4, strUtGMT.length - 7);
	
	lockScrolling = false;
	
	timeOutId = setTimeout(function() {
		updateFlights();
	}, nextTO * 1000);
}

var fetchData = function(status) {
	document.body.scrollTop = document.documentElement.scrollTop = 0;
	
	if(timeOutId != undefined)
		clearTimeout(timeOutId);
	
	$.getJSON('API/server.php', {'status':status},function(receivedData) {
		currStatus = status;
		data = receivedData;
		document.getElementById("table_content").innerHTML = "";
		var render = data.length < renderAtOnce ? data.length : renderAtOnce;
		
		for (var i = 0; i <render ; i++) {
			appendRow(i);
		}
		
		currRow = render;
		
		updateFlights();
	});
}

var changeState = function(state) {
	var sch_img_node = document.getElementById("scheduled_image");
	var dep_img_node = document.getElementById("departed_image");
	var par_node = document.getElementById("partition");
	var sch_sub_node = document.getElementById("scheduled_sub");
	var dep_sub_node = document.getElementById("departed_sub");
	
	if (state == "All") {
		sch_img_node.src = "Images/bright.png";
		dep_img_node.src = "Images/bright.png";
		par_node.style.backgroundColor = "rgb(255,255,255)";
		sch_sub_node.style.color = "rgb(255,255,255)";
		dep_sub_node.style.color = "rgb(255,255,255)";
	} else if (state == "Scheduled") {
		sch_img_node.src = "Images/bright.png";
		dep_img_node.src = "Images/dark.png";
		par_node.style.backgroundColor = "rgb(200,200,200)";
		sch_sub_node.style.color = "rgb(255,255,255)";
		dep_sub_node.style.color = "rgb(200,200,200)";
	} else if (state == "InAir"){
		sch_img_node.src = "Images/dark.png";
		dep_img_node.src = "Images/bright.png";
		par_node.style.backgroundColor = "rgb(200,200,200)";
		sch_sub_node.style.color = "rgb(200,200,200)";
		dep_sub_node.style.color = "rgb(255,255,255)";
	}
}

var fetchJSONData = function() {
	
	wdata = (function () {
	    var json = null;
	    $.ajax({
	        'async': false,
	        'global': false,
	        'url': 'JSON/Weather_modal.json',
	        'dataType': "json",
	        'success': function (data) {
	            json = data;
	        }
	    });
	    return json;
	})(); 

	airport_names = (function () {
	    var json = null;
	    $.ajax({
	        'async': false,
	        'global': false,
	        'url': 'JSON/Airport.json',
	        'dataType': "json",
	        'success': function (data) {
	            json = data;
	        }
	    });
	    return json;
	})();
}

var displayData = function(obj) {
	//Displaying the modal
	var modal = document.getElementById("simpleModal");
	modal.style.display="block";

	//Closing the modal on close button
	var closeBtn = document.getElementsByClassName("closeBtn")[0];
	closeBtn.addEventListener("click", closeModal);
	function closeModal(){
		modal.style.display="none";
	}

	//Closing the modal on clicking outside the window
	window.addEventListener("click", clickOutside);
	function clickOutside(e){
	if(e.target == modal){
		modal.style.display="none";
		}
	}

	//Adding Weather content
	var w_epoch = obj['Weather']['Epoch'];
	var og = obj['OriginAirport'];

	if(w_epoch != -1) {
		document.getElementById("icon").innerHTML = "<img src='Images/Weather_icons/"+wdata[og][w_epoch]['wx_icon']+".svg'>";
		document.getElementById("og_apt").innerHTML = airport_names[og];
		document.getElementById("phrase").innerHTML = wdata[og][w_epoch]['wx_phrase'];
		document.getElementById("t_val").innerHTML = wdata[og][w_epoch]['temp']+"<span>&deg;</span>F";
		document.getElementById("h_val").innerHTML = wdata[og][w_epoch]['rh']+"&percnt;";
		document.getElementById("p_val").innerHTML = wdata[og][w_epoch]['pressure']+"in";
		document.getElementById("v_val").innerHTML = wdata[og][w_epoch]['vis'];
		document.getElementById("d_val").innerHTML = wdata[og][w_epoch]['dewPt']+"<span>&deg;</span>F";
		document.getElementById("w_val").innerHTML = wdata[og][w_epoch]['wspd']+"mph";
	} else {
		document.getElementById("icon").innerHTML = "<img src='Images/Weather_icons/0.svg'>";
		document.getElementById("og_apt").innerHTML = airport_names[og];
		document.getElementById("phrase").innerHTML = "Data Not Available";
		document.getElementById("t_val").innerHTML = "--";
		document.getElementById("h_val").innerHTML = "--";
		document.getElementById("p_val").innerHTML = "--";
		document.getElementById("v_val").innerHTML = "--";
		document.getElementById("d_val").innerHTML = "--";
		document.getElementById("w_val").innerHTML = "--";
	}

	//Adding Flight content
	document.getElementById("from").innerHTML = airport_names[og];
	document.getElementById("to").innerHTML = airport_names[obj['DestinationAirport']];
	document.getElementById("flight-no").innerHTML = "WN"+obj['FlightNumber'];
	document.getElementById("tail-no").innerHTML = obj['TailNumber'];
	document.getElementById("dist").innerHTML = obj['Distance'] + " mi";
	document.getElementById("sch-time").innerHTML = obj['ScheduledTime'].replace('<br>', ' & ');
	document.getElementById("sch-date").innerHTML = obj['ScheduledDate'];
	document.getElementById("sch-dep").innerHTML = obj['ScheduledDepartureGMT'];
	document.getElementById("sch-arr").innerHTML = obj['ScheduledArrivalGMT'];
	
	if (obj['PrevFlight']['Interval'] == -999) {
		document.getElementById("sch-int").innerHTML = "Info Not Available";
		document.getElementById("prev-arr-delay").innerHTML = "Info Not Available";
	} else {
		document.getElementById("sch-int").innerHTML = obj['PrevFlight']['Interval'] + " mins";
		document.getElementById("prev-arr-delay").innerHTML = obj['PrevFlight']['Delay'] + " mins";
	}
	
	var compDelay = obj['PrevFlight']['Delay'] - obj['PrevFlight']['Interval'];
	compDelay = compDelay >= 0 ? compDelay : 0;
	
	if (obj['Status'] != 'Not Yet Departed') {
		document.getElementById("comp-delay").innerHTML = "NA";
	} else if (obj['PrevFlight']['Delay'] == -999) {
		document.getElementById("comp-delay").innerHTML = "Info Not Available";
	} else {
		document.getElementById("comp-delay").innerHTML = compDelay + " mins";
	}
	
	var wDelay = obj['Weather']['Delay'];
	
	if (obj['Weather']['Epoch'] == -1) {		
		document.getElementById("w-delay").innerHTML = "Info Not available";
	} else if (wDelay == -1) {
		document.getElementById("w-delay").innerHTML = "NA";
	} else{
		document.getElementById("w-delay").innerHTML = wDelay + " mins";
	}
	
	tDelay = obj['DepartureDelay'];
	gDelay = tDelay - compDelay - wDelay;
	
	if (obj['Status'] == 'Not Yet Departed') {
		document.getElementById("gen-delay").innerHTML = gDelay + " mins";
		document.getElementById("t-d-delay").innerHTML = tDelay + " mins";
	} else {
		document.getElementById("gen-delay").innerHTML = "NA";
		document.getElementById("t-d-delay").innerHTML = "NA";
	}
	
	if (obj['Status'] != 'Not Yet Departed') {
		document.getElementById("act-dep-delay").innerHTML = obj['DepartureDelay'] + " mins";
		document.getElementById("t-a-delay").innerHTML = obj['ArrivalDelay'] + " mins";
	} else {
		document.getElementById("act-dep-delay").innerHTML = "NA";
		document.getElementById("t-a-delay").innerHTML = obj['ArrivalDelay'] + " mins";
	}
}

var checkNode = function(node) {
	while(true) {
		if(node.tagName == 'HTML' || node.tagName == 'TH') {
			break;
		}
		if (node.tagName == 'TR') {
			if (node.hasAttribute('id')) {
				obj = data.find((x) => x.FlightIdentifier == node.id)
				displayData(obj);
			}
			break;
		}
		node = node.parentElement;
	};
}
