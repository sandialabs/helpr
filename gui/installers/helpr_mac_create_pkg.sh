#!/bin/sh

# Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.
# You should have received a copy of the BSD License along with HELPR.


# Create .pkg installer.
# Pass codesign identity as first arg and credential profile as second; remember to use "" around it if spaces
# $ ./helpr_mac_create_pkg.sh "<Installer ID>" "<Profile>"

# NOTE: to store your credentials:
# xcrun notarytool store-credentials "AC_PASSWORD"
#               --apple-id "AC_USERNAME"
#               --team-id <WWDRTeamID>
#               --password <secret_2FA_password>
#
# To verify that .app is codesigned:
# codesign -v -vvv --deep --strict dist/HELPR.app
#
# REFERENCES
# https://www.unix.com/man-page/osx/1/productbuild/
# https://www.unix.com/man-page/osx/1/pkgbuild/
# https://developer.apple.com/library/archive/documentation/DeveloperTools/Reference/DistributionDefinitionRef/Chapters/Introduction.html
# https://stackoverflow.com/a/11487658

programName="HELPR"
version="1.0.0"  # Make sure to update distribution file entry as well

doDevBuild=false

# Specify app created by pyinstaller
origAppFile="dist/$programName.app"
movedAppFile="dist/app/$programName.app"
appDir="dist/app/"

resourcePath="building_mac"
distrFile="building_mac/distribution_mac.xml"

# Intermediate build packages and files; must match distribution xml entry
buildfile="dist/build-$programName.pkg"
buildPkgPath="dist"

# Output package ready for use
pkgFile="dist/$programName-$version-macOS-setup.pkg"

echo " "
echo "=============================="
echo "BUILDING HELPR DISTRIBUTION..."
echo "Version $version"
echo "AppDir: $appDir"
echo "Package: $pkgFile"
echo "id: $1"

echo " "
echo "Deleting stale packages..."
test -f "$pkgFile" && rm "$pkgFile"
test -f "$buildfile" && rm "$buildfile"

if [ ! -d "$appDir" ]; then
  mkdir -p $appDir
fi

if [ -d "$origAppFile" ]; then
  echo "Moving HELPR.app to child directory"
  mv $origAppFile $movedAppFile
fi

if [ ! -d "$movedAppFile" ]; then
  echo "ERROR - HELPR.app not found in app directory. Make sure it exists and is not in dist/ directory."
  exit
fi


# ==============================
# ==== TEST WITHOUT SIGNING ====
# Test PKG build. Comment this out for regular build.
if $doDevBuild
then
  echo "(DEV ONLY) Test package creation"
  sleep 1
  pkgbuild \
      --root $appDir \
      --install-location /Applications \
      --component-plist $resourcePath/components.plist \
      --identifier "com.SandiaNationalLaboratories.HELPR" \
      --timestamp \
      --version $version \
      $buildfile
  productbuild \
      --distribution $distrFile \
      --package-path $buildPkgPath \
      --resources $resourcePath \
      --timestamp \
      --version $version \
      $pkgFile
  echo "Creation of Test pkg complete!"
  echo "==== HALTING - dev build flag is ENABLED. Disable this to proceed with creation of signed distribution! ===="

  exit

fi


echo "Creating intermediate package(s)..."
sleep 1
pkgbuild \
    --root $appDir \
    --install-location /Applications \
    --component-plist $resourcePath/components.plist \
    --identifier "com.SandiaNationalLaboratories.HELPR" \
    --sign "$1" \
    --timestamp \
    --version $version \
    $buildfile

echo "Creating distribution package..."
productbuild \
    --distribution $distrFile \
    --package-path $buildPkgPath \
    --resources $resourcePath \
    --sign "$1" \
    --timestamp \
    --version $version \
    $pkgFile
echo "Distribution package complete!"
echo " "
sleep 1

echo "Verifying package signature..."
pkgutil --check-signature $pkgFile
sleep 2

echo " "
echo "Submitting to Apple for notarization."
echo "This may take 5-10 minutes."
xcrun notarytool submit $pkgFile --wait --keychain-profile "$2"
echo "Notarization complete"

# Verify notarization. Should output "Source=Notarized..."
# echo spctl -a -v $pkgFile
echo "VERIFYING PACKAGE NOTARIZATION..."
echo "Below must include 'trusted by Apple notary service' "
pkgutil --check-signature $pkgFile
sleep 2
echo " "

# Staple notarization to pkg
echo "Stapling notarization to pkg"
xcrun stapler staple $pkgFile

echo " ==== ==== ==== "
echo "PACKAGE CONSTRUCTION COMPLETE!"
echo "To test the notarized installation, upload it to a file-share service, download it, and execute the installer."
echo " "
