# Contributing to Datalad-Dateverse

These contributing guidelines have been adjusted from:
https://github.com/datalad/datalad/blob/master/CONTRIBUTING.md

## General
You are very welcome to help out developing this tool further.
You can contribute by:

- Creating an issue for bugs or tips for further development
- Making a pull request for any changes suggested by yourself
- Testing out the software and communicating your feedback to us

## How to contribute

The preferred way to contribute to this repository is to fork the [main branch
of this repository](https://github.com/datalad/datalad-dataverse) on GitHub.

Here we outline the workflow used by the developers:

- Clone this repository.
0. Have a clone of our main [main branch of this
   repository](https://github.com/datalad/datalad-dataverse) as `origin` remote
   in your git:

          git clone git@github.com:datalad/datalad-dataverse.git

1. Fork the [main branch of this
   repository](https://github.com/datalad/datalad-dataverse): click on the
   'Fork' button near the top of the page.  This creates a copy of the code base
   under your account on the GitHub server.

2. Add your forked clone as a remote to the local clone you already have on your
   local disk:

          git remote add gh-YourLogin git@github.com:YourLogin/datalad-dataverse.git
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

         ghremote git@github.com:YourLogin/datalad-dataverse.git

    to add the above `gh-YourLogin` remote.

3. Create a branch (generally off the `origin/main`) to hold your changes:

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

You can find our user documentation
[here](http://docs.datalad.org/projects/datalad-dataverse/en/latest/).

### Docstrings

We use [NumPy standard] for the description of parameters docstrings.  If you
are using PyCharm, set your project settings (`Tools` -> `Python integrated
tools` -> `Docstring format`).

[NumPy standard]: https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt#docstring-standard

In addition, we follow the guidelines of [Restructured Text] with the
additional features and treatments provided by [Sphinx].

[Restructured Text]: http://docutils.sourceforge.net/docs/user/rst/quickstart.html
[Sphinx]: http://www.sphinx-doc.org/en/stable/

Additional Hints
----------------

### Merge commits

For merge commits to have more informative description, add to your
`.git/config` or `~/.gitconfig` following section:

    [merge]
    log = true

and if conflicts occur, provide short summary on how they were resolved in
"Conflicts" listing within the merge commit (see
[example](https://github.com/datalad/datalad/commit/eb062a8009d160ae51929998771964738636dcc2)).

Quality Assurance
-----------------

It is recommended to check that your contribution complies with the following
rules before submitting a pull request:

- All public methods should have informative docstrings with sample usage
  presented as doctests when appropriate.
- All other tests pass when everything is rebuilt from scratch.
- New code should be accompanied by tests.

Tests can be executed with `pytest`. By default, all tests are performed against
the public https://demo.dataverse.org Dataverse deployment. In order to run the
tests, one needs to sign up for an account, and supply the API token for this
account via the `DATAVERSE_TEST_APITOKEN_TESTADMIN` environment variable, like so:

    DATAVERSE_TEST_APITOKEN_TESTADMIN=<token> python -m pytest -s -v

Alternatively, it is possible to run the tests against another dataverse deployment
by setting the `DATAVERSE_TEST_BASEURL` environment variable to its base URL.


Recognizing contributions
-------------------------

We welcome and recognize all contributions from documentation to testing to
code development.  You can see a list of current contributors in our [readme
file](https://github.com/datalad/datalad-dataverse/blob/main/README.md).  For
recognizing contributions, we use the **all-contributors bot**, which
isinstalled in this repository. You can simply ask the bot to add you as a
contributor in every issue or pull request with this format: `@all-contributors
please add @gitusername for contribution1 contribution2`

Example: `@all-contributors please add @adswa for projectManagement maintenance
code doc` See the [emoji key](https://allcontributors.org/docs/en/emoji-key)
for the different contributions.

Thank you!
----------

You're awesome. :wave::smiley:

If you want to dive deep into DataLad's features for aiding development, take a
look at https://github.com/datalad/datalad/blob/master/CONTRIBUTING.md
