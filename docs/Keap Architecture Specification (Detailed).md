

# == GID 1 - memory instructions ==
## SWP - fast local-to-local swap (swaps between two regs)
| iid | kyte | registers |
| ---- | ---- | ---- |
| 0 | 1 0 0 | r0 <-> r1 |
| 1 | 1 0 1 | r0 <-> r2 |
| 2 | 1 0 2 | r0 <-> r3 |
| 3 | 1 0 3 | r0 <-> r4 |
| 4 | 1 0 4 | r1 <-> r2 |
| 5 | 1 0 5 | r1 <-> r3 |
| 6 | 1 0 6 | r1 <-> r4 |
| 7 | 1 0 7 | r2 <-> r3 |
| 8 | 1 0 8 | r2 <-> r4 |
| 9 | 1 0 9 | r3 <-> r4 |

## WLL - local to local write (copy from reg to reg2)
| iid | kyte | registers |
| ---- | ---- | ---- |
| 10 | 1 1 1 | r0 -> r1 |
| 11 | 1 1 2 | r0 -> r2 |
| 12 | 1 1 3 | r0 -> r3 |
| 13 | 1 1 4 | r0 -> r4 |
| 14 | 1 1 5 | r1 -> r0 |
| 15 | 1 1 6 | r1 -> r2 |
| 16 | 1 1 7 | r1 -> r3 |
| 17 | 1 1 8 | r1 -> r4 |
| 18 | 1 2 0 | r2 -> r0 |
| 19 | 1 2 1 | r2 -> r1 |
| 20 | 1 2 2 | r2 -> r3 |
| 21 | 1 2 3 | r2 -> r4 |
| 22 | 1 2 4 | r3 -> r0 |
| 23 | 1 2 5 | r3 -> r1 |
| 24 | 1 2 6 | r3 -> r2 |
| 25 | 1 2 7 | r3 -> r4 |
| 26 | 1 2 8 | r4 -> r0 |
| 27 | 1 3 0 | r4 -> r1 |
| 28 | 1 3 1 | r4 -> r2 |
| 29 | 1 3 2 | r4 -> r3 |

## WLR - local to remote write (copy data from reg to ram at reg2)
| iid | kyte | registers |
| ---- | ---- | ---- |
| 30 | 1 3 3 | r0 -> r1 |
| 31 | 1 3 4 | r0 -> r2 |
| 32 | 1 3 5 | r0 -> r3 |
| 33 | 1 3 6 | r0 -> r4 |
| 34 | 1 3 7 | r1 -> r0 |
| 35 | 1 3 8 | r1 -> r2 |
| 36 | 1 4 0 | r1 -> r3 |
| 37 | 1 4 1 | r1 -> r4 |
| 38 | 1 4 2 | r2 -> r0 |
| 39 | 1 4 3 | r2 -> r1 |
| 40 | 1 4 4 | r2 -> r3 |
| 41 | 1 4 5 | r2 -> r4 |
| 42 | 1 4 6 | r3 -> r0 |
| 43 | 1 4 7 | r3 -> r1 |
| 44 | 1 4 8 | r3 -> r2 |
| 45 | 1 5 0 | r3 -> r4 |
| 46 | 1 5 1 | r4 -> r0 |
| 47 | 1 5 2 | r4 -> r1 |
| 48 | 1 5 3 | r4 -> r2 |
| 49 | 1 5 4 | r4 -> r3 |

## WRL - remote to local write (copy data from ram at reg2 to reg)
| iid | kyte | registers |
| ---- | ---- | ---- |
| 50 | 1 5 5 | r0 <- r1 |
| 51 | 1 5 6 | r0 <- r2 |
| 52 | 1 5 7 | r0 <- r3 |
| 53 | 1 5 8 | r0 <- r4 |
| 54 | 1 6 0 | r1 <- r0 |
| 55 | 1 6 1 | r1 <- r2 |
| 56 | 1 6 2 | r1 <- r3 |
| 57 | 1 6 3 | r1 <- r4 |
| 58 | 1 6 4 | r2 <- r0 |
| 59 | 1 6 5 | r2 <- r1 |
| 60 | 1 6 6 | r2 <- r3 |
| 61 | 1 6 7 | r2 <- r4 |
| 62 | 1 6 8 | r3 <- r0 |
| 63 | 1 7 0 | r3 <- r1 |
| 64 | 1 7 1 | r3 <- r2 |
| 65 | 1 7 2 | r3 <- r4 |
| 66 | 1 7 3 | r4 <- r0 |
| 67 | 1 7 4 | r4 <- r1 |
| 68 | 1 7 5 | r4 <- r2 |
| 69 | 1 7 6 | r4 <- r3 |

