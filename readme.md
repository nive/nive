
# Nive application base package
This is the base package. Please refer to 'nive_cms', nive_userdb' 
or 'nive_datastore' for functional applications.

## Version
The package will soon be released as stable 1.0 version. For a better package management the previous
`nive` package has been split up into several smaller packages.

If you are updating from version 0.9.11 or older please read `update-0.9.11-to-1.0.txt`.
Version 0.9.12 is compatible.

## Source code
The source code is hosted on github: https://github.com/nive/nive

### The form module nive.components.reform
The reform package is a merge of deform and colander and includes several changes 
to make form handling easier. Please see nive.components.reform.README.txt for details.

### Translations
Translations can be extracted using lingua>=3.2

    > pip install lingua-3.2
    > bin/pot-create -o nive/locale/nive.pot nive



