rm -rf dist
rm -rf build
rm -rf django_aries_community.egg-info

cp ../LICENSE .
cp -R ../docs/ ./docs
cp -R ../aries_community_demo/aries_community/ ./aries_community
rm -rf aries_community/static

#python setup.py sdist
python setup.py sdist bdist_wheel

rm LICENSE
rm -rf ./docs
rm -rf ./aries_community

