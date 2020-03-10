# The default profile for "my-vendor"
Profile: my-vendor/main
# It has all the checks and settings from the "debian" profile
Extends: debian/main
# Add checks specific to "my-vendor"
Enable-Tags-From-Check:
  my-vendor/some-check,
  my-vendor/another-check,
# Disable a tag
Disable-Tags: dir-or-file-in-opt

# Bump severity of no-md5sums-control-file
# and file-missing-in-md5sums and make them
# non-overridable
Tags: no-md5sums-control-file,
      file-missing-in-md5sums,
Severity: serious
Overridable: no
