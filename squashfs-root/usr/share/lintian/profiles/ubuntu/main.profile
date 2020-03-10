# The default profile for Ubuntu and derivatives thereof.
Profile: ubuntu/main
Extends: debian/main
Disable-Tags: changelog-should-mention-nmu,
 debian-changelog-file-is-a-symlink, lzma-deb-archive,
 maintainer-address-causes-mail-loops-or-bounces,
 maintainer-upload-has-incorrect-version-number,
 no-upstream-changelog, qa-upload-has-incorrect-version-number,
 source-nmu-has-incorrect-version-number,
 team-upload-has-incorrect-version-number,
 uploader-address-causes-mail-loops-or-bounces,
 upstart-job-in-etc-init.d-not-registered-via-update-rc.d,
 no-human-maintainers, bugs-field-does-not-refer-to-debian-infrastructure
