# Karel Processing Unit

**(Outdated and Deprecated; development moved to `KPUv1b`)**

An octal-digit based CPU run entirely by Karel the robot.

This file describes the high level workings of the `KPUv1` architecture
## Implementation

`kat` (`karel digit`) - octal-base digit (8 possible states)
`Kyte` - 4 `kats` (4096 possible states)

overlap with real world architectures:
- City = Registers, Ram, ALU operations (see [[#Arithmetic and Logic]])
- Karel = Control Unit, Memory Controller
- Tags / City cells = Memory cell (1 `kat`)
- Karel Code = CPU Microcode

Apart from main addressable memory `KPUv1` contains:
- 8 registers (indexible by 1 `kat`)
- Program Counter
- ALU flags (less, equal, grater, zero)
- 10 `Kytes` of `op_mem` cache

## Instructions

One Instruction is always aligned to a single `Kyte`.
It's constructed from and `kat` sized Id and its attributes. (also `kat` sized)

This `KPUv1` supports the following instructions:

| Name | kat Id | Attributes | Description |
| -- | -- | -- | -- |
| add | `00` | r0, r1 | Adds r1 to r0 |
| sub | `01` | r0, r1 | Subs r1 from r0 |
| mul | `02` | r0, r1 | Multiplies r1 and r0 |
| inc | `03` | r0 | Adds 1 to r0 |
| dec | `04` | r0 | Subs 1 to r0 |
| mov | `05` | var, r0, r1 | General Move Instruction (var sets move variant) |
| mov_local |
| mov_to | `06` | r0, r1 | Moves `Kyte` from address in r1 to r0 | 
| mov_from | `07` | r0, r1 | Moves `Kyte` from r0 to address in r1 |
| mov_literal | `10` | r0 | Moves the next `Kyte` to r0 | 
| drain_reg | `11` | r0 | Nullifies r0 register |
| drain_adr | `12` | r0 | Nullifies address in r0 |
| cmp | `13` | r0, r1 | Compare two registers and set ALU flags |
| jmp | `13` | r0, con | Jump (set Program Counter) to address in r0 (Possibly Conditional) |
| test | `14` | r0 | A "Compare" for one register|

## Memory

The City (or Memory as it will be referred to from now on) is split into 2 segments:
- fixed-space registers and `op_mem`
- addressable RAM

And so for that reason Karel (when acting as the Memory Controller) has two modes he can operate in. In fixed-space mode, Karel always knows (aka the Microcode knows) **exactly** where Karel currently is. This allows for efficient fixed movement on the Memory without the need for any looped scanning of his position.

The opposite is the relative (addressable) mode. In relative mode, Karel doesn't know exactly where he is. Relative mode is only used for addressing the RAM, after the address and it's value has been found, Karel immediately aligns himself to the fixed-space mode. 

Here's an overview of the Memory segments as they are in physical space:
![[2023-10-17-211014_hyprshot.png]]

### `op_mem` cache
This is just an implementation detail but an important one.

Because Karel himself has a really small amount of memory nearing 0 we have to get creative when moving things around.

The only common way to read and save a **single** bit of data is trough *recursion*. The only problem is that recursive reads of `KPUv1s` data units (tags) are **destructive**, You can read it once but you delete the data in the process. And i found only a single way to work around this.

The `op_mem` is like a stack of shadow registers, it is 10 `Kytes` in size and it is essentially invisible to the `KPUv1` instructions. (it's managed only by the Microcode)

The point is that when the `KPUv1` needs to read **any** register **or any** address it will first *cache* the value to `op_mem` by doing a so called *copy-fetch*.

Then `op_mem` is used by the instructions as the *operating memory* where data can be overridden and destroyed freely. It essentially acts as the registers of the individual instructions. 

> note: because `op_mems` lifetime is only a single instruction (`op_mem` caches are never shared), the layout of `op_mem` caches is also specific to every instruction.

### *copy-fetching*

>TL;DR the job of a *copy-fetch* is to copy data from source to destination without destroying the data stored in source.

*copy-fetch* pseudo-code:
```
recursive_start(read value) ->  
	goto `op_mem` ->
recursive_end(write to `op_mem` -> write to `op_mem`) ->

recursive_start(read `op_mem`) ->
	goto value ->
recursive_end(write to value) -> `end`
```

After a value has been *copy-fetched* to an `op_mem` cache, it can be recursively read from the `op_mem` without any data loss.

The Microcode will also precache *copy-fetches* by copying to 2 or more `op_mem` caches in the same *copy-fetch* allowing to re-read the same value multiple times. This is called a *copy-**pre**fetch*

the `KPUv1` supports these *copy-fetch* subroutines:
- `copy-fetch[r, op]` - *fetch* a register to a `op_mem` cache (eg. `copy-fetch[r2, op1]`)
- `copy-prefetch[r, op, num]` - *prefetch* a register to multiple `op_mem` caches (eg. `copy-prefetch[r6, 3, op1` will fill `op1`, `op2`, `op3` with `r6` contents)
- `rel-copy-fetch[adr_r, r]` - *fetch* to a register `r` from address stored in register `adr_r`

This can be extended to essentially ***save and load*** *recursive states* by saving to multiple `op_mem` caches.

> note: `op0` cache exists but it's reserved for the *copy-fetching* subroutines for their internal execution

## Arithmetic and Logic

Karel is quite limited when it comes to arithmetic by basically not being capable of it.

All he can do is really increment or decrement tags in a cell + some recursive logic.
In the `KPUv1` simple arithmetic operations are supported using *tag-counting* on the `op_mem` caches.

> Signed integers or any floating point numbers are **not** supported

Supported `KPUv1` operations:
- Addition and Subtraction using basic *tag-counting* and `is tag` checks.
- Multiplication using recursive tag incrementing

> Division is not currently supported

> note: unsigned overflow and underflow work as expected

Possible Future:
- Accelerated by 2 and by 4 Modulation (% operation) using Karel's rotation

Due to how Karel stores tags, trying to increment a cell that already has 8 tags is a hardware crash and must be prevented by the Microcode.

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

Addition is essentially Inverted Substraction because Karel can check for zero tags but not max tags.

Therefore Substraction is just an Addition operation without the invert on the beginning and end.

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

Modulation by 4 pseudo-code:
```
// fetch first kat to op_mem
copy-fetch-kat0[r0, op1]

// start modulation
goto op1

// note: only first kat can affect the mod result
recursive_start(
	read kat0 of op1
)
	// align for mod
	align to north
recursive_end(
	turn-left
)

drain

if to north
else if to east
	place 1
	align
else if to south
	place 2
	align
else if to west
	place 3
	align
end

write kat of op1 to r0
```
## Control Logic

Conditions and Jumps are (for the first time) pretty simple with Karel's default capabilities.

Conditions are handled by Karel alone with his if statements, the part where we actually have to help Karel is expressing the condition. 

For example if you want to conditionally jump when a value is equal to another, you need to first execute a `cmp` instruction to compare the value(s) raise the ALU flags and then do a conditional jump by executing a `jmp` instruction with the condition var set:

```
cmp 0, 2 // compare register 0 and 2
jmp 1, 3 // jump to address in register 1 if grater ALU flag is set
```

`cmp` pseudo-code:
```
// fetch to op_mem
copy-fetch[r0, op1]
copy-fetch[r1, op2]

// substract
sub op1 op2

// set flags
if underflow
	set less
else if zero
	set equal
else
	set grater
end

```