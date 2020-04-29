#!/usr/bin/env python3

import os
import yaml


def yaml_files(directory):
    return [os.path.join(directory, filename)
            for filename in os.listdir(directory)
            if filename.endswith('.yaml')]


def load_yaml(filename):
    with open(filename) as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def merge_cfn_dicts(dict_1, dict_2):
    new_dict = {}
    new_dict.setdefault('Resources', {})
    new_dict.setdefault('Outputs', {})
    new_dict.update(dict_1)
    new_dict['Resources'].update(dict_2.get('Resources', {}))
    new_dict['Outputs'].update(dict_2.get('Outputs', {}))
    new_dict.update((k, v) for k, v in dict_2.items() if k not in ('Resources', 'Outputs'))
    return new_dict


if __name__ == '__main__':
    cfn_dict = {}
    for f in yaml_files(os.getcwd()):
        current_dict = load_yaml(f)
        cfn_dict = merge_cfn_dicts(cfn_dict, current_dict)

    print(yaml.dump(cfn_dict, indent=2, width=200))
