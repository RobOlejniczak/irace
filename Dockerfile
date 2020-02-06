# iRace dockerfile

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
    apt-get install -qqy git && \
    echo " ---> Install packages (pip)" && \
    pip install -qU requests docopt couchdb \
                    git+git://github.com/a-tal/requests-throttler.git && \
    echo " ---> Clean up" && \
    apt-get remove -qqy git && \
    rm -rf /var/lib/apt/lists/*

COPY README.md setup.py tox.ini .pylintrc /src/
COPY irace /src/irace

RUN cd /src && \
    find . -type d -exec chmod 755 {} \; && \
    find . -type f -exec chmod 644 {} \; && \
    pip install -q .[db] && \
    cd / && \
    rm -rf /src

USER irace

CMD irace-python
