VERSION=$(shell grep "version=" setup.py | sed -e "s/^.*=\\\"//" -e "s/\\\"[    ]*,$$//")
MAJOR=$(shell LC_ALL=C echo ${VERSION} | sed -e "s/\..*$$//" )
MINOR=$(shell LC_ALL=C /usr/bin/printf "%.*f\n" 2 ${VERSION} | sed -e "s/^[0-9][0-9]*\.//")
NEXTMAJOR="$(shell expr ${MAJOR} + 1).0"
NEXTDOTMINOR=$(shell expr ${MINOR} + 1)
NEXTMINOR="${MAJOR}.${NEXTDOTMINOR}"


all:
		@echo "VERSION       = ${VERSION}"
		@echo "MAJOR         = ${MAJOR}"
		@echo "MINOR         = ${MINOR}"
		@echo "NEXTMAJOR     = ${NEXTMAJOR}"
		@echo "NEXTDOTMINOR  = ${NEXTDOTMINOR}"
		@echo "NEXTMINOR     = ${NEXTMINOR}"

develop:
		python3 setup.py develop

testpublish:
		@echo "Publishing to PiPi: v${VERSION} => v${NEXTMINOR}"
		@echo "    Updating version from ${VERSION} to ${NEXTMINOR}"
		sed -i '' -e "s/version=..*$$/version=\\\"${NEXTMINOR}\\\",/" setup.py
		@echo "    Building ..."
		python3 setup.py build
		@echo "    Building dist wheel"
		python3 setup.py sdist bdist_wheel
		@echo "    ============"
		@echo "    plocher/mf__WwHHKx!XnwWVNwz6"
		@echo "    ============"
		@echo "    Uploading to testpypi..."
		python3 -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*${NEXTMINOR}*
		@echo "Published to PyPi: v${VERSION} => v${NEXTMINOR}"
		@echo "    Installing new version"
		pip3 install --upgrade -i https://test.pypi.org/simple/ CAMTool
