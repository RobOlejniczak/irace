"""iRace web frontend.

Currently only contains a stats module for fetching information from iRacing.
Not guaranteed to contain all the methods required for fetching all relevant
information as of yet. API is subject to change rapidly and no other projects
should be using `irace.stats.Client` until the 1.0.0 release (TBD).

In the near-term future we will be adding a storage layer and an additional
frontend API for the website javascript to tie into. Perhaps other admin
functionality as well, depending on how we decide to implement teams and
other features as requested.
"""
