# DataLad Dataverse extension

[![Documentation Status](https://readthedocs.org/projects/datalad-dataverse/badge/?version=latest)](http://docs.datalad.org/projects/datalad-dataverse/en/latest/?badge=latest)

<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-14-orange.svg?style=flat-square)](#contributors-)
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

## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="https://github.com/likeajumprope"><img src="https://avatars.githubusercontent.com/u/23728822?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Johanna Bayer</b></sub></a><br /><a href="https://github.com/datalad/datalad-dataverse/commits?author=likeajumprope" title="Documentation">📖</a></td>
    <td align="center"><a href="https://github.com/nadinespy"><img src="https://avatars.githubusercontent.com/u/46372572?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Nadine Spychala</b></sub></a><br /><a href="#infra-nadinespy" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a></td>
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
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!
