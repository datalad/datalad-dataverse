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

          git checkout -b my-feature

4. Work on this copy on your computer using Git to do the version control. When
   you're done editing, do:

          git add modified_files
          git commit

   to record your changes in Git. If a commit closes an existing DataLad issue,
   then add to the end of the message `(Closes #ISSUE_NUMER)`

5. Push to GitHub with:

          git push -u gh-YourLogin my-feature

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

If you want to dive deep into DataLad's features for aiding development, take a look at 
https://github.com/datalad/datalad/blob/master/CONTRIBUTING.md




Appendix: Dataverse docker for running tests
--------------------------------------------

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

Notes:

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
