# pylint: disable=line-too-long, inconsistent-return-statements
"""
REST API for Logitech Media Server built with Python Flask
"""
import os

from flask import Flask, abort, jsonify
from flask_smorest import Api
from healthcheck import HealthCheck, EnvironmentDump
from squeezebox_controller import SqueezeBoxController, commands

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
    """
    Index
    :return:
    """
    result = {}
    defaultplayer_info = controller._get_player_info(app.config.get("DEFAULT_PLAYER"))  # pylint:disable=protected-access
    result['defaultplayer'] = {
        'name': app.config.get("DEFAULT_PLAYER"),
        'volume': defaultplayer_info['mixer volume'],
        'mode': defaultplayer_info['mode'],
        'playlist repeat': defaultplayer_info['playlist repeat'],
        'power': defaultplayer_info['power'],
        'title': defaultplayer_info['remoteMeta']['title']
    }
    for name, mac in controller.player_macs.items():
        if app.config.get("DEFAULT_PLAYER") == name:
            result['defaultplayer']['mac'] = mac
    result['player'] = {}
    for pmac in sorted(controller.player_macs):
        if pmac != "ALL":
            result['player'][pmac] = {}
            playerinfo: dict = controller._get_player_info(pmac)  # pylint: disable=protected-access
            for pinfo in sorted(playerinfo.keys()):
                result['player'][pmac][pinfo] = playerinfo[pinfo]
                for name, mac in controller.player_macs.items():
                    if pmac == name:
                        result['player'][pmac]['mac'] = mac

    return result


@app.route("/<player>", methods=['GET'])
def getplayer(player=app.config.get("DEFAULT_PLAYER")):
    """
    Players
    :param player:
    :return:
    """
    if player not in controller.player_macs:
        abort(404, "Player must be in " + str(controller.player_macs.keys()))
    else:
        return controller._get_player_info(player)  # pylint:disable=protected-access


@app.route("/mac/<player>", methods=['GET'])
def getplayer_bymac(player):
    """
    Single player
    :param player:
    :return:
    """
    if player not in controller.player_macs.values():
        abort(404, "Player must be in " + str(controller.player_macs.values()))
    else:
        return controller._get_player_info(player)  # pylint:disable=protected-access


@app.route("/<player>/<command>", methods=['GET'])
def playercommand(player: str, command: str):
    """
    Run command on default player
    :param player:
    :param command:
    :return:
    """
    return process(command, player)


@app.route("/mac/<player>/<command>", methods=['GET'])
def playercommand_bymac(player: str, command: str):
    """
    Run command on layer given my mac
    """
    return process_bymac(command, player)


@app.route("/play", methods=['GET'])
def play(player=app.config.get("DEFAULT_PLAYER")):
    """
    Press "play" on default player
    :param player:
    :return:
    """
    return process("play", player)


@app.route("/pause", methods=['GET'])
def pause(player=app.config.get("DEFAULT_PLAYER")):
    """
    Press "pause" in default player
    :param player:
    :return:
    """
    return process("pause", player)


@app.route("/poweron", methods=['GET'])
def poweron(player=app.config.get("DEFAULT_PLAYER")):
    """
    Poweron default player
    :param player:
    :return:
    """
    return process("poweron", player)


@app.route("/poweroff", methods=['GET'])
def poweroff(player=app.config.get("DEFAULT_PLAYER")):
    """
    Poweroff default player
    :param player:
    :return:
    """
    return process("poweroff", player)


@app.route("/volup", methods=['GET'])
def volup(player=app.config.get("DEFAULT_PLAYER")):
    """
    Vollume up on default player
    :param player:
    :return:
    """
    return process("volup", player)


@app.route("/voldown", methods=['GET'])
def voldown(player=app.config.get("DEFAULT_PLAYER")):
    """
    Volume down on defaut player
    :param player:
    :return:
    """
    return process("voldown", player)


@app.route("/next", methods=['GET'])
def nexttitle(player=app.config.get("DEFAULT_PLAYER")):
    """
    Nexttitle on default player
    :param player:
    :return:
    """
    return process("next", player)


@app.route("/prev", methods=['GET'])
def prev(player=app.config.get("DEFAULT_PLAYER")):
    """
    Previous title on default player
    :param player:
    :return:
    """
    return process("prev", player)


def process(command, player):
    """
    Process command
    :param command:
    :param player:
    :return:
    """
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


def process_bymac(command, player):
    """
    Process command by mac
    :param command:
    :param player:
    :return:
    """
    if player not in controller.player_macs.values():
        abort(404, "Player must be in " + str(controller.player_macs.values()))
    else:
        if command not in getroutes():
            abort(406, "command must be in " + str(getroutes()))
        else:
            for name, mac in controller.player_macs.items():
                if player == mac:
                    player = name
            controller.simple_command({
                "player": player,
                "command": mapcommand(command)
            })
        return getplayer(player)


def mapcommand(command):  # pylint: disable=too-many-return-statements
    """
    Command mapping
    :param command:
    :return:
    """
    if command == "play":
        return "PLAY"
    if command == "pause":
        return "PAUSE"
    if command == "poweron":
        return "POWER ON"
    if command == "poweroff":
        return "POWER OFF"
    if command == "volup":
        return "VOLUME UP"
    if command == "voldown":
        return "VOLUME DOWN"
    if command == "next":
        return "SKIP"
    if command == "prev":
        return "PREVIOUS"


def getroutes():
    """
    Get routes in app
    :return:
    """
    result = []
    for rule in app.url_map.iter_rules():
        if str(rule) not in ["/openapi.json", "/static/<path:filename>", "/", "/<player>", "/<player>/<command>",
                             "/swagger", "/redoc"]:
            result.append(str(rule).strip("/"))
    return result


def checklms():
    """
    Check if LMS is working
    :return:
    """
    is_lms_working = False
    output = 'LMS is broken'
    try:
        is_lms_working = True
        output = "LMS is working"
    except Exception as exc:  # pylint: disable=broad-except
        output = output + ". " + str(exc)
    return is_lms_working, output


HEALTH.add_check(checklms)

# Add a flask route to expose information
app.add_url_rule("/healthcheck", "healthcheck", view_func=lambda: HEALTH.run())  # pylint: disable=unnecessary-lambda
app.add_url_rule("/environment", "environment", view_func=lambda: ENVDUMP.run())  # pylint: disable=unnecessary-lambda

if __name__ == '__main__':
    app.run()
