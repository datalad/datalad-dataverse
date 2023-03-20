# DataLad extension for working Dataverse

[![Build status](https://ci.appveyor.com/api/projects/status/fm24tes0vxlq7qis/branch/main?svg=true)](https://ci.appveyor.com/project/mih/datalad-dataverse/branch/main)
[![codecov](https://codecov.io/gh/datalad/datalad-dataverse/branch/main/graph/badge.svg?token=cPUPplOH3o)](https://codecov.io/gh/datalad/datalad-dataverse)
[![Documentation Status](https://readthedocs.org/projects/datalad-dataverse/badge/?version=latest)](http://docs.datalad.org/projects/datalad-dataverse/en/latest/?badge=latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub release](https://img.shields.io/github/release/datalad/datalad-dataverse.svg)](https://GitHub.com/datalad/datalad-dataverse/releases/)
[![PyPI version fury.io](https://badge.fury.io/py/datalad-dataverse.svg)](https://pypi.python.org/pypi/datalad-dataverse/)
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-15-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

[Dataverse](https://dataverse.org) is open source research data repository software that is deployed all over the world as data or metadata repositories.
It supports sharing, preserving, citing, exploring, and analyzing research data with descriptive metadata, and thus contributes greatly to open, reproducible, and FAIR science.
[DataLad](https://www.datalad.org), on the other hand, is a data management and data publication tool build on Git and git-annex.
Its core data structure, DataLad datasets, can version control files of any size, and streamline data sharing, updating, and collaboration.
This DataLad extension package provides interoperablity with Dataverse to support dataset transport to and from Dataverse instances.

## Installation

```
# create and enter a new virtual environment (optional)
$ virtualenv --python=python3 ~/env/dl-dataverse
$ . ~/env/dl-dataverse/bin/activate
# install from PyPi
$ python -m pip install datalad-dataverse
```

## How to use

Additional commands provided by this extension are immediately available
after installation. However, in order to fully benefit from all improvements,
the extension has to be enabled for auto-loading by executing:

    git config --global --add datalad.extensions.load dataverse

Doing so will enable the extension to also alter the behavior the core DataLad
package and its commands, from example to be able to directly clone from
a Dataverse dataset landing page.


## Summary of functionality provided by this extension

- Interoperability between DataLad and Dataverse version 5 (or later).
- A `add-sibling-dataverse` command to register a Dataverse dataset as remote sibling for a DataLad dataset.
- A `git-annex-remote-dataverse` special remote implementation for storage and retrieval of data in Dataverse dataset via git-annex.
- These two features combined enable the deposition and retrieveal of complete DataLad dataset on Dataverse, including version history and metadata. A direct `datalad clone` from a Dataverse dataset landing page is supported, and yields a fully functional DataLad dataset clone (Git repository).


## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="https://github.com/likeajumprope"><img src="https://avatars.githubusercontent.com/u/23728822?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Johanna Bayer</b></sub></a><br /><a href="https://github.com/datalad/datalad-dataverse/commits?author=likeajumprope" title="Documentation">📖</a></td>
    <td align="center"><a href="https://github.com/nadinespy"><img src="https://avatars.githubusercontent.com/u/46372572?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Nadine Spychala</b></sub></a><br /><a href="#infra-nadinespy" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="https://github.com/datalad/datalad-dataverse/commits?author=nadinespy" title="Documentation">📖</a></td>
    <td align="center"><a href="https://github.com/bpoldrack"><img src="https://avatars.githubusercontent.com/u/10498301?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Benjamin Poldrack</b></sub></a><br /><a href="#infra-bpoldrack" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="https://github.com/datalad/datalad-dataverse/commits?author=bpoldrack" title="Code">💻</a> <a href="https://github.com/datalad/datalad-dataverse/commits?author=bpoldrack" title="Documentation">📖</a> <a href="#maintenance-bpoldrack" title="Maintenance">🚧</a> <a href="https://github.com/datalad/datalad-dataverse/pulls?q=is%3Apr+reviewed-by%3Abpoldrack" title="Reviewed Pull Requests">👀</a> <a href="#ideas-bpoldrack" title="Ideas, Planning, & Feedback">🤔</a> <a href="#tool-bpoldrack" title="Tools">🔧</a></td>
    <td align="center"><a href="http://www.adina-wagner.com"><img src="https://avatars.githubusercontent.com/u/29738718?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Adina Wagner</b></sub></a><br /><a href="https://github.com/datalad/datalad-dataverse/commits?author=adswa" title="Code">💻</a> <a href="#ideas-adswa" title="Ideas, Planning, & Feedback">🤔</a> <a href="#infra-adswa" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="https://github.com/datalad/datalad-dataverse/commits?author=adswa" title="Documentation">📖</a> <a href="#maintenance-adswa" title="Maintenance">🚧</a> <a href="https://github.com/datalad/datalad-dataverse/pulls?q=is%3Apr+reviewed-by%3Aadswa" title="Reviewed Pull Requests">👀</a></td>
    <td align="center"><a href="http://psychoinformatics.de"><img src="https://avatars.githubusercontent.com/u/136479?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Michael Hanke</b></sub></a><br /><a href="https://github.com/datalad/datalad-dataverse/commits?author=mih" title="Code">💻</a> <a href="#ideas-mih" title="Ideas, Planning, & Feedback">🤔</a> <a href="#maintenance-mih" title="Maintenance">🚧</a> <a href="#infra-mih" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="https://github.com/datalad/datalad-dataverse/pulls?q=is%3Apr+reviewed-by%3Amih" title="Reviewed Pull Requests">👀</a> <a href="#tool-mih" title="Tools">🔧</a></td>
    <td align="center"><a href="https://github.com/enicolaisen"><img src="https://avatars.githubusercontent.com/u/59887397?v=4?s=100" width="100px;" alt=""/><br /><sub><b>enicolaisen</b></sub></a><br /><a href="https://github.com/datalad/datalad-dataverse/commits?author=enicolaisen" title="Documentation">📖</a></td>
    <td align="center"><a href="https://rgbayrak.github.io/"><img src="https://avatars.githubusercontent.com/u/26470013?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Roza</b></sub></a><br /><a href="https://github.com/datalad/datalad-dataverse/commits?author=rgbayrak" title="Documentation">📖</a></td>
  </tr>
  <tr>
    <td align="center"><a href="https://github.com/ksarink"><img src="https://avatars.githubusercontent.com/u/2464969?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Kelvin Sarink</b></sub></a><br /><a href="https://github.com/datalad/datalad-dataverse/commits?author=ksarink" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/jernsting"><img src="https://avatars.githubusercontent.com/u/7760472?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Jan Ernsting</b></sub></a><br /><a href="https://github.com/datalad/datalad-dataverse/commits?author=jernsting" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/effigies"><img src="https://avatars.githubusercontent.com/u/83442?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Chris Markiewicz</b></sub></a><br /><a href="https://github.com/datalad/datalad-dataverse/commits?author=effigies" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/aqw"><img src="https://avatars.githubusercontent.com/u/765557?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Alex Waite</b></sub></a><br /><a href="#infra-aqw" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a> <a href="https://github.com/datalad/datalad-dataverse/commits?author=aqw" title="Code">💻</a> <a href="#maintenance-aqw" title="Maintenance">🚧</a> <a href="#tool-aqw" title="Tools">🔧</a></td>
    <td align="center"><a href="https://github.com/Shammi270787"><img src="https://avatars.githubusercontent.com/u/23641510?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Shammi270787</b></sub></a><br /><a href="https://github.com/datalad/datalad-dataverse/commits?author=Shammi270787" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/jadecci"><img src="https://avatars.githubusercontent.com/u/14807815?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Wu Jianxiao</b></sub></a><br /><a href="https://github.com/datalad/datalad-dataverse/commits?author=jadecci" title="Code">💻</a> <a href="https://github.com/datalad/datalad-dataverse/pulls?q=is%3Apr+reviewed-by%3Ajadecci" title="Reviewed Pull Requests">👀</a> <a href="#userTesting-jadecci" title="User Testing">📓</a></td>
    <td align="center"><a href="https://github.com/loj"><img src="https://avatars.githubusercontent.com/u/15157717?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Laura Waite</b></sub></a><br /><a href="https://github.com/datalad/datalad-dataverse/commits?author=loj" title="Documentation">📖</a></td>
  </tr>
  <tr>
    <td align="center"><a href="https://github.com/mslw"><img src="https://avatars.githubusercontent.com/u/11985212?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Michał Szczepanik</b></sub></a><br /><a href="#infra-mslw" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a></td>
  </tr>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!


## Acknowledgements

This DataLad extension was developed with support from the German Federal
Ministry of Education and Research (BMBF 01GQ1905), the US National Science
Foundation (NSF 1912266), the Helmholtz research center Jülich (RDM challenge
2022), and the Deutsche Forschungsgemeinschaft (DFG, German Research
Foundation) under grant SFB 1451
([431549029](https://gepris.dfg.de/gepris/projekt/431549029), INF project).
