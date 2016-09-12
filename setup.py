#!/usb/bin/env python

from setuptools import setup

setup(
    name='tem_circlefind', version='0.0.1', author='Andras Wacha',
    author_email='awacha@gmail.com', url='http://github.com/awacha/tem_circlefind',
    description='GUI utility for finding circles in images (especiall transmission electronmicrography)',
    package_dir={'': 'src'},
    packages=['tem_circlefind'],
    package_data={'': ['*.ui']},
    # cmdclass = {'build_ext': build_ext},
    install_requires=['numpy>=1.0.0', 'scipy>=0.7.0', 'matplotlib',
                      'PyQt5'],
    entry_points={'gui_scripts': ['tem_circlefind = tem_circlefind.__main__:run']},
    keywords="TEM, electron microscopy, circles, histogram",
    license="BSD 3-clause",
    zip_safe=False,
)
