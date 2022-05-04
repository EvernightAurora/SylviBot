import yaml


with open('config.yaml', 'r', encoding='utf-8') as f:
    configs = yaml.unsafe_load(f)


def get_config(key, default_value):
    global configs
    if key in configs.keys():
        return configs[key]
    else:
        return default_value


