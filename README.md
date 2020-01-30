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


## iRace-admin

There is an included Dockerfile to run an accompanying service to monitor
seasons in leagues and automatically pull race data, regenerate HTML and
push the resulting files to your iRace webhost.

### .env

The `.env` file is used by the Docker compose build system. Your `.env` file
should contain:

```
COUCHDB_USER=some_random_username
COUCHDB_PASSWORD=some_random_password
IRACE_GID=1000
IRACE_UID=1000
IRACE_ROOT=/path/on/docker/host/to/irace
IRACE_DATA=/path/on/docker/host/to/couchdb
IRACE_EXPOSED_PORT=8080
```

`IRACE_ROOT` should be the path to this directory on your docker host.

`IRACE_DATA` is a path on the Docker host where you'd like to keep couchdb data.

`IRACE_EXPOSED_PORT` controls what port the nginx container listens on. Ensure
this port is accessible on your docker host.

Ensure `IRACE_GID`:`IRACE_UID` has write access to `${IRACE_ROOT}/html` on the
Docker host.

### `env.vars`

The `env.vars` file is used to configure iRace environment variables at runtime.
Be sure to create your `env.vars` file before building your `irace` docker
container or the build will fail.

The `env.vars` file is `source`'d, so any bash syntax will work, but generally
it should only contain lines of `export KEY="some_value"` where `KEY` is:

Name             | Required | Type | Purpose
-----------------|------|--------|--------
IRACING_USERNAME | yes* | string | your iRacing.com username/email for fetching data
IRACING_PASSWORD | yes* | string | your iRacing.com password for fetching data
IRACING_CUSTID   | no   | int    | your iRacing.com customer ID
IRACING_LOGIN    | no   | string | alternative slug to log in with
IRACE_DEBUG      | no   | bool   | 1 or 0 to send debug information to stdout
IRACE_HTML       | no   | string | path to html output directory
IRACE_RESULTS    | no   | string | path to results output direction, if required
IRACE_HOST       | no   | string | webhost to push results to
IRACE_HOST_HTML  | no   | string | path on webhost to push results to
IRACE_EXPOSED    | no   | bool   | if irace-admin should listen on 0.0.0.0
IRACE_PORT       | no   | int    | alternative port to run irace-admin on
IRACE_HTTPS      | no   | bool   | if the webhost is running https
COUCHDB_HOST     | no   | string | name or IP address of couchDB
COUCHDB_SSL      | no   | bool   | if the couchDB server is running https
COUCHDB_USER     | no   | string | couchDB username, if required
COUCHDB_PASSWORD | no   | string | couchDB password, if required

### SSH

You will need to configure ssh keys for your container if you want to push
results to your webhost. Place all relevant files into the `.ssh` directory
before building your admin container. Don't forget to include `known_hosts`.

Alternatively, mount `/home/irace/.ssh` inside the container at runtime.

SSH keys are only used if both `IRACE_HOST` and `IRACE_HOST_HTML` are provided
via `env.vars`.

### Building

Finally, with `.env` and `env.vars` configured, run `docker-compose build`.
Assuming there are no errors, run `docker-compose up -d`.

You should now be able to visit http://your-docker-host:8080/ and/or use
`docker logs -f irace_admin_1` to check the status of your iRace admin app.
