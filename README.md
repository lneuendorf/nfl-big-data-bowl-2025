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
- qb kneel & qb spike

# Classifying Events
    1. Line Set
        - at least 10/11 offensive players stationary (<= 0.5 yards/sec) for 2 consecutive frames
    2. Motion
        a. Player in motion: player must be moving at 1 yards/sec for 5 consecutive frames
        b. Occurs after line set event and before ball snap event
        c. All other players stationary for duration of motion (<=0.5 yards/sec) 
        d. Direction of Motion: player must not be moving forward at time of snap (dy of 5 frames before snap <= 1 yard)
        e. Player moving at time of snap or immediantely before the snap (<0.2 seconds before, 1 second stationary is shift)

# Shift and Motion Plays
- result in illegal motion penalty if all players fail to reset for one second after shift and before the motion
    - pre-snap begins | lineset | shift | lineset | motion | ballsnap | post-snap begins

# TODO
- may have to split up getting first line set and then subsiquent to make first more leniant (10 player min)

# Problem Plays
2022091113_1363 - counts qb as motion when qb moves up to talk to center and then moves back to shotgun
2022091102_2738 - receiver never gets set before shifting
2022091102_2436 - receiver doesnt get set enough and goes in motion, line_set at end of motion
2022091200_3596 - fly motion, receiver never sets before starting motion
2022091108_1354 - fly shift and motion with no initial line set

# Gameplan
2. Classify motions
    i. look at value counts
4. Study up on how defenses counter motion