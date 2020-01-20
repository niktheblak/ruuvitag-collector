import yaml


def get_ruuvitags(cfg_file='ruuvitags.yaml'):
    with open(cfg_file, 'r') as stream:
        cfg = yaml.safe_load(stream)
        return cfg.get('ruuvitags')
