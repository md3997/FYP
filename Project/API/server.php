<?php
	header('Content-Type: application/json');
	include 'Includes/dbc.inc.php';
	include 'Includes/functions.inc.php';
	
	if($_GET['status'] == 'All')
		$sqlst = "SELECT * FROM ((SELECT flightinfo.FlightIdentifier, flightinfo.LastUpdateEpoch, '' as ScheduledDate, flightinfo.SchDepEpoch as SchDepEpoch, flightinfo.SchArrEpoch, flightinfo.Airline, flightinfo.FlightNumber, flightinfo.TailNumber, flightinfo.OriginAirport, flightinfo.DestinationAirport, flightinfo.ScheduledDeparture, flightinfo.ScheduledArrival, flightinfo.ScheduledTime, flightinfo.Distance, scheduled.DepartureDelay, scheduled.ArrivalDelay, flightinfo.HasDeparted, scheduled.Wrong FROM flightinfo, scheduled WHERE flightinfo.FlightIdentifier = scheduled.FlightIdentifier) UNION (SELECT flightinfo.FlightIdentifier, flightinfo.LastUpdateEpoch,'' as ScheduledDate, flightinfo.SchDepEpoch as SchDepEpoch, flightinfo.SchArrEpoch, flightinfo.Airline, flightinfo.FlightNumber, flightinfo.TailNumber, flightinfo.OriginAirport, flightinfo.DestinationAirport, flightinfo.ScheduledDeparture, flightinfo.ScheduledArrival, flightinfo.ScheduledTime, flightinfo.Distance, inair.DepartureDelay, inair.ArrivalDelay, flightinfo.HasDeparted, inair.Wrong FROM flightinfo, inair WHERE flightinfo.FlightIdentifier = inair.FlightIdentifier)) t1 INNER JOIN WeatherInfo ON WeatherInfo.FlightIdentifier = t1.FlightIdentifier INNER JOIN PrevFlightInfo ON PrevFlightInfo.FlightIdentifier = t1.FlightIdentifier ORDER BY SchDepEpoch";
	else if($_GET['status'] == 'Scheduled')
		$sqlst = "SELECT * FROM (SELECT flightinfo.FlightIdentifier, flightinfo.LastUpdateEpoch, '' as ScheduledDate, flightinfo.SchDepEpoch as SchDepEpoch, flightinfo.SchArrEpoch, flightinfo.Airline, flightinfo.FlightNumber, flightinfo.TailNumber, flightinfo.OriginAirport, flightinfo.DestinationAirport, flightinfo.ScheduledDeparture, flightinfo.ScheduledArrival, flightinfo.ScheduledTime, flightinfo.Distance, scheduled.DepartureDelay, scheduled.ArrivalDelay, flightinfo.HasDeparted, scheduled.Wrong FROM flightinfo, scheduled WHERE flightinfo.FlightIdentifier = scheduled.FlightIdentifier) t1 INNER JOIN WeatherInfo ON WeatherInfo.FlightIdentifier = t1.FlightIdentifier INNER JOIN PrevFlightInfo ON PrevFlightInfo.FlightIdentifier = t1.FlightIdentifier ORDER BY SchDepEpoch";
	else if($_GET['status'] == 'InAir')
		$sqlst = "SELECT * FROM (SELECT flightinfo.FlightIdentifier, flightinfo.LastUpdateEpoch,'' as ScheduledDate, flightinfo.SchDepEpoch as SchDepEpoch, flightinfo.SchArrEpoch, flightinfo.Airline, flightinfo.FlightNumber, flightinfo.TailNumber, flightinfo.OriginAirport, flightinfo.DestinationAirport, flightinfo.ScheduledDeparture, flightinfo.ScheduledArrival, flightinfo.ScheduledTime, flightinfo.Distance, inair.DepartureDelay, inair.ArrivalDelay, flightinfo.HasDeparted, inair.Wrong FROM flightinfo, inair WHERE flightinfo.FlightIdentifier = inair.FlightIdentifier) t1 INNER JOIN WeatherInfo ON WeatherInfo.FlightIdentifier = t1.FlightIdentifier INNER JOIN PrevFlightInfo ON PrevFlightInfo.FlightIdentifier = t1.FlightIdentifier ORDER BY SchDepEpoch";
	
	$result = $conn->query($sqlst);
	
	$array=[];
	
	if ($result->num_rows > 0) {
		while($row = $result->fetch_assoc()){
			$row = getArray($row, false);
			$array[]=$row;
		}
	}
	
	echo json_encode($array, JSON_NUMERIC_CHECK);
?>