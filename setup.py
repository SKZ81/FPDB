# setup.py
# Python packaging for fpdb

from distutils.core import setup

setup(name = 'fpdb',
    description = 'Free Poker Database',
    version = '0.11.3',
    author = 'FPDB team',
    author_email = 'fpdb-main@lists.sourceforge.net',
    packages = ['fpdb'],
    package_dir = { 'fpdb' : 'pyfpdb' },
    data_files = [
        ('/usr/share/doc/python-fpdb',
            ['docs/readme.txt', 'docs/release-notes.txt',
            'docs/tabledesign.html', 'THANKS.txt']),
        ('/usr/share/pixmaps',
            ['gfx/fpdb-icon.png']),
        ('/usr/share/applications',
            ['files/fpdb.desktop']),
        ('/usr/share/python-fpdb',
            ['pyfpdb/logging.conf', 'pyfpdb/Cards01.png',
             'pyfpdb/HUD_config.xml.example'
            ])
        ]
)
