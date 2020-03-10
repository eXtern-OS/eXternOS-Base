require '_h2ph_pre.ph';

no warnings qw(redefine misc);

unless(defined(&_BITS_SYSMACROS_H)) {
    eval 'sub _BITS_SYSMACROS_H () {1;}' unless defined(&_BITS_SYSMACROS_H);
    unless(defined(&_SYS_SYSMACROS_H)) {
	die("Never include <bits/sysmacros.h> directly; use <sys/sysmacros.h> instead.");
    }
    eval 'sub __SYSMACROS_DECLARE_MAJOR {
        my($DECL_TEMPL) = @_;
	    eval q($DECL_TEMPL(\'unsigned int\',  &major, ( &__dev_t  &__dev)));
    }' unless defined(&__SYSMACROS_DECLARE_MAJOR);
    eval 'sub __SYSMACROS_DEFINE_MAJOR {
        my($DECL_TEMPL) = @_;
	    eval q( &__SYSMACROS_DECLARE_MAJOR ($DECL_TEMPL) { \'unsigned int __major\';  &__major = (( &__dev & ( &__dev_t) 0xfff00) >> 8);  &__major |= (( &__dev & ( &__dev_t) 0xfffff00000000000) >> 32);  &return  &__major; });
    }' unless defined(&__SYSMACROS_DEFINE_MAJOR);
    eval 'sub __SYSMACROS_DECLARE_MINOR {
        my($DECL_TEMPL) = @_;
	    eval q($DECL_TEMPL(\'unsigned int\',  &minor, ( &__dev_t  &__dev)));
    }' unless defined(&__SYSMACROS_DECLARE_MINOR);
    eval 'sub __SYSMACROS_DEFINE_MINOR {
        my($DECL_TEMPL) = @_;
	    eval q( &__SYSMACROS_DECLARE_MINOR ($DECL_TEMPL) { \'unsigned int __minor\';  &__minor = (( &__dev & ( &__dev_t) 0xff) >> 0);  &__minor |= (( &__dev & ( &__dev_t) 0xffffff00000) >> 12);  &return  &__minor; });
    }' unless defined(&__SYSMACROS_DEFINE_MINOR);
    eval 'sub __SYSMACROS_DECLARE_MAKEDEV {
        my($DECL_TEMPL) = @_;
	    eval q($DECL_TEMPL( &__dev_t,  &makedev, (\'unsigned int __major\', \'unsigned int __minor\')));
    }' unless defined(&__SYSMACROS_DECLARE_MAKEDEV);
    eval 'sub __SYSMACROS_DEFINE_MAKEDEV {
        my($DECL_TEMPL) = @_;
	    eval q( &__SYSMACROS_DECLARE_MAKEDEV ($DECL_TEMPL) {  &__dev_t  &__dev;  &__dev = ((( &__dev_t) ( &__major & 0xfff)) << 8);  &__dev |= ((( &__dev_t) ( &__major & 0xfffff000)) << 32);  &__dev |= ((( &__dev_t) ( &__minor & 0xff)) << 0);  &__dev |= ((( &__dev_t) ( &__minor & 0xffffff00)) << 12);  &return  &__dev; });
    }' unless defined(&__SYSMACROS_DEFINE_MAKEDEV);
}
1;
