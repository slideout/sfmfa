# SingleEntry MFA (MultiFactor Authentication)

* * *

> Hackathon work-in-progress

* * *

This hack experiments with using NuPIC to learn a password sequence as well as a keystroke timing "fingerprint" of the person typing the password.  The fingerprint consists of the latency times of each keystroke transition - the start key, the time the key is down, the elapsed time until the next key, and then the next key.  The goal of this hack would be to tell the difference between the password owner typing the password, and an unauthorized person or program entering the same password.

Uses two models - the character model for learning the passphrase sequence, and a timing model to learn the keystroke transitions as a subset of the overall password.  Each keystroke transition is a unique sequence.

Patterns the data - the learned timing sequence is (startChar, nextChar, elapsedMs, downMs) via both category and scalar encoders (previous version used a single scalar and converted the characters to large-value integers).  The sequence is created by setting the unused field parameter to None (example is in the code).  Sequencing the two known character values earlier in the prediction sequence let the anomaly represent changes in timing more reliably.

Uses sub-sequencing / priming - found that resetting the model sequence before each sequence, in order to train smaller sequences, works well.  Inserting a common primer value before each sequence helped the first real value in the sequence be less anomalous.

Experimented with the Subutai anomaly routines.  Found that with the small data set and small anomaly counts, noise wasn't a large enough issue to make the anomaly routines useful.

Experimented with different encoders (PassThruEncoder and NonUniformScalarEncoder).  Found that the passthru encoder doesn't seem to be integratable with the CLAModel.  The nonuniformscalar was able to focus more resolution at points in the range - but the overall issue was solved more cleanly by using both a category and scalar encoder, and passing None values to create the sequence.

Experimented with training each learned password sequence in order, vs random.  Random learning of each password attempt resulted in a model that better understood the variances in each password entry - as apposed to "forgetting" the older password entries if multiple iterations of password were trained together.

Requires pygame - recording key down/up events wasn't possible using plain python/termio.


## Future:

Simply recording a character keypair and a percentage variance on two timings isn't complex using standard code (i.e no CLA).  Experiment with learning deeper information about keystroke entry - such as an O-R and R-E key timing being different when part of two different words, such as "CORE" and "MORE".

If the entry passes, retrain the model using all existing valid passwords - so the model adapts to the user over time.

Add environment data such as keyboard hardware, time of day, or network identifiers to the timing model, so the timings can reflect the real-world state as well as the user.

Train on both a password and a longer passphrase.  On password fail, fallback to a passphrase entry using the same learned timings.


## To reset learned data (stored in mfaLearn.csv):

    python mfa.py learn

## To reset test data (stored in mfaTest.csv):

    python mfa.py test

## To run (run is split up from learn/test so that model tuning can be better analyzed, static data):

    python mfa.py run

