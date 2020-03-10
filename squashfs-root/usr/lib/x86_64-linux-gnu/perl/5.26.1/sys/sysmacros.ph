require '_h2ph_pre.ph';

no warnings qw(redefine misc);

unless(defined(&_SYS_SYSMACROS_H_OUTER)) {
    unless(defined(&__SYSMACROS_DEPRECATED_INCLUSION)) {
	eval 'sub _SYS_SYSMACROS_H_OUTER () {1;}' unless defined(&_SYS_SYSMACROS_H_OUTER);
    }
    undef(&major) if defined(&major);
    undef(&minor) if defined(&minor);
    undef(&makedev) if defined(&makedev);
    unless(defined(&_SYS_SYSMACROS_H)) {
	eval 'sub _SYS_SYSMACROS_H () {1;}' unless defined(&_SYS_SYSMACROS_H);
	require 'features.ph';
	require 'bits/types.ph';
	require 'bits/sysmacros.ph';
	eval 'sub __SYSMACROS_DM {
	    my($symbol) = @_;
    	    eval q( &__SYSMACROS_DM1 ( &In  &the  &GNU  &C  &Library, $symbol  &is defined\\\\ &n  &by < &sys/ ($sysmacros->{h})>.  &For  &historical  &compatibility,  &it  &is\\\\ &n  &currently defined  &by < &sys/ ($types->{h})>  &as  &well,  &but  &we  &plan  &to\\\\ &n  &remove  &this  &soon.  &To  &use $symbol,  &include < &sys/ ($sysmacros->{h})>\\\\ &n  &directly.  &If  &you  &did  &not  &intend  &to  &use  &a  &system-defined  &macro\\\\ &n $symbol,  &you  &should  &undefine  &it  &after  &including < &sys/ ($types->{h})>.));
	}' unless defined(&__SYSMACROS_DM);
	eval 'sub __SYSMACROS_DM1 () {(...)  &__glibc_macro_warning ( &__VA_ARGS__);}' unless defined(&__SYSMACROS_DM1);
	eval 'sub __SYSMACROS_DECL_TEMPL {
	    my($rtype, $name, $proto) = @_;
    	    eval q( &extern $rtype  &gnu_dev_$name $proto  &__THROW  &__attribute_const__;);
	}' unless defined(&__SYSMACROS_DECL_TEMPL);
	eval 'sub __SYSMACROS_IMPL_TEMPL {
	    my($rtype, $name, $proto) = @_;
    	    eval q( &__extension__  &__extern_inline  &__attribute_const__ $rtype  &__NTH ( &gnu_dev_$name $proto));
	}' unless defined(&__SYSMACROS_IMPL_TEMPL);
	if(defined(&__USE_EXTERN_INLINES)) {
	}
    }
    unless(defined(&__SYSMACROS_NEED_IMPLEMENTATION)) {
	undef(&__SYSMACROS_DECL_TEMPL) if defined(&__SYSMACROS_DECL_TEMPL);
	undef(&__SYSMACROS_IMPL_TEMPL) if defined(&__SYSMACROS_IMPL_TEMPL);
	undef(&__SYSMACROS_DECLARE_MAJOR) if defined(&__SYSMACROS_DECLARE_MAJOR);
	undef(&__SYSMACROS_DECLARE_MINOR) if defined(&__SYSMACROS_DECLARE_MINOR);
	undef(&__SYSMACROS_DECLARE_MAKEDEV) if defined(&__SYSMACROS_DECLARE_MAKEDEV);
	undef(&__SYSMACROS_DEFINE_MAJOR) if defined(&__SYSMACROS_DEFINE_MAJOR);
	undef(&__SYSMACROS_DEFINE_MINOR) if defined(&__SYSMACROS_DEFINE_MINOR);
	undef(&__SYSMACROS_DEFINE_MAKEDEV) if defined(&__SYSMACROS_DEFINE_MAKEDEV);
    }
    if(defined(&__SYSMACROS_DEPRECATED_INCLUSION)) {
	eval 'sub major {
	    my($dev) = @_;
    	    eval q( &__SYSMACROS_DM ( &major)  &gnu_dev_major ($dev));
	}' unless defined(&major);
	eval 'sub minor {
	    my($dev) = @_;
    	    eval q( &__SYSMACROS_DM ( &minor)  &gnu_dev_minor ($dev));
	}' unless defined(&minor);
	eval 'sub makedev {
	    my($maj, $min) = @_;
    	    eval q( &__SYSMACROS_DM ( &makedev)  &gnu_dev_makedev ($maj, $min));
	}' unless defined(&makedev);
    } else {
	eval 'sub major {
	    my($dev) = @_;
    	    eval q( &gnu_dev_major ($dev));
	}' unless defined(&major);
	eval 'sub minor {
	    my($dev) = @_;
    	    eval q( &gnu_dev_minor ($dev));
	}' unless defined(&minor);
	eval 'sub makedev {
	    my($maj, $min) = @_;
    	    eval q( &gnu_dev_makedev ($maj, $min));
	}' unless defined(&makedev);
    }
}
1;
