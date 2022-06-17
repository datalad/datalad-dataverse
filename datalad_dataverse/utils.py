from pyDataverse.api import NativeApi

# This cannot currently be queried for via public API. See gh-27
DATASET_SUBJECTS = [
 'Agricultural Sciences',
 'Arts and Humanities',
 'Astronomy and Astrophysics',
 'Business and Management',
 'Chemistry',
 'Computer and Information Science',
 'Earth and Environmental Sciences',
 'Engineering',
 'Law',
 'Mathematical Sciences',
 'Medicine, Health and Life Sciences',
 'Physics',
 'Social Sciences',
 'Other']


def get_native_api(baseurl, token):
    """
    Returns
    -------
    NativeApi
      The pyDataverse API wrapper
    """
    return NativeApi(baseurl, token)
