	.file	"bounds.c"
# GNU C89 (Ubuntu 7.4.0-1ubuntu1~18.04.1) version 7.4.0 (x86_64-linux-gnu)
#	compiled by GNU C version 7.4.0, GMP version 6.1.2, MPFR version 4.0.1, MPC version 1.1.0, isl version isl-0.19-GMP

# GGC heuristics: --param ggc-min-expand=100 --param ggc-min-heapsize=131072
# options passed:  -nostdinc -I /usr/src/linux-headers-lbm-
# -I /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/arch/x86/include
# -I ./arch/x86/include/generated
# -I /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include -I ./include
# -I /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/arch/x86/include/uapi
# -I ./arch/x86/include/generated/uapi
# -I /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/uapi
# -I ./include/generated/uapi -I ubuntu/include
# -I /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/ubuntu/include
# -I /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/. -I .
# -imultiarch x86_64-linux-gnu -D __KERNEL__ -D CONFIG_X86_X32_ABI
# -D CONFIG_AS_CFI=1 -D CONFIG_AS_CFI_SIGNAL_FRAME=1
# -D CONFIG_AS_CFI_SECTIONS=1 -D CONFIG_AS_FXSAVEQ=1 -D CONFIG_AS_SSSE3=1
# -D CONFIG_AS_AVX=1 -D CONFIG_AS_AVX2=1 -D CONFIG_AS_AVX512=1
# -D CONFIG_AS_SHA1_NI=1 -D CONFIG_AS_SHA256_NI=1 -D CC_USING_FENTRY
# -D KBUILD_BASENAME="bounds" -D KBUILD_MODNAME="bounds"
# -isystem /usr/lib/gcc/x86_64-linux-gnu/7/include
# -include /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/kconfig.h
# -include /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/compiler_types.h
# -MD kernel/.bounds.s.d
# /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/kernel/bounds.c -mno-sse -mno-mmx
# -mno-sse2 -mno-3dnow -mno-avx -m64 -mno-80387 -mno-fp-ret-in-387
# -mpreferred-stack-boundary=3 -mskip-rax-setup -mtune=generic
# -mno-red-zone -mcmodel=kernel -mindirect-branch=thunk-extern
# -mindirect-branch-register -mrecord-mcount -mfentry -march=x86-64
# -auxbase-strip kernel/bounds.s -O2 -Wall -Wundef
# -Werror=strict-prototypes -Wno-trigraphs
# -Werror=implicit-function-declaration -Werror=implicit-int
# -Wno-format-security -Wno-sign-compare -Wno-frame-address
# -Wformat-truncation=0 -Wformat-overflow=0 -Wno-int-in-bool-context
# -Wframe-larger-than=1024 -Wno-unused-but-set-variable
# -Wunused-const-variable=0 -Wdeclaration-after-statement -Wvla
# -Wno-pointer-sign -Werror=date-time -Werror=incompatible-pointer-types
# -Werror=designated-init -std=gnu90 -p -fno-strict-aliasing -fno-common
# -fshort-wchar -fno-PIE -falign-jumps=1 -falign-loops=1
# -fno-asynchronous-unwind-tables -fno-jump-tables
# -fno-delete-null-pointer-checks -fstack-protector-strong
# -fno-omit-frame-pointer -fno-optimize-sibling-calls
# -fno-var-tracking-assignments -fno-inline-functions-called-once
# -fno-strict-overflow -fno-merge-all-constants -fmerge-constants
# -fstack-check=no -fconserve-stack -fverbose-asm
# --param allow-store-data-races=0 -fstack-protector-strong
# options enabled:  -faggressive-loop-optimizations -falign-labels
# -fauto-inc-dec -fbranch-count-reg -fcaller-saves
# -fchkp-check-incomplete-type -fchkp-check-read -fchkp-check-write
# -fchkp-instrument-calls -fchkp-narrow-bounds -fchkp-optimize
# -fchkp-store-bounds -fchkp-use-static-bounds
# -fchkp-use-static-const-bounds -fchkp-use-wrappers -fcode-hoisting
# -fcombine-stack-adjustments -fcompare-elim -fcprop-registers
# -fcrossjumping -fcse-follow-jumps -fdefer-pop -fdevirtualize
# -fdevirtualize-speculatively -fdwarf2-cfi-asm -fearly-inlining
# -feliminate-unused-debug-types -fexpensive-optimizations
# -fforward-propagate -ffp-int-builtin-inexact -ffunction-cse -fgcse
# -fgcse-lm -fgnu-runtime -fgnu-unique -fguess-branch-probability
# -fhoist-adjacent-loads -fident -fif-conversion -fif-conversion2
# -findirect-inlining -finline -finline-atomics -finline-small-functions
# -fipa-bit-cp -fipa-cp -fipa-icf -fipa-icf-functions -fipa-icf-variables
# -fipa-profile -fipa-pure-const -fipa-reference -fipa-sra -fipa-vrp
# -fira-hoist-pressure -fira-share-save-slots -fira-share-spill-slots
# -fisolate-erroneous-paths-dereference -fivopts -fkeep-static-consts
# -fleading-underscore -flifetime-dse -flra-remat -flto-odr-type-merging
# -fmath-errno -fmerge-constants -fmerge-debug-strings
# -fmove-loop-invariants -foptimize-strlen -fpartial-inlining -fpeephole
# -fpeephole2 -fplt -fprefetch-loop-arrays -fprofile -free
# -freg-struct-return -freorder-blocks -freorder-functions
# -frerun-cse-after-loop -fsched-critical-path-heuristic
# -fsched-dep-count-heuristic -fsched-group-heuristic -fsched-interblock
# -fsched-last-insn-heuristic -fsched-rank-heuristic -fsched-spec
# -fsched-spec-insn-heuristic -fsched-stalled-insns-dep -fschedule-fusion
# -fschedule-insns2 -fsemantic-interposition -fshow-column -fshrink-wrap
# -fshrink-wrap-separate -fsigned-zeros -fsplit-ivs-in-unroller
# -fsplit-wide-types -fssa-backprop -fssa-phiopt -fstack-protector-strong
# -fstdarg-opt -fstore-merging -fstrict-volatile-bitfields -fsync-libcalls
# -fthread-jumps -ftoplevel-reorder -ftrapping-math -ftree-bit-ccp
# -ftree-builtin-call-dce -ftree-ccp -ftree-ch -ftree-coalesce-vars
# -ftree-copy-prop -ftree-cselim -ftree-dce -ftree-dominator-opts
# -ftree-dse -ftree-forwprop -ftree-fre -ftree-loop-if-convert
# -ftree-loop-im -ftree-loop-ivcanon -ftree-loop-optimize
# -ftree-parallelize-loops= -ftree-phiprop -ftree-pre -ftree-pta
# -ftree-reassoc -ftree-scev-cprop -ftree-sink -ftree-slsr -ftree-sra
# -ftree-switch-conversion -ftree-tail-merge -ftree-ter -ftree-vrp
# -funit-at-a-time -fverbose-asm -fzero-initialized-in-bss
# -m128bit-long-double -m64 -malign-stringops -mavx256-split-unaligned-load
# -mavx256-split-unaligned-store -mfentry -mfxsr -mglibc -mieee-fp
# -mindirect-branch-register -mlong-double-80 -mno-fancy-math-387
# -mno-red-zone -mno-sse4 -mpush-args -mrecord-mcount -mskip-rax-setup
# -mtls-direct-seg-refs -mvzeroupper

	.text
	.section	.text.startup,"ax",@progbits
	.p2align 4,,15
	.globl	main
	.type	main, @function
main:
1:	call	__fentry__
	.section __mcount_loc, "a",@progbits
	.quad 1b
	.previous
	pushq	%rbp	#
	movq	%rsp, %rbp	#,
# /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/kernel/bounds.c:19: 	DEFINE(NR_PAGEFLAGS, __NR_PAGEFLAGS);
#APP
# 19 "/build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/kernel/bounds.c" 1
	
.ascii "->NR_PAGEFLAGS $26 __NR_PAGEFLAGS"	#
# 0 "" 2
# /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/kernel/bounds.c:20: 	DEFINE(MAX_NR_ZONES, __MAX_NR_ZONES);
# 20 "/build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/kernel/bounds.c" 1
	
.ascii "->MAX_NR_ZONES $5 __MAX_NR_ZONES"	#
# 0 "" 2
# /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/kernel/bounds.c:22: 	DEFINE(NR_CPUS_BITS, ilog2(CONFIG_NR_CPUS));
# 22 "/build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/kernel/bounds.c" 1
	
.ascii "->NR_CPUS_BITS $13 ilog2(CONFIG_NR_CPUS)"	#
# 0 "" 2
# /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/kernel/bounds.c:24: 	DEFINE(SPINLOCK_SIZE, sizeof(spinlock_t));
# 24 "/build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/kernel/bounds.c" 1
	
.ascii "->SPINLOCK_SIZE $4 sizeof(spinlock_t)"	#
# 0 "" 2
# /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/kernel/bounds.c:28: }
#NO_APP
	xorl	%eax, %eax	#
	popq	%rbp	#
	ret
	.size	main, .-main
	.ident	"GCC: (Ubuntu 7.4.0-1ubuntu1~18.04.1) 7.4.0"
	.section	.note.GNU-stack,"",@progbits
