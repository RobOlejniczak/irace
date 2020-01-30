"""iRace admin web endpoints."""


import os

try:
    import flask_socketio
except ImportError:
    raise SystemExit(
        "irace-admin requires the admin extras. "
        "Use `pip install .[admin]` to install them."
    )

from flask import abort
from flask import Flask
from flask import request
from flask import jsonify
from flask import redirect
from flask import render_template

from .. import __version__
from .worker import Worker
from .worker import utcnow


app = Flask(  # pylint: disable=invalid-name
    __name__,
    template_folder=os.path.join("..", "templates"),
)
socketio = flask_socketio.SocketIO(app)  # pylint: disable=invalid-name
worker = Worker(socketio)  # pylint: disable=invalid-name


@app.context_processor
def inject_irace_host():
    """Inject our static runtime variables to the jinja2 environment."""

    return dict(
        irace_host="http{}://{}".format(
            "s" * int(bool(int(os.getenv("IRACE_HTTPS") or 1))),
            os.getenv("IRACE_HOST", "irace.talsma.ca"),
        ),
        version=__version__,
        utcnow=utcnow,
    )


@app.route("/style.css", methods=["GET"])
def style_get():
    """Return the stylesheet."""

    return render_template("style.css.j2"), 200, {
        "Content-Type": "text/css; charset=utf-8"
    }


@app.route("/", methods=["GET"])
def all_leagues():
    """Return top level details for all tracked leagues."""

    return render_template(
        "admin.html.j2",
        leagues=worker.stats["leagues"],
        last_sync=worker.stats["last_sync"],
    )


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""

    if worker.alive:
        reqs_made = worker.num_requests
        return "OK [{} request{}]".format(reqs_made, "s" * int(reqs_made != 1))
    return abort(503)


@app.route("/state", methods=["GET"])
def state():
    """State check endpoint."""

    return jsonify(worker.state)


@app.route("/ping", methods=["GET"])
def ping():
    """Ping route."""

    return "pong"


@app.route("/leagues/<int:league_id>/", methods=["GET"])
def league_details(league_id: int):
    """Return details for all seasons in a league."""

    for league in worker.stats["leagues"]:
        if league["league_id"] == league_id:
            return render_template(
                "admin_leagues.html.j2",
                league=league,
                last_sync=worker.stats["last_sync"],
            )
    return abort(404)


@app.route("/update/members/<int:league_id>/", methods=["GET"])
def update_members(league_id: int):
    """Update the member list for the league."""

    if worker.known_league_id(league_id):
        worker.update_members(league_id)
        return redirect("/")
    return abort(404)


@app.route("/update/seasons/<int:league_id>/", methods=["GET"])
def update_seasons(league_id: int):
    """Update all seasons in the league."""

    if worker.known_league_id(league_id):
        worker.update_seasons(league_id)
        return redirect("/")
    return abort(404)


@app.route("/update/seasons/<int:league_id>/<int:season_id>/", methods=["GET"])
def update_season(league_id: int, season_id: int):
    """Update a specific season in a league."""

    if worker.known_league_id(league_id):
        worker.update_season(league_id, season_id)
        return redirect("/")
    return abort(404)


@app.route("/add_league", methods=["GET"])
def add_league():
    """Add a new league."""

    try:
        league_id = int(request.args["league_id"])
    except Exception:
        return abort(400)

    worker.add_league(league_id)
    return redirect("/")


@app.route("/delete_league", methods=["GET"])
def delete_league():
    """Delete a league."""

    try:
        league_id = int(request.args["league_id"])
    except Exception:
        return abort(400)

    if worker.known_league_id(league_id):
        worker.delete_league(league_id)
        return redirect("/")

    return abort(404)


@app.route("/regenerate_html", methods=["GET"])
def regenerate_all_html():
    """Regenerate HTML for all leagues."""

    worker.regenerate_all_html()
    return redirect("/")


def main():
    """Launch the background worker and admin web frontend."""

    socketio.run(
        app,
        host="0.0.0.0" if bool(int(os.getenv("IRACE_EXPOSED") or 0)) else None,
        port=int(os.getenv("IRACE_PORT") or 8000),
        debug=bool(int(os.getenv("IRACE_DEBUG") or 0))
    )


if __name__ == "__main__":
    main()
