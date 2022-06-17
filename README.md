# DataLad Dataverse extension
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-3-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

[![Build status](https://ci.appveyor.com/api/projects/status/fm24tes0vxlq7qis/branch/master?svg=true)](https://ci.appveyor.com/project/mih/datalad-dataverse/branch/master) [![codecov.io](https://codecov.io/github/datalad/datalad-dataverse/coverage.svg?branch=master)](https://codecov.io/github/datalad/datalad-dataverse?branch=master) [![crippled-filesystems](https://github.com/datalad/datalad-dataverse/workflows/crippled-filesystems/badge.svg)](https://github.com/datalad/datalad-dataverse/actions?query=workflow%3Acrippled-filesystems) [![docs](https://github.com/datalad/datalad-dataverse/workflows/docs/badge.svg)](https://github.com/datalad/datalad-dataverse/actions?query=workflow%3Adocs)


Welcome to the DataLad-Dataverse project of the OHBM 2022 Brainhack!

What do we want to do during this Brainhack?
[Dataverse](https://dataverse.org) is open source research data repository software that is deployed all over the world in data or metadata repositories.
It supports sharing, preserving, citing, exploring, and analyzing research data with descriptive metadata, and thus contributes greatly to open, reproducible, and FAIR science.
[DataLad](https://www.datalad.org), on the other hand, is a data management and data publication tool build on Git and git-annex.
Its core data structure, DataLad datasets, can version control files of any size, and streamline data sharing, updating, and collaboration.
In this hackathon project, we aim to make DataLad interoperable with Dataverse to support dataset transport from and to Dataverse instances.
To this end, we will build a new DataLad extension datalad-dataverse, and would be delighted to welcome you onboard of the contributor team.

SKILLS

We plan to start from zero with this project, and welcome all kinds of contributions from various skills at any level.
From setting up and writing documentation, discussing relevant functionality, or user-experience-testing, to Python-based implementation of the desired functionality and creating real-world use cases and workflows.
Here is a non-exhaustive list of skills that can be beneficial in this project:
- You have used a Dataverse instance before and/or have access to one, or you are interested in using one in the future
- You know technical details about Dataverse, such as its API, or would have fun finding out about them
- You know Python
- You have experience with the Unix command line
- You are interested in creating accessible documentation
- You are interested in learning about the DataLad ecosystem or the process of creating a DataLad extension
- Your secret hobby is Git plumbing
- You know git-annex, and/or about its backends
- You want to help create metadata extractors for Dataverse to generate dataset metadata automatically


## Getting started

Great that you're joining us in this project! Here's a list of things that can help you to prepare or to get started:

- Create a GitHub account. Ideally, set up SSH keys following [the Github docs](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account).
- Clone this repository. If you haven't, install Git first [the Traintrack installation instructions](https://psy6983.brainhackmtl.org/modules/installation/) can help with this.

```
git clone git@github.com:datalad/datalad-dataverse.git
```
- Install DataLad and its dependencies. The [DataLad Handbook](http://handbook.datalad.org/en/latest/intro/installation.html#install) has installation instructions for your operating system.
- Set up a Python environment. This project is written in Python, and creating a Python development environment is the best preparation to get started right away. There are a multitude of ways in which one can set up a virtual environment, and some might fit better to your operating system or to the software you already have installed. The brainhack [traintrack corner](https://psy6983.brainhackmtl.org/modules/installation) can show you how to do it with Miniconda. Below, you'll find code snippets how the DataLad team usually creates their development environment.

```
# create a virtual environment (for Linux/MacOS)
virtualenv --python=python3 ~/env/hacking
# activate the virtual environment
source ~/env/hacking/bin/activate
# install datalad-dataverse in its development version
cd datalad-dataverse
pip install -e .
pip install -r requirements-devel.txt
```
- Take a look at the section "Dataverse docker for running tests" to learn how to spin up your own dataverse instance (if you are on a Linux computer or Mac). Alternatively or in addition, checkout [demo.dataverse.org](https://demo.dataverse.org), a free dataverse installation for testing purposes that you can register, sign-up, and play in.
- Check out the [Dataverse Documentation](https://guides.dataverse.org/en/latest) for an overview of the software, and likewise, the [DataLad docs](http://docs.datalad.org/en/stable/). A few specialized dataverse doc links that may be of particular relevance are [this section of the API guide](https://guides.dataverse.org/en/5.10.1/api/intro.html#developers-of-integrations-external-tools-and-apps), which is about third party integrations. Among other things, it mentions https://pydataverse.readthedocs.io/en/latest, a Python library to access the Dataverse API’s and manipulating and using the Dataverse (meta)data - Dataverses, Datasets, Datafiles (it will likely become this extensions backend). For metadata, there also is [this guide](https://guides.dataverse.org/en/latest/admin/metadatacustomization.html).
- In order to **build the documentation**, you should be able to run `make -C docs html` from the root of the repository. ``make -C docs clean`` wipes created documentation again, and might be necessary for a rebuild sometimes
- In order to **run unit tests**, you should be able to run ``python -m pytest <path to test>``, for example ``python -m pytest datalad_dataverse/tests/test_register.py`` 

## Contact

The virtual lead for this project (time zone: EMEA) is @bpoldrack.
The on-site lead for this project (time zone: Glasgow) is @adswa.
The best way to reach us is by tagging us in issues or pull requests.
You can find us and our voice channel [on Discord](https://discord.com/invite/qUzW56dZT2).


## Dataverse docker for running tests

The [dataverse-docker](https://github.com/IQSS/dataverse-docker) repository 
provides everything needed to run dataverse in a container. The continuous 
integration test build is based on that. The setup script used for the 
respective AppVeyor build is under `tools/ci/setup_docker_dataverse`.

You can use this docker setup locally on your machine, too, provided it's 
running Linux and you have `docker` and `docker-compose` installed. All 
involved scripts (from our end as well as the dataverse-docker repo) are 
completely ignorant of Windows.
The basic setup is this:

    git clone https://github.com/IQSS/dataverse-docker
    cd dataverse-docker
    export traefikhost=localhost
    docker network create traefik
    cp .env_sample .env

If you want to customize your setup, you may want to edit this `.env` file.
Note, that the following call to `docker-compose` relies on being in the 
directory of the docker-compose file and that `.env`. If that's not suitable 
in your case, `docker-compose` provides a `--file` and a `--env-file` 
parameter to pass their paths to.
Note, however, that even if you call it with those parameters from the 
outside, the several specified paths in both files refer to their base 
directory (the cloned repo's root) and more configs underneath it. Hence, 
residual directories `minio-data` and `database-data` are still created within
the repository.

    docker-compose up -d

This should give you a running server at `http://localhost:8080`. Note, that 
it may take a moment for the server to come up. If you go to that address in 
a browser you should be abe to log in as `dataverseAdmin` with password 
`admin` (which you will instantly be required to change). This allows to 
create dataverses, datasets, files, etc. An API token for that user is to be 
found under that user's menu (upper right).

Apart from the webinterface, you should be able to send some basic requests:

    $> curl "http://localhost:8080/api/search?q=data"
    {"status":"OK","data":{"q":"data","total_count":0,"start":0,"spelling_alternatives":{},"items":[],"count_in_response":0}}
    $> curl "http://localhost:8080/api/dataverses/root/contents"                                                                                                                   
    {"status":"ERROR","message":"User :guest is not permitted to perform requested action."}                                                                                            

With the token the latter response would change if you authenticate that way:

    $> curl -H X-Dataverse-key:<TOKEN> "http://localhost:8080/api/dataverses/root/contents"
    {"status":"OK","data":[{"type":"dataverse","id":2,"title":"Dataverse Admin Dataverse"}]}

Several additional notes:

- The initial `docker-compose` call could give an error message if you 
  already have an active port mapping. However, this does not necessarily 
  mean you need to change. It may work just fine. Try despite such an error 
  message.
- This is only the most basic setup. Within the container there are a bunch 
  of setup scripts to initialize the demo version. If you get into the 
  container, you can find them in HOME (`/opt/payara/dvinstall`). You may 
  want to check out `setup-users.sh` and `setup-dvs.sh` to see some basic 
  API requests setting up users and dataverses. `setup-dvs.sh` doesn't 
  actually run, though, since `setup-users.sh` doesn't assign `pete` the 
  required permissions. That piece seems to be missing.
- The dataverse-docker repo comes with a bunch of docker-compose recipes. We 
  currently use just the default.
- If you run this locally and need to start over for some reason, note that 
  there is some persistent files that would need to be wiped out, too. They 
  are generated during the setup described earlier. A `git status` or 
  `datalad status` should show you the `.env` file and a `minio-data/` 
  directory as untracked. However, there's one more: `database-data/`. That 
  one is readable only by `root`, hence a regular user's `git status` 
  doesn't show it. A `sudo git status` would confirm, that this is untracked,
  too.
- If you need to wipe out your local instance and you don't have any other 
  docker images, then this command may be useful for you:
    `for i in $(docker ps -qa); do docker stop $i && docker rm $i; done;`
  It stops all containers and removes them, so you get back to where you 
  started. If you only want currently running containers to be affected, 
  leave out the `a` option to `docker ps`. If you have other containers 
  running, I assume you know how to deal with that anyway.
  Don't forget to `rm` everything untracked in `dataverse-docker`. If you 
  followed those instructions, this would be `.env` and the two directories 
  `minio-data` and `database-data`. The latter is only readable by root, so 
  you'll need `sudo` for `rm`'ing it as well as to see it reported untracked 
  by `git status`.

The CI setup results in two users and a root dataverse being created. A 
superuser 'testadmin' and a regular user 'user1'. Their API tokens are 
acccessible for the tests via the environment variables `TESTS_TOKEN_TESTADMIN`
and `TESTS_TOKEN_USER1` respectively.
If you want to see how that is done, so you can reproduce it locally check 
`setup_docker_dataverse.sh` for how it calls `docker cp` to 
copy several JSON files and `init_dataverse.sh` into the container and then 
executes the latter. Both scripts and the JSONs are here in the repository 
under `tools/ci`.

## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="https://github.com/likeajumprope"><img src="https://avatars.githubusercontent.com/u/23728822?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Johanna Bayer</b></sub></a><br /><a href="https://github.com/datalad/datalad-dataverse/commits?author=likeajumprope" title="Documentation">📖</a></td>
    <td align="center"><a href="https://github.com/nadinespy"><img src="https://avatars.githubusercontent.com/u/46372572?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Nadine Spychala</b></sub></a><br /><a href="#infra-nadinespy" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a></td>
    <td align="center"><a href="http://www.adina-wagner.com"><img src="https://avatars.githubusercontent.com/u/29738718?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Adina Wagner</b></sub></a><br /><a href="https://github.com/datalad/datalad-dataverse/commits?author=adswa" title="Code">💻</a> <a href="#ideas-adswa" title="Ideas, Planning, & Feedback">🤔</a> <a href="#infra-adswa" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="https://github.com/datalad/datalad-dataverse/commits?author=adswa" title="Documentation">📖</a> <a href="#maintenance-adswa" title="Maintenance">🚧</a> <a href="https://github.com/datalad/datalad-dataverse/pulls?q=is%3Apr+reviewed-by%3Aadswa" title="Reviewed Pull Requests">👀</a> <a href="#tool-adswa" title="Tools">🔧</a></td>
  </tr>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!