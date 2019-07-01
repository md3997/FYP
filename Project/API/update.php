<?php
	header('Content-Type: application/json');
	include 'Includes/dbc.inc.php';
	include 'Includes/functions.inc.php';
	
	$timeStamps = json_decode($_POST['timeStamps'], $assoc = true);
	
	$sqlst = "";
	
	if ($_POST['status'] == 'All')
		$sqlst = "SELECT FlightIdentifier, LastUpdateEpoch FROM flightInfo;";
	else if ($_POST['status'] == 'Scheduled')
		$sqlst = "SELECT FlightIdentifier, LastUpdateEpoch FROM flightInfo WHERE HasDeparted = 'N';";
	else if ($_POST['status'] == 'InAir')
		$sqlst = "SELECT FlightIdentifier, LastUpdateEpoch FROM flightInfo WHERE HasDeparted = 'Y';";
	
	$result = $conn->query($sqlst);
	
	$changed = array();
	$unchanged = array();
	$deleted = array();
	$added = array();
	
	if ($result->num_rows > 0) {
		while($row = $result->fetch_assoc()) {
			if(array_key_exists($row["FlightIdentifier"],$timeStamps) == true) {
				if($row["LastUpdateEpoch"] != $timeStamps[$row["FlightIdentifier"]]) {
					array_push($changed,$row["FlightIdentifier"]);
				} else {
					array_push($unchanged,$row["FlightIdentifier"]);
				}
			} else {
				array_push($added,$row["FlightIdentifier"]);
			}
		}
	}
	
	$deleted = array_values(array_diff(array_keys($timeStamps), $changed, $unchanged));
	
	$jsonData = array();
	
	$jsonData["flightsDeleted"] = $deleted;
	
	$tarray=[];
	
	$sqlst = "SELECT * FROM (SELECT * FROM ((SELECT flightinfo.FlightIdentifier, flightinfo.LastUpdateEpoch, '' as ScheduledDate, flightinfo.SchDepEpoch as SchDepEpoch, flightinfo.SchArrEpoch, flightinfo.Airline, flightinfo.FlightNumber, flightinfo.TailNumber, flightinfo.OriginAirport, flightinfo.DestinationAirport, flightinfo.ScheduledDeparture, flightinfo.ScheduledArrival, flightinfo.ScheduledTime, flightinfo.Distance, scheduled.DepartureDelay, scheduled.ArrivalDelay, flightinfo.HasDeparted, scheduled.Wrong from flightinfo, scheduled where flightinfo.FlightIdentifier = scheduled.FlightIdentifier) UNION (SELECT flightinfo.FlightIdentifier, flightinfo.LastUpdateEpoch,'' as ScheduledDate, flightinfo.SchDepEpoch as SchDepEpoch, flightinfo.SchArrEpoch, flightinfo.Airline, flightinfo.FlightNumber, flightinfo.TailNumber, flightinfo.OriginAirport, flightinfo.DestinationAirport, flightinfo.ScheduledDeparture, flightinfo.ScheduledArrival, flightinfo.ScheduledTime, flightinfo.Distance, inair.DepartureDelay, inair.ArrivalDelay, flightinfo.HasDeparted, inair.Wrong from flightinfo, inair where flightinfo.FlightIdentifier = inair.FlightIdentifier)) as U WHERE FlightIdentifier IN (";
	
	foreach($changed as $fi) {
		$sqlst = $sqlst."'".$fi."', ";
	}
	
	$sqlst = $sqlst."'Junk')) t1 INNER JOIN WeatherInfo ON WeatherInfo.FlightIdentifier = t1.FlightIdentifier INNER JOIN PrevFlightInfo ON PrevFlightInfo.FlightIdentifier = t1.FlightIdentifier order by SchDepEpoch";
	
	$result = $conn->query($sqlst);	
	
	if ($result->num_rows > 0) {
		while($row = $result->fetch_assoc()){ 
			$row = getArray($row, true);
			$tarray[]=$row;
		}
	}
	
	$jsonData["flightsChanged"] = $tarray;
	
	$tarray=[];
	
	$sqlst = "SELECT * FROM (SELECT * FROM ((SELECT flightinfo.FlightIdentifier, flightinfo.LastUpdateEpoch, '' as ScheduledDate, flightinfo.SchDepEpoch as SchDepEpoch, flightinfo.SchArrEpoch, flightinfo.Airline, flightinfo.FlightNumber, flightinfo.TailNumber, flightinfo.OriginAirport, flightinfo.DestinationAirport, flightinfo.ScheduledDeparture, flightinfo.ScheduledArrival, flightinfo.ScheduledTime, flightinfo.Distance, scheduled.DepartureDelay, scheduled.ArrivalDelay, flightinfo.HasDeparted, scheduled.Wrong from flightinfo, scheduled where flightinfo.FlightIdentifier = scheduled.FlightIdentifier) UNION (SELECT flightinfo.FlightIdentifier, flightinfo.LastUpdateEpoch,'' as ScheduledDate, flightinfo.SchDepEpoch as SchDepEpoch, flightinfo.SchArrEpoch, flightinfo.Airline, flightinfo.FlightNumber, flightinfo.TailNumber, flightinfo.OriginAirport, flightinfo.DestinationAirport, flightinfo.ScheduledDeparture, flightinfo.ScheduledArrival, flightinfo.ScheduledTime, flightinfo.Distance, inair.DepartureDelay, inair.ArrivalDelay, flightinfo.HasDeparted, inair.Wrong from flightinfo, inair where flightinfo.FlightIdentifier = inair.FlightIdentifier)) as U WHERE FlightIdentifier IN (";
	
	foreach($added as $fi) {
		$sqlst = $sqlst."'".$fi."', ";
	}
	
	$sqlst = $sqlst."'Junk')) t1 INNER JOIN WeatherInfo ON WeatherInfo.FlightIdentifier = t1.FlightIdentifier INNER JOIN PrevFlightInfo ON PrevFlightInfo.FlightIdentifier = t1.FlightIdentifier order by SchDepEpoch";
	
	$result = $conn->query($sqlst);
	
	if ($result->num_rows > 0) {
		while($row = $result->fetch_assoc()){ 
			$row = getArray($row, false);
			$tarray[]=$row;
		}
	}
	
	$jsonData["flightsAdded"] = $tarray;
	
	echo json_encode($jsonData, JSON_NUMERIC_CHECK);
	
	$conn->close();
?>