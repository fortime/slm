import logging
import os
import sys

from optparse import OptionParser, Option

from .manager import Manager

option_parser = OptionParser()
option_parser.add_option(
        Option(
            '-c', '--config', action='store',
            dest='config_path',
            help='path of config file, default: ~/.slm.yaml'
            )
        )
logger = logging.getLogger(__name__)

def run():
    options, _ = option_parser.parse_args(sys.argv)
    config_path = options.config_path
    if not config_path:
        config_path = os.path.expanduser('~/.slm.yaml')
    if not os.path.exists(config_path):
        print("config file '{}' doesn't exist".format(config_path), file=sys.stderr)
        sys.exit(1)
    manager = Manager(config_path)
    manager.run()
    '''
    creator = factory.get_creator(options.service_type, options.props_file)
    try:
        creator.gather()
        creator.create()
    except:
        props = creator.props
        with open('falied.props', 'w') as fout:
            fout.write(props)
        raise
    '''

if __name__ == '__main__':
    run()
