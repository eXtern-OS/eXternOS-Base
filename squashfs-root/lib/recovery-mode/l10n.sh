# default eval_gettext() to ensure that we do not fail
# if gettext-base is not installed
eval_gettext() {
    echo "$1"
}

# Deal with systems where /usr isn't mounted
if [ ! -d /usr/share/locale ]; then
    return
fi

# blacklist some languages that we don't have a good console fonts for
# see bug #573502
in_lang_blacklist() {
    LANG_BLACKLIST="ar_ he_IL ja_JP ko_KR ru_RU sl_SI vi_VN zh_"
    LANG=$1
    for b in $LANG_BLACKLIST; do
        # equal to lang.startswith(b)
        if expr match "$LANG" ^"$b" >/dev/null ; then
            export LANG=C.UTF-8
            export LANGUAGE=en
            return 0
        fi
    done
    return 1
}

# There is no environment set, as these steps are skipped, 
# so we need to source the variables needed for localization ourselves
if [ -r /etc/default/locale ]; then
 . /etc/default/locale
 if ! in_lang_blacklist "$LANG"; then
     export LANG LANGUAGE
 fi
elif [ -r /etc/environment ]; then
 . /etc/environment
 if ! in_lang_blacklist "$LANG"; then
     export LANG LANGUAGE
 fi
fi

. gettext.sh
export TEXTDOMAIN=friendly-recovery
export TEXTDOMAINDIR=/usr/share/locale
