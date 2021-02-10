Event-driven dashboarding
-------------------------

This repository demonstrates automated dashboard creation for detected events, using semantic reasoning, as discussed in

S. Vanden Hautte, D. De Paepe, B. Steenwinckel, P. Moens, B. Steenwinckel, S. Verstichel, S. Vandekerckhove, F. Ongenae and S. Van Hoecke, “Event-driven dashboarding and feedback capturing for improved event detection and reduced human labeling effort”, Engineering Applications of Artificial Intelligence (submitted).

# Demo movie

A demo movie is provided at https://www.youtube.com/watch?v=r7ygntYFLxo.

# Running the semantic reasoning for anomaly investigation dashboard creation

The following instructions allow to run the semantic reasoning that is used to automatically create dashboard tabs for the investigation of events.
The semantic reasoning will be run for all types of events produced by the detectors.

Installation & running instructions:

1. Install the EYE reasoner on your machine (see http://eulersharp.sourceforge.net/INSTALL).
2. Clone or download this repository to your machine.
3. Install the required python libraries: `pip install -r requirements.txt`.
3. Run `python test.py`; 

Questions can be e-mailed to `dieter.depaepe@ugent.be` or `sofie.vanhoecke@ugent.be`.