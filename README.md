# Custom Ubuntu Repository

## Table of Contents

1. [Installation](#installation)
2. [Usage](#usage)
3. [Configure](#configure)
    1. [Server](#server)
    2. [Client](#client)
    3. [Package Managers](#package-managers)
4. [Cleanup](#cleanup)

## Installation

- Create a personal access token on https://github.com/settings/tokens

```sh
# install git, gpg, and dh-make
sudo apt update && sudo apt install git gpg dh-make -y

# install build requirements (for conda and choco)
conda create -n repo python=3.10 -y
conda install mono dotnet-sdk conda-build -y

# build choco for linux
export CHOCO_DIR=/opt/chocolatey
git clone https://github.com/chocolatey/choco.git
cd choco
bash build.official.sh
cp -r code_drop/temp/_PublishedApps/choco $CHOCO_DIR
cp -r code_drop/temp/_PublishedLibs/chocolatey $CHOCO_DIR/lib

# install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# install this package
git clone https://github.com/tim25651/custom-repo.git
cd custom-repo
pip install . 
playwright install
sudo $(which playwright) install-deps
```

## Usage

1. Initialize the repository
```sh
# create a new folder for the repository
mkdir -p ~/custom-repo
```
2. Build the repository
```sh
# build the repository for the directory
# provide the GPG key (if the file doesn't exist, the command will create a new key at the specified location) 
# the domain where the repository is hosted,
# the github token (or set GH_TOKEN in the environment),
# the user (default: repo)
# the password for the repository (or set REPO_PASS in the environment)
# and if to include the restart command (else the server has to be restarted manually, see 5.)
custom-repo build ~/custom-repo \
    -k /path/to/key.gpg \
    -d %domain% \
    -t /path/to/.gh_token \
    # -u %user% \
    -p /path/to/.repo.passwd
    # -r
```
3. Create a new package: see [COMMANDS.md](COMMANDS.md)
4. Run the command from 2. again
5. Start the chocolatey server (has to be called after each change)
```sh
custom-repo restart ~/custom-repo
```

## Configure

### Server
1. Set the repository user and password
```sh
export $REPO_USER=...
export $REPO_PASS=...
# set the repo HTTP password
sudo apt install apache2-utils nginx -y
sudo mkdir -p /var/www/secure/%server_name%
sudo htpasswd -c /var/www/secure/%server_name%/.htpasswd $REPO_USER $REPO_PASS
sudo chmod 644 /var/www/secure/%server_name%/.htpasswd
sudo chown www-data:www-data /var/www/secure/%server_name%/.htpasswd
```
2. Create the NGINX configuration
```sh
cat <<EOF > /etc/nginx/sites-available/%server_name%
server {
    server_name %server_name%;

    auth_basic "Restricted Repository";
    auth_basic_user_file /var/www/secure/%server_name%/.htpasswd;

    root /home/%user%/custom-repo;

    location / {
        autoindex on;
    }
    location /choco/ {
        proxy_pass http://127.0.0.1:7996/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    location /download/ {
        proxy_pass http://127.0.0.1:7996;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/%server_name%/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/%server_name%/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
}
server {
    if ($host = %server_name%) {
        return 301 https://$host$request_uri;
    } # managed by Certbot

    server_name %server_name%;
    listen 80;
    return 404; # managed by Certbot
}
EOF
sudo ln -s /etc/nginx/sites-available/%server_name% /etc/nginx/sites-enabled/%server_name%
sudo nginx -t
sudo systemctl restart nginx
```
- See [Certbot](https://certbot.eff.org/instructions?ws=nginx&os=ubuntufocal) for SSL configuration

### Client

- Create a `.netrc` file in the home directory
```sh
export $REPO_USER=...
export $REPO_PASS=...
echo "machine %domain% login $REPO_USER password $REPO_PASS" >> ~/.netrc
chmod 600 ~/.netrc
```

### Package Managers
1. Homebrew
```sh
# patch the curl formula to use the .netrc file
perl -pi0e 's/_curl_args\n    args = \[\]/_curl_args\n    args = \["-n"\]/igs\' /opt/homebrew/Library/Homebrew/curl.rb
# add the repository
brew tap %arbitraryuser%/%arbitraryname% %domain%/tap.git
brew update
```
2. APT
```sh
# add the key
curl -n --output - %domain%/pub.gpg | sudo tee /usr/share/keyrings/%arbitraryname%.gpg > /dev/null
# add the source
echo "deb [signed-by=/usr/share/keyrings/%arbitraryname%.gpg] %domain%/debs/ stable main" | sudo tee /etc/apt/sources.list.d/%arbitraryname%.list > /dev/null
# add the credentials
echo "machine %server_name% login $REPO_USER password $REPO_PASS" | sudo tee /etc/apt/auth.conf.d/%arbitraryname%.conf > /dev/null
sudo chmod 600 /etc/apt/auth.conf.d/%arbitraryname%.conf
sudo apt update
```
3. Chocolatey
```powershell
export $REPO_USER=...
export $REPO_PASS=...
choco source add -n=%arbitraryname% -s="https://%domain%/choco/" -u=$REPO_USER -p=$REPO_PASS
```
4. Conda
```sh
conda config --add channels %domain%/conda
```

## Cleanup

1. Server
```sh
export $CHOCO_DIR=/opt/chocolatey
sudo rm -rf /var/www/secure/%server_name%
sudo rm /etc/nginx/sites-available/%server_name%
sudo rm /etc/nginx/sites-enabled/%server_name%
sudo nginx -t
sudo systemctl restart nginx
sudo apt remove git gpg dh-make apache2-utils nginx -y
sudo rm -rf ~/.nvm
sudo $(which playwright) uninstall
sudo rm -rf $CHOCO_DIR
conda env remove -n repo
rm -rf ~/custom-repo
```

2. Client
```sh
sed -i '/%domain%/d' ~/.netrc
sudo rm /usr/share/keyrings/%arbitraryname%.gpg
sudo rm /etc/apt/sources.list.d/%arbitraryname%.list
sudo rm /etc/apt/auth.conf.d/%arbitraryname%.conf
sudo apt update
perl -pi0e 's/_curl_args\n    args = \["-n"\]/_curl_args\n    args = \[\]/igs\' /opt/homebrew/Library/Homebrew/curl.rb
brew untap %arbitraryuser%/%arbitraryname%
choco source remove -n=%arbitraryname%
conda config --remove channels %domain%/conda
```

