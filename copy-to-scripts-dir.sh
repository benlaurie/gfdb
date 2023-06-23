#!/bin/sh

# Note that this might not be right for everyone
FUSION_360_API_DIR="/Users/$USER/Library/Application Support/Autodesk/Autodesk Fusion 360/API"
FUSION_360_SCRIPTS_DIR="${FUSION_360_API_DIR}/Scripts"

if [ -d "${FUSION_360_API_DIR}" ]
then
    mkdir -p "${FUSION_360_SCRIPTS_DIR}"
	cd /Users/jamie/Projects/GitRepo/gfdb
    cp GridFinityDividerBoxMaker/GridFinityDividerBoxMaker.py "${FUSION_360_SCRIPTS_DIR}"
	cp RemoteHolster/RemoteHolsterMaker.py "${FUSION_360_SCRIPTS_DIR}"
else
    echo "Fusion 360 API directory (${FUSION_360_API_DIR}) not found, aborting"
    exit 9
fi
