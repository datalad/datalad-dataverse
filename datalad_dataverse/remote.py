import os
import re

from datalad.customremotes import SpecialRemote
from datalad.customremotes.main import main as super_main
from pyDataverse.api import DataAccessApi
from pyDataverse.models import Datafile
from requests import delete
from requests.auth import HTTPBasicAuth
from datalad_dataverse.utils import (
    get_native_api,
)


class DataverseRemote(SpecialRemote):

    def __init__(self, *args):
        super().__init__(*args)
        self.configs['url'] = 'The Dataverse URL for the remote'
        self.configs['doi'] = 'DOI to the dataset'
        self._doi = None
        self._url = None
        self._api = None

    def initremote(self):
        """
            Use this command to initialize a remote
            git annex initremote dv1 type=external externaltype=dataverse encryption=none
        """
        # check if instance is readable and authenticated
        resp = self.api.get_info_version()
        if resp.json()['status'] != 'OK':
            raise RuntimeError(f'Cannot connect to dataverse instance (status: {resp.json()["status"]})')

        # check if project with specified doi exists
        dv_ds = self.api.get_dataset(identifier=self.doi)
        if not dv_ds.ok:
            raise RuntimeError("Cannot find dataset")

    @property
    def url(self):
        if self._url is None:
            self._url = self.annex.getconfig('url')
            if self._url == '':
                raise ValueError('url must be specified')
            # remove trailing slash in URL
            elif self._url.endswith('/'):
                self._url = self._url[:-1]
        return self._url

    @property
    def doi(self):
        if self._doi is None:
            self._doi = self.annex.getconfig('doi')
            if self._doi == '':
                raise ValueError('doi must be specified')
            self._doi = _format_doi(self._doi)
        return self._doi

    @property
    def api(self):
        if self._api is None:
            # connect to dataverse instance
            self._api = get_native_api(
                baseurl=self.url,
                token=os.environ["DATAVERSE_API_TOKEN"],
            )
        return self._api

    def prepare(self):
        # trigger API instance in order to get possibly auth/connection errors
        # right away
        self.api

    def checkpresent(self, key):
        dataset = self.api.get_dataset(identifier=self.doi)

        datafiles = dataset.json()['data']['latestVersion']['files']
        if next((item for item in datafiles if item['label'] == key), None):
            return True
        else:
            return False

    def transfer_store(self, key, local_file):
        ds_pid = self.doi

        datafile = Datafile()
        datafile.set({'pid': ds_pid, 'filename': local_file, 'label': key})
        resp = self.api.upload_datafile(ds_pid, local_file, datafile.json())
        resp.raise_for_status()

    def transfer_retrieve(self, key, file):
        data_api = DataAccessApi(
            base_url=self.url,
            api_token=os.environ["DATAVERSE_API_TOKEN"]
        )
        dataset = self.api.get_dataset(identifier=self.doi)

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

        response = data_api.get_datafile(file_id)
        # http error handling
        response.raise_for_status()
        with open(file, "wb") as f:
            f.write(response.content)

    def remove(self, key):
        # get the dataset and a list of all files
        dataset = self.api.get_dataset(identifier=self.doi)
        # http error handling
        dataset.raise_for_status()
        files_list = dataset.json()['data']['latestVersion']['files']

        file_id = None

        # find the file we want to delete
        for file in files_list:
            filename = file['dataFile']['filename']
            if filename == key:
                file_id = file['dataFile']['id']
                break

        if file_id is None:
            # the key is not present, we can return, protocol
            # declare this condition to be a successful removal
            return

        # delete the file
        status = delete(f'{self.url}/dvn/api/data-deposit/v1.1/swordv2/edit-media/file/{file_id}',
                        auth=HTTPBasicAuth(os.environ["DATAVERSE_API_TOKEN"], ''))
        # http error handling
        status.raise_for_status()


def _format_doi(doi_in: str) -> str:
    """
    Converts unformatted DOI strings into the format needed in the dataverse API. Compatible with DOIs starting
    with "doi:", as URL or raw (i.e. 10.5072/FK2/WQCBX1).

    :param doi_in: unformatted doi string provided by user
    :returns: DOI string as needed for dataverse API, None if string is empty.
    """
    dataverse_doi_pattern = r'^doi:'
    if re.match(pattern=dataverse_doi_pattern, string=doi_in):
        return doi_in

    url_doi_pattern = r'^https?:\/\/doi\.org\/'
    if re.match(url_doi_pattern, doi_in):
        return re.sub(pattern=url_doi_pattern, repl='doi:', string=doi_in)

    return f'doi:{doi_in}'


def main():
    """cmdline entry point"""
    super_main(
        cls=DataverseRemote,
        remote_name='dataverse',
        description=\
        "transport file content to and from a Dataverse dataset",
)
