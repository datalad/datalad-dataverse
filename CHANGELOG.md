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
