# iRace

Web frontend for iRacing league results.


## Installation


```bash
git clone https://github.com/a-tal/irace.git
cd irace
pip install .
```


## Fetching data from iRacing

**Set the environment variables `IRACING_USERNAME` and `IRACING_PASSWORD` to
your iRacing.com account credentials.**

*After using any of the `irace-populate` commands, run `irace-generate` to
regenerate the html from templates and the updated data.*


### Find your league ID

```bash
irace-league "name of your club"
```

Look for "leagueid" in the output


### First time only


With no other arguments this will fetch all data relevant to your league.
Only do this once, schedule other updates as appropriate.

```
irace-populate --club=<id>
```

### After a race


You can also limit this to a single season if desired. It will also update the
calendar for seasons queried.

```
irace-populate --club=<id> --races
```

### Occasionally for new members

This will populate their driver details page. New members can still race and
show up in results without this being ran, it's only for the overview.

```
irace-populate --club=<id> --members
```
