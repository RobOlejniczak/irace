# iRace admin dockerfile

FROM python:3-slim

ARG IRACE_GID
ARG IRACE_UID

ENV IRACE_GID=${IRACE_GID:-1000} IRACE_UID=${IRACE_UID:-1000}

RUN echo " ---> Create user and group" && \
    addgroup --system --gid=$IRACE_GID irace > /dev/null 2>&1 ; \
    adduser --system --gid=$IRACE_GID --uid=$IRACE_UID irace && \
    echo " ---> Update package repos" && \
    apt-get update -qq && \
    echo " ---> Install packages (apt)" && \
    apt-get install -qqy rsync nginx git gcc && \
    echo " ---> Install packages (pip)" && \
    pip install -qU requests docopt jinja2 \
                    flask gevent couchdb Flask-SocketIO \
                    git+git://github.com/a-tal/requests-throttler.git && \
    echo " ---> Clean up" && \
    apt-get remove -qqy git gcc && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 8000

VOLUME /irace/html

ENV IRACE_EXPOSED=1 IRACE_PORT=8000 IRACE_HTML=/irace/html/

COPY MANIFEST.in README.md setup.py tox.ini .pylintrc /irace/
COPY static /irace/static
COPY irace /irace/irace

WORKDIR /irace

RUN pip install -q .[admin]

COPY .ssh /home/irace/.ssh
COPY env.vars /irace/

RUN chown "$IRACE_UID:$IRACE_GID" -R /home/irace/.ssh /irace && \
    chmod 400 /irace/env.vars

USER irace

# see the README.md for more details about env.vars
CMD /bin/bash -c 'source env.vars && irace-admin'
