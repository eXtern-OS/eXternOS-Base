cmd_kernel/bounds.s := gcc -Wp,-MD,kernel/.bounds.s.d  -nostdinc -isystem /usr/lib/gcc/x86_64-linux-gnu/7/include -I/usr/src/linux-headers-lbm- -I/build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/arch/x86/include -I./arch/x86/include/generated  -I/build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include -I./include -I/build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/arch/x86/include/uapi -I./arch/x86/include/generated/uapi -I/build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/uapi -I./include/generated/uapi -include /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/kconfig.h -Iubuntu/include -I/build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/ubuntu/include -include /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/compiler_types.h  -I/build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/. -I. -D__KERNEL__ -Wall -Wundef -Werror=strict-prototypes -Wno-trigraphs -fno-strict-aliasing -fno-common -fshort-wchar -fno-PIE -Werror-implicit-function-declaration -Werror=implicit-int -Wno-format-security -std=gnu89 -mno-sse -mno-mmx -mno-sse2 -mno-3dnow -mno-avx -m64 -falign-jumps=1 -falign-loops=1 -mno-80387 -mno-fp-ret-in-387 -mpreferred-stack-boundary=3 -mskip-rax-setup -mtune=generic -mno-red-zone -mcmodel=kernel -DCONFIG_X86_X32_ABI -DCONFIG_AS_CFI=1 -DCONFIG_AS_CFI_SIGNAL_FRAME=1 -DCONFIG_AS_CFI_SECTIONS=1 -DCONFIG_AS_FXSAVEQ=1 -DCONFIG_AS_SSSE3=1 -DCONFIG_AS_AVX=1 -DCONFIG_AS_AVX2=1 -DCONFIG_AS_AVX512=1 -DCONFIG_AS_SHA1_NI=1 -DCONFIG_AS_SHA256_NI=1 -Wno-sign-compare -fno-asynchronous-unwind-tables -mindirect-branch=thunk-extern -mindirect-branch-register -fno-jump-tables -fno-delete-null-pointer-checks -Wno-frame-address -Wno-format-truncation -Wno-format-overflow -Wno-int-in-bool-context -O2 --param=allow-store-data-races=0 -Wframe-larger-than=1024 -fstack-protector-strong -Wno-unused-but-set-variable -Wno-unused-const-variable -fno-omit-frame-pointer -fno-optimize-sibling-calls -fno-var-tracking-assignments -pg -mrecord-mcount -mfentry -DCC_USING_FENTRY -fno-inline-functions-called-once -Wdeclaration-after-statement -Wvla -Wno-pointer-sign -fno-strict-overflow -fno-merge-all-constants -fmerge-constants -fno-stack-check -fconserve-stack -Werror=date-time -Werror=incompatible-pointer-types -Werror=designated-init    -DKBUILD_BASENAME='"bounds"' -DKBUILD_MODNAME='"bounds"'  -fverbose-asm -S -o kernel/bounds.s /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/kernel/bounds.c

source_kernel/bounds.s := /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/kernel/bounds.c

deps_kernel/bounds.s := \
    $(wildcard include/config/smp.h) \
    $(wildcard include/config/nr/cpus.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/kconfig.h \
    $(wildcard include/config/cpu/big/endian.h) \
    $(wildcard include/config/booger.h) \
    $(wildcard include/config/foo.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/compiler_types.h \
    $(wildcard include/config/have/arch/compiler/h.h) \
    $(wildcard include/config/enable/must/check.h) \
    $(wildcard include/config/arch/supports/optimized/inlining.h) \
    $(wildcard include/config/optimize/inlining.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/compiler_attributes.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/compiler-gcc.h \
    $(wildcard include/config/retpoline.h) \
    $(wildcard include/config/arch/use/builtin/bswap.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/page-flags.h \
    $(wildcard include/config/mmu.h) \
    $(wildcard include/config/arch/uses/pg/uncached.h) \
    $(wildcard include/config/memory/failure.h) \
    $(wildcard include/config/idle/page/tracking.h) \
    $(wildcard include/config/64bit.h) \
    $(wildcard include/config/debug/vm.h) \
    $(wildcard include/config/highmem.h) \
    $(wildcard include/config/swap.h) \
    $(wildcard include/config/thp/swap.h) \
    $(wildcard include/config/ksm.h) \
    $(wildcard include/config/transparent/hugepage.h) \
    $(wildcard include/config/hugetlb/page.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/types.h \
    $(wildcard include/config/have/uid16.h) \
    $(wildcard include/config/uid16.h) \
    $(wildcard include/config/lbdaf.h) \
    $(wildcard include/config/arch/dma/addr/t/64bit.h) \
    $(wildcard include/config/phys/addr/t/64bit.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/uapi/linux/types.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/arch/x86/include/uapi/asm/types.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/uapi/asm-generic/types.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/asm-generic/int-ll64.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/uapi/asm-generic/int-ll64.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/arch/x86/include/uapi/asm/bitsperlong.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/asm-generic/bitsperlong.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/uapi/asm-generic/bitsperlong.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/uapi/linux/posix_types.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/stddef.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/uapi/linux/stddef.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/compiler_types.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/arch/x86/include/asm/posix_types.h \
    $(wildcard include/config/x86/32.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/arch/x86/include/uapi/asm/posix_types_64.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/uapi/asm-generic/posix_types.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/bug.h \
    $(wildcard include/config/generic/bug.h) \
    $(wildcard include/config/bug/on/data/corruption.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/arch/x86/include/asm/bug.h \
    $(wildcard include/config/debug/bugverbose.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/stringify.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/asm-generic/bug.h \
    $(wildcard include/config/bug.h) \
    $(wildcard include/config/generic/bug/relative/pointers.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/compiler.h \
    $(wildcard include/config/trace/branch/profiling.h) \
    $(wildcard include/config/profile/all/branches.h) \
    $(wildcard include/config/stack/validation.h) \
    $(wildcard include/config/kasan.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/arch/x86/include/asm/barrier.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/arch/x86/include/asm/alternative.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/arch/x86/include/asm/asm.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/arch/x86/include/asm/nops.h \
    $(wildcard include/config/mk7.h) \
    $(wildcard include/config/x86/p6/nop.h) \
    $(wildcard include/config/x86/64.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/asm-generic/barrier.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/kasan-checks.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/kernel.h \
    $(wildcard include/config/preempt/voluntary.h) \
    $(wildcard include/config/debug/atomic/sleep.h) \
    $(wildcard include/config/prove/locking.h) \
    $(wildcard include/config/arch/has/refcount.h) \
    $(wildcard include/config/lock/down/kernel.h) \
    $(wildcard include/config/lock/down/mandatory.h) \
    $(wildcard include/config/panic/timeout.h) \
    $(wildcard include/config/tracing.h) \
    $(wildcard include/config/ftrace/mcount/record.h) \
  /usr/lib/gcc/x86_64-linux-gnu/7/include/stdarg.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/linkage.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/export.h \
    $(wildcard include/config/modules.h) \
    $(wildcard include/config/modversions.h) \
    $(wildcard include/config/module/rel/crcs.h) \
    $(wildcard include/config/have/arch/prel32/relocations.h) \
    $(wildcard include/config/trim/unused/ksyms.h) \
    $(wildcard include/config/unused/symbols.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/arch/x86/include/asm/linkage.h \
    $(wildcard include/config/x86/alignment/16.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/bitops.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/bits.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/arch/x86/include/asm/bitops.h \
    $(wildcard include/config/x86/cmov.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/arch/x86/include/asm/rmwcc.h \
    $(wildcard include/config/cc/has/asm/goto.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/asm-generic/bitops/find.h \
    $(wildcard include/config/generic/find/first/bit.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/asm-generic/bitops/sched.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/arch/x86/include/asm/arch_hweight.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/arch/x86/include/asm/cpufeatures.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/arch/x86/include/asm/required-features.h \
    $(wildcard include/config/x86/minimum/cpu/family.h) \
    $(wildcard include/config/math/emulation.h) \
    $(wildcard include/config/x86/pae.h) \
    $(wildcard include/config/x86/cmpxchg64.h) \
    $(wildcard include/config/x86/use/3dnow.h) \
    $(wildcard include/config/matom.h) \
    $(wildcard include/config/paravirt.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/arch/x86/include/asm/disabled-features.h \
    $(wildcard include/config/x86/intel/mpx.h) \
    $(wildcard include/config/x86/smap.h) \
    $(wildcard include/config/x86/intel/umip.h) \
    $(wildcard include/config/x86/intel/memory/protection/keys.h) \
    $(wildcard include/config/x86/5level.h) \
    $(wildcard include/config/page/table/isolation.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/asm-generic/bitops/const_hweight.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/asm-generic/bitops/le.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/arch/x86/include/uapi/asm/byteorder.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/byteorder/little_endian.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/uapi/linux/byteorder/little_endian.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/swab.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/uapi/linux/swab.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/arch/x86/include/uapi/asm/swab.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/byteorder/generic.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/asm-generic/bitops/ext2-atomic-setbit.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/log2.h \
    $(wildcard include/config/arch/has/ilog2/u32.h) \
    $(wildcard include/config/arch/has/ilog2/u64.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/typecheck.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/printk.h \
    $(wildcard include/config/message/loglevel/default.h) \
    $(wildcard include/config/console/loglevel/default.h) \
    $(wildcard include/config/console/loglevel/quiet.h) \
    $(wildcard include/config/early/printk.h) \
    $(wildcard include/config/printk/nmi.h) \
    $(wildcard include/config/printk.h) \
    $(wildcard include/config/kmsg/ids.h) \
    $(wildcard include/config/dynamic/debug.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/init.h \
    $(wildcard include/config/strict/kernel/rwx.h) \
    $(wildcard include/config/strict/module/rwx.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/kern_levels.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/cache.h \
    $(wildcard include/config/arch/has/cache/line/size.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/uapi/linux/kernel.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/uapi/linux/sysinfo.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/arch/x86/include/asm/cache.h \
    $(wildcard include/config/x86/l1/cache/shift.h) \
    $(wildcard include/config/x86/internode/cache/shift.h) \
    $(wildcard include/config/x86/vsmp.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/dynamic_debug.h \
    $(wildcard include/config/jump/label.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/jump_label.h \
    $(wildcard include/config/have/arch/jump/label/relative.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/arch/x86/include/asm/jump_label.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/build_bug.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/mmdebug.h \
    $(wildcard include/config/debug/virtual.h) \
    $(wildcard include/config/debug/vm/pgflags.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/mmzone.h \
    $(wildcard include/config/force/max/zoneorder.h) \
    $(wildcard include/config/cma.h) \
    $(wildcard include/config/memory/isolation.h) \
    $(wildcard include/config/numa.h) \
    $(wildcard include/config/zsmalloc.h) \
    $(wildcard include/config/memcg.h) \
    $(wildcard include/config/zone/dma.h) \
    $(wildcard include/config/zone/dma32.h) \
    $(wildcard include/config/zone/device.h) \
    $(wildcard include/config/sparsemem.h) \
    $(wildcard include/config/memory/hotplug.h) \
    $(wildcard include/config/compaction.h) \
    $(wildcard include/config/discontigmem.h) \
    $(wildcard include/config/flat/node/mem/map.h) \
    $(wildcard include/config/page/extension.h) \
    $(wildcard include/config/deferred/struct/page/init.h) \
    $(wildcard include/config/have/memory/present.h) \
    $(wildcard include/config/have/memoryless/nodes.h) \
    $(wildcard include/config/have/memblock/node/map.h) \
    $(wildcard include/config/need/multiple/nodes.h) \
    $(wildcard include/config/have/arch/early/pfn/to/nid.h) \
    $(wildcard include/config/flatmem.h) \
    $(wildcard include/config/sparsemem/extreme.h) \
    $(wildcard include/config/memory/hotremove.h) \
    $(wildcard include/config/have/arch/pfn/valid.h) \
    $(wildcard include/config/holes/in/zone.h) \
    $(wildcard include/config/arch/has/holes/memorymodel.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/kbuild.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/spinlock_types.h \
    $(wildcard include/config/debug/spinlock.h) \
    $(wildcard include/config/debug/lock/alloc.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/arch/x86/include/asm/spinlock_types.h \
    $(wildcard include/config/paravirt/spinlocks.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/asm-generic/qspinlock_types.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/asm-generic/qrwlock_types.h \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/lockdep.h \
    $(wildcard include/config/lockdep.h) \
    $(wildcard include/config/lock/stat.h) \
  /build/linux-hwe-zHO4ZF/linux-hwe-5.0.0/include/linux/rwlock_types.h \

kernel/bounds.s: $(deps_kernel/bounds.s)

$(deps_kernel/bounds.s):
