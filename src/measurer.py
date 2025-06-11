#!/usr/bin/env python
#
# Copyright 2015 British Broadcasting Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''
Wrapper class for detect.py and analyse.py functions to gather measurmeents
from an arduino and analyse them.

'''


import analyse
import arduino
import detect


class DubiousInput(Exception):

    def __init__(self, value):
        super(DubiousInput, self).__init__(value)


class Measurer:

    def __init__(self, role, pinsToMeasure, expectedTimings, eventDurations, videoStartTicks, wallClock, syncTimelineClock, syncTimelineTickRate, wcPrecisionNanos, acPrecisionNanos, captureSecs):
        """\

        connect with the arduino and send commands on which pins are to be read during
        data capture.

        :param role "master" or "client" which role the measurement system is acting in
        :param pinsToMeasure a list of pin names that are to be measured.
                a name must be one of "LIGHT_0", "LIGHT_1", "AUDIO_0" or "AUDIO_1"
        :param expectedTimings  dict mapping pin names ("LIGHT_0","LIGHT_1","AUDIO_0","AUDIO_1") to lists containing expected flash/beep times
        read from a json metadata file. For pins that are not specified as arguments, there will be no entry in the dict.
        :param eventdurations dict mapping pin names to the expected duration of the flash/beep in seconds (e.g. 0.001 = 1 millisecond)
        :param videoStartTicks initial sync time line clock value
        :param wallClock the wall clock object.  This will be used in arduino.py
                to take various time snapshots
        :param syncTimelineClock the sync time line clock object
        :param syncTimelineTickRate: tick rate of the sync timeline
        :param wcPrecisionNanos the wall clock precision in nanoseconds
        :param acPrecisionNanos the arduino clock's precision in nanoseconds
        :param captureSecs length of the capture to be taken on arduino in seconds
        """

        self.role = role
        self.pinsToMeasure = pinsToMeasure
        self.expectedTimings = expectedTimings
        self.eventDurations = eventDurations
        self.videoStartTicks = videoStartTicks
        self.wallClock = wallClock
        self.syncTimelineClock = syncTimelineClock
        self.syncClockTickRate = syncTimelineTickRate
        self.wcPrecisionNanos = wcPrecisionNanos
        self.acPrecisionNanos = acPrecisionNanos

        self.f = arduino.connect()
        self.pinMap = {"LIGHT_0": 0, "AUDIO_0": 1, "LIGHT_1": 2, "AUDIO_1": 3}
        self.activatePinReading()
        self.nActivePins  = arduino.prepareToCapture(self.f, wallClock, captureSecs)[0]

        if self.nActivePins != len(self.pinsToMeasure) :
            raise ValueError("# activated pins mismatches request: ")



    def ctsRecorder(self, speedChanged):
        """\

        Only used when the measurement system is acting as client.
        Append to list of reported correlations as a tuple
        (local wallclock time, (received wallclock, received sync time line clock value, speed multiplier of sync time line clock)

        """

        whenReceived = self.wallClock.ticks
        cts = self.syncTimelineClockController.latestCt
        rcvdTimestamp = cts.timestamp
        rcvdWallClock= rcvdTimestamp.wallClockTime
        rcvdSyncTimeLineClockValue = rcvdTimestamp.contentTime
        speedMultiplier = cts.timelineSpeedMultiplier
        self.timestampedReceivedControlTimeStamps.append( (whenReceived, (rcvdWallClock, rcvdSyncTimeLineClockValue, speedMultiplier)) )





    def setSyncTimeLinelockController(self, syncTimelineClockController):
        """\

        Only used when the measurement system is acting as client.
        Remember the clock controller used to drive changes to our
        emulation of the sync timeline based on correlations received over
        the TS protocol.  Initialise the list that will capture these
        reported correlations also.  Set the bound function to be called back
        by the clock controller as any time changes are detected by the controller examining
        the TS protocol messages.  These are notified using the bound function "ctsRecorder" above

        """

        self.timestampedReceivedControlTimeStamps = []
        self.syncTimelineClockController = syncTimelineClockController
        syncTimelineClockController.onTimingChange = self.ctsRecorder




    def activatePinReading(self):
        """\

        Activate each of the pins mentioned in the input array for reading
        during the Arduino capture phase

        :param pinsToMeasure a list of pin names that are to be measured.
                    a name must be one of "LIGHT_0", "LIGHT_1", "AUDIO_0" or "AUDIO_1"
        :param pinMap dictionary that maps from pin name to pin number
        :param f: the file handle for serial communication with the Arduino
        :param wallClock: the wall clock providing times for the CSS_WC protocol
         (wall clock protocol)

        """

        for pin in self.pinsToMeasure:
             arduino.samplePinDuringCapture(self.f, self.pinMap[pin], self.wallClock)


    def snapShot(self):
        """\

        only used when measurement system is acting as master

        take correlation between wall clock and sync time line

        :attribute syncTimelineClock the sync time line clock
        :attribute wallClock the wall clock
        :returns: tuple (wcWhenSnapshotted, (wcTime, syncTime, speed) where:
         * wcWhenSnapshotted is the wall clock time when the snapshot was taken
         * wctime and syncTime are a correlation between wall clock and sync timeline time
         * speed is the current speed of the sync timeline

        """
        syncTimeNow = self.syncTimelineClock.ticks
        # convert from pts to wallclock
        wcNow = self.syncTimelineClock.toOtherClockTicks(self.wallClock, syncTimeNow)
        speed = self.syncTimelineClock.speed
        whenSnapshotted = wcNow
        return (whenSnapshotted, (wcNow, syncTimeNow, speed))


    def capture(self):
        """\

        initiate the data capture.  For the sync time line correlations, use the observed
        correlations provided by the TS server when the measurement system is acting as a client,
        or use snapshots of the timeline being published by the measurement when it is acting
        as a server

        """
        if self.nActivePins > 0:
            if self.role == "master":
                correlationPre = self.snapShot()
            (self.channels, self.dueStartTimeUsecs, self.dueFinishTimeUsecs, timeDataPre, timeDataPost) = \
                                        captureAndPackageIntoChannels(self.f, self.pinsToMeasure, self.pinMap, self.wallClock)
            self.wcAcReqResp = {"pre":timeDataPre, "post":timeDataPost}
            if self.role == "master":
                 correlationPost = self.snapShot()
                 self.wcSyncTimeCorrelations = [correlationPre, correlationPost]
            elif self.role == "client":
                self.wcSyncTimeCorrelations = self.timestampedReceivedControlTimeStamps


    def detectBeepsAndFlashes(self, dispersionFunc):
        """\

        Uses the detect module to detect any flashes or beeps
        and sets the results in self.testPackage (a list with one entry per
        input being sampled)

        :param dispersionFunc: a function that, when called and passed a wall clock time, will return the wall clock dispersion
            corresponding to that time. When testing a CSA, this should be the dispersion
            measured by the CSA. When testing a TV, it should be the dispersion
            reported by the local wall clock client algorithm in the measuring system.
        """
        # add hint about duration of flashes/beeps to self.channels
        for pinName in self.eventDurations:
            self.channels[self.pinMap[pinName]]["eventDuration"] = self.eventDurations[pinName]

        # copy self.channels, but only the entries that are not 'None'
        measuredChannels = []
        for channel in self.channels:
            if channel is not None:
                measuredChannels.append(channel)

        # run detection process
        detector = detect.BeepFlashDetector(self.wcAcReqResp, self.syncClockTickRate, \
                                            self.wcSyncTimeCorrelations, dispersionFunc, \
                                            self.wcPrecisionNanos, self.acPrecisionNanos)
        self.observedTimings = analyse.runDetection(detector, measuredChannels, self.dueStartTimeUsecs, self.dueFinishTimeUsecs)

        self.testPackage = []
        for result in self.observedTimings:
            pinName = result["pinName"]
            self.testPackage.append( { "pinName":pinName,  "observed": result["observed"],  "expected":self.expectedTimings[pinName] } )




    def getComparisonChannels(self):
        """\

        :return the measurement results, ready for iteration by the user of this service

        """
        return self.testPackage




    def doComparison(self, channel):
        """\

        run a comparison of observed and expected times for a given pin (represented by the channel input)

        :param channel a tuple
            { "pinName":pinName,  "observed": list of observed times,  "expected": list of expected times }
        :returns tuple summary of results of analysis.
            (index into expected times for video at which strongest correlation (lowest variance) is found,
            list of expected times for video,
            list of (diff, err) for the best match, corresponding to the individual time differences and each one's error bound)
        :raise DubiousInput exception if the observed data is longer than the expected data

        Results are normalised to be in units of seconds since start of the test video sequence.

        """
        if  (len(channel["observed"]) - len(channel["expected"]) > 0) or len(channel["observed"]) == 0 :
            raise DubiousInput("poor data or no data")

        test = (channel["observed"], channel["expected"])
        matchIndex, expected, diffsAndErrors = analyse.doComparison(test, self.videoStartTicks, self.syncClockTickRate)

        # convert everything to units of seconds
        expectedSecs = [ ((e-self.videoStartTicks) / self.syncClockTickRate) for e in expected ]
        diffsAndErrorsSecs = [ (d/self.syncClockTickRate, e/self.syncClockTickRate) for (d,e) in diffsAndErrors ]

        return matchIndex, expectedSecs, diffsAndErrorsSecs

def isAudio(pinName):
    """\

    Predicate to check whether the input corresponds to an audio- or light sensor-input

    :param pinName: indicates a pin to add to the set of pins to be read  during capture.
        one of "LIGHT_0", "AUDIO_0", "LIGHT_1", "AUDIO_1"
    :returns boolean: True if pin is associated with audio input on arduino
    and False otherwise (pin is connected to light sensor input

    """
    if pinName == "LIGHT_0" or pinName == "LIGHT_1":
        return False
    elif pinName == "AUDIO_0" or pinName == "AUDIO_1":
        return True
    else:
        raise ValueError("Unrecognised pin identifier: "+repr(pinName))



def repackageSamples(pinsToMeasure, pinMap, nMilliBlocks, samples):
    """\

    reformat the sample data into separate data channels that can be passed to
    the detect module

    :param pinsToMeasure: string array of pin names to be read  during capture.  An entry is one of:
        "LIGHT_0", "LIGHT_1", "AUDIO_0" and "AUDIO_1".
    :param pinMap dictionary to map from pin names to arduino pin numbers

    :param nMilliBlocks number of millisecond blocks in the sample data
    :param samples the arduino sample data.  Each millisecond block holds data
    for each activated pin, where that data are the high and low values observed
    on that pin over a millisecond
    :returns: the data channels for the sample data separated out per pin.  This is a
    list of dictionaries or None, one per sampled pin. It will be 'None' if nothing was sampled for that pin.
        A dictionary is { "pin": pin name, "isAudio": true or false,
            "min": list of sampled minimum values for that pin (each value is the minimum over a millisecond period)
            "max": list of sampled maximum values for that pin (each value is the maximum over same millisecond period) }

    """

    channels = [None, None, None, None]
    for pinName in pinsToMeasure:
        channels[pinMap[pinName]] = ( { "pinName": pinName, "isAudio": isAudio(pinName), "min": [], "max": [] } )

    i = 0
    for blk in range(0, nMilliBlocks):
        for channel in channels:
            if channel != None:
                channel["max"].append(ord(samples[i]))
                i += 1
                channel["min"].append(ord(samples[i]))
                i += 1

    return channels






def captureAndPackageIntoChannels(f, pinsToMeasure, pinMap, wallClock):
    """\

    capture the data on the arduino, transfer it, and repackage

    :param f: the file handle for serial communication with the Arduino
    :param pinsToMeasure: string array of pin names to be read during capture.  Names are
        LIGHT_0, LIGHT_1, AUDIO_0 and AUDIO_1.
    :param pinMap: dictionary that maps from pin name to arduino pin number
    :param wallClock: the wall clock providing times for the CSS_WC protocol (wall clock protocol)
    :returns a tuple: (data channels (see repackageSamples() ),
        nanosecond time when sampling commenced,
        nanosecond time when sampling ended,
        round trip timing data taken just before sampling started
        round trip timing data taken just after sampling finished )

    """

    dueStartTimeUsecs, dueFinishTimeUsecs, nMilliBlocks, timeDataPre, timeDataPost = arduino.capture(f, wallClock)
    samples = arduino.bulkTransfer(f, wallClock)[0]
    channels = repackageSamples(pinsToMeasure, pinMap, nMilliBlocks, samples)
    return (channels, dueStartTimeUsecs, dueFinishTimeUsecs, timeDataPre, timeDataPost)
