#!/usb/bin/env python

import os

from PyQt5.uic import compileUi
from setuptools import setup


def compile_uis(packageroot):
    for dirpath, dirnames, filenames in os.walk(packageroot):
        for fn in [fn_ for fn_ in filenames if fn_.endswith('.ui')]:
            fname = os.path.join(dirpath, fn)
            pyfilename = os.path.splitext(fname)[0] + '_ui.py'
            with open(pyfilename, 'wt', encoding='utf-8') as pyfile:
                compileUi(fname, pyfile)
            print('Compiled UI file: {} -> {}.'.format(fname, pyfilename))


compile_uis('src')
setup(
    name='tem_circlefind', author='Andras Wacha',
    author_email='awacha@gmail.com', url='http://github.com/awacha/tem_circlefind',
    description='GUI utility for finding circles in images (especiall transmission electronmicrography)',
    package_dir={'': 'src'},
    packages=['tem_circlefind'],
    package_data={'': ['*.ui']},
    # cmdclass = {'build_ext': build_ext},
    setup_requires=['setuptools_scm'],
    use_scm_version=True,
    install_requires=['numpy>=1.0.0', 'scipy>=0.7.0', 'matplotlib', 'imageio'],
    entry_points={'gui_scripts': ['tem_circlefind = tem_circlefind.__main__:run']},
    keywords="TEM, electron microscopy, circles, histogram",
    license="BSD 3-clause",
    zip_safe=False,
)
