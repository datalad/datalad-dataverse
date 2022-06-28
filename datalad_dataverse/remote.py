import os

from datalad.customremotes.main import main as super_main
from pyDataverse.api import DataAccessApi
from pyDataverse.models import Datafile
from requests import delete
from requests.auth import HTTPBasicAuth
from annexremote import ExportRemote
from datalad.support.annexrepo import AnnexRepo

from datalad_next.credman import CredentialManager
from datalad_next.utils import update_specialremote_credential

from datalad_dataverse.utils import (
    get_native_api,
    format_doi,
)
import os
import re


from datalad.customremotes import SpecialRemote

class DataverseRemote(ExportRemote, SpecialRemote):

    def __init__(self, *args):
        super().__init__(*args)
        self.configs['url'] = 'The Dataverse URL for the remote'
        self.configs['doi'] = 'DOI to the dataset'
        self.configs['dlacredential'] = \
            'Identifier used to retrieve an API token from a local ' \
            'credential store'
        self.configs['version'] = 'Dataverse dataset version'
        self._doi = None
        self._url = None
        self._api = None
        self._token = None
        self._dataset_version = None

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
            self._doi = format_doi(self._doi)
        return self._doi

    @property
    def api(self):
        if self._api is None:
            # we know that we will need a token
            repo = AnnexRepo(self.annex.getgitdir())
            # TODO the below is almost literally taken from
            # the datalad-annex:: implementation in datalad-next
            # this could become a comming helper
            credman = CredentialManager(repo.config)
            credential_name = self.annex.getconfig('dlacredential')
            credential_realm = self.url.rstrip('/') + '/dataverse'
            cred = None
            if credential_name:
                # we can ask blindly first, caller seems to know what to do
                cred = credman.get(
                    name=credential_name,
                    # give to make legacy credentials accessible
                    _type_hint='token',
                )
            if not cred:
                creds = credman.query(
                    _sortby='last-used',
                    realm=credential_realm,
                )
                if creds:
                    credential_name, cred = creds[0]
            if not cred:
                # credential query failed too, enable manual entry
                cred = credman.get(
                    # this might still be None
                    name=credential_name,
                    _type_hint='token',
                    _prompt=f'A dataverse API token is required for access',
                    # inject anything we already know to make sure we store it
                    # at the very end, and can use it for discovery next time
                    realm=credential_realm,
                )
            if not 'secret' in cred:
                self.message('No token available', type='error')

            # connect to dataverse instance
            api = get_native_api(
                baseurl=self.url,
                token=cred['secret'],
            )
            # make one cheap request to ensure that the token is
            # in-principle working -- we won't be able to verify all necessary
            # permissions for all possible operations anyways
            api.get_info_version()

            update_specialremote_credential(
                'dataverse',
                credman,
                credential_name,
                cred,
                credtype_hint='token',
                duplicate_hint=
                'Specify a credential name via the dlacredential= '
                'special remote parameter, and/or configure a credential '
                'with the datalad-credentials command{}'.format(
                    f' with a `realm={cred["realm"]}` property'
                    if 'realm' in cred else ''),
            )
            # store for reuse with data access API
            self._token = cred['secret']
            self._api = api

        return self._api

    @property
    def dataset_version(self):
        if self._dataset_version is None:
            self._dataset_version = self.annex.getconfig('version')
            if len(self._dataset_version) == 0:
                self._dataset_version = ":latest"
        return self._dataset_version

    def prepare(self):
        # trigger API instance in order to get possibly auth/connection errors
        # right away
        self.api

    def checkpresent(self, key):
        dataset = self.api.get_dataset(identifier=self.doi)

        datafiles = dataset.json()['data']['latestVersion']['files']
        if next((item for item in datafiles if item['dataFile']['filename'] == key), None):
            return True
        else:
            return False

    def checkpresentexport(self, key, remote_file):
        return self.checkpresent(key=remote_file)

    def transfer_store(self, key, local_file, datafile=None):
        if not self.dataset_version == ':latest':
            raise RuntimeError('Cannot store files if a specific version is checked out!')
        ds_pid = self.doi
        if datafile is None:
            datafile = Datafile()
            datafile.set({'filename': key, 'label': key})
        datafile.set({'pid': ds_pid})
        
        resp = self.api.upload_datafile(identifier=ds_pid, filename=local_file, json_str=datafile.json())
        resp.raise_for_status()

    def transferexport_store(self, key, local_file, remote_file):
        remote_dir = os.path.dirname(remote_file)
        if re.search(pattern='[^a-z0-9_\-.\\/\ ]', string=remote_dir, flags=re.ASCII | re.IGNORECASE):
            self.annex.error(f"Invalid character in directory name of {remote_file}."
                             f"Valid characters are a-Z, 0-9, '_', '-', '.', '\\', '/' and ' ' (white space).")

        datafile = Datafile()
        datafile.set({'filename': remote_file,
                      'directoryLabel': remote_dir,
                      'label': os.path.basename(remote_file)})
        self.transfer_store(key=remote_file, local_file=local_file, datafile=datafile)

    def transfer_retrieve(self, key, file):
        data_api = DataAccessApi(
            base_url=self.url,
            # this relies on having established the NativeApi in prepare()
            api_token=self._token,
        )
        dataset = self.api.get_dataset_version(identifier=self.doi, version=self.dataset_version)

        # http error handling
        dataset.raise_for_status()

        files_list = dataset.json()['data']['files']

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

    def transferexport_retrieve(self, key, local_file, remote_file):
        self.transfer_retrieve(key=remote_file, file=local_file)

    def remove(self, key):
        if not self.dataset_version == ':latest':
            raise RuntimeError('Cannot remove file if a specific version is checked out!')
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
        status = delete(
            f'{self.url}/dvn/api/data-deposit/v1.1/swordv2/'
            f'edit-media/file/{file_id}',
            # this relies on having established the NativeApi in prepare()
            auth=HTTPBasicAuth(self._token, ''))
        # http error handling
        status.raise_for_status()
    
    def removeexport(self, key, remote_file):
        return self.remove(key=remote_file)


def main():
    """cmdline entry point"""
    super_main(
        cls=DataverseRemote,
        remote_name='dataverse',
        description=\
        "transport file content to and from a Dataverse dataset",
)
