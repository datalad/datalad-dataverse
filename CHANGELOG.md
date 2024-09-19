# 1.0.2 (2024-09-19)

## Dependencies

- The dependency on PyDataverse has been set to 0.3.4 or higher: [PR330](https://github.com/datalad/datalad-dataverse/pull/330) by [@adswa](https://github.com/adswa)

## 🐛 Bug fixes

- Fixed file retrieval of tabular data: [PR314](https://github.com/datalad/datalad-dataverse/pull/314) by [@shoeffner](https://github.com/shoeffner)
- Use non-persistentID mode for data retrieval via PyDataverse: [PR311](https://github.com/datalad/datalad-dataverse/pull/311) by [@shoeffner](https://github.com/shoeffner)
- Adjustment to PyDataverse's change from ``requests`` to ``https``: [PR309](https://github.com/datalad/datalad-dataverse/pull/309) by [@shoeffner](https://github.com/shoeffner)

## 🧪 Tests

- Appveyor tests are now run weekly in order to find breakage sooner
- Tests were adjusted to take required metadata specifications directly from the API guide, rather than hard coding: [PR299](https://github.com/datalad/datalad-dataverse/pull/299) by [@adswa](https://github.com/adswa)
- Test helpers accommodate PyDataverse versions 0.3.2+: [PR319](https://github.com/datalad/datalad-dataverse/pull/319) by [@mih](https://github.com/mih)
- The test suite can now also be run against docker: [PR323](https://github.com/datalad/datalad-dataverse/pull/323) by [@shoeffner](https://github.com/shoeffner)
- Testremote-calling tests were adjusted to account for an expected failure to replace identical files: [PR324](https://github.com/datalad/datalad-dataverse/pull/324) by [@adswa](https://github.com/adswa)

## Documentation

- README badge was updated with a correct link to the docs: [PR296](https://github.com/datalad/datalad-dataverse/pull/296) by [@behinger](https://github.com/behinger))
- The docs now contain a copy-pastable instruction on DataLad dataset basics: [PR301](https://github.com/datalad/datalad-dataverse/pull/301) by [@adswa](https://github.com/adswa)
- It is now explicit that the next-extension needs to be loaded: [PR305](https://github.com/datalad/datalad-dataverse/pull/305) by [@bpoldrack](https://github.com/bpoldrack)
- The minimum git-annex version for Windows compatibility is now mentioned: [PR315](https://github.com/datalad/datalad-dataverse/pull/315) by [@mih](https://github.com/mih)

# 1.0.1 (2023-04-20)

## 🐛 Bug Fixes

- Wrong argument specification broke the command line interface of
  `add-sibling-dataverse`.  Fixes
  https://github.com/datalad/datalad-dataverse/issues/289 via
  https://github.com/datalad/datalad-dataverse/pull/290 (by
  [@mih](https://github.com/mih))

## 🧪 Tests

- Update tests to use a different metadata format (with fully qualified URLs as
  keys) that now seems to be required by Dataverse v5.13 (deployed at
  demo.dataverse.org) https://github.com/datalad/datalad-dataverse/pull/293 (by
  [@mih](https://github.com/mih))

# 1.0.0 (2022-03-17) --  Dataverse!

- Initial release. See the documentation for a description of the implemented
  functionality.
