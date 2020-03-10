cmd_scripts/mod/empty.o := gcc -Wp,-MD,scripts/mod/.empty.o.d  -nostdinc -isystem /usr/lib/gcc/x86_64-linux-gnu/7/include -I/usr/src/linux-headers-lbm- -I/build/linux-hwe-iAAoxd/linux-hwe-5.0.0/arch/x86/include -I./arch/x86/include/generated  -I/build/linux-hwe-iAAoxd/linux-hwe-5.0.0/include -I./include -I/build/linux-hwe-iAAoxd/linux-hwe-5.0.0/arch/x86/include/uapi -I./arch/x86/include/generated/uapi -I/build/linux-hwe-iAAoxd/linux-hwe-5.0.0/include/uapi -I./include/generated/uapi -include /build/linux-hwe-iAAoxd/linux-hwe-5.0.0/include/linux/kconfig.h -Iubuntu/include -I/build/linux-hwe-iAAoxd/linux-hwe-5.0.0/ubuntu/include -include /build/linux-hwe-iAAoxd/linux-hwe-5.0.0/include/linux/compiler_types.h  -I/build/linux-hwe-iAAoxd/linux-hwe-5.0.0/scripts/mod -Iscripts/mod -D__KERNEL__ -Wall -Wundef -Werror=strict-prototypes -Wno-trigraphs -fno-strict-aliasing -fno-common -fshort-wchar -fno-PIE -Werror-implicit-function-declaration -Werror=implicit-int -Wno-format-security -std=gnu89 -mno-sse -mno-mmx -mno-sse2 -mno-3dnow -mno-avx -m64 -falign-jumps=1 -falign-loops=1 -mno-80387 -mno-fp-ret-in-387 -mpreferred-stack-boundary=3 -mskip-rax-setup -mtune=generic -mno-red-zone -mcmodel=kernel -DCONFIG_X86_X32_ABI -DCONFIG_AS_CFI=1 -DCONFIG_AS_CFI_SIGNAL_FRAME=1 -DCONFIG_AS_CFI_SECTIONS=1 -DCONFIG_AS_FXSAVEQ=1 -DCONFIG_AS_SSSE3=1 -DCONFIG_AS_AVX=1 -DCONFIG_AS_AVX2=1 -DCONFIG_AS_AVX512=1 -DCONFIG_AS_SHA1_NI=1 -DCONFIG_AS_SHA256_NI=1 -Wno-sign-compare -fno-asynchronous-unwind-tables -mindirect-branch=thunk-extern -mindirect-branch-register -fno-jump-tables -fno-delete-null-pointer-checks -Wno-frame-address -Wno-format-truncation -Wno-format-overflow -Wno-int-in-bool-context -O2 --param=allow-store-data-races=0 -Wframe-larger-than=1024 -fstack-protector-strong -Wno-unused-but-set-variable -Wno-unused-const-variable -fno-omit-frame-pointer -fno-optimize-sibling-calls -fno-var-tracking-assignments -pg -mrecord-mcount -mfentry -DCC_USING_FENTRY -fno-inline-functions-called-once -Wdeclaration-after-statement -Wvla -Wno-pointer-sign -fno-strict-overflow -fno-merge-all-constants -fmerge-constants -fno-stack-check -fconserve-stack -Werror=date-time -Werror=incompatible-pointer-types -Werror=designated-init    -DKBUILD_BASENAME='"empty"' -DKBUILD_MODNAME='"empty"' -c -o scripts/mod/empty.o /build/linux-hwe-iAAoxd/linux-hwe-5.0.0/scripts/mod/empty.c

source_scripts/mod/empty.o := /build/linux-hwe-iAAoxd/linux-hwe-5.0.0/scripts/mod/empty.c

deps_scripts/mod/empty.o := \
  /build/linux-hwe-iAAoxd/linux-hwe-5.0.0/include/linux/kconfig.h \
    $(wildcard include/config/cpu/big/endian.h) \
    $(wildcard include/config/booger.h) \
    $(wildcard include/config/foo.h) \
  /build/linux-hwe-iAAoxd/linux-hwe-5.0.0/include/linux/compiler_types.h \
    $(wildcard include/config/have/arch/compiler/h.h) \
    $(wildcard include/config/enable/must/check.h) \
    $(wildcard include/config/arch/supports/optimized/inlining.h) \
    $(wildcard include/config/optimize/inlining.h) \
  /build/linux-hwe-iAAoxd/linux-hwe-5.0.0/include/linux/compiler_attributes.h \
  /build/linux-hwe-iAAoxd/linux-hwe-5.0.0/include/linux/compiler-gcc.h \
    $(wildcard include/config/retpoline.h) \
    $(wildcard include/config/arch/use/builtin/bswap.h) \

scripts/mod/empty.o: $(deps_scripts/mod/empty.o)

$(deps_scripts/mod/empty.o):
