#!/bin/bash

VERSION=$1

script="$0"
basename="$(dirname $script)"
cd $basename/../

python3 setup.py bdist_wheel

gpg --detach-sign -a dist/python_juicenet-$VERSION-py2.py3-none-any.whl

twine upload dist/python_juicenet-$VERSION-py2.py3-none-any.whl dist/python_juicenet-$VERSION-py2.py3-none-any.whl.asc
