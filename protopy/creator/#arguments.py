import argparse

def mk_args():
    """ 
        run like: kwargs = arguments.mk_args().__dict__
    """
    parser = argparse.ArgumentParser(description="Archive your files and folders!")
    
    parser.add_argument('-s', '--sources', required=False, nargs='+',
                                                type=str,
                                                default=None, 
                                                help='source paths to archive'
                                                )

    parser.add_argument('-n', '--target', required=False, nargs='+',
                                                type=str,
                                                default=None, 
                                                help='archive target'
                                                )

    parser.add_argument('-r', '--rename', required=False, nargs=None,
                                                type=str,
                                                default=None, 
                                                help='archive rename start directory'
                                                )

    parser.add_argument('-m', '--comment', required=False, nargs=None,
                                                type=str,
                                                default=None, 
                                                help='archive comment'
                                                )

    parser.add_argument('-y', '--allYes',  required=False, nargs='?' , const=1,
                                                type=bool,
                                                default=False, 
                                                help='allYes render wihout checks'
                                                )

    parser.add_argument('-d', '--direct',  required=False, nargs='?' , const=1,
                                                type=bool,
                                                default=False, 
                                                help='copy files with ingnore logic'
                                                )

    parser.add_argument('-v', '--verbose', required=False, nargs=None,
                                                type=int,
                                                default=0, 
                                                help='verbosity i.e. 1, 2, 3'
                                                )

    return parser.parse_args()