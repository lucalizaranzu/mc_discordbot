from . import util as ut

default_config = {
    "guild_id": -1,
    "mcserver_ip": "",
    "rcon_port": 25575,
    "rcon_password": "",
    "default_role": -1,
    "existing_permissions": [],
    "role_permissions": {},
}

class Server:
    """
    Represents an instance of the bot per discord guild + minecraft server combo
    """
    def __init__(self, guild_id):
        self.guild_id = guild_id

        self.config = ut.readJSON(f"data/config/{guild_id}.json") #Get current version of the server config file
        self.whitelist = ut.readJSON(f"data/whitelist/{guild_id}.json") #Get current version of the server whitelist

    def get_whitelist(self):
        return self.whitelist
    def get_config(self):
        return self.config
    def get_guild_id(self):
        return self.guild_id


    def set_mcserver_ip(self, ip):
        self.config["mcserver_ip"] = ip
        ut.updateJSON(f"data/config/{self.guild_id}.json", self.config)

    def set_rcon_port(self, port):
        self.config["rcon_port"] = port
        ut.updateJSON(f"data/config/{self.guild_id}.json", self.config)

    def set_rcon_password(self, password):
        self.config["rcon_password"] = password
        ut.updateJSON(f"data/config/{self.guild_id}.json", self.config)

    def set_default_role(self, role_id):
        self.config["default_role"] = role_id
        ut.updateJSON(f"data/config/{self.guild_id}.json", self.config)

    def update_config(self):
        ut.updateJSON(f"data/config/{self.guild_id}.json", self.config)
    def update_whitelist(self):
        ut.updateJSON(f"data/whitelist/{self.guild_id}.json", self.whitelist)


def add_server(guild_id):

    config_data = default_config

    config_data["guild_id"] = guild_id

    ut.updateJSON(f"data/config/{guild_id}.json", default_config)
    ut.updateJSON(f"data/whitelist/{guild_id}.json", {})


def get_server(guild_id) -> Server | None:
    if not ut.readJSON(f"data/config/{guild_id}.json"):
        print(f"No server config found for guild ID {guild_id}.")
        return None
    return Server(guild_id)