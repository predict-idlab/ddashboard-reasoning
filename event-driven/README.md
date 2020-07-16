Event-driven dashboarding
-------------------------

This repository demonstrates automated, event-driven dashboarding, as discussed in

S. Vanden Hautte, D. De Paepe, B. Steenwinckel, P. Moens, S. Verstichel, S. Vandekerckhove, F. Ongenae and S. Van Hoecke, “Event-driven dashboarding and feedback capturing for improved anomaly and fault detection and reduced human labeling effort”, Decision Support Systems (submitted).

# Demo movie

A demo movie is provided with `demo-dyversify-renson.mp4`.
The following is an explanation of the evolution of detected anomalies and faults, due to the interplay of data- and knowledge-driven event detectors and feedback capturing in a dynamic dashboard that visualizes events automatically for investigation purposes.

- 00:00 The demo starts with a dashboard that has been created by the user to monitor the air quality in two rooms of a house (room 2 and 4).
- 01:04 The first alerts are anomalies indicating that valves may have been incorrectly installed, with regard to the room they control airflow for. This detector is not discussed in the above-mentioned paper, therefore these events are ignored in this explanation. Note that the times on the bottom right of every event in the list are the times of detection, not the start or end time of the event. The dates differ, since for demo purposes, historical sensor data was streamed as a "replay" to the Kafka.
- 01:40 The next alerts are anomalies found by the unknown pattern detector, their description is "Unusual pattern detected.".
- 01:53 The anomaly investigation tab is created to inspect a humidity peak that occurred in the data on the 25th of July around 10:30AM. The widgets in the anomaly tab are created automatically, using semantic reasoning about the available metadata of the detected event (including, for example, which sensor property that showed abnormal behavior). The expert labels the anomaly as "Shower".
- 02:07 On scrolling up in the event list, the new description "Shower" of the relabeled anomaly is visible; also new unknown anomalies have been detected in the meantime, as well as a "shower": note the different writing compared to the "Shower" label that was just created: the "shower" is created by the semantic fault detector.
- 02:11 A new Shower is detected, this time by the known pattern detector, because it has found a pattern that is similar to the anomaly that has been relabeled by the user to a Shower.
- 02:14 The user navigates back to the user-driven dashboard, monitoring the system status, while new unknown anomalies are logged, as well as Showers (found by the known pattern detector) and showers (found by the semantic fault detector) are logged.
- 03:34 Right before the monitored ventilation unit fails to send data for a while, a humidity peak in room 4 again leads to the detection, a few seconds later, of a Shower. The user again opens an anomaly investigation tab for that event. The shown pattern is compared with the pattern that had been relabeled previously to a Shower, to show that the patterns are indeed similar, which motivated the detection of the Shower displayed in the newly opened dashboard tab.
- 03:54 The user navigates back to the user-driven dashboard. New sensor observations, anomalies and faults are being received. Around 04:11, the monitored Healthbox again fails for a moment to provide sensor data to the cloud environment.
- 05:23 An unknown anomaly is investigated, its behavior is different from the patterns that were displayed in the anomaly tabs opened earlier on. This pattern shows a shower echo effect, so the expert labels it as such.
- 05:38 Upon return on the user-driven dashboard, the humidity in room 2 is at a high level and then decreases again. The semantic fault detector detects a humid weather fault, thanks to the acquired expert knowledge. The customer in this case must have left a window open. The platform keeps detecting events, such as the two showers visible at 6:35 on top of the event list and in the bottom right widget.
- 06:48 A new shower echo effect is automatically labeled by the known pattern detector, because it was similar to the pattern labeled earlier by the user as an echo effect. The anomaly tab opened for investigation of this echo effect shows that indeed the pattern is similar and has been detected by the known pattern detector (it has been assigned the type KnownPatternAnomaly).

We can conclude that a considerable amount of events were labeled automatically, whereas the user only labeled 4 anomalies. The detectors incorporated the user feedback collected in the dashboard to detect new, similar patterns and assign the same label. The collected user feedback thus decreases the number of false negatives in this demo; additionally, by relabeling wrongly detected faults, false negatives could of course also be reduced. Also, the symbiosis of the detectors was demonstrated, e.g. new shower effects are only detected by the known pattern detector because a first shower effect was detected with the knowledge-driven semantic fault detector.

# Running the semantic reasoning for anomaly investigation dashboard creation

The following instructions allow to run the semantic reasoning that is used to automatically create anomaly investigation dashboards.
The semantic reasoning will be run for all types of anomalies and faults produced by the detetors.

Installation & running instructions:

1. Install the EYE reasoner on your machine (see http://eulersharp.sourceforge.net/INSTALL).
2. Clone or download this repository to your machine.
3. Install the required python libraries: `pip install -r requirements.txt`.
3. Run `python test.py`; 

Questions can be e-mailed to `sander.vandenhautte@ugent.be`.