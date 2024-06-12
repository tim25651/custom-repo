# export GH_TOKEN=$(cat .../.gh_token)
export CONFIGS=tests/configs
export REPO_NAME=tmp-repo-test
export REPO_DIR=~/$REPO_NAME
export PRIV_FILE=tests/UNSAFE_DONT_USE_GPG.key
export REPO_USER=repo
export PASS_FILE=tests/UNSAFE_DONT_USE_REPO.passwd
export DOMAIN=http://localhost

rm -rf $REPO_DIR
mkdir $REPO_DIR
custom-repo $REPO_DIR -k $PRIV_FILE -d $DOMAIN -u $REPO_USER -p $PASS_FILE -vv
cp -r $CONFIGS/* $REPO_DIR/configs
custom-repo $REPO_DIR -k $PRIV_FILE -d $DOMAIN  -u $REPO_USER -p $PASS_FILE -vv
custom-repo-restart $REPO_DIR -vv

# Test APT
echo "deb [signed-by=/usr/share/keyrings/$REPO_NAME.gpg] file://$REPO_DIR/public/debs stable main" | \
    sudo tee  /etc/apt/sources.list.d/$REPO_NAME.list > /dev/null
cat $REPO_DIR/public/debs/pub.gpg | sudo tee /usr/share/keyrings/$REPO_NAME.gpg > /dev/null
sudo apt update
apt search enroot


# Test CONDA
conda search -c file://$REPO_DIR/public/conda chocolatey
choco search eduvpn --source http://localhost:7996/choco
brew tap test-user/$REPO_NAME file://$REPO_DIR/public/tap.git
brew update
brew search mestrenova

# uninstall everything
rm -rf $REPO_DIR
sudo rm /etc/apt/sources.list.d/$REPO_NAME.list
sudo rm /usr/share/keyrings/$REPO_NAME.gpg
sudo apt update
brew untap user/repo
brew update