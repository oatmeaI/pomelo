import sys

path_arg = sys.argv[1] if len(sys.argv) > 1 else None

base_path = path_arg if path_arg is not None else "/config"
config_path = f"{path_arg}/pomelo" if path_arg is not None else "/pomelo"
