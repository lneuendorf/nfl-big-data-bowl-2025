# Todo
1. plotting
    1. create process to generate and save many plots to icloud
    2. clean up plotting code
    3. plot dots with orientation and color by position
2. look into plays where there are motions and shifts, do defenders shift in response? Do they shift to fill gaps?


# Notes:
* The motion and shift events are human tagged, whereas the motion and shift binary player play columns are tagged via a rule-based process


# Good Pre-Snap Plays
2022102302, 2606
2022100903, 2974 - good shift play where defense stays is gap sound -> inside run no gain
2022101610, 2602 - mistagged - event has shift, when it was motion 
2022100903, 369 - mislabled as is an inside left run but runs right

# Weird Plays
2022091101_1826 - balls stays on the qb when its an RB run for a gain of 1


# Removed Plays:
- plays with a penalty


line set
    Case 1: line is already set at start of recording
    Case 2: line is set midway through recording (after huddle_break_offense) prior to snap
        a. set and then immediate shifts or motion (e.g. 2022091102_2738)
        b. set and then motion or shifts after a bit of time
        c. set and no motion or shifts
        d. set and immediate ball snap
