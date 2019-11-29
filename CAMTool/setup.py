from setuptools import setup, find_packages

with open("CAMtool/README.md", "r") as fh:
    long_description = fh.read()


setup(
    name="CAMTool",
    version="0.14",

    packages=find_packages(),
	
    entry_points={
	    'console_scripts': [
		'eagle2cam    = CAMTool.eagle2CAM:main',
		'eagle2bom    = CAMTool.eagle2bom:main',
		'eagle2chmt   = CAMTool.eagle2chmt:main',
		'eagle2svg    = CAMTool.eagle2svg:main',
		'eagleLib2TOC = CAMTool.eagleLib2TOC:main',
	    ]
    },
    package_data = {
        # If any package contains *.config files, include them:
        'CAMTool': ['*.cfg'],
    },

    install_requires = [
    	'svgwrite>=1.3.0'
    ],

    # metadata to display on PyPI
    
    author="John Plocher",
    author_email="JohnPlocher@gmail.com",
    description="Tools that interact with EAGLE CAD schematics, boards and Libraries",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="eagle schematic charmhigh pcb",
    url="https://github.com/plocher/EagleTools",   # project home page, if any
    classifiers=[
        'License :: OSI Approved :: Python Software Foundation License'
    ]
)
