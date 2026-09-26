import os
import re
import shutil
import sys


def ensure_account_folder():
    """Scaffold a new account folder from config-examples/ if it doesn't exist yet."""
    for i, arg in enumerate(sys.argv):
        if arg == "--config" and i + 1 < len(sys.argv):
            config_path = sys.argv[i + 1]
            account_dir = os.path.dirname(config_path)

            if account_dir and not os.path.isdir(account_dir):
                print(
                    f"Account folder '{account_dir}' not found — creating it from config-examples/"
                )
                shutil.copytree("config-examples", account_dir)

                username = os.path.basename(account_dir)
                config_yml = os.path.join(account_dir, "config.yml")
                if os.path.exists(config_yml):
                    with open(config_yml, "r") as f:
                        content = f.read()
                    content = re.sub(
                        r"^username:.*$",
                        f"username: {username}",
                        content,
                        flags=re.MULTILINE,
                    )
                    with open(config_yml, "w") as f:
                        f.write(content)

                print(
                    f"Created {account_dir}/ from template — set 'device:' and review filters.yml before running again."
                )
                sys.exit(0)
            break


ensure_account_folder()

import InstaAddict

InstaAddict.run()
