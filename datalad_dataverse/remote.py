from datalad.customremotes import SpecialRemote
from datalad.customremotes.main import main as super_main


class DataverseRemote(SpecialRemote):
    def initremote(self):
        raise

    def prepare(self):
        raise
        pass

    def checkpresent(self, key):
        raise
        pass

    def transfer_store(self, key, local_file):
        raise
        pass

    def transfer_retrieve(self, key, file):
        raise
        pass

    def remove(self, key):
        raise
        pass


def main():
    """cmdline entry point"""
    super_main(
        cls=DataverseRemote,
        remote_name='dataverse',
        description=\
        "transport file content to and from a Dataverse dataset",
)
