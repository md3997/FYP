<?php
	function getArray($row, $mini) {
		foreach ($row as $key => $value) {
			if (is_int($key)) {
				unset($row[$key]);
			}
		}
		
		$row['Weather'] = array();
		$row['Weather']['Delay'] = $row['WeatherDelay'];
		$row['Weather']['Epoch'] = $row['WeatherPointEpoch'];
		
		$row['PrevFlight'] = array();
		$row['PrevFlight']['Delay'] = $row['PrevArrivalDelay'];
		$row['PrevFlight']['Interval'] = $row['PrepTime'];
		
		$SchDep=$row['SchDepEpoch'];
		$SchArr=$row['SchArrEpoch'];

		$row['ScheduledDate'] = gmdate("d F Y", $SchDep*60);

		$row['ScheduledDepartureGMT']= gmdate('H:i',$SchDep*60)." UTC";
		$row['ScheduledArrivalGMT']= gmdate('H:i', $SchArr*60)." UTC";
		
		$row['ScheduledDeparture'] = str_pad($row['ScheduledDeparture'], 4, "0", STR_PAD_LEFT);
		$row['ScheduledArrival'] = str_pad($row['ScheduledArrival'], 4, "0", STR_PAD_LEFT);
		
		$row['ScheduledDepartureLocal']="Local Time ".substr($row['ScheduledDeparture'], 0, 2).":".substr($row['ScheduledDeparture'], 2, 2)." | ".$row['OriginAirport'];
		$row['ScheduledArrivalLocal']="Local Time ".substr($row['ScheduledArrival'], 0, 2).":".substr($row['ScheduledArrival'], 2, 2)." | ".$row['DestinationAirport'];

		$d = (int)$row['DepartureDelay'];
			
		if($d > 0) {
			$d = "<br>(+ ".$d." mins)";
		} else {
			$d = "<br>(− ".(-1*$d)." mins)";
		}
		
		if($row['HasDeparted']=='N'){
			
			$row['ActualDepartureGMT'] = "NA";
			$row['ActualDepartureLocal'] = "NA";
			
			$row['PredictedDepartureGMT']= gmdate('H:i',($SchDep+$row['DepartureDelay'])*60)." UTC".$d;
			
			$row['PredictedDepartureLocal']=(int)(substr($row['ScheduledDeparture'], 0, 2))*60+(int)(substr($row['ScheduledDeparture'], 2, 2))+(int)$row['DepartureDelay'];
		
			if($row['PredictedDepartureLocal'] > 1440)
				$row['PredictedDepartureLocal']-=1440;
		
			$row['PredictedDepartureLocal'] = "Local Time ".str_pad(floor($row['PredictedDepartureLocal'] / 60), 2, "0", STR_PAD_LEFT).':'.str_pad(($row['PredictedDepartureLocal'] - floor($row['PredictedDepartureLocal'] / 60) * 60), 2, "0", STR_PAD_LEFT)." | ".$row['OriginAirport'];
		} else {
			$row['PredictedDepartureGMT'] = "NA";
			$row['PredictedDepartureLocal'] = "NA";
			
			$row['ActualDepartureGMT'] = gmdate('H:i',($SchDep+$row['DepartureDelay'])*60)." UTC".$d;
			
			$row['ActualDepartureLocal']=(int)(substr($row['ScheduledDeparture'], 0, 2))*60+(int)(substr($row['ScheduledDeparture'], 2, 2))+(int)$row['DepartureDelay'];
		
			if($row['ActualDepartureLocal'] > 1440)
				$row['ActualDepartureLocal']-=1440;
		
			$row['ActualDepartureLocal'] = "Local Time ".str_pad(floor($row['ActualDepartureLocal'] / 60), 2, "0", STR_PAD_LEFT).':'.str_pad(($row['ActualDepartureLocal'] - floor($row['ActualDepartureLocal'] / 60) * 60), 2, "0", STR_PAD_LEFT)." | ".$row['OriginAirport'];
		}
		
		$d = (int)$row['ArrivalDelay'];
		
		if($d > 0) {
			$d = "<br>(+ ".$d." mins)";
		} else if ($d < 0){
			$d = "<br>(− ".(-1*$d)." mins)";
		} else {
			$d = "<br>(".$d." mins)";
		}
		
		$row['PredictedArrivalGMT']= gmdate('H:i', ($SchArr+$row['ArrivalDelay'])*60)." UTC".$d;
		
		$row['PredictedArrivalLocal']=(int)(substr($row['ScheduledArrival'], 0, 2))*60+(int)(substr($row['ScheduledArrival'], 2, 2))+(int)$row['ArrivalDelay'];
		
		if($row['PredictedArrivalLocal']> 1440)
			$row['PredictedArrivalLocal']-=1440;
		
		$row['PredictedArrivalLocal'] = "Local Time ".str_pad(floor($row['PredictedArrivalLocal'] / 60), 2, "0", STR_PAD_LEFT).':'.str_pad(($row['PredictedArrivalLocal'] - floor($row['PredictedArrivalLocal'] / 60) * 60), 2, "0", STR_PAD_LEFT)." | ".$row['DestinationAirport'];
		
		$minutes=$row['ScheduledTime'];
		$row['ScheduledTime'] = floor($minutes / 60)." hrs<br>".($minutes -   floor($minutes / 60) * 60).' mins';
		
		if($row['HasDeparted']=='N')
			$temp=(int)$row['DepartureDelay'];
		else
			$temp=(int)$row['ArrivalDelay'];
		
		if($temp<=10)
			$row['Level']=1;
		else if($temp>10 && $temp<=30)
			$row['Level']=2;
		else if($temp>30 && $temp<=60)
			$row['Level']=3;
		else if($temp>60 && $temp<=120)
			$row['Level']=4;
		else if($temp>120)
			$row['Level']=5;
		
		if ($row['HasDeparted'] == 'Y') {
			$row['Status']= "Departed At ".gmdate('H:i',($row['SchDepEpoch']+$row['DepartureDelay'])*60)." UTC";
		} else {
			$row['Status']='Not Yet Departed';
		}
		
		unset($row['SchArrEpoch']);
		unset($row['ScheduledDeparture']);
		unset($row['ScheduledArrival']);
		unset($row['HasDeparted']);
		unset($row['WeatherDelay']);
		unset($row['WeatherPointEpoch']);
		unset($row['PrevArrivalDelay']);
		unset($row['PrepTime']);
		
		if($mini == true) {	
			unset($row['Airline']);
			unset($row['DestinationAirport']);
			unset($row['Distance']);
			unset($row['FlightNumber']);
			unset($row['OriginAirport']);
			unset($row['ScheduledArrivalGMT']);
			unset($row['ScheduledArrivalLocal']);
			unset($row['ScheduledDate']);
			unset($row['ScheduledDepartureGMT']);
			unset($row['ScheduledDepartureLocal']);
			unset($row['ScheduledTime']);
			unset($row['TailNumber']);
		}
		return $row;
	}
?>