gimp -idf --batch-interpreter python-fu-eval -b "import sys;sys.path=['.']+sys.path;import oilify;oilify.run('./images')" -b "pdb.gimp_quit(1)"
