# Flight-Delay-Prediction
Using Machine Learning to predict flight delays.

1) Install using apt-get:<br/>
	<ul>
		<li>pip3</li>
		<li>python3-tk</li>
	</ul>
2) Install following libraries using pip3:<br/>
	<ul>
		<li>numpy</li>
		<li>pandas</li>
		<li>scipy</li>
		<li>scikit-learn</li>
		<li>mysql.connector</li>
		<li>pytz</li>
		<li>matplotlib</li>
	</ul>
3) Install lampp<br/>

4) Paste in file /opt/lampp/etc/ under section [mysqld]<br/>
	lower_case_table_names = 1<br/>

5) Start Apache and MySql from Lampp GUI<br/>
	To start Lampp GUI,<br/>
		sudo /opt/lampp/manager-linux-x64.run<br/>

6) Import "DB.sql" with name "flights"<br/>

7) Copy folder CronJob to Home directory(/home/<username>/)<br/>

8) Copy the Project folder to /opt/lampp/htdocs/<br/>

9) Set current time to Friday, Fri 02 January 2015, 21:43 GMT<br/>

10) Start cronjob<br/>
	i) crontab -e<br/>
	ii) Paste: */2 * * * * cd /home/<username>/CronJob && /usr/bin/python3 /home/<username>/CronJob/cron_job.py<br/>
	iii) Save and Exit

11) Navigate to:<br/>
	localhost/Project/<br/>
