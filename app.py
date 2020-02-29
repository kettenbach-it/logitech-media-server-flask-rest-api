import re, os
from flask import Flask, request, abort, jsonify
from flask_smorest import Api
from squeezebox_controller import SqueezeBoxController, commands
from healthcheck import HealthCheck, EnvironmentDump

app = Flask("LMS REST API")
app.config.update(
    LMS_HOST = os.environ['LMS_HOST'],
    LMS_PORT = os.environ['LMS_PORT'],
    VOLUMESTEP = os.environ.get("VOLUMESTEP"),
    DEFAULT_PLAYER = os.environ.get("DEFAULT_PLAYER"),
    #OPENAPI_URL_PREFIX="/",
    OPENAPI_URL_PREFIX=None,
    OPENAPI_VERSION='3.0.2',
    OPENAPI_REDOC_PATH="/redoc",
    OPENAPI_REDOC_VERSION="next",
    OPENAPI_SWAGGER_UI_PATH="/swagger",
    # https://github.com/swagger-api/swagger-ui/releases
    OPENAPI_SWAGGER_UI_VERSION="3.24.2"
)
api = Api(app)
HEALTH = HealthCheck()
ENVDUMP = EnvironmentDump()


print(f"Running LMS API for host {app.config.get('LMS_HOST')}:{app.config.get('LMS_PORT')}")

controller = SqueezeBoxController(app.config.get('LMS_HOST'), app.config.get('LMS_PORT'))
commands.update({
    "VOLUME UP": ["mixer","volume", "+" + app.config.get('VOLUMESTEP')],
    "VOLUME DOWN": ["mixer","volume", "-" + app.config.get('VOLUMESTEP')]
})


@app.errorhandler(404)
def custom404(error):
    """ customer error handler for 404 """
    return jsonify(
        code=error.code,
        status="Not found",
        message=str(error.description)
    ), 404


@app.errorhandler(406)
def custom406(error):
    """ customer error handler for 406 """
    return jsonify(
        code=error.code,
        status="Not acceptable",
        message=str(error.description)
    ), 406


@app.route("/", methods=['GET'])
def index():
    result = {}
    defaultplayer_info = controller._get_player_info(app.config.get("DEFAULT_PLAYER"))
    result['defaultplayer'] = {
        'name': app.config.get("DEFAULT_PLAYER"),
        'volume': defaultplayer_info['mixer volume'],
        'mode': defaultplayer_info['mode'],
        'playlist repeat': defaultplayer_info['playlist repeat'],
        'power': defaultplayer_info['power'],
        'title': defaultplayer_info['remoteMeta']['title']
    }
    result['player'] = {}
    for p in sorted(controller.player_macs):
        if p is not "ALL":
            result['player'][p] = {}
            playerinfo: dict = controller._get_player_info(p)
            for pi in sorted(playerinfo.keys()):
                result['player'][p][pi] = playerinfo[pi]

    return result


@app.route("/<player>", methods=['GET'])
def getplayer(player=app.config.get("DEFAULT_PLAYER")):
    if player not in controller.player_macs:
        abort(404, "Player must be in " + str(controller.player_macs.keys()))
    else:
        return controller._get_player_info(player)


@app.route("/play", methods=['GET'])
def play(player=app.config.get("DEFAULT_PLAYER")):
    return process("play", player)


@app.route("/pause", methods=['GET'])
def pause(player=app.config.get("DEFAULT_PLAYER")):
    return process("pause", player)


@app.route("/poweron", methods=['GET'])
def poweron(player=app.config.get("DEFAULT_PLAYER")):
    return process("poweron", player)


@app.route("/poweroff", methods=['GET'])
def poweroff(player=app.config.get("DEFAULT_PLAYER")):
    return process("poweroff", player)


@app.route("/volup", methods=['GET'])
def volup(player=app.config.get("DEFAULT_PLAYER")):
    return process("volup", player)


@app.route("/voldown", methods=['GET'])
def voldown(player=app.config.get("DEFAULT_PLAYER")):
    return process("voldown", player)


@app.route("/next", methods=['GET'])
def nexttitle(player=app.config.get("DEFAULT_PLAYER")):
    return process("next", player)


@app.route("/prev", methods=['GET'])
def prev(player=app.config.get("DEFAULT_PLAYER")):
    return process("prev", player)


@app.route("/<player>/<command>", methods=['GET'])
def playercommand(player: str, command: str):
    return process(command, player)


def process(command, player):
    if player not in controller.player_macs:
        abort(404, "Player must be in " + str(controller.player_macs.keys()))
    else:
        if command not in getroutes():
            abort(406, "command must be in " + str(getroutes()))
        else:
            controller.simple_command({
                "player": player,
                "command": mapcommand(command)
            })
        return getplayer(player)


def mapcommand(command):
    if command == "play":
        return "PLAY"
    elif command == "pause":
        return "PAUSE"
    elif command == "poweron":
        return "POWER ON"
    elif command == "poweroff":
        return "POWER OFF"
    elif command == "volup":
        return "VOLUME UP"
    elif command == "voldown":
        return "VOLUME DOWN"
    elif command == "next":
        return "SKIP"
    elif command == "prev":
        return "PREVIOUS"


def getroutes():
    result = []
    for rule in app.url_map.iter_rules():
        if str(rule) not in ["/openapi.json", "/static/<path:filename>", "/", "/<player>", "/<player>/<command>",
                             "/swagger", "/redoc"]:
            result.append(str(rule).strip("/"))
    return result


def checklms():
    is_lms_working = False
    output = 'LMS is broken'
    try:
        is_lms_working = True
        output = "LMS is working"
    except Exception as exc:
        output = output + ". " + str(exc)
    return is_lms_working, output


HEALTH.add_check(checklms)

# Add a flask route to expose information
app.add_url_rule("/healthcheck", "healthcheck", view_func=lambda: HEALTH.run())  # pylint: disable=unnecessary-lambda
app.add_url_rule("/environment", "environment", view_func=lambda: ENVDUMP.run())  # pylint: disable=unnecessary-lambda

if __name__ == '__main__':
    app.run()
