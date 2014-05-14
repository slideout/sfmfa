# SingleEntry MFA (MultiFactor Authentication)

* * *

> Hackathon work-in-progress

* * *

This hack experiments with using NuPIC to learn a password sequence as well as a keystroke timing "fingerprint" of the person typing the password.  The fingerprint consists of the latency times of each keystroke transition - the start key, the time the key is down, the elapsed time until the next key, and then the next key.  The goal of this hack would be to tell the difference between the password owner typing the password, and an unauthorized person or program entering the same password.

Uses two models - the character model for learning the passphrase sequence, and a timing model to learn the keystroke transitions as a subset of the overall password.  Each keystroke transition is a unique sequence.

Patterns the data - the learned timing sequence is (startChar, nextChar, elapsedMs, downMs) as the same scalar input in a sequence (not separate inputs).  Sequencing the two known values earlier in the prediction sequence let the anomaly represent changes in timing more reliably.

Uses sub-sequencing / priming - found that resetting the model sequence after each sequence, in order to train smaller sequences, works well.  Inserting a common primer value before each sequence helped the first real value in the sequence be less anomalous.

Requires pygame - recording key down/up events wasn't possible using plain python/termio.


## Future:

Convert the > 0.1 anomaly threshold for pass/fail to use the Subutai anomaly handling routine.

If the entry passes, turn on learning and teach the model - so the model adapts to the user over time.

Try implementing a custom encoder for the character/timing sequence, versus the current broad value range and char*30 approach.  Once implemented, experiment with higher timing resolution of the keystroke gaps.

Add environment data such as keyboard hardware, time of day, or network identifiers to the timing model, so the timings can reflect the real-world state as well as the user.

Train on both a password and a longer passphrase.  On password fail, fallback to a passphrase entry using the same learned timings.


## To re-swarm:

    python mfa.py swarm

## To run:

    python mfa.py