## DRL - local drain (set local register to zero)
| iid | kyte | registers |
| ---- | ---- | ---- |
| 70 | 1 7 7 | r0 |
| 71 | 1 7 8 | r1 |
| 72 | 1 8 0 | r2 |
| 73 | 1 8 1 | r3 |
| 74 | 1 8 2 | r4 |

## DRR - remote drain (set remote address at reg to zero)
| iid | kyte | registers |
| ---- | ---- | ---- |
| 75 | 1 8 3 | r0 |
| 76 | 1 8 4 | r1 |
| 77 | 1 8 5 | r2 |
| 78 | 1 8 6 | r3 |
| 79 | 1 8 7 | r4 |


# == GID 2 - short kyte basic arithmetics ==

## UADD - add unsigned value in reg2 to reg
| iid | kyte | registers |
| ---- | ---- | ---- |
|  0 | 2 0 0 | r0 <- r0|
|  1 | 2 0 1 | r0 <- r1|
|  2 | 2 0 2 | r0 <- r2|
|  3 | 2 0 3 | r0 <- r3|
|  4 | 2 0 4 | r1 <- r0|
|  5 | 2 0 5 | r1 <- r1|
|  6 | 2 0 6 | r1 <- r2|
|  7 | 2 0 7 | r1 <- r3|
|  8 | 2 0 8 | r2 <- r0|
|  9 | 2 1 0 | r2 <- r1|
| 10 | 2 1 1 | r2 <- r2|
| 11 | 2 1 2 | r2 <- r3|
| 12 | 2 1 3 | r3 <- r0|
| 13 | 2 1 4 | r3 <- r1|
| 14 | 2 1 5 | r3 <- r2|
| 15 | 2 1 6 | r3 <- r3|

## USUB - substract unsigned value in reg2 from reg
| iid | kyte | registers |
| ---- | ---- | ---- |
| 16 | 2 1 7 | r0 <- r1 |
| 17 | 2 1 8 | r0 <- r2 |
| 18 | 2 2 0 | r0 <- r3 |
| 19 | 2 2 1 | r1 <- r0 |
| 20 | 2 2 2 | r1 <- r2 |
| 21 | 2 2 3 | r1 <- r3 |
| 22 | 2 2 4 | r2 <- r0 |
| 23 | 2 2 5 | r2 <- r1 |
| 24 | 2 2 6 | r2 <- r3 |
| 25 | 2 2 7 | r3 <- r0 |
| 26 | 2 2 8 | r3 <- r1 |
| 27 | 2 3 0 | r3 <- r2 |

## UMUL - multiply register by register2 (TODO/RESERVED)
| iids | kyte | registers |
| --- | --- | --- |
| 28 | 2 3 1 | r0 <- r1 |
| 29 | 2 3 2 | r0 <- r2 |
| 30 | 2 3 3 | r0 <- r3 |
| 31 | 2 3 4 | r1 <- r0 |
| 32 | 2 3 5 | r1 <- r2 |
| 33 | 2 3 6 | r1 <- r3 |
| 34 | 2 3 7 | r2 <- r0 |
| 35 | 2 3 8 | r2 <- r1 |
| 36 | 2 4 0 | r2 <- r3 |
| 37 | 2 4 1 | r3 <- r0 |
| 38 | 2 4 2 | r3 <- r1 |
| 39 | 2 4 3 | r3 <- r2 |


## UDIV - divide register by register2 (TODO/RESERVED)
| iids | kyte | registers |
| --- | --- | --- |
| 40 | 2 4 4 | r0 <- r1 |
| 41 | 2 4 5 | r0 <- r2 |
| 42 | 2 4 6 | r0 <- r3 |
| 43 | 2 4 7 | r1 <- r0 |
| 44 | 2 4 8 | r1 <- r2 |
| 45 | 2 5 0 | r1 <- r3 |
| 46 | 2 5 1 | r2 <- r0 |
| 47 | 2 5 2 | r2 <- r1 |
| 48 | 2 5 3 | r2 <- r3 |
| 49 | 2 5 4 | r3 <- r0 |
| 50 | 2 5 5 | r3 <- r1 |
| 51 | 2 5 6 | r3 <- r2 |
## UINC  - increment register by 1
| iid | kyte | registers |
| ---- | ---- | ---- |
| 52 | 2 5 7 | r0 |
| 53 | 2 5 8 | r1 |
| 54 | 2 6 0 | r2 |
| 55 | 2 6 1 | r3 |

## UDEC decrement register by 1
| iid | kyte | registers |
| ---- | ---- | ---- |
| 56 | 2 6 2 | r0 |
| 57 | 2 6 3 | r1 |
| 58 | 2 6 4 | r2 |
| 59 | 2 6 5| r3 |


# == GID 2 - control ==