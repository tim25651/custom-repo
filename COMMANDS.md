## Table of Contents

1. [Commands](#Commands)
    1. [General commands](#General-commands)
        1. [Version (`VERSION`)](#Version-VERSION)
        2. [Set variables (`SET`)](#Set-variables-SET)
    2. [Download commands](#Download-commands)
        1. [Download from GitHub (`DOWNLOAD_GH`)](#Download-from-GitHub-DOWNLOAD_GH)
        2. [Direct download (`DOWNLOAD`)](#Direct-download-DOWNLOAD)
        3. [Direct download with remote file name (`DOWNLOAD_REMOTE_NAME`)](#Direct-download-with-remote-file-name-DOWNLOAD_REMOTE_NAME)
        4. [Browser download (`DOWNLOAD_BROWSER`)](#Browser-download-DOWNLOAD_BROWSER)
        5. [Copy from the private directory (`COPY_SRC`)](#Copy-from-the-private-directory-COPY_SRC)
        6. [Symlink from the private directory (`SYMLINK_SRC`)](#Symlink-from-the-private-directory-SYMLINK_SRC)
    3. [File modifiers](#File-modifiers)
        1. [Extract (`EXTRACT`)](#Extract-EXTRACT)
        2. [Create a directory (`MKDIR`)](#Create-a-directory-MKDIR)
        3. [Rename a file (`RENAME`)](#Rename-a-file-RENAME)
    4. [Copy commands](#Copy-commands)
        1. [Copy a file (`COPY`)](#Copy-a-file-COPY)
        2. [Copy a file and adjust variables (`COPY_FIX`)](#Copy-a-file-and-adjust-variables-COPY_FIX)
        3. [Copy multiple files (`COPY_GLOB`)](#Copy-multiple-files-COPY_GLOB)
        4. [Copy a directory (`COPY_DIR`)](#Copy-a-directory-COPY_DIR)
    5. [Debian packages from scratch only](#Debian-packages-from-scratch-only)
        1. [Sandbox (`SANDBOX`)](#Sandbox-SANDBOX)
        2. [Create debian upstream (`CREATE_DEB`)](#Create-debian-upstream-CREATE_DEB)
        3. [Build debian package (`BUILD_DEB`)](#Build-debian-package-BUILD_DEB)
2. [Package types](#Package-types)
    1. [Chocolatey Packages (Windows only)](#Chocolatey-Packages-Windows-only)
    2. [Homebrew Cask (macOS only)](#Homebrew-Cask-macOS-only)
    3. [Debian packages from scratch](#Debian-packages-from-scratch)
    4. [Debian packages from Website](#Debian-packages-from-Website)
    5. [Debian packages from GitHub](#Debian-packages-from-GitHub)
3. [Variables](#Variables)

## Commands

### General commands

#### Version (`VERSION`)
- Must be the first line of the file
- Only allowed to be omitted for `DOWNLOAD_GH` files
- Sets the version of the package

1. `VERSION 1.2.3`: explicitly set the version
2. `VERSION re:test_name-([0-9.+]+).tar.gz`: use a regex to extract the version from the file name
3. `VERSION gh:user/repo`: use the latest release from a GitHub repository

#### Set variables (`SET`)
- Set a variable to be used in the following commands and files which are copied with `COPY_FIX`
- Not allowed to set already defined variables like `NAME` or `VERSION`
- `SET TEST_KEY test_value`

### Download commands
- The actual path can be linked with `$TAP_FILE` or `$CHOCO_FILE` in the respective files

#### Download from GitHub (`DOWNLOAD_GH`)
- Download a file from a GitHub repository
- Currently only for Debian packages!!!
- If no tag is provided, the latest release is used where an asset matches the pattern

1. `DOWNLOAD_GH user/repo pattern`
2. `DOWNLOAD_GH user/repo pattern tag`
#### Direct download (`DOWNLOAD`)
- Download a file from an URL to the working directory
- The last part of the URL is used as the file name
- `DOWNLOAD https://example.com/file.tar.gz`

#### Direct download with remote file name (`DOWNLOAD_REMOTE_NAME`)
- Download a file from an URL to the working directory
- The file name is extracted from the remote download header
- `DOWNLOAD_REMOTE_NAME https://example.com/latest

#### Browser download (`DOWNLOAD_BROWSER`)
- Download a file from an URL using a browser
- Clicks are separated by `>` and either text or css selectors can be used
- `DOWNLOAD_BROWSER "https://example.com>#banner>Download Text"`

#### Copy from the private directory (`COPY_SRC`)
- Copy the file from the private directory (`$REPO_DIR/private`) to the working directory
- `COPY_SRC %name%/file.tar.gz`

#### Symlink from the private directory (`SYMLINK_SRC`)
- Create a symlink to a file from the private directory (`$REPO_DIR/private`) in the working directory
- `SYMLINK_SRC %name%/large_file.deb`

### File modifiers

#### Extract (`EXTRACT`)
- Extract the first file in the working directory
- If a glob is provided, only the files matching the glob are extracted
1. `EXTRACT`
2. `EXTRACT *.deb`

#### Create a directory (`MKDIR`)
- Create the directory including all parent directories in the working directory
- `MKDIR path/to/dir`

#### Rename a file (`RENAME`)
- Rename/move the first file/folder in the working directory
- Creates parent directories if necessary
- `RENAME /path/to/new_name`

### Copy commands
- Use `$PKG` to access the source package directory

#### Copy a file (`COPY`)
- Copy a file within the working directory
- `COPY file.tar.gz /path/to/file.tar.gz`

#### Copy a file and adjust variables (`COPY_FIX`)
- Copy a file within the working directory and adjust variables
- See Variables section for more information
- `COPY_FIX $PKG/install /path/to/install`

#### Copy multiple files (`COPY_GLOB`)
- Copy multiple files matching a glob within the working directory
- `COPY_GLOB *.deb /path/to/`

#### Copy a directory (`COPY_DIR`)
- Copy a directory tree within the working directory
- `COPY_DIR directory /path/to/directory`

####

### Debian packages from scratch only
#### Sandbox (`SANDBOX`)
- Run the following commands in a temporary directory
- Needs `BUILD_DEB` to copy the files to the package directory
- `SANDBOX`

#### Create debian upstream (`CREATE_DEB`)
- Needs a folder in the working directory with the name of the package and its version (`%name%-%version%` or `$DEST`)
- Creates a `debian` directory with the necessary files
- Adds dependencies to the control file if provided
- `CREATE_DEB "python3-psutil, mono-runtime"`

#### Build debian package (`BUILD_DEB`)
- Builds the .deb file from the `$DEST` directory in the temporary directory
- Copies the `.deb` file to the package directory
- `BUILD_DEB`

## Package types

### Chocolatey Packages (Windows only)
- See https://docs.chocolatey.org/en-us/create/create-packages for more information
- Create a `%name%.choco` directory including a
    - `tools` directory with a
        - `chocolateyInstall.ps1` file
        - optional additional files
        - and an optional `chocolateyuninstall.ps1` file
    - `%name%.nuspec` file and a
    - `%name%.choco` file
- Content of the `%name%.choco` file:
```sh
VERSION %see VERSION section%
# download is optional (only if the file is not publicly available)
DOWNLOAD %see DOWNLOAD section%
CHOCO
```
- The `%name%.nuspec` file has to include the tools directory
- Content of the `chocolateyInstall.ps1` file:
```ps1
$ErrorActionPreference = 'Stop'

$packageArgs = @{
  packageName       = "%name%"
  fileType          = 'exe'
  file              = "${ENV:TEMP}\%name%.exe"
# use $CHOCO_FILE to use downloaded file or %url% to directly download
  url = "$CHOCO_FILE" | url = "%url%"
  checksum          = %checksum%
  checksumType      = 'sha256'
  validExitCodes    = @(0)
  silentArgs        = '/S'
  softwareName      = 'Software Name*'
}

# If downloaded file is used
$options = @{
  Headers = @{
    Authorization = "Basic $AUTHORIZATION"
  }
}

Get-ChocolateyWebFile @packageArgs -Options @options

Install-ChocolateyPackage @packageArgs @options
```
- Test it first outside of the repository

### Homebrew Cask (macOS only)
- See https://docs.brew.sh/Cask-Cookbook for more information
- Create a `%name%.tap` file:
```sh
VERSION %see VERSION section%
# download is optional (only if the file is not publicly available)
DOWNLOAD %see DOWNLOAD section%
CASK
# from now on intend the commands
  cask "%name%" do
    version "$VERSION"
    sha256 %sha256%

    # use $TAP_FILE to use downloaded file or %url% to directly download
    url "$TAP_FILE" | url "%url%"
    name "%Full Name%"
    desc "%desc"
    homepage "%homepage%"

    # for example
    app "%name%.app"
  end
```
### Debian packages from scratch
- Create a `%name%.rep` directory including a
    - `install` file
    - optional `include-binaries` and `links` files
    - optional `postinst` and `postrm` files and a
    - `%name%.rep` file
- See https://www.debian.org/doc/manuals/maint-guide/dreq.en.html for more information
- Content of the `%name%.rep` file:
```sh
VERSION %see VERSION section%
SANDBOX
# set the install dir
SET INSTALL_DIR /opt/%name%
# download for example a .tar.gz file
DOWNLOAD %see DOWNLOAD section%
# extract the content to SANDBOX_DIR/%name%
EXTRACT
# move the content to %name%-%version%/data
RENAME $DEST/data
# create the .deb file with python3-psutil and mono as dependencies
CREATE_DEB "python3-psutil, mono-runtime"
# copy the install and include-binaries file to the package directory
COPY_FIX $PKG/install $DEST/debian/install
COPY_FIX $PKG/include-binaries $DEST/debian/source/include-binaries

MKDIR | RENAME | ...

# build the .deb file
BUILD_DEB
```
### Debian packages from Website
- Create a `%name%.rep` file:
```sh
VERSION %see VERSION section%
DOWNLOAD %see DOWNLOAD section%
```

### Debian packages from GitHub
- Create a `%name%.rep` file:
```sh
DOWNLOAD_GH %user%/%repo% %pattern% [%tag]
```

### Conda (Linux-64 only)
- Create a `%name%.conda` directory including a
    - `recipe` directory with a
        - `meta.yaml` file
        - `build.sh` file
        - and an optional `run_test.sh` file and a
    - `%name%.conda` file
    - Layout of the `recipe`from 
- See https://docs.conda.io/projects/conda-build/en/stable/ for more information
- Header of the `meta.yaml` file:
```yaml
package:
  name: %name%
  version: $VERSION

source:
  url: $FILE        | git_rev: %version%
  sha256: %sha256%  | git_url: %url%

...
```
- Content of the `%name%.conda` file:
```sh
VERSION %version%   | re:%regex_pattern% | gh:%user%/%repo%
DOWNLOAD %url%      | DOWNLOAD_BROWSER %url%>%click%>%click%...
CONDA
```

## Variables
| Variable | Description |
| --- | --- |
| `$NAME` | The name of the package (`$NAME`.rep/`$NAME`.pkg/`$NAME`.tap) |
| `$DIR` | Either `tap` if .tap file, `tmp` if `SANDBOX` is used or `debs` if not |
| `$REPO` | The provided repository directory |
| `$DOMAIN` | The provided domain |
| `$VERSION` | The version of the package |
| `$PKG` | The package directory |
| `$FILE` | The location to the file through `DOWNLOAD`, `DOWNLOAD_BROWSER`, `DOWNLOAD_GH`, or `SYMLINK_SRC` |
| `$DEST` | `$NAME-$VERSION` (only usable in `CREATE_DEB` and `BUILD_DEB`) |
| `$TAP_FILE` | `$DOMAIN/` + `$FILE` relative to `$REPO/debs` (only usable in `CASK`) |
| `$CHOCO_FILE` | `$DOMAIN/` + `$FILE` relative to `$REPO/debs` (only usable in `CHOCO`) |
| `$AUTHORIZATION` | The authorization header for HTTP basic auth |
- all other can be set with `SET %key% %value%`