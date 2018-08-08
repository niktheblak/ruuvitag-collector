import configparser

def get_ruuvitags(inifile="ruuvitags.ini", section="DEFAULT"):
    parser = configparser.ConfigParser(delimiters=('='))
    parser.optionxform = str
    parser.read(inifile)
    return dict(parser.items(section))
