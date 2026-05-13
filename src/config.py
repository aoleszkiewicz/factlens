from dotenv import load_dotenv, find_dotenv

is_env_loaded = load_dotenv(dotenv_path=find_dotenv(raise_error_if_not_found=True))

if not is_env_loaded:
    ...
