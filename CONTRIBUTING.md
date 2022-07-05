# Contributing to Datalad-Dateverse

These contributing guidelines have been adjusted from: https://github.com/datalad/datalad/blob/master/CONTRIBUTING.md

## General
You are very welcome to help out developing this tool further. You can contribute by:

- Creating an issue for bugs or tips for further development
- Making a pull request for any changes suggested by yourself
- Testing out the software and communicating your feedback to us

## How to contribute

The preferred way to contribute to this repository is
to fork the [main branch of this repository](https://github.com/datalad/datalad-dataverse) on GitHub.

Here we outline the workflow used by the developers:

- Clone this repository.
0. Have a clone of our main [main branch of this repository](https://github.com/datalad/datalad-dataverse) as `origin`
   remote in your git:

          git clone git@github.com:datalad/datalad-dataverse.git

1. Fork the [main branch of this repository](https://github.com/datalad/datalad-dataverse): click on the 'Fork'
   button near the top of the page.  This creates a copy of the code
   base under your account on the GitHub server.

2. Add your forked clone as a remote to the local clone you already have on your
   local disk:

          git remote add gh-YourLogin git@github.com:YourLogin/datalad/datalad-dataverse.git
          git fetch gh-YourLogin

    To ease addition of other github repositories as remotes, here is
    a little bash function/script to add to your `~/.bashrc`:

        ghremote () {
                url="$1"
                proj=${url##*/}
                url_=${url%/*}
                login=${url_##*/}
                git remote add gh-$login $url
                git fetch gh-$login
        }

    thus you could simply run:

         ghremote git@github.com:YourLogin/datalad/datalad-dataverse.git

    to add the above `gh-YourLogin` remote.  Additional handy aliases
    such as `ghpr` (to fetch existing pr from someone's remote) and
    `ghsendpr` could be found at [yarikoptic's bash config file](http://git.onerussian.com/?p=etc/bash.git;a=blob;f=.bash/bashrc/30_aliases_sh;hb=HEAD#l865)

3. Create a branch (generally off the `origin/master`) to hold your changes:

          git checkout -b nf-my-feature

    and start making changes. Ideally, use a prefix signaling the purpose of the
    branch
    - `nf-` for new features
    - `bf-` for bug fixes
    - `rf-` for refactoring
    - `doc-` for documentation contributions (including in the code docstrings).
    - `bm-` for changes to benchmarks
    We recommend to **not** work in the ``main`` branch!

4. Work on this copy on your computer using Git to do the version control. When
   you're done editing, do:

          git add modified_files
          git commit

   to record your changes in Git.  Ideally, prefix your commit messages with the
   `NF`, `BF`, `RF`, `DOC`, `BM` similar to the branch name prefixes, but you could
   also use `TST` for commits concerned solely with tests, and `BK` to signal
   that the commit causes a breakage (e.g. of tests) at that point.  Multiple
   entries could be listed joined with a `+` (e.g. `rf+doc-`).  See `git log` for
   examples.  If a commit closes an existing DataLad issue, then add to the end
   of the message `(Closes #ISSUE_NUMER)`

5. Push to GitHub with:

          git push -u gh-YourLogin nf-my-feature

   Finally, go to the web page of your fork of the DataLad repo, and click
   'Pull request' (PR) to send your changes to the maintainers for review. This
   will send an email to the committers.  You can commit new changes to this branch
   and keep pushing to your remote -- github automagically adds them to your
   previously opened PR.

(If any of the above seems like magic to you, then look up the
[Git documentation](http://git-scm.com/documentation) on the web.)

Documentation
-------------
You can find our user documentation [here](http://docs.datalad.org/projects/datalad-dataverse/en/latest/).

### Docstrings

We use [NumPy standard] for the description of parameters docstrings.  If you are using
PyCharm, set your project settings (`Tools` -> `Python integrated tools` -> `Docstring format`).

[NumPy standard]: https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt#docstring-standard

In addition, we follow the guidelines of [Restructured Text] with the additional features and treatments
provided by [Sphinx].

[Restructured Text]: http://docutils.sourceforge.net/docs/user/rst/quickstart.html
[Sphinx]: http://www.sphinx-doc.org/en/stable/

Additional Hints
----------------

### Merge commits

For merge commits to have more informative description, add to your
`.git/config` or `~/.gitconfig` following section:

    [merge]
    log = true

and if conflicts occur, provide short summary on how they were resolved
in "Conflicts" listing within the merge commit
(see [example](https://github.com/datalad/datalad/commit/eb062a8009d160ae51929998771964738636dcc2)).

Quality Assurance
-----------------

It is recommended to check that your contribution complies with the following
rules before submitting a pull request:

- All public methods should have informative docstrings with sample usage
  presented as doctests when appropriate.
- All other tests pass when everything is rebuilt from scratch.
- New code should be accompanied by tests.


Recognizing contributions
-------------------------

We welcome and recognize all contributions from documentation to testing to code development.
You can see a list of current contributors in our [readme file](https://github.com/datalad/datalad-dataverse/blob/main/README.md).
For recognizing contributions, we use the **all-contributors bot**, which isinstalled in this repository. You can simply ask the bot
to add you as a contributor in every issue or pull request with this format:
`@all-contributors please add @gitusername for contribution1 contribution2`

Example: `@all-contributors please add @adswa for projectManagement maintenance code doc`
See the [emoji key](https://allcontributors.org/docs/en/emoji-key) for the different contributions.

Thank you!
----------

You're awesome. :wave::smiley:

Various hints for developers
----------------------------

### Useful tools

- While performing IO/net heavy operations use [dstat](http://dag.wieers.com/home-made/dstat)
  for quick logging of various health stats in a separate terminal window:
  
        dstat -c --top-cpu -d --top-bio --top-latency --net

- To monitor speed of any data pipelining [pv](http://www.ivarch.com/programs/pv.shtml) is really handy,
  just plug it in the middle of your pipe.

- For remote debugging epdb could be used (avail in pip) by using
  `import epdb; epdb.serve()` in Python code and then connecting to it with
  `python -c "import epdb; epdb.connect()".`

- We are using codecov which has extensions for the popular browsers
  (Firefox, Chrome) which annotates pull requests on github regarding changed coverage.

### Useful Environment Variables
Refer datalad/config.py for information on how to add these environment variables to the config file and their naming convention

- *DATALAD_DATASETS_TOPURL*:
  Used to point to an alternative location for `///` dataset. If running
  tests preferred to be set to http://datasets-tests.datalad.org
- *DATALAD_LOG_LEVEL*:
  Used for control the verbosity of logs printed to stdout while running datalad commands/debugging
- *DATALAD_LOG_CMD_OUTPUTS*:
  Used to control either both stdout and stderr of external commands execution are logged in detail (at DEBUG level)
- *DATALAD_LOG_CMD_ENV*:
  If contains a digit (e.g. 1), would log entire environment passed into
  the Runner.run's popen call.  Otherwise could be a comma separated list
  of environment variables to log
- *DATALAD_LOG_CMD_STDIN*:
  Whether to log stdin for the command
- *DATALAD_LOG_CMD_CWD*:
  Whether to log cwd where command to be executed
- *DATALAD_LOG_PID*
  To instruct datalad to log PID of the process
- *DATALAD_LOG_TARGET*
  Where to log: `stderr` (default), `stdout`, or another filename
- *DATALAD_LOG_TIMESTAMP*:
  Used to add timestamp to datalad logs
- *DATALAD_LOG_TRACEBACK*:
  Runs TraceBack function with collide set to True, if this flag is set to 'collide'.
  This replaces any common prefix between current traceback log and previous invocation with "..."
- *DATALAD_LOG_VMEM*:
  Reports memory utilization (resident/virtual) at every log line, needs `psutil` module
- *DATALAD_EXC_STR_TBLIMIT*: 
  This flag is used by the datalad extract_tb function which extracts and formats stack-traces.
  It caps the number of lines to DATALAD_EXC_STR_TBLIMIT of pre-processed entries from traceback.
- *DATALAD_SEED*:
  To seed Python's `random` RNG, which will also be used for generation of dataset UUIDs to make
  those random values reproducible.  You might want also to set all the relevant git config variables
  like we do in one of the travis runs
- *DATALAD_TESTS_TEMP_KEEP*: 
  Function rmtemp will not remove temporary file/directory created for testing if this flag is set
- *DATALAD_TESTS_TEMP_DIR*: 
  Create a temporary directory at location specified by this flag.
  It is used by tests to create a temporary git directory while testing git annex archives etc
- *DATALAD_TESTS_NONETWORK*: 
  Skips network tests completely if this flag is set
  Examples include test for s3, git_repositories, openfmri etc
- *DATALAD_TESTS_SSH*: 
  Skips SSH tests if this flag is **not** set
- *DATALAD_TESTS_NOTEARDOWN*: 
  Does not execute teardown_package which cleans up temp files and directories created by tests if this flag is set
- *DATALAD_TESTS_USECASSETTE*:
  Specifies the location of the file to record network transactions by the VCR module.
  Currently used by when testing custom special remotes
- *DATALAD_TESTS_OBSCURE_PREFIX*:
  A string to prefix the most obscure (but supported by the filesystem test filename
- *DATALAD_TESTS_PROTOCOLREMOTE*:
  Binary flag to specify whether to test protocol interactions of custom remote with annex
- *DATALAD_TESTS_RUNCMDLINE*:
  Binary flag to specify if shell testing using shunit2 to be carried out
- *DATALAD_TESTS_TEMP_FS*:
  Specify the temporary file system to use as loop device for testing DATALAD_TESTS_TEMP_DIR creation
- *DATALAD_TESTS_TEMP_FSSIZE*:
  Specify the size of temporary file system to use as loop device for testing DATALAD_TESTS_TEMP_DIR creation
- *DATALAD_TESTS_NONLO*:
  Specifies network interfaces to bring down/up for testing. Currently used by travis.
- *DATALAD_CMD_PROTOCOL*: 
  Specifies the protocol number used by the Runner to note shell command or python function call times and allows for dry runs. 
  'externals-time' for ExecutionTimeExternalsProtocol, 'time' for ExecutionTimeProtocol and 'null' for NullProtocol.
  Any new DATALAD_CMD_PROTOCOL has to implement datalad.support.protocol.ProtocolInterface
- *DATALAD_CMD_PROTOCOL_PREFIX*: 
  Sets a prefix to add before the command call times are noted by DATALAD_CMD_PROTOCOL.
- *DATALAD_USE_DEFAULT_GIT*:
  Instructs to use `git` as available in current environment, and not the one which possibly comes with git-annex (default behavior).
- *DATALAD_ASSERT_NO_OPEN_FILES*:
  Instructs test helpers to check for open files at the end of a test. If set, remaining open files are logged at ERROR level. Alternative modes are: "assert" (raise AssertionError if any open file is found), "pdb"/"epdb" (drop into debugger when open files are found, info on files is provided in a "files" dictionary, mapping filenames to psutil process objects).
- *DATALAD_ALLOW_FAIL*:
  Instructs `@never_fail` decorator to allow to fail, e.g. to ease debugging.

## Getting started

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
acccessible for the tests via the environment variables
`DATAVERSE_TEST_APITOKEN_TESTADMIN` and `DATAVERSE_TEST_APITOKEN_USER1` respectively.
If you want to see how that is done, so you can reproduce it locally check 
`setup_docker_dataverse.sh` for how it calls `docker cp` to 
copy several JSON files and `init_dataverse.sh` into the container and then 
executes the latter. Both scripts and the JSONs are here in the repository 
under `tools/ci`.





