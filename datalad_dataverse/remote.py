from datalad.customremotes import SpecialRemote
from datalad.customremotes.main import main as super_main
from pyDataverse.api import NativeApi, DataAccessApi
from pyDataverse.models import Datafile
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
        api = NativeApi(base_url=self.annex.getconfig('url'),
                        api_token=os.environ["DATAVERSE_API_TOKEN"])
        data_api = DataAccessApi(base_url=self.annes.getconfig('url'),
                        api_token=os.environ["DATAVERSE_API_TOKEN"])
        dataset = api.get_dataset(identifier=self.annex.getconfig('doi'))

        # http error handling
        dataset.raise_for_status()

        files_list = dataset.json()['data']['latestVersion']['files']

        # find the file we want to download
        file_id = None
        for current_file in files_list:
            filename = current_file['dataFile']['filename']
            if filename == key:
                file_id = current_file['dataFile']['id']
                break
        
        # error handling if file was not found on remote
        if file_id is None:
            raise ValueError(f"File {key} is unknown to remote")
        
        response = data_api.get_datafile(key)
        # http error handling
        response.raise_for_status()
        with open(file, "wb") as f:
            f.write(response.content)

        

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
