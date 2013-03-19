from bottle import route,run,template,post,request
from gateway_code.gateway_manager import GatewayManager

@route('/hello/:name')
def index(name='World'):
    return template('<b>Hello {{name}}</b>!', name=name)

@post('/exp/start/:expid/:username')
def exp_start():
    #files = request.files.keys()
    values = request.files.values()
    for field in values:
        with open(field.filename, 'w') as file:
            file.write(field.file.read())
    return str('experiment %s started by %s' % (expid, username) )

def parse_arguments(args):
    """
    Parsing arguments:

    host port
    Only pass arguments to function without script name

    """
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('host', type=str,
            help="Server address to bind to")
    parser.add_argument('port', type=int, help="Server port to bind to")
    arguments = parser.parse_args(args)

    return arguments.host, arguments.port

def main(args):
    """
    Command line main function
    """
    host, port = parse_arguments(args[1:])
    run(host=host, port=port, server='paste')
