from os.path import abspath, dirname, join as pjoin
from os import getenv
from configparser import ConfigParser
from socket import socket
from warnings import warn

LIBDIR = dirname(abspath(__file__))


def get_ports(name=None):
    print('')
    DASH_PORTS = getenv('DASH_PORTS')
    if not DASH_PORTS:
        warn('Environment variable DASH_PORTS not defined, using default configuration scripts/ports.cfg')
        ports_cfg = pjoin(LIBDIR, 'ports.cfg')
    else:
        ports_cfg = DASH_PORTS
        print('Using port configuration specified in', ports_cfg)

    config = ConfigParser()
    config.read(ports_cfg)
    dash_ports = config['DEFAULT']

    print('')

    if name:
        port = int(dash_ports[name])
        check_port(name, port)
        return port

    else:
        for key in dash_ports.keys():
            port = int(dash_ports[key])
            check_port(key, port)
        return dash_ports


def check_port(key, port):

    s = socket()
    print(key, port)
    print('')

    if port > 2 ** 16 - 1:
        raise ValueError('port must be 0-65535')

    try:
        s.connect(('localhost', port))
        raise EnvironmentError(f'http://localhost:{port} is in use, specify another port for {key}')
    except ConnectionRefusedError:
        pass

if __name__=='__main__':
    check_port('summary_port',8050)
