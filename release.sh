rm -r dist src/xenopy.egg-info/
python -m build
twine upload dist/*