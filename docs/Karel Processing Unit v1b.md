# Karel Processing Unit
A nonary-digit based CPU run entirely by Karel the robot.

This file describes the high level workings of the `KPUv1b` implementation.

Table of Contents:
- [[#Overview]]
	- [[#CPU Pipeline]]

- [[#Instructions]]

- [[#Memory]]
	- [[#`op_mem` cache]]
	- [[#*copy-fetching*]]

- [[#Arithmetic and Logic]]
- [[#Faults (`STOPs`)]]

---
## Overview

The `KPUv1b` is a is a nonary/ternary digital processor. It supports many basic instructions that a normal CPU architecture would have like `add`, `wll` (`mov` equivalent) and `cmp`, etc. It can be programmed by putting instructions into its memory and pointing to it using its *Program Counter* or by using the [[Karel Assembly]] toolchain.

It supports memory operations, (unsigned integer) arithmetic operations, ternary logic operations, and proper comparison and branching. (see [[#Instructions]] for available instructions)

Due to limitations of Karel the main bottleneck of this design is Memory. Memory is solved using tags and the City that Karel lives on. Every square can have between 0 to 8 tags so 9 possible states (this is where the nonary base comes from) and the City can be at max 20 by 20 squares.

From these limits i named some basic units that would fit nicely onto the City: 
`kat` (`karel digit`) - nonary-base digit (9 possible states)
`Kyte` - 3 `kats` (729 possible states; equivalent to a `Tryte`)

The `KPUv1b` design tries to save space using methods like *ternary-packing* and *instruction permutations* but you still have to be very much aware of the Memory limits when coding for this arch as the current design has 120 `Kytes` of available Ram. (including code)

The `KPUv1b` is an implementation of the [[Keap Architecture Specification|keap]] architecture. (warning: very high amount of details, may induce headaches, you have been warned!)

some overlap with real world architectures:
- City = Registers, Ram, hidden registers
- Karel = Control Unit, Memory Controller and Memory Bus
- Tags / City squares = The simplest register (1 `kat`)
- Karel's Code = CPU Microcode

and maybe a *better* example from the real world overlap would be a VM:
- City = VMs state (Ram, regs, `op_mem`)
- Karel and Code = The Hypervisor

> [!todo]
> Future improvements in V2:
> - ISM (infinite stack machine) keap extension
> - fault handling
> - increased general refs count
> - unordered CPU Pipeline (`F_S_DR_E` model)
> - long kyte (6 kat) memory and arithmetic

---
### CPU Pipeline

This section describes the pipeline for executing the instruction at the program counters position.

main stages of the cpu pipeline are similar to a real cpu:
- `Fetch` - get instruction(s) from the Ram.
- `Decode` - decode requested instruction
- `Restore` - a *copy-fetch* like restoration of the instruction
- `Execute` - runs the instructions subroutine

Unlike in real world these stages *aren't* asynchronously executed because they are all handled by a single Karel

> [!todo]
> look into out-of-order CPU Pipeline design (`F_S_RD_E`) to potentially save a big amount of slow `Fetch` stages.

#### `Fetch` Stage

This stages job is to get to the next instructions position in the memory. It reads the *program counter* a simply addresses that location.

> [!warning]
> If the *program counter* is out of bound Microcode will raise a [[#Faults (`STOPs`)|fault]].

#### `Decode` and `Restore` Stage

This stages job is to find the internal branch referring to this *instruction permutation* in the giant if block of all possible permutations.

As reading is **destructive** in Karel, the `Restore` stage is responsible for restoring that instruction in memory.

> [!warning]
> Bad or Corrupted instructions (eg. by memory writes) can cause a [[#Faults (`STOPs`)|fault]] if the instruction id is not found.

#### `Execute` Stage

This stage executes the given instructions in the instructions branch. The *program counter* is incremented by the instruction size before the instruction executes.

Unless stopped by the instruction (eg. `halt`, `fault`) the cpu pipeline is stated again from the `Fetch` stage.

### Microcode Naming Conventions

To aid in readability of the Microcode this section defines some naming conventions that are followed by the Microcode source code.

- `do-stuff` - an internal function; no decorations
- `do-stuff<var>` - an internal function instantiated from a template
- `[user mid point]` - a part of a template to be implemented by their derivations (only in source; never should be present in the final Microcode)

- `==run==` - an user input function; equal enclosure; intended to be run by the user
- `__fetch__` - an core function starting or separating major systems (eg. CPU Pipeline stages)
- `// note` - an **no-op** function that serves as a comment in functions that use it

---
## Instructions

`KPUv1b` is a `keap` machine.

For a list of `KPUv1b` supported instructions, see [[Keap Architecture Specification#Root Instruction Set|keap root instruction set]]. (`KPUv1b` doesn't support any `keap` extensions)

---
## Memory

The City (or Memory as it will be referred to from now on) is split into 2 segments:
- fixed-space registers and `op_mem`
- addressable RAM

And so for that reason Karel has two modes he can operate in. In fixed-space mode, Karel always knows (aka the Microcode knows) **exactly** where Karel currently is. This allows for efficient fixed movement on the Memory without the need for any looped scanning of his position.

The opposite is the relative (addressable) mode. In relative mode, Karel doesn't know exactly where he is. Relative mode is only used for addressing the Ram, after the address and it's value has been found, Karel immediately aligns himself to the fixed-space mode. 

Here's an overview of the Memory segments as they are in physical space:
![[2023-11-14-172254_hyprshot.png]] 
### `op_mem` cache
This is just an implementation detail but an important one.

Because Karel himself has a really small amount of memory nearing 0 we have to get creative when moving things around.

The only real way to read and use a "variable" is trough *recursion*. The only problem is that recursive reads of `KPUv1b` data units (tags) are **destructive**, You can read a value once but you delete the data in the process. (and if you write the data back to restore it, you will lose the recursion) And together with *copy-fetching* this is a workaround around that issue.

The `op_mem` is like a stack of shadow registers, it is 5 `Kytes` in size and it is essentially invisible to `KPUv1b` instructions. (it's managed only by the Microcode)

The point is that when the `KPUv1b` needs to read **any** register **or any** address it will first *cache* the value to `op_mem` by doing a so called *copy-fetch*.

Then `op_mem` is used by the instructions as the *operating memory* where data can be overridden and destroyed freely. It essentially acts as the registers of the individual instructions. 

> [!note]
> because `op_mems` lifetime is only a single instruction (`op_mem` caches are never shared between instructions), the layout of `op_mem` caches is also specific to every instruction.

> [!warning]
> because `op_mem` is never shared, it is expected that it will be clean when executing a new instruction. Not cleaning the `op_mem` cache will cause *undefined behaviour*; if the `op_mem` cache is not clean between instructions, it's a Microcode bug.

### *copy-fetching*

>TL;DR the job of a *copy-fetch* is to copy data from source to destination without destroying the data stored in source.

*copy-fetch* pseudo-code:
```
recursive_start(read value) -> // destructively reads value
	goto `op_mem` ->
recursive_end(write to `op_mem` -> write to `op_mem`) -> // writes to op_mem two duplicats of data

recursive_start(read `op_mem`) -> // destructively reads one duplicate, leaving the other behind
	goto value ->
recursive_end(write to value) -> `end`
```

After a value has been *copy-fetched* to an `op_mem` cache, it can be recursively read from the `op_mem` without any data loss.

The Microcode will also precache *copy-fetches* by copying to 2 or more `op_mem` caches in the same *copy-fetch* allowing to re-read the same value multiple times for free. This is called a *copy-**pre**fetch*

the `KPUv1` supports these *copy-fetch* subroutines:
- `copy-fetch<r, op>` - *fetch* a register to a `op_mem` cache (eg. `copy-fetch<r2, op1>`) 
- `copy-prefetch<r, op[, op...]>` - *prefetch* a register to multiple `op_mem` caches (eg. `copy-prefetch<r1, op1, op2>` will fill `op1` and `op2` with `r1` contents)

This can be extended to essentially ***save and load*** *recursive states* by saving to multiple `op_mem` caches.

> [!note]
> `op0` cache exists but it's reserved for the *copy-fetching* subroutines for their internal execution

---
## Arithmetic and Logic

Karel's ability to effectively count tags is exploited in the `KPUv1b` for all arithmetic and logic that the arch can do.

The `KPUv1b` is capable of unsigned and signed integer arithmetic and very limited logic operations. 

Unsigned integers are encoded in a kyte as a nonary based (base 9) number.

A kyte containing a signed integer is encoded and packed as a *balanced ternary* based ([balanced ternary](https://en.wikipedia.org/wiki/Balanced_ternary) = { -1; 0; 1 }) number which is unpacked to its ternary form in `op_mem` when [operating](https://homepage.divms.uiowa.edu/~jones/ternary/multiply.shtml) on the value.

> Any forms of floating point numbers are **not** supported

> unsigned overflow and underflow work as on an real world machine, signed overflow and underflow not tested

## Unsigned Arithmetic

Due to how Karel stores tags, trying to increment a cell that already has 8 tags is a hardware fault and must be prevented by the Microcode. But the Microcode is able to check if there are 0 tags which leads to subtraction being *the* basic arithmetic operation on which other operations are derived from.

Subtraction pseudo-code:
```
// fetch registers to op_mem
copy-fetch[r0, op1]
copy-fetch[r1, op2]

// start subtraction
goto kat 0 of op2

// first kat without carry
recursive_start(read)
	goto op1
recursive_end (
	if tag
		dec
	else
		write 8
		goto op2
		inc // next carry
		goto op1
	end
)

goto op2

// add other kats with carry

for 3 (
	// check for carry
	if tag
		dec
		goto kat -1
		
		// add kat
		recursive_start(read)
			goto op1
		recursive_end(
			if tag
				dec
			else
				write 8
				goto op2
				inc // next carry
				goto op1
			end
		)
		
		// add last carry
		if tag
			dec
		else
			write 8
			goto op2
			inc // next carry
			goto op1
		end
		
		goto op2
)

if tag // check for underflow
	dec
	// may raise a underflow flag
end

write op1 to r0
```

Addition is essentially inverted Subtraction. We (kat-wise) invert one of the arguments at the start and at the end of the operation to *emulate* addition using substraction.

Addition pseudo-code:
```
// fetch registers to op_mem
copy-fetch[r0, op1]
copy-fetch[r1, op3]

invert op1 to op2 // does 8 - value for every kat

// start addition
goto kat 0 of op3

// first kat without carry
recursive_start(read)
	goto op2
recursive_end (
	if tag
		dec
	else
		write 8
		goto op3
		inc // next carry
		goto op2
	end
)

goto op3

// add other kats with carry

for 3 (
	// check for carry
	if tag
		dec
		goto kat -1
		
		// add kat
		recursive_start(read)
			goto op2
		recursive_end(
			if tag
				dec
			else
				write 8
				goto op3
				inc // next carry
				goto op2
			end
		)
		
		// add last carry
		if tag
			dec
		else
			write 8
			goto op3
			inc // next carry
			goto op2
		end
		
		goto op3
)

if tag // check for overflow
	dec
	// may raise a overflow flag
end

invert op2 to op1
write op1 to r0
```

Long Division possible pseudo-implementation (WIP):
```
// fetch divident and divisor
copy-fetch[r0, op2] // divisor
copy-fetch[r1, op4] // divident

// begin division

repeat 3
	copy-fetch[op2, op3]
	
	// todo: figure out how many digits are in the step
	div_step:
	recursive_start(
		read op3
	)
		move op4
	recursive_end(
		// todo: figure out if over remaider and write inverse of remainder
		dec
	)
	
	if tag
		// step not finished, inc result
		move op5
		inc
		move op3
		goto div_step
	else
		// step finished, write remainder
		inv op4 // invert *currently worked on* kats (8 - value)
		move op4 kat + 1
	end
	
end

// writeback result

drain op2
drain op4

write op5 to r0
```

## Signed (Ternary) Arithmetic

TODO