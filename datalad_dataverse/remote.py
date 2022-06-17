from datalad.customremotes import SpecialRemote
from datalad.customremotes.main import main as super_main
from pyDataverse.api import NativeApi
import os
from requests import delete
from requests.auth import HTTPBasicAuth


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
         # connect to dataverse instance
        api = NativeApi(base_url=self.annex.getconfig('url'),
                        api_token=os.environ["DATAVERSE_API_TOKEN"])
        
        # get the dataset and a list of all files
        dataset = api.get_dataset(identifier=self.annex.getconfig('doi'))
        files_list = dataset.json()['data']['latestVersion']['files']

        file_id = None

        # find the file we want to delete
        for file in files_list:
            filename = file['dataFile']['filename']
            if filename == key:
                file_id = file['dataFile']['id']
                break
        
        if file_id is None:
            # todo: What to do if the file is not present?
            raise
        
        # delete the file
        delete(f'{self.annex.getconfig("url")}/dvn/api/data-deposit/v1.1/swordv2/edit-media/file/4', 
               auth=HTTPBasicAuth(os.environ["DATAVERSE_API_TOKEN"], ''))
        # todo error handling?


def main():
    """cmdline entry point"""
    super_main(
        cls=DataverseRemote,
        remote_name='dataverse',
        description=\
        "transport file content to and from a Dataverse dataset",
)
