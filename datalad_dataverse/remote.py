from datalad.customremotes import SpecialRemote
from datalad.customremotes.main import main as super_main
from pyDataverse.api import NativeApi
from pyDataverse.models import Datafile
import os


class DataverseRemote(SpecialRemote):

    def __init__(self, *args):
        super().__init__(*args)
        self.configs['url'] = 'The Dataverse URL for the remote'
        self.configs['doi'] = 'DOI to the dataset'

    def initremote(self):
        """
            Use this command to initialize a remote
            git annex initremote dv1 type=external externaltype=dataverse encryption=none
        """
        if self.annex.getconfig('url') is None or self.annex.getconfig('doi') is None:
            raise ValueError('url and doi must be specified')

        # connect to dataverse instance
        api = NativeApi(base_url=self.annex.getconfig('url'),
                        api_token=os.environ["DATAVERSE_API_TOKEN"])

        # check if instance is readable and authenticated
        resp = api.get_info_version()
        if resp.json()['status'] != 'OK':
            raise RuntimeError(f'Cannot connect to dataverse instance (status: {resp.json()["status"]})')

        # check if project with specified doi exists
        dv_ds = api.get_dataset(identifier=self.annex.getconfig('doi'))
        if not dv_ds.ok:
            raise RuntimeError("Cannot find dataset")

    def prepare(self):
        pass

    def checkpresent(self, key):
        api = NativeApi(self.annex.getconfig('url'), os.environ.get('DATAVERSE_API_TOKEN', None))
        dataset = api.get_dataset(identifier=self.annex.getconfig('doi'))

        datafiles = dataset.json()['data']['latestVersion']['files']
        if next((item for item in datafiles if item['label'] == key), None):
            return True
        else:
            return False

    def transfer_store(self, key, local_file):
        api = NativeApi(self.annex.getconfig('url'), os.environ.get('DATAVERSE_API_TOKEN', None))
        ds_pid = self.annex.getconfig('doi')

        datafile = Datafile()
        datafile.set({'pid': ds_pid, 'filename': local_file})
        resp = api.upload_datafile(ds_pid, local_file, datafile.json())
        resp.raise_for_status()

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
