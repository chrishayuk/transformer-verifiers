#!/bin/sh
# Builds ggml's own Q8_0 reference encoder (quantize_row_q8_0_ref) from the pinned source in inputs/, unmodified.
# The pinned tree omits gguf.h, ggml-cpu.h and ggml-cpu/ggml-cpu-impl.h, which the reference encoder does not use, so empty stubs
# stand in on the include path.
# stubs.c supplies the other ggml_* symbols the file references. They abort if called; only quantize_row_q8_0_ref is called.
set -eu
cd "$(dirname "$0")/.."
G=../../inputs/ggml-facdc44a67da17df4433adcc468b424f48e9ded2
(cd "$G" && shasum -a 256 -c SHA256SUMS >/dev/null)
mkdir -p build/stub/ggml-cpu
: > build/stub/gguf.h
: > build/stub/ggml-cpu.h
: > build/stub/ggml-cpu/ggml-cpu-impl.h
cc -O2 -fno-fast-math -std=c11 -D_DARWIN_C_SOURCE -I"$G/include" -I"$G/src" -Ibuild/stub \
   -dynamiclib -o build/libggmlq8ref.dylib "$G/src/ggml-quants.c" ggml_shim/stubs.c
