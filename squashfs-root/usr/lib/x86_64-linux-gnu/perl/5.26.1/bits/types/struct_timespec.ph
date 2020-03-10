require '_h2ph_pre.ph';

no warnings qw(redefine misc);

unless(defined(&__timespec_defined)) {
    eval 'sub __timespec_defined () {1;}' unless defined(&__timespec_defined);
    require 'bits/types.ph';
}
1;
