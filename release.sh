rm -r dist src/easybird.egg-info/
python -m build
twine upload dist/*