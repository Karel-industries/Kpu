This file describes a toolchain designed for the [[Karel Processing Unit v1b]] and its later versions.

This toolchain includes the `kasm` tool witch is an Assembler for the Karel Assembly language.

---
# Karel Assembly Language

eg.
```
.text 0n020

wll 0n001 r0
wll 0n005 r1

accumulate:
add r0 r1
comp r0 0n500
bls accumulate

halt
```

---
# Karel Assembler

Features:
- compile-time goto tags
- end of program `halt` checks
- basic Assembly validation
- helpful errors
- target architecture descriptor files
- built-in machine code flashing