import re, os
from flask import Flask, request
from flask_restful import Resource, Api, reqparse

# Package needs to be fixed: https://github.com/jinglemansweep/PyLMS/issues/15
from pylms.server import Server
from pylms.player import Player

DEFAULT_PLAYER="00:04:20:23:a4:61"

app = Flask(__name__)
app.config['LMS_HOST'] = os.environ['LMS_HOST']
app.config['LMS_PORT'] = os.environ['LMS_PORT']

api = Api(app)

def returnDefaultRecord(sq):
    print(request.endpoint + " for " + sq.get_name())
    return {
        'mac': sq.get_ref(),
        'name': sq.get_name(),
        'ip': sq.get_ip_address(),
        'power': sq.get_power_state(),
        'mode': sq.get_mode(),
        'volume': sq.get_volume(),
        'title': sq.get_track_title(),
        'artist': sq.get_track_artist(),
        'album': sq.get_track_album(),
        'model': sq.get_model(),
    }


def ProcessCommand():
    print("Connecting to " + app.config.get('LMS_HOST') + ":" + app.config.get('LMS_PORT'))
    sc = Server(hostname=(app.config.get('LMS_HOST')), port=app.config.get('LMS_PORT'))
    sc.connect()
    parser = reqparse.RequestParser()
    parser.add_argument('player', type=str, help='Mac address of player')
    args = parser.parse_args()

    if args.player is None:
        sq = sc.get_player(DEFAULT_PLAYER)  # type: Player
    else:
        if not re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", args.player.lower()):
            return {
                'status': 'error',
                'msg': 'invalid mac address'
            }
        else:
            sq = sc.get_player(args.player)
            if sq is None:
                return {
                    'status': 'error',
                    'msg': 'player not found'
                }

    if request.endpoint == "root":
        result = {}
        playerresult = {}
        players = sc.get_players()
        for p in players:
            playerresult[p.get_ref()] = returnDefaultRecord(p)
            result['DEFAULT_PLAYER'] = DEFAULT_PLAYER
            result['SERVER'] = {
                'version': sc.get_version(),
                'playercount': sc.get_player_count()
            }
            result['PLAYER'] = playerresult
        return result

    if request.endpoint == "stop":
        sq.stop()

    if request.endpoint == "start":
        sq.play()

    if request.endpoint == "toggle":
        sq.toggle()

    if request.endpoint == "pause":
        sq.pause()

    if request.endpoint == "unpause":
        sq.unpause()

    if request.endpoint == "next":
        sq.next()

    if request.endpoint == "prev":
        sq.prev()

    if request.endpoint == "volup":
        sq.volume_up(3)

    if request.endpoint == "voldown":
        sq.volume_down(3)


    return (returnDefaultRecord(sq))


class Root(Resource):
    def get(self):
        return ProcessCommand()


class Stop(Resource):
    def get(self):
        return ProcessCommand()


class Start(Resource):
    def get(self):
        return ProcessCommand()


class Toggle(Resource):
    def get(self):
        return ProcessCommand()


class Pause(Resource):
    def get(self):
        return ProcessCommand()


class UnPause(Resource):
    def get(self):
        return ProcessCommand()


class Next(Resource):
    def get(self):
        return ProcessCommand()


class Prev(Resource):
    def get(self):
        return ProcessCommand()


class VolUp(Resource):
    def get(self):
        return ProcessCommand()


class VolDown(Resource):
    def get(self):
        return ProcessCommand()


api.add_resource(Root, '/')
api.add_resource(Stop, '/stop')
api.add_resource(Start, '/start')
api.add_resource(Toggle, '/toggle')
api.add_resource(Pause, '/pause')
api.add_resource(UnPause, '/unpause')
api.add_resource(Next, '/next')
api.add_resource(Prev, '/prev')
api.add_resource(VolUp, '/volup')
api.add_resource(VolDown, '/voldown')


if __name__ == '__main__':
    app.run()
