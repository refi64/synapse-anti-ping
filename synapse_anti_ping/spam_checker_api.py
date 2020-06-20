class ServerConfig:
    server_name: str
    public_baseurl: str


class SynapseHomeServer:
    config: ServerConfig


class SpamCheckerApi:
    hs: SynapseHomeServer
