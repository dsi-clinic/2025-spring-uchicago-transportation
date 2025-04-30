Meeting with Beth Tindel, Director of Transportation & Parking Services

**Meeting Info**

Date: 4/29, 3:45pm-4:15pm, on Zoom

Attendees: Kristen, Minjae, Luna, Leah, Polly

Minjae and Luna presented our findings so far this quarter with a quick slide deck. 

**Meeting Notes**

1) How much do wait times vary at a given stop? We noticed that the law school has particularly long stop durations. 
We also see stop events outside of the scheduled time for lots of routes like DCC and 53rd Express.

ANSWER: Consider that these are stops where drivers tend to rest, go to the bathroom, etc. Beth mentioned both the law school and Logan Center as stops with accessible bathrooms, so she was not surprised to see them at the top of the stop duration visualization. To the point about erroneous stop events: delete them (TODO). Attributed this most likely to driver error like not turning GPS off. Takeaway: don't worry about these.

2) How do you all handle bunching? We have some preliminary findings but would like your input.

ANSWER: The various headways you see on the official transportation site are mainly a function of how many buses are going on a route at once, and they are often pulled on/off a given route as demand requires it. (For example, the Midway Metra is meant to come every 15 minutes from 4p-11p because there are two buses; that headway extends to every 30 minutes from 11p-4a because the route is only serviced by one bus in that timeframe.) Sometimes they also hold buses at particular chokepoints to address bunching. 

- TODO: Beth says she will give a list of these 'holdover' stops/what time buses stop at those places/how often by this Friday May 2nd.

3) NightRide Efficiency (focus area for UChicago Transportation)

The introduction of Ridesmart by via dissolved late night ridership. This used to be very high pre covid because there was no other available service. Then, they introduced the Lyft program as people came back to campus, the nightride shuttles fell out of favor, and the unlimited point-to-point nature of Via's has continued this steady decline in ridership.

- TODO: Look into ridership patterns at late night. For example, the South route ridership is basically non existent, as is north (east/central is high until around 9pm. virtually to nobody riding after midnight). They basically already have this data but are curious if we find something interesting from a different POV.

- TODO: making night time routes more efficient in relation to the Downtown Campus Connector (average headways per hour per time of day at each stop location). They would like to maximize ridership during periods where it is actually being used. Look at differences in ridership by hour and see if there's a relation to headway (This ask sounds similar to Minjae's initial scatterplot of ridership vs variance, but segmented out much more specifically.)


**Next Steps**

Kristen will change the assign_expected_frequencies() function to ignore stop events outside of official schedule instead of defaulting them all to 30 minutes, and add the night route logic that Beth mentioned (4p-11pm every 15 min, 11p-4a every 30 min)

Luna will look into the night ride data. Analyse trends in NightRide shuttles after the introduction of RideSmart by Via. If we don't get historical ridership data, then just compare night ridership versus daytime ridership

Minjae will visualize bunching patterns over time on some sort of map for the Downtown Connector

Pending Beth's data on holdover stops, Leah will visualise these separately to see how they behave differently than the rest of the stop events