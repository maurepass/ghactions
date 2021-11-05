# encoding: utf-8

from fabric.utils import _AttributeDict


class BaseConfig(object):
    def __init__(self):
        self.env = _AttributeDict()

        self.env.git_server = "git@github.com"
        self.env.git_repo = "maurepass/ghactions"
        self.env.git_branch = "main"

        self.env.project_dir = "ghactions"
        self.env.project_name = "ghactions"
        self.env.settings = "ghactions.settings"

        self.env.path = "%s" % self.env.project_dir
        self.env.forward_agent = True
        # You might want to add to your .bashrc ssh-add ~/.ssh/id_rsa
        # to make use of the forward_agent
        self.env.use_ssh_config = False
        self.env.pip_version = "21.3.1"
        self.env.virtualenv_path = "~/venv"
        self.env.virtualenv_args = "--python=python3"
        self.env.project_path = self.env.project_name
        self.env.requirements_file = "requirements.txt"
        self.env.pip_args = ""
        self.env.skip_dbbackup = True

        self.collectstatic_excluded = []
        self.env.excluded_files = self.get_excluded_files()


    def init_roles(self):
        """by default all hosts have all roles"""
        self.env.roledefs = {
            "webserver": self.env.hosts,
        }

    def get_excluded_files(self):
        return " ".join("--ignore=%s" % rule for rule in self.collectstatic_excluded)


class StageConfig(BaseConfig):
    def __init__(self):
        super(StageConfig, self).__init__()
        self.env.settings = "ghactions.settings"
        self.env.hosts = ["ghactions_stage@ghactions.deployed.space:2222"]
        self.env.envname = "stage"
        self.env.roledefs = {
            "webserver": self.env.hosts,
        }
        self.env.vhost = "ghactions.deployed.space"
        self.env.requirements_file = "requirements.txt"


class ProdConfig(BaseConfig):
    pass
    # def __init__(self):
    #     super(ProdConfig, self).__init__()
    #     self.env.settings = "riskity.settings.prod"
    #     self.env.hosts = ["medici_prod@geocoding.medicifac.com:2222"]
    #     self.env.envname = "prod"
    #     self.env.roledefs = {
    #         "webserver": self.env.hosts,
    #         "worker": self.env.hosts,
    #         "extra": self.env.hosts
    #     }
    #     self.env.vhost = "medici-prod.deployed.pl"
    #     self.env.requirements_file = "requirements_prod.txt"


CONFIG_MAP = {
    "stage": StageConfig,
    "prod": ProdConfig
}
