#!/usr/bin/env bash
# exit on error
set -o errexit

STORAGE_DIR=/opt/render/project/.render

if [[ ! -d $STORAGE_DIR/chrome ]]; then
  echo "...Downloading Chrome"
  mkdir -p $STORAGE_DIR/chrome
  cd $STORAGE_DIR/chrome
  wget -P ./ https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
  dpkg -x ./google-chrome-stable_current_amd64.deb $STORAGE_DIR/chrome
  rm ./google-chrome-stable_current_amd64.deb
  cd /opt/render/project/src
else
  echo "...Using Chrome from cache"
fi

export NLTK_DATA=/app/nltk_data
mkdir -p $NLTK_DATA
pip install --no-cache-dir -r requirements.txt
python -m nltk.downloader -d $NLTK_DATA punkt stopwords averaged_perceptron_tagger punkt_tab
