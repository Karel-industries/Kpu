# Karel Extensible Aggressively Packed Architecture

> Still WIP, major parts are missing

## Instruction Layout and Architecture

- A singular *instruction* in a `keap` machine is an operation that the host machine is able to carry out.
- *Instructions* are contained inside *Instruction Sets* which are lists of of 729 (9^3) *instructions* encoded using an *instruction id*.
	- note: for better clarity, *instruction ids* are represented as a pair of ids: a group id (`gid`; 0-8) and a instruction id (`iid`; 0-80)
	- note: because *sets* and id groups are usually created as list of related *instructions*, not all *instruction ids* inside a *set* have to be populated. Usage of unused *instruction ids* is a [[#Faults (`STOPs`)|fault]]
- An *instruction id* can encode an *instruction* with all its parameters as *instruction* parameters (like conditions and registers) are expanded into all possible *instruction permutations* every one of which has its own *instruction id*.
- An *Instruction opcode* encodes an *instruction id* in memory, it is stored inside a single `kyte`, more specifically it's encoded as a group id (kat 0) and an instruction id. (high - kat 1; low - kat 2)
- An *Instruction Set* can encode one of its *instruction ids* as an *extended instruction*. *Extended Instructions* opcodes are followed (in ram) by a second *instruction opcode* which encodes an *instruction id* into a **different** *Instruction Set*. As a convention the first `gid` of a *set* is dedicated to *Extended Instructions*.
- *Instruction opcodes* can have data embedded in `Kytes` right after the opcode in ram. The instruction is responsible to jumping to the next valid *Instruction* opcode.
- A *Root Instruction Set* is the *set* which is used for interpreting the first *Instruction opcode* when fetching an *instruction*. The *Root Instruction Set* is identical between all `keap` machines with the same `keap` arch level.
- A `keap` machine is a machine which operates on the `keap` arch model and supports the minimal *requirements*. These can vary based on the `keap` arch level supported.
- A `keap` machine can support extra `keap` extensions which increase requirements by new *instruction sets* mapped as *extended instructions*.

---

## `keap-v1` Minimal Requirements

This section describes what requirements a `keap` machine must support to be able to execute `keap-v1` machine code.

### Fixed Space Requirements

Minimal Registers Features:
- `r0`, `r1`, `r2`, `r3` - general reg; arithmetic capable; remote address reg
- `r4`/`pc` - memory instruction group only; remote address reg; *Program Counter*

one `kat` register reserved for fault codes.

### Root Instruction Set

This `keap-v1` supports the following instruction groups:

| gid | name | description |
| ---- | ---- | ---- |
| `0` | extended | A gid reserved for extended instruction sets |
| `1` | memory | Instructions for managing and moving `Kytes` of data |
| `2` | arithmetic | Instructions for processing data stored in registers |
| `4` | control | Instructions for controlling conditional execution and branching  |
| `5` | control-2 | Instructions for controlling conditional execution and branching (part 2) |

Specific instructions are described in their group segments bellow.

> [!warning]
>  Unknown gid and iid combinations will cause a [[#Faults (`STOPs`)|fault]]

#### Memory Instructions
| iid | name | description |
| ---- | ---- | ---- |
| `0-9` | `swp` | fast local-to-local swap. Swaps the data between two regs |
| `10-29` | `wll` | local-to-local write. Copies data from reg to reg2 |
| `30-49` | `wlr` | local-to-remote write. Copies data from reg to an address in adr_reg |
| `50-69` | `wrl` | remote-to-local write. Copies data from an address adr_reg to reg |
| `70-74` | `drl` | local drain. Sets a local register to zero |
| `75-79` | `drr` | remote drain. Sets a remote address to zero |

Register arguments are packed as *permutations*. Addresses can be read only from *Remote Address Registers* (see [[#Register Features]])

#### Arithmetic Instructions

| iid | name | description |
| ---- | ---- | ---- |
| `0-15` | `uadd` | Adds unsigned value in reg2 to reg. Saves result to reg. |
| `16-27` | `usub` | Subtracts unsigned value in reg2 from reg. Saves result to reg |
| `28-39` | `umul` | Multiplies unsigned reg and reg2 and saves result to reg. |
|  | `udiv` | Long Divides unsigned reg by reg2 and saves result to reg. |
| `40-43` | `uinc` | Increments unsigned reg by 1 |
| `44-47` | `udec` | Decrements unsigned reg by 1 |
|  | `sadd` | Adds signed value in reg2 to reg. Saves result to reg. |
|  | `ssub` | Subtracts signed value in reg2 from reg. Saves result to reg |
|  | `smul` | Multiplies signed reg and reg2 and saves result to reg. |
|  | `sdiv` | Long Divides signed reg by reg2 and saves result to reg. |
|  | `sign` | Converts value in reg from unsigned to signed form. |
|  | `unsign` | Converts value in reg from signed to unsigned form. |
|  | `ueval` | Sets ALU Flags based on a unsigned value in a reg |
|  | `ucmp` | Sets ALU Flags based on the relation between two unsigned values in reg and reg2 |

> [!warning]
> - division by zero will cause a [[#Faults (`STOPs`)|fault]]
> - conversion from a negative signed integer to unsigned will cause a [[#Faults (`STOPs`)|fault]]

#### Conditional Instructions

Unless extended by an extension, all conditional execution on a `keap` machine is done using *Conditional Bits*. Instead of conventional instructions like conditional jumps (`x86`) and generic conditional flags (`ARM`), *Conditional Bits* are instructions that control whether the *Execute* stage of the *CPU Pipeline* is **Disabled** until another *Conditional Bit* instruction is encountered.

This allows for space efficient conditionals on small branches like simple if statements.

```keap-asm
wrl r1 r0

cel // disables the execution if a condition is not met

// instructions here are scipped if condition is not met
wlr r1 r2
uinc r0

bl r0

re // resumes execution if disabled (no-op otherwise)

halt
```

The suffix syntax is modelled after the `arm` arch. add these behind a conditional instruction to specify the condition

| Condition code | Meaning |
| ---- | ---- |
| `eq` | Equal |
| `ne` | Not Equal |
| `nz` | Not Zero |
| `iz` | Zero |
| `of` | Overflow |
| `uf` | Underflow |
| `nf` | Normalflow |
| `gt` | Greter than |
| `lt` | Lesser than |
| `ge` | Greter or equal |
| `le` | Lesser or equal |

This instruction group implements *Conditional Bits* together with conventional *unconditional* branching/jumping instructions.

> [!note]
> if you need non-linking branching use a `wll` or any of the other write operations to register `r4`/`pc` 

| iid | name | description |
| ---- | ---- | ---- |
| `0` | `bl` | Linked Branch to routine in reg. Saves origin routine address + 1 to `r3` |
|  | `sbl` | Swapping Linked Branch. Branches to routine in `r3` while saving the origin routine address + 1 to `r3`. |
|  | `ce` | Conditional Execution. Disables *Execute* stage of the CPU Pipeline if the condition **is not** met. |
|  | `de` | Conditional Disable. Disables *Execute* stage of the CPU Pipeline if the condition **is** met. |
|  | `re` | Resume Execution. Resumes *Execute* stage if it is currently Conditionally disabled, otherwise no-op. |
|  | `halt` |  |
|  | `fault` |  |

#### Control Instructions

Instructions for controlling code flow and the CPU.

- `halt`
- `fault`

---
### Faults (`STOPs`)

Faults (which are invoked by `STOP` commands) are used in `keap` as an "error" event.  You could compare these to an `assert` from other languages.

A Fault is raised when a situation that should never happen is encountered, the current list of possible faults is:
- Unknown Instruction Fault - code `0`
- Out Of Bounds Address Fault - code `1`
- Unreachable Microcode (Reserved) Fault - code `2`
- Division By Zero Fault - code `3`
- Negative Unsigned Value Conversion Fault - code `4`

more may be added..

When Faults occur, Karel travels to the top right square, dumps the Fault code and `STOPs`. 

> [!warning]
> Faults are mostly generated by bugs in the Microcode and are a way of debugging the `KPUv1b`. Some faults however can be caused by wrong code provided by the user, for example jumping to a random address can raise an Unknown Instruction Fault.

> [!danger]
> If you get a fault from the KPU and want to run it again, **check the data** before running it because some faults (eg. the out of bounds fault) can bail before restoring data and ***cause data loss!***

---

`But can it run Crysis...`