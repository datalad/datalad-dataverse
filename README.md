# DataLad Dataverse extension

[![Build status](https://ci.appveyor.com/api/projects/status/fm24tes0vxlq7qis/branch/master?svg=true)](https://ci.appveyor.com/project/mih/datalad-dataverse/branch/master) [![codecov.io](https://codecov.io/github/datalad/datalad-dataverse/coverage.svg?branch=master)](https://codecov.io/github/datalad/datalad-dataverse?branch=master) [![crippled-filesystems](https://github.com/datalad/datalad-dataverse/workflows/crippled-filesystems/badge.svg)](https://github.com/datalad/datalad-dataverse/actions?query=workflow%3Acrippled-filesystems) [![docs](https://github.com/datalad/datalad-dataverse/workflows/docs/badge.svg)](https://github.com/datalad/datalad-dataverse/actions?query=workflow%3Adocs)


This repository contains an extension template that can serve as a starting point
for implementing a [DataLad](http://datalad.org) extension. An extension can
provide any number of additional DataLad commands that are automatically
included in DataLad's command line and Python API.

For a demo, clone this repository and install the demo extension via

    pip install -e .

DataLad will now expose a new command suite with a `hello...` command.

    % datalad --help |grep -B2 -A2 hello
    *Demo DataLad command suite*

      hello-cmd
          Short description of the command

To start implementing your own extension, [use this
template](https://github.com/datalad/datalad-extension-template/generate), and
adjust as necessary. A good approach is to

- Pick a name for the new extension.
- Look through the sources and replace `datalad_helloworld` with
  `datalad_<newname>` (hint: `git grep datalad_helloworld` should find all
  spots).
- Delete the example command implementation in `datalad_helloworld/__init__.py`
  by (re)moving the `HelloWorld` class.
- Implement a new command, and adjust the `command_suite` in
  `datalad_helloworld/__init__.py` to point to it.
- Replace `hello_cmd` with the name of the new command in
  `datalad_helloworld/tests/test_register.py` to automatically test whether the
  new extension installs correctly.
- Adjust the documentation in `docs/source/index.rst`. Refer to [`docs/README.md`](docs/README.md) for more information on documentation building, testing and publishing.
- Replace this README.
- Update `setup.cfg` with appropriate metadata on the new extension.

You can consider filling in the provided [.zenodo.json](.zenodo.json) file with
contributor information and [meta data](https://developers.zenodo.org/#representation)
to acknowledge contributors and describe the publication record that is created when
[you make your code citeable](https://guides.github.com/activities/citable-code/)
by archiving it using [zenodo.org](https://zenodo.org/). You may also want to
consider acknowledging contributors with the
[allcontributors bot](https://allcontributors.org/docs/en/bot/overview).


## Dataverse docker

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
in your case, `docker-compose` provides a `--file` and a `--env-file` parameter.

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
  want to check out `init-setup.sh`, `setup-dvs.sh`, `setup-users.sh` (see 
  also the aforementioned script in this repository here.)
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