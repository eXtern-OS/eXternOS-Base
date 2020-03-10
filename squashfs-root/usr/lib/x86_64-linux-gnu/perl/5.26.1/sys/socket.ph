require '_h2ph_pre.ph';

no warnings qw(redefine misc);

unless(defined(&_SYS_SOCKET_H)) {
    eval 'sub _SYS_SOCKET_H () {1;}' unless defined(&_SYS_SOCKET_H);
    require 'features.ph';
    require 'bits/types/struct_iovec.ph';
    eval 'sub __need_size_t () {1;}' unless defined(&__need_size_t);
    require 'stddef.ph';
    require 'bits/socket.ph';
    if(defined(&__USE_MISC)) {
	require 'bits/types/struct_osockaddr.ph';
    }
    eval("sub SHUT_RD () { 0; }") unless defined(&SHUT_RD);
    eval("sub SHUT_WR () { 1; }") unless defined(&SHUT_WR);
    eval("sub SHUT_RDWR () { 2; }") unless defined(&SHUT_RDWR);
    if(defined (&__cplusplus) || ! &__GNUC_PREREQ (2, 7) || !defined (&__USE_GNU)) {
	eval 'sub __SOCKADDR_ARG () {1;}' unless defined(&__SOCKADDR_ARG);
	eval 'sub __CONST_SOCKADDR_ARG () { &const 1;}' unless defined(&__CONST_SOCKADDR_ARG);
    } else {
	eval 'sub __SOCKADDR_ALLTYPES () { &__SOCKADDR_ONETYPE ( &sockaddr)  &__SOCKADDR_ONETYPE ( &sockaddr_at)  &__SOCKADDR_ONETYPE ( &sockaddr_ax25)  &__SOCKADDR_ONETYPE ( &sockaddr_dl)  &__SOCKADDR_ONETYPE ( &sockaddr_eon)  &__SOCKADDR_ONETYPE ( &sockaddr_in)  &__SOCKADDR_ONETYPE ( &sockaddr_in6)  &__SOCKADDR_ONETYPE ( &sockaddr_inarp)  &__SOCKADDR_ONETYPE ( &sockaddr_ipx)  &__SOCKADDR_ONETYPE ( &sockaddr_iso)  &__SOCKADDR_ONETYPE ( &sockaddr_ns)  &__SOCKADDR_ONETYPE ( &sockaddr_un)  &__SOCKADDR_ONETYPE ( &sockaddr_x25);}' unless defined(&__SOCKADDR_ALLTYPES);
	eval 'sub __SOCKADDR_ONETYPE {
	    my($type) = @_;
    	    eval q(1;);
	}' unless defined(&__SOCKADDR_ONETYPE);
	undef(&__SOCKADDR_ONETYPE) if defined(&__SOCKADDR_ONETYPE);
	eval 'sub __SOCKADDR_ONETYPE {
	    my($type) = @_;
    	    eval q( &const 1;);
	}' unless defined(&__SOCKADDR_ONETYPE);
	undef(&__SOCKADDR_ONETYPE) if defined(&__SOCKADDR_ONETYPE);
    }
    if(defined(&__USE_GNU)) {
    }
    if(defined(&__USE_GNU)) {
    }
    if(defined(&__USE_GNU)) {
    }
    if(defined(&__USE_GNU)) {
    }
    if(defined(&__USE_XOPEN2K)) {
    }
    if(defined(&__USE_MISC)) {
    }
    if((defined(&__USE_FORTIFY_LEVEL) ? &__USE_FORTIFY_LEVEL : undef) > 0 && defined (&__fortify_function)) {
	require 'bits/socket2.ph';
    }
}
1;
