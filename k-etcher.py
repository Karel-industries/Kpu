#!/bin/python3

from pprint import pprint


save_copy_as_KPU = True # saves the KPUv1b... file as KPU.K99
save_to_Keap_ASM = True # saves a copy to Keap/assembly folder

csv_path = "Keap/KeapV1.csv"
csv_file = []

with open(csv_path, "r") as f:
   lines = f.readlines()
   for line in lines:
      csv_file.append(line.lstrip().rstrip().split(","))
   csv_file.pop(0)

instructions = {}

for line in csv_file:
   if len(line) == 5:
      gid, iid, ins, reg0, reg1 = line
      if not ins in list(instructions.keys()):
         instructions[ins] = []
      instructions[ins].append([gid, iid, reg0, reg1])

   elif len(line) == 4:
      gid, iid, ins, reg0 = line
      if not ins in list(instructions.keys()):
         instructions[ins] = []
      instructions[ins].append([gid, iid, reg0])

   elif len(line) == 8:
      gid, iid, ins, _, _, cond, bit, _ = line
      if not ins in list(instructions.keys()):
         instructions[ins] = []
      instructions[ins].append([gid, iid, cond, bit])


arch = "KPU"

major = "1b"
minor = "29-main"

out = open(f"{arch}v{major}.{minor}.K99", "w")
print(f"KPUv{major}.{minor} stats")

# English translation
#
# krok -> step
# vlevo-vbok -> left
# zvedni -> pick
# polož -> place
# opakuj -> repeat
# krát -> times
# dokud -> until
# když -> if
# jinak -> else
# je -> is
# není -> isnot
# zeď -> wall
# značka -> flag
# domov -> home
# sever -> north
# jih -> south
# západ -> west
# východ -> east
# konec -> end
#
#
# Velikost města: 20, 20  ->   Map size: 20, 20
# Pozice Karla: 7, 1      ->   Karel position: 7, 1
# Otočení Karla: VÝCHOD   ->   Karel rotation: EAST
# Umístění domova: 7, 1   ->   Home position: 7, 1
# Definice města:         ->   Map definition:
#


# defines a new ucode function in output and returns the function name (for calling)
def ucode_define(impl):
   out.write(impl.upper())
   out.write('\n')

   lines = impl.split('\n')
   last_def = "s"

   for l in lines:
      if not l.startswith(" ") and (l.strip() != "konec" and l != ""):
         last_def = l

   return last_def

# performs variable substitution on a variable function implemetation (replaces placeholders in vars with final values in vals), defines the function in output and returns the function name (for calling)


def ucode_instantiate_var(var_impl, vars, vals):
   impl = var_impl
   for i in range(len(vars)):
      impl = impl.replace(str(vars[i]), str(vals[i]))

   if '[' in impl or ']' in impl:
      raise ValueError(
         "Not all variadic placeholders were substituted after variable function instantiation! Variable substitution not finished!")

   out.write(impl.upper())
   out.write('\n')

   lines = impl.split('\n')
   last_def = "s"

   for l in lines:
      if not l.startswith(" ") and (l.strip() != "konec" and l != ""):
         last_def = l

   return last_def

# performs variable substitution and returns the function implementation (used for inserting variable funcs into other variable funcs)
# vars are substitution is order dependent, beware of unintended replacing


def ucode_redefine_var_func(var_impl, vars, vals):
   impl = var_impl
   for i in range(len(vars)):
      impl = impl.replace(str(vars[i]), str(vals[i]))

   return impl

# gets the expected name of the func returned by ucode_define without writing it to out

def ucode_dry_define(impl):
   lines = impl.split('\n')
   last_def = "s"

   for l in lines:
      if not l.startswith(" ") and (l.strip() != "konec" and l != ""):
         last_def = l

   return last_def

# == begin ucode ==

# faults


fault_align = ucode_define("""
fault-align
   dokud není východ
      vlevo-vbok
   konec
   dokud není zeď
      krok
   konec
   vlevo-vbok
   dokud není zeď
      krok
   konec
konec
""")

_f_unknown_instruction = ucode_define(f"""
__fault-unknown-instruction__
   {fault_align}
   dokud je značka
      zvedni
   konec
   stop
konec
""")

_f_unreachable = ucode_define(f"""
__fault-unreachable-ucode__
   {fault_align}
   dokud je značka
      zvedni
   konec
   polož
   polož
   stop
konec
""")

_f_out_of_bounds_address = ucode_define(f"""
__fault-out-of-bounds-address__
   {fault_align}
   dokud je značka
      zvedni
   konec
   polož
   stop
konec
""")

# internal - common

root_align = ucode_define("""
root-align
   dokud není sever
      vlevo-vbok
   konec
   dokud není zeď
      krok
   konec
   vlevo-vbok
   dokud není domov
      když je zeď
         vlevo-vbok
         vlevo-vbok
      konec, jinak
      konec
      krok
   konec
   dokud není východ
      vlevo-vbok
   konec
konec
""")

behind = ucode_define(f"""
behind
   vlevo-vbok
   vlevo-vbok
konec
""")

right_side = ucode_define(f"""
right-side
   vlevo-vbok
   vlevo-vbok
   vlevo-vbok
konec""")

dkrok = ucode_define(f"""
dkrok
   krok
   krok
konec""")

tkrok = ucode_define(f"""
tkrok
   krok
   krok
   krok
konec""")

shift_left = ucode_define(f"""
shift-left
   vlevo-vbok
   krok
   {right_side}
konec""")

shift_right = ucode_define(f"""
shift-right
   {right_side}
   krok
   vlevo-vbok
konec""")

fill = ucode_define(f"""
fill
   opakuj 8-krát
      polož
   konec
konec""")

drain = ucode_define(f"""
drain
   dokud je značka
      zvedni
   konec
konec""")

invert_kat = ucode_define(f"""
invert-kat
   když je značka
      zvedni
      invert-kat
      zvedni
   konec, jinak
      {fill}
   konec
konec
""")

invert = ucode_define(f"""
invert
   {invert_kat}
   krok
   {invert_kat}
   krok
   {invert_kat}
   {behind}
   {dkrok}
   {behind}
konec
""")

inc_and_carry = ucode_define(f"""
inc-and-ignore
   {invert_kat}
   když je značka
      zvedni
   konec, jinak
      fill
   konec
   {invert_kat}
konec

inc-and-carry2
   {invert_kat}
   když je značka
      zvedni
   konec, jinak
      krok
      inc-and-ignore
      {behind}
      krok
      {behind}
      fill
   konec
   {invert_kat}
konec

inc-and-carry
   {invert_kat}
   když je značka
      zvedni
   konec, jinak
      krok
      inc-and-carry2
      {behind}
      krok
      {behind}
      fill
   konec
   {invert_kat}
konec
""")

inc_and_carry_no_inv = ucode_define(f"""
inc-and-ignore-no-inv
   když je značka
      zvedni
   konec, jinak
      fill
   konec
konec

inc-and-carry2-no-inv
   když je značka
      zvedni
   konec, jinak
      krok
      inc-and-ignore-no-inv
      {behind}
      krok
      {behind}
      fill
   konec
konec

inc-and-carry-no-inv
   když je značka
      zvedni
   konec, jinak
      krok
      inc-and-carry2-no-inv
      {behind}
      krok
      {behind}
      fill
   konec
konec
""")

adr_step = ucode_define(f"""
adr-step
   když není zeď
      krok
   konec, jinak
      {right_side}
      když je zeď
         {_f_out_of_bounds_address}
      konec, jinak
      konec
      {tkrok}
      {right_side}
      dokud není zeď
         krok
      konec
      {behind}
   konec
konec
""")

address = ucode_define(f"""
adr-setup
   {root_align}
   {behind}
   {tkrok}
   {tkrok}
   vlevo-vbok
   {dkrok}
   {dkrok}
   vlevo-vbok
konec

address3
   když je značka
      zvedni
      address3
      opakuj 81-krát
         {adr_step}
      konec
   konec, jinak
      krok
      adr-setup
   konec
konec

address2
   když je značka
      zvedni
      address2
      opakuj 9-krát
         {adr_step}
      konec
   konec, jinak
      krok
      address3
   konec
konec

address1
   když je značka
      zvedni
      address1
      {adr_step}
   konec, jinak
      krok
      address2
   konec
konec

address
   address1
   vlevo-vbok
konec
""")

sub_one_and_carry = ucode_define(f"""
sub-one-and-carry
   když je značka
      // subtract 1
      zvedni
   konec, jinak
      // 0 - 1 = 8 and carry
      {fill}
      vlevo-vbok
      krok
      // signal carry
      polož
      {behind}
      krok
      vlevo-vbok
   konec
konec
""")

sub_kat = ucode_define(f"""
sub-kat-sumup
   když je značka
      zvedni
      sub-kat-sumup
      {sub_one_and_carry}
   konec, jinak
      {shift_right}
   konec
konec

sub-kat
   {shift_left}
   // check for carry
   když je značka
      zvedni
      krok
      sub-kat-sumup
      {sub_one_and_carry}
   konec, jinak
      krok
      sub-kat-sumup
   konec
konec
""")

safe_zvedni = ucode_define(f"""
safe-zvedni
   když je značka
      zvedni
   konec, jinak
   konec
konec
""")

set_normalflow = ucode_define(f"""
set-normalflow
   opakuj 2-krát
      {safe_zvedni}
   konec
   když je značka
      zvedni
      set-normalflow
      opakuj 3-krát
         polož
      konec
   konec, jinak
   konec
konec
""")

set_underflow = ucode_define(f"""
set-underflow
   opakuj 2-krát
      {safe_zvedni}
   konec
   když je značka
      zvedni
      set-underflow
      opakuj 3-krát
         polož
      konec
   konec, jinak
      polož
   konec
konec
""")

set_overflow = ucode_define(f"""
set-overflow
   opakuj 2-krát
      {safe_zvedni}
   konec
   když je značka
      zvedni
      set-overflow
      opakuj 3-krát
         polož
      konec
   konec, jinak
      polož
      polož
   konec
konec
""")

set_value = []

set_value.append("no-op")

set_value.append(ucode_define(f"""
write-value<1>
   opakuj 1-krát
      polož
   konec
konec
"""))

set_value.append(ucode_define(f"""
write-value<2>
   opakuj 2-krát
      polož
   konec
konec
"""))

set_value.append(ucode_define(f"""
write-value<3>
   opakuj 3-krát
      polož
   konec
konec
"""))

set_value.append(ucode_define(f"""
write-value<4>
   opakuj 4-krát
      polož
   konec
konec
"""))

set_value.append(ucode_define(f"""
write-value<5>
   opakuj 5-krát
      polož
   konec
konec
"""))

set_value.append(ucode_define(f"""
write-value<6>
   opakuj 6-krát
      polož
   konec
konec
"""))

set_value.append(ucode_define(f"""
write-value<7>
   opakuj 7-krát
      polož
   konec
konec
"""))

set_value.append(fill)

# internal - move funcs

# note r4 pos = root pos

r_to_r = [[], [], [], [], []]

# r0

r_to_r[0].append("no-op")

r_to_r[0].append(ucode_define(f"""
r0-to-r1
   {shift_right}
konec
"""))

r_to_r[0].append(ucode_define(f"""
r0-to-r2
   {tkrok}
konec
"""))

r_to_r[0].append(ucode_define(f"""
r0-to-r3
   {tkrok}
   {shift_right}
konec
"""))

r_to_r[0].append(ucode_define(f"""
r0-to-r4
   {tkrok}
   {tkrok}
konec
"""))

# r1

r_to_r[1].append(ucode_define(f"""
r1-to-r0
   {shift_left}
konec
"""))

r_to_r[1].append("no-op")

r_to_r[1].append(ucode_define(f"""
r1-to-r2
   {tkrok}
   {shift_left}
konec
"""))

r_to_r[1].append(ucode_define(f"""
r1-to-r3
   {tkrok}
konec
"""))

r_to_r[1].append(ucode_define(f"""
r1-to-r4
   {tkrok}
   {tkrok}
   {shift_left}
konec
"""))

# r2

r_to_r[2].append(ucode_define(f"""
r2-to-r0
   {behind}
   {tkrok}
   {behind}
konec
"""))

r_to_r[2].append(ucode_define(f"""
r2-to-r1
   {behind}
   {tkrok}
   vlevo-vbok
   krok
   vlevo-vbok
konec
"""))

r_to_r[2].append("no-op")

r_to_r[2].append(ucode_define(f"""
r2-to-r3
   {shift_right}
konec
"""))

r_to_r[2].append(ucode_define(f"""
r2-to-r4
   {tkrok}
konec
"""))

# r3

r_to_r[3].append(ucode_define(f"""
r3-to-r0
   {behind}
   {tkrok}
   {behind}
   {shift_left}
konec
"""))

r_to_r[3].append(ucode_define(f"""
r3-to-r1
   {behind}
   {tkrok}
   {behind}
konec
"""))

r_to_r[3].append(ucode_define(f"""
r3-to-r2
   {shift_left}
konec
"""))

r_to_r[3].append("no-op")

r_to_r[3].append(ucode_define(f"""
r3-to-r4
   {tkrok}
   {shift_left}
konec
"""))

# r4

r_to_r[4].append(ucode_define(f"""
r4-to-r0
   {behind}
   {tkrok}
   {tkrok}
   {behind}
konec
"""))

r_to_r[4].append(ucode_define(f"""
r4-to-r1
   {behind}
   {tkrok}
   {tkrok}
   vlevo-vbok
   krok
   vlevo-vbok
konec
"""))

r_to_r[4].append(ucode_define(f"""
r4-to-r2
   {behind}
   {tkrok}
   {behind}
konec
"""))

r_to_r[4].append(ucode_define(f"""
r4-to-r3
   {behind}
   {tkrok}
   vlevo-vbok
   krok
   vlevo-vbok
konec
"""))

r_to_r[4].append("no-op")

r_to_op0 = []

r_to_op0.append(ucode_define(f"""
r0-to-op0
   {tkrok}
   {tkrok}
   {tkrok}
konec
"""))

r_to_op0.append(ucode_define(f"""
r1-to-op0
   {tkrok}
   {tkrok}
   {tkrok}
   {shift_left}
konec
"""))

r_to_op0.append(ucode_define(f"""
r2-to-op0
   {tkrok}
   {tkrok}
konec
"""))

r_to_op0.append(ucode_define(f"""
r3-to-op0
   {tkrok}
   {tkrok}
   {shift_left}
konec
"""))

r_to_op0.append(ucode_define(f"""
r4-to-op0
   {tkrok}
konec
"""))

# op_mem movment

op0_to_op = []

op0_to_op.append("no-op")

op0_to_op.append(ucode_define(f"""
op0-to-op1
   {shift_right}
konec
"""))

op0_to_op.append(ucode_define(f"""
op0-to-op2
   {tkrok}
konec
"""))

op0_to_op.append(ucode_define(f"""
op0-to-op3
   {tkrok}
   {shift_right}
konec
"""))

op0_to_op.append(ucode_define(f"""
op0-to-op4
   {tkrok}
   {tkrok}
konec
"""))

op0_to_op.append(ucode_define(f"""
op0-to-op5
   {tkrok}
   {tkrok}
   {shift_right}
konec
"""))

# internal - common vars

# move kyte vars:
# var - variable id
# user place - function used for placing a flag (usually just a polož)
# user mid point - function called at recursive mid point (usually used to move karel to location where data is to be stored)
#
# assumes starting position at reading kyte
# ends at writing kyte (at kat 0)
#
# (safe move variant; always drains write kyte)

move_kyte_var = f"""
move-kyte3<[var]>
   když je značka
      zvedni
      move-kyte3<[var]>
      [user place]
   konec, jinak
      [user mid point]
      {behind}
      {drain}
   konec
konec

move-kyte2<[var]>
   když je značka
      zvedni
      move-kyte2<[var]>
      [user place]
   konec, jinak
      krok
      move-kyte3<[var]>
      krok
      {drain}
   konec
konec

move-kyte1<[var]>
   když je značka
      zvedni
      move-kyte1<[var]>
      [user place]
   konec, jinak
      krok
      move-kyte2<[var]>
      krok
      {drain}
   konec
konec

move-kyte<[var]>
   move-kyte1<[var]>
   {behind}
konec
"""

# cf vars:
# var - variable id
# p0 to op0 - func to move from p0 to op0 (inversible)
# p1 to op0 - func to move from p1 to op0 (inversible)
#
# assumes starting position at p0
# also ends at p0
# leaves a copy of data from p0 in p1

copy_fetch_var = f"""
copy-fetch<[var]>-duplicate
   polož
   {behind}
   [p1 to op0]
   polož
   {behind}
   [p1 to op0]
konec

copy-fetch<[var]>-mid
   {behind}
   [p0 to op0]
   {behind}
konec

{ucode_redefine_var_func(move_kyte_var, ("[var]", "[user place]", "[user mid point]"), ("cf-to-[var]", "copy-fetch<[var]>-duplicate", "[p0 to op0]"))}
{ucode_redefine_var_func(move_kyte_var, ("[var]", "[user place]", "[user mid point]"), ("cf-from-[var]", "polož", "copy-fetch<[var]>-mid"))}

copy-fetch<[var]>
   move-kyte<cf-to-[var]>
   move-kyte<cf-from-[var]>
konec
"""

# rcf vars:
# var - variable id
# p0 to op0 - func to move from p0 to op0
# p1 to op0 - func to move from p1 to op0 (inversible)
# op0 to p2 - func to move from op0 to adr_source
#
# assumes starting position at p0
# also ends at p0
# assumes p2 contains address to p0
# leaves a copy of data from p0 in p1

remote_copy_fetch_var = f"""
r-copy-fetch<[var]>-duplicate
   polož
   {behind}
   [p1 to op0]
   polož
   {behind}
   [p1 to op0]
konec

r-copy-fetch<to-[var]>-mid
   [p0 to op0]
   {dkrok}
konec

{ucode_redefine_var_func(move_kyte_var, ("[var]", "[user place]", "[user mid point]"), ("rcf-to-[var]", "r-copy-fetch<[var]>-duplicate", "r-copy-fetch<to-[var]>-mid"))}

r-copy-fetch<from-[var]>-mid
   [op0 to p2]
   {behind}
   {dkrok}
   {behind}
   {address}
   {dkrok}
konec

{ucode_redefine_var_func(move_kyte_var, ("[var]", "[user place]", "[user mid point]"), ("rcf-from-[var]", "polož", "r-copy-fetch<from-[var]>-mid"))}

r-copy-fetch<[var]>
   move-kyte<rcf-to-[var]>
   move-kyte<rcf-from-[var]>
konec
"""

# cpf vars:
# var - variable id
# p0 to op0 - func to move from p0 to op0 (inversible)
# p1 to op0 - func to move from p1 to op0 (inversible)
# p2 to op0 - func to move from p2 to op0 (inversible)
#
# assumes starting position at p0
# also ends at p0
# leaves a copy of data from p0 in p1

copy_prefetch_var = f"""
copy-prefetch<[var]>-duplicate
   polož
   {behind}
   [p1 to op0]
   polož
   {behind}
   [p1 to op0]
   {behind}
   [p2 to op0]
   polož
   {behind}
   [p2 to op0]
konec

copy-prefetch<[var]>-mid
   {behind}
   [p0 to op0]
   {behind}
konec

{ucode_redefine_var_func(move_kyte_var, ("[var]", "[user place]", "[user mid point]"), ("cpf-to-[var]", "copy-prefetch<[var]>-duplicate", "[p0 to op0]"))}
{ucode_redefine_var_func(move_kyte_var, ("[var]", "[user place]", "[user mid point]"), ("cpf-from-[var]", "polož", "copy-prefetch<[var]>-mid"))}

copy-prefetch<[var]>
   move-kyte<cpf-to-[var]>
   move-kyte<cpf-from-[var]>
konec
"""

# test trit 0 vars:
# var - variable id
# read 0 - func called when trit value is equal to 0
# read 1 - func called when trit value is equal to 1
# read 2 - func called when trit value is equal to 2

tt0_var = f"""
test-trit-0-2<[var]>
   když není značka
      [read 2]
   konec, jinak
      zvedni
      test-trit-0<[var]>
      polož
   konec
konec

test-trit-0-1<[var]>
   když není značka
      [read 1]
   konec, jinak
      zvedni
      test-trit-0-2<[var]>
      polož
   konec
konec

test-trit-0<[var]>
   když není značka
      [read 0]
   konec, jinak
      zvedni
      test-trit-0-1<[var]>
      polož
   konec
konec
"""

# test trit 1 vars:
# var - variable id
# read 0 - func called when trit value is equal to 0
# read 1 - func called when trit value is equal to 1
# read 2 - func called when trit value is equal to 2

tt1_step_var = f"""
test-trit-1-step<[var]>
   když není značka
      [mid]
   konec, jinak
      zvedni
      když není značka
         polož
         [mid]
      konec, jinak
         zvedni
         když není značka
            polož
            polož
            [mid]
         konec, jinak
            zvedni
            [next]
            polož
            polož
            polož
         konec
      konec
   konec
konec
"""

tt1_var = f"""

{ucode_redefine_var_func(tt1_step_var, ("[var]", "[mid]", "[next]"), ("[var]-2", "[read 2]", _f_unreachable))}
{ucode_redefine_var_func(tt1_step_var, ("[var]", "[mid]", "[next]"), ("[var]-1", "[read 1]", "test-trit-1-step<[var]-2>"))}
{ucode_redefine_var_func(tt1_step_var, ("[var]", "[mid]", "[next]"), ("[var]-0", "[read 0]", "test-trit-1-step<[var]-1>"))}

test-trit-1<[var]>
   test-trit-1-step<[var]-0>
konec
"""

# condition checks
# var - variable id
# success - func called when condition is met
# fail - func called when condition is not met

cond_check_vars = []

cond_check_vars.append(f"""
check-eq-success<[var]>
   [success]
konec

check-eq-failed<[var]>
   [fail]
konec

{ucode_redefine_var_func(tt0_var, ("[var]", "[read 0]", "[read 1]", "[read 2]"), ("eq-[var]", "check-eq-success<[var]>", "check-eq-failed<[var]>", "check-eq-failed<[var]>"))}

check-eq<[var]>
   test-trit-0<eq-[var]>
konec
""")

cond_check_vars.append(f"""
check-iz-success<[var]>
   [success]
   krok
konec

check-iz-failed<[var]>
   [fail]
   krok
konec

{ucode_redefine_var_func(tt0_var, ("[var]", "[read 0]", "[read 1]", "[read 2]"), ("iz-[var]", "check-iz-failed<[var]>", "check-iz-success<[var]>", "check-iz-failed<[var]>"))}

check-iz<[var]>
   krok
   test-trit-0<iz-[var]>
   {behind}
   krok
   {behind}
konec
""")

cond_check_vars.append(f"""
check-of-success<[var]>
   [success]
konec

check-of-failed<[var]>
   [fail]
konec

{ucode_redefine_var_func(tt1_var, ("[var]", "[read 0]", "[read 1]", "[read 2]"), ("of-[var]", "check-of-failed<[var]>", "check-of-failed<[var]>", "check-of-success<[var]>"))}

check-of<[var]>
   test-trit-1<of-[var]>
konec
""")

cond_check_vars.append(f"""
check-uf-success<[var]>
   [success]
konec

check-uf-failed<[var]>
   [fail]
konec

{ucode_redefine_var_func(tt1_var, ("[var]", "[read 0]", "[read 1]", "[read 2]"), ("uf-[var]", "check-uf-failed<[var]>", "check-uf-success<[var]>", "check-uf-failed<[var]>"))}

check-uf<[var]>
   test-trit-1<uf-[var]>
konec
""")

cond_check_vars.append(f"""
check-nf-success<[var]>
   [success]
konec

check-nf-failed<[var]>
   [fail]
konec

{ucode_redefine_var_func(tt1_var, ("[var]", "[read 0]", "[read 1]", "[read 2]"), ("nf-[var]", "check-nf-success<[var]>", "check-nf-failed<[var]>", "check-nf-failed<[var]>"))}

check-nf<[var]>
   test-trit-1<nf-[var]>
konec
""")

cond_check_vars.append(f"""
check-gt-success<[var]>
   [success]
konec

check-gt-failed<[var]>
   [fail]
konec

{ucode_redefine_var_func(tt0_var, ("[var]", "[read 0]", "[read 1]", "[read 2]"), ("gt-[var]", "check-gt-failed<[var]>", "check-gt-failed<[var]>", "check-gt-success<[var]>"))}

check-gt<[var]>
   test-trit-0<gt-[var]>
konec
""")

cond_check_vars.append(f"""
check-lt-success<[var]>
   [success]
konec

check-lt-failed<[var]>
   [fail]
konec

{ucode_redefine_var_func(tt0_var, ("[var]", "[read 0]", "[read 1]", "[read 2]"), ("lt-[var]", "check-lt-success<[var]>", "check-lt-failed<[var]>", "check-lt-failed<[var]>"))}

check-lt<[var]>
   test-trit-0<lt-[var]>
konec
""")

cond_check_vars.append(f"""
check-ge-success<[var]>
   [success]
konec

check-ge-failed<[var]>
   [fail]
konec

{ucode_redefine_var_func(tt0_var, ("[var]", "[read 0]", "[read 1]", "[read 2]"), ("ge-[var]", "check-ge-failed<[var]>", "check-ge-success<[var]>", "check-ge-success<[var]>"))}

check-ge<[var]>
   test-trit-0<ge-[var]>
konec
""")

cond_check_vars.append(f"""
check-le-success<[var]>
   [success]
konec

check-le-failed<[var]>
   [fail]
konec

{ucode_redefine_var_func(tt0_var, ("[var]", "[read 0]", "[read 1]", "[read 2]"), ("le-[var]", "check-le-success<[var]>", "check-le-success<[var]>", "check-le-failed<[var]>"))}

check-le<[var]>
   test-trit-0<le-[var]>
konec
""")

# instructions

# maps dre iids to ucode instruction funcs
ins_map = [[], [], [], [], [], [], [], [], []]

for gid_map in ins_map:
   for iid in range(81):
      gid_map.append(_f_unknown_instruction)

#print("reserving extended group - gid: 0")

#print("")

#print("memory instruction group - gid: 1")

# swp ins
# var - variable id
# root to p0 - func to move from root to p0
# p0 to p1 - func to move from p0 to p1 (inversible)

swp_var = f"""
swp2<[var]>-mid
   {behind}
   [p0 to p1]
   {behind}
konec

{ucode_redefine_var_func(move_kyte_var, ("[var]", "[user place]", "[user mid point]"), ("swp2-[var]", "polož", "swp2<[var]>-mid"))}

swp<[var]>-mid
   [p0 to p1]
   {behind}
   {dkrok}
   {behind}
   move-kyte<swp2-[var]>
   [p0 to p1]
   {dkrok}
konec

{ucode_redefine_var_func(move_kyte_var, ("[var]", "[user place]", "[user mid point]"), ("swp-[var]", "polož", "swp<[var]>-mid"))}

swp<[var]>
   {root_align}
   {inc_and_carry}
   [root to p0]
   move-kyte<swp-[var]>
   {root_align}
konec
"""


for ins_data in instructions["swp"]:
   ins_map[int(ins_data[0])][int(ins_data[1])] = ucode_instantiate_var(swp_var, ("[var]", "[root to p0]", "[p0 to p1]"), (f"r{int(ins_data[2])}-r{int(ins_data[3])}", r_to_r[4][int(ins_data[2])], r_to_r[int(ins_data[2])][int(ins_data[3])]))

#ins_map[1][0] = ucode_instantiate_var(swp_var, ("[var]", "[root to p0]", "[p0 to p1]"), ("r0-r1", r_to_r[4][0], r_to_r[0][1]))
#ins_map[1][1] = ucode_instantiate_var(swp_var, ("[var]", "[root to p0]", "[p0 to p1]"), ("r0-r2", r_to_r[4][0], r_to_r[0][2]))
#ins_map[1][2] = ucode_instantiate_var(swp_var, ("[var]", "[root to p0]", "[p0 to p1]"), ("r0-r3", r_to_r[4][0], r_to_r[0][3]))
#ins_map[1][3] = ucode_instantiate_var(swp_var, ("[var]", "[root to p0]", "[p0 to p1]"), ("r0-r4", r_to_r[4][0], r_to_r[0][4]))
#ins_map[1][4] = ucode_instantiate_var(swp_var, ("[var]", "[root to p0]", "[p0 to p1]"), ("r1-r2", r_to_r[4][1], r_to_r[1][2]))
#ins_map[1][5] = ucode_instantiate_var(swp_var, ("[var]", "[root to p0]", "[p0 to p1]"), ("r1-r3", r_to_r[4][1], r_to_r[1][3]))
#ins_map[1][6] = ucode_instantiate_var(swp_var, ("[var]", "[root to p0]", "[p0 to p1]"), ("r1-r4", r_to_r[4][1], r_to_r[1][4]))
#ins_map[1][7] = ucode_instantiate_var(swp_var, ("[var]", "[root to p0]", "[p0 to p1]"), ("r2-r3", r_to_r[4][2], r_to_r[2][3]))
#ins_map[1][8] = ucode_instantiate_var(swp_var, ("[var]", "[root to p0]", "[p0 to p1]"), ("r2-r4", r_to_r[4][2], r_to_r[2][4]))
#ins_map[1][9] = ucode_instantiate_var(swp_var, ("[var]", "[root to p0]", "[p0 to p1]"), ("r3-r4", r_to_r[4][3], r_to_r[3][4]))


#if not detailed_print:
#   print("  swp - iids: 0 - 9")

# wll ins
# var - variable id
# root to p0 - func to move from root to p0
# p0 to op0 - func to move from p0 to op0 (inversible)
# p1 to op0 - func to move from p1 to op0 (inversible)

wll_var = f"""
{ucode_redefine_var_func(copy_fetch_var, ("[var]", "[p1 to op0]"), ("wll-[var]", op0_to_op[1]))}

wll<[var]>-mid
   {behind}
   {op0_to_op[1]}
   [p1 to op0]
   {behind}
konec

{ucode_redefine_var_func(move_kyte_var, ("[var]", "[user place]", "[user mid point]"), ("wll-[var]", "polož", "wll<[var]>-mid"))}

wll<[var]>
   {root_align}
   {inc_and_carry}
   [root to p0]
   copy-fetch<wll-[var]>
   [p0 to op0]
   op0-to-op1
   move-kyte<wll-[var]>
   {root_align}
konec
"""

#i = 10
#pre_i = i

#if detailed_print:
#   print("\nwll - copy from reg2 to reg")

for ins_data in instructions["wll"]:
   ins_map[int(ins_data[0])][int(ins_data[1])] = ucode_instantiate_var(wll_var, ("[var]", "[root to p0]", "[p0 to op0]", "[p1 to op0]"), (f"r{int(ins_data[2])}-r{int(ins_data[3])}", r_to_r[4][int(ins_data[2])], r_to_op0[int(ins_data[2])], r_to_op0[int(ins_data[3])]))


#for fr in range(5):
#   for sr in range(5):
#      if not fr == sr:
#         ins_map[1][i] = ucode_instantiate_var(wll_var, ("[var]", "[root to p0]", "[p0 to op0]", "[p1 to op0]"), (f"r{fr}-r{sr}", r_to_r[4][fr], r_to_op0[fr], r_to_op0[sr]))
#         if detailed_print:
#            print(f"   {i} - [1 {int(i/9)} {i%9}] - r{fr} <- r{sr}")
#         i += 1

#if not detailed_print:
#   print(f"  wll - iids: {pre_i} - {i - 1}")

# wlr ins
# var - variable id
# root to p0 - func to move from root to source
# p0 to op0 - func to move from source to op0 (inversible)
# p0 to p1 - func to move from source to adr_source
# p1 to op0 - func to move from adr_source to op0 (inversible)

wlr_var = f"""
{ucode_redefine_var_func(copy_fetch_var, ("[var]", "[p1 to op0]"), ("wlr-d-[var]", op0_to_op[1]))}
{ucode_redefine_var_func(copy_fetch_var, ("[var]", "[p1 to op0]", "[p0 to op0]"), ("wlr-a-[var]", op0_to_op[2], "[p1 to op0]"))}

wlr<[var]>-mid
   {behind}
   {dkrok}
   {op0_to_op[1]}
   {behind}
   {op0_to_op[2]}
   {address}
   {dkrok}
konec

{ucode_redefine_var_func(move_kyte_var, ("[var]", "[user place]", "[user mid point]"), ("wlr-[var]", "polož", "wlr<[var]>-mid"))}

wlr<[var]>
   {root_align}
   {inc_and_carry}
   [root to p0]
   copy-fetch<wlr-d-[var]>
   [p0 to p1]
   copy-fetch<wlr-a-[var]>
   [p1 to op0]
   {op0_to_op[1]}
   move-kyte<wlr-[var]>
   {root_align}
konec
"""

#pre_i = i

#if detailed_print:
#   print("\nwlr - copy from reg2 to ram (adr in reg)")

for ins_data in instructions["wlr"]:
   ins_map[int(ins_data[0])][int(ins_data[1])] = ucode_instantiate_var(wlr_var, ("[var]", "[root to p0]", "[p0 to op0]", "[p0 to p1]", "[p1 to op0]"), (f"r{int(ins_data[2])}-r{int(ins_data[3])}", r_to_r[4][int(ins_data[2])], r_to_op0[int(ins_data[2])], r_to_r[int(ins_data[2])][int(ins_data[3])], r_to_op0[int(ins_data[3])]))

#for fr in range(5):
#   for sr in range(5):
#      if not fr == sr:
#         ins_map[1][i] = ucode_instantiate_var(wlr_var, ("[var]", "[root to p0]", "[p0 to op0]", "[p0 to p1]", "[p1 to op0]"), (f"r{fr}-r{sr}", r_to_r[4][fr], r_to_op0[fr], r_to_r[fr][sr], r_to_op0[sr]))
#         if detailed_print:
#            print(f"   {i} - [1 {int(i/9)} {i%9}] - r{fr} <- r{sr}")
#         i += 1

#if not detailed_print:
#   print(f"  wlr - iids: {pre_i} - {i - 1}")

# wrl ins
# var - variable id
# root to p1 - func to move from root to adr_source
# p0 to op0 - func to move from dest to op0 (inversible)
# p1 to op0 - func to move from adr_source to op0 (inversible)

wrl_var = f"""
{ucode_redefine_var_func(copy_prefetch_var, ("[var]", "[p1 to op0]", "[p2 to op0]", "[p0 to op0]"), ("wrl-a-[var]", op0_to_op[1], op0_to_op[2], "[p1 to op0]"))}

wrl<[var]>-rcf-d-mid
   {root_align}
   {r_to_op0[4]}
konec

{ucode_redefine_var_func(remote_copy_fetch_var, ("[var]", "[p0 to op0]", "[p1 to op0]", "[op0 to p2]"), ("wrl-d-[var]", "wrl<[var]>-rcf-d-mid", op0_to_op[1], op0_to_op[2]))}

wrl<[var]>-mk-d-mid
   {behind}
   {op0_to_op[1]}
   [p0 to op0]
   {behind}
konec

{ucode_redefine_var_func(move_kyte_var, ("[var]", "[user place]", "[user mid point]"), ("wrl-d-[var]", "polož", "wrl<[var]>-mk-d-mid"))}

wrl<[var]>
   {root_align}
   {inc_and_carry}
   [root to p1]
   copy-prefetch<wrl-a-[var]>
   [p1 to op0]
   {op0_to_op[1]}
   {address}
   r-copy-fetch<wrl-d-[var]>
   {root_align}
   {r_to_op0[4]}
   {op0_to_op[1]}
   move-kyte<wrl-d-[var]>
   {root_align}
konec
"""

#pre_i = i

#if detailed_print:
#   print("\nwrl - copy from ram (adr in reg2) to reg")


for ins_data in instructions["wrl"]:
   ins_map[int(ins_data[0])][int(ins_data[1])] = ucode_instantiate_var(wrl_var, ("[var]", "[root to p1]", "[p0 to op0]", "[p1 to op0]"), (f"r{int(ins_data[2])}-r{int(ins_data[3])}", r_to_r[4][int(ins_data[3])], r_to_op0[int(ins_data[2])], r_to_op0[int(ins_data[3])]))


#for fr in range(5):
#   for sr in range(5):
#      if not fr == sr:
#         ins_map[1][i] = ucode_instantiate_var(wrl_var, ("[var]", "[root to p1]", "[p0 to op0]", "[p1 to op0]"), (f"r{fr}-r{sr}", r_to_r[4][sr], r_to_op0[fr], r_to_op0[sr]))
#         if detailed_print:
#            print(f"   {i} - [1 {int(i/9)} {i%9}] - r{fr} <- r{sr}")
#         i += 1

#if not detailed_print:
#   print(f"  wrl - iids: {pre_i} - {i - 1}")

# drl ins
# root to p0 - func to move from root to dest

drl_var = f"""
drl<[var]>
   {root_align}
   {inc_and_carry}
   [root to p0]
   {drain}
   krok
   {drain}
   krok
   {drain}
   {root_align}
konec
"""

#pre_i = i

#if detailed_print:
#   print("\ndrl - drain reg")

for ins_data in instructions["drl"]:
   ins_map[int(ins_data[0])][int(ins_data[1])] = ucode_instantiate_var(drl_var, ("[var]", "[root to p0]"), (f"r{int(ins_data[2])}", r_to_r[4][int(ins_data[2])]))

#for fr in range(5):
#   ins_map[1][i] = ucode_instantiate_var(drl_var, ("[var]", "[root to p0]"), (f"r{fr}", r_to_r[4][fr]))
#   if detailed_print:
#      print(f"   {i} - [1 {int(i/9)} {i%9}] - r{fr}")
#   i += 1

#if not detailed_print:
#   print(f"  drl - iids: {pre_i} - {i - 1}")

# drr ins
# root to p0 - func to move from root to adr_source
# p0 to op0 - func to move form p0 to op0 (inversible)

drr_var = f"""
{ucode_redefine_var_func(copy_fetch_var, ("[var]", "[p1 to op0]"), ("drr-[var]", op0_to_op[1]))}

drr<[var]>
   {root_align}
   {inc_and_carry}
   [root to p0]
   copy-fetch<drr-[var]>
   [p0 to op0]
   {op0_to_op[1]}
   {address}
   {drain}
   krok
   {drain}
   krok
   {drain}
   {root_align}
konec
"""

#pre_i = i

#if detailed_print:
#   print("\ndrr - drain ram (adr in reg)")

for ins_data in instructions["drr"]:
   ins_map[int(ins_data[0])][int(ins_data[1])] = ucode_instantiate_var(drr_var, ("[var]", "[root to p0]", "[p0 to op0]"), (f"r{int(ins_data[2])}", r_to_r[4][int(ins_data[2])], r_to_op0[int(ins_data[2])]))

#for fr in range(5):
#   ins_map[1][i] = ucode_instantiate_var(drr_var, ("[var]", "[root to p0]", "[p0 to op0]"), (f"r{fr}", r_to_r[4][fr], r_to_op0[fr]))
#   if detailed_print:
#      print(f"   {i} - [1 {int(i/9)} {i%9}] - r{fr}")
#   i += 1

#if not detailed_print:
#   print(f"  drr - iids: {pre_i} - {i - 1}")

#print("")

#print("short kyte basic arithmetic - gid: 2")

#i = 0

# uadd ins
# root to p0 - func to move from root to addition term 1
# p0 to op0 - func to move from addition term 1 to op0 (inversible)
# p1 to op0 - func to move from addition term 2 to op0 (inversible)

uadd_var = f"""
uadd-t0-mid<[var]>
   [p0 to op0]
   {op0_to_op[3]}
konec

{ucode_redefine_var_func(move_kyte_var, ("[var]", "[user place]", "[user mid point]"), ("uadd-t0-[var]", "polož", "uadd-t0-mid<[var]>"))}
{ucode_redefine_var_func(copy_fetch_var, ("[var]", "[p1 to op0]", "[p0 to op0]"), ("uadd-t1-[var]", op0_to_op[2], "[p1 to op0]"))}

uadd-sum-mid<[var]>
   {behind}
   {op0_to_op[3]}
   [p0 to op0]
   {behind}
konec

{ucode_redefine_var_func(move_kyte_var, ("[var]", "[user place]", "[user mid point]"), ("uadd-sum-[var]", "polož", "uadd-sum-mid<[var]>"))}

uadd<[var]>
   {root_align}
   {inc_and_carry}
   [root to p0]
   move-kyte<uadd-t0-[var]>
   {behind}
   {op0_to_op[3]}
   [p1 to op0]
   {behind}
   copy-fetch<uadd-t1-[var]>
   [p1 to op0]
   {op0_to_op[3]}
   {invert}
   {behind}
   krok
   {behind}
   opakuj 3-krát
      {sub_kat}
   konec
   {shift_left}
   // check for overflow
   když je značka
      zvedni
      {behind}
      {dkrok}
      {op0_to_op[2]}
      {r_to_op0[4]}
      {behind}
      {shift_right}
      {set_overflow}
   konec, jinak
      {behind}
      {dkrok}
      {op0_to_op[2]}
      {r_to_op0[4]}
      {behind}
      {shift_right}
      {set_normalflow}
   konec
   {shift_left}
   {r_to_op0[4]}
   {op0_to_op[3]}
   {invert}
   move-kyte<uadd-sum-[var]>
   {root_align}
konec
"""

uadd_same_term_var = f"""
uadd-t0-mid<[var]>
   [p0 to op0]
   {op0_to_op[3]}
konec

uadd-t1-mid<[var]>
   {behind}
   {op0_to_op[3]}
   {behind}
konec

{ucode_redefine_var_func(move_kyte_var, ("[var]", "[user place]", "[user mid point]"), ("uadd-t0-[var]", "polož", "uadd-t0-mid<[var]>"))}
{ucode_redefine_var_func(copy_fetch_var, ("[var]", "[p1 to op0]", "[p0 to op0]"), ("uadd-t1-[var]", op0_to_op[2], "uadd-t1-mid<[var]>"))}

uadd-sum-mid<[var]>
   {behind}
   {op0_to_op[3]}
   [p0 to op0]
   {behind}
konec

{ucode_redefine_var_func(move_kyte_var, ("[var]", "[user place]", "[user mid point]"), ("uadd-sum-[var]", "polož", "uadd-sum-mid<[var]>"))}

uadd<[var]>
   {root_align}
   {inc_and_carry}
   [root to p0]
   move-kyte<uadd-t0-[var]>
   copy-fetch<uadd-t1-[var]>
   {invert}
   {behind}
   krok
   {behind}
   opakuj 3-krát
      {sub_kat}
   konec
   {shift_left}
   // check for overflow
   když je značka
      zvedni
      {behind}
      {dkrok}
      {op0_to_op[2]}
      {r_to_op0[4]}
      {behind}
      {shift_right}
      {set_overflow}
   konec, jinak
      {behind}
      {dkrok}
      {op0_to_op[2]}
      {r_to_op0[4]}
      {behind}
      {shift_right}
      {set_normalflow}
   konec
   {shift_left}
   {r_to_op0[4]}
   {op0_to_op[3]}
   {invert}
   move-kyte<uadd-sum-[var]>
   {root_align}
konec
"""

#pre_i = i

#if detailed_print:
#   print("\nuadd - add register 2 to register")

for ins_data in instructions["uadd"]:
   if not int(ins_data[2]) == int(ins_data[3]):
      ins_map[int(ins_data[0])][int(ins_data[1])] = ucode_instantiate_var(uadd_var, ("[var]", "[root to p0]", "[p0 to op0]", "[p1 to op0]"), (f"r{int(ins_data[2])}-r{int(ins_data[3])}", r_to_r[4][int(ins_data[2])], r_to_op0[int(ins_data[2])], r_to_op0[int(ins_data[3])]))
   else:
      ins_map[int(ins_data[0])][int(ins_data[1])] = ucode_instantiate_var(uadd_same_term_var, ("[var]", "[root to p0]", "[p0 to op0]", "[p1 to op0]"), (f"r{int(ins_data[2])}-r{int(ins_data[3])}", r_to_r[4][int(ins_data[2])], r_to_op0[int(ins_data[2])], r_to_op0[int(ins_data[3])]))

#for fr in range(4):
#   for sr in range(4):
#      if not fr == sr:
#         ins_map[2][i] = ucode_instantiate_var(uadd_var, ("[var]", "[root to p0]", "[p0 to op0]", "[p1 to op0]"), (f"r{fr}-r{sr}", r_to_r[4][fr], r_to_op0[fr], r_to_op0[sr]))
#      else:
#         ins_map[2][i] = ucode_instantiate_var(uadd_same_term_var, ("[var]", "[root to p0]", "[p0 to op0]", "[p1 to op0]"), (f"r{fr}-r{sr}", r_to_r[4][fr], r_to_op0[fr], r_to_op0[sr]))
#      if detailed_print:
#         print(f"   {i} - [2 {int(i/9)} {i%9}] - r{fr} <- r{sr}")
#      i += 1
      
#if not detailed_print:
#   print(f"  uadd - iids: {pre_i} - {i - 1}")



# usub ins
# root to p0 - func to move from root to term 1
# p0 to op0 - func to move from term 1 to op0 (inversible)
# p1 to op0 - func to move from term 2 to op0 (inversible)

usub_var = f"""
usub-t0-mid<[var]>
   [p0 to op0]
   {op0_to_op[3]}
konec

{ucode_redefine_var_func(move_kyte_var, ("[var]", "[user place]", "[user mid point]"), ("usub-t0-[var]", "polož", "usub-t0-mid<[var]>"))}
{ucode_redefine_var_func(copy_fetch_var, ("[var]", "[p1 to op0]", "[p0 to op0]"), ("usub-t1-[var]", op0_to_op[2], "[p1 to op0]"))}

usub-diff-mid<[var]>
   {behind}
   {op0_to_op[3]}
   [p0 to op0]
   {behind}
konec

{ucode_redefine_var_func(move_kyte_var, ("[var]", "[user place]", "[user mid point]"), ("usub-diff-[var]", "polož", "usub-diff-mid<[var]>"))}

usub<[var]>
   {root_align}
   {inc_and_carry}
   [root to p0]
   move-kyte<usub-t0-[var]>
   {behind}
   {op0_to_op[3]}
   [p1 to op0]
   {behind}
   copy-fetch<usub-t1-[var]>
   [p1 to op0]
   {op0_to_op[3]}
   {behind}
   krok
   {behind}
   opakuj 3-krát
      {sub_kat}
   konec
   {shift_left}
   // check for underflow
   když je značka
      zvedni
      {behind}
      {dkrok}
      {op0_to_op[2]}
      {r_to_op0[4]}
      {behind}
      {shift_right}
      {set_underflow}
   konec, jinak
      {behind}
      {dkrok}
      {op0_to_op[2]}
      {r_to_op0[4]}
      {behind}
      {shift_right}
      {set_normalflow}
   konec
   {shift_left}
   {r_to_op0[4]}
   {op0_to_op[3]}
   move-kyte<usub-diff-[var]>
   {root_align}
konec
"""

# usub_same_term_var = f"""
# usub-t0-mid<[var]>
#    [p0 to op0]
#    {op0_to_op[3]}
# konec
# 
# usub-t1-mid<[var]>
#    {behind}
#    {op0_to_op[3]}
#    {behind}
# konec
# 
# {ucode_redefine_var_func(move_kyte_var, ("[var]", "[user place]", "[user mid point]"), ("usub-t0-[var]", "polož", "usub-t0-mid<[var]>"))}
# {ucode_redefine_var_func(copy_fetch_var, ("[var]", "[p1 to op0]", "[p0 to op0]"), ("usub-t1-[var]", op0_to_op[2], "usub-t1-mid<[var]>"))}
# 
# usub-diff-mid<[var]>
#    {behind}
#    {op0_to_op[3]}
#    [p0 to op0]
#    {behind}
# konec
# 
# {ucode_redefine_var_func(move_kyte_var, ("[var]", "[user place]", "[user mid point]"), ("usub-diff-[var]", "polož", "usub-diff-mid<[var]>"))}
# 
# usub<[var]>
#    {root_align}
#    {inc_and_carry}
#    [root to p0]
#    move-kyte<usub-t0-[var]>
#    copy-fetch<usub-t1-[var]>
#    {behind}
#    krok
#    {behind}
#    opakuj 3-krát
#       {sub_kat}
#    konec
#    {shift_left}
#    // check for overflow
#    když je značka
#       zvedni
#       {behind}
#       {dkrok}
#       {op0_to_op[2]}
#       {r_to_op0[4]}
#       {behind}
#       {shift_right}
#       {set_overflow}
#    konec, jinak
#       {behind}
#       {dkrok}
#       {op0_to_op[2]}
#       {r_to_op0[4]}
#       {behind}
#       {shift_right}
#       {set_normalflow}
#    konec
#    {shift_left}
#    {r_to_op0[4]}
#    {op0_to_op[3]}
#    move-kyte<usub-diff-[var]>
#    {root_align}
# konec
# """

#pre_i = i

#if detailed_print:
#   print("\nusub - subtract register 2 from register")

for ins_data in instructions["usub"]:
   if not int(ins_data[2]) == int(ins_data[3]):
      ins_map[int(ins_data[0])][int(ins_data[1])] = ucode_instantiate_var(usub_var, ("[var]", "[root to p0]", "[p0 to op0]", "[p1 to op0]"), (f"r{int(ins_data[2])}-r{int(ins_data[3])}", r_to_r[4][int(ins_data[2])], r_to_op0[int(ins_data[2])], r_to_op0[int(ins_data[3])]))   
   #else:
   #   ins_map[2][i] = ucode_instantiate_var(usub_same_term_var, ("[var]", "[root to p0]", "[p0 to op0]", "[p1 to op0]"), (f"r{fr}-r{sr}", r_to_r[4][fr], r_to_op0[fr], r_to_op0[sr]))


#for fr in range(4):
#   for sr in range(4):
#      if not fr == sr:
#         ins_map[2][i] = ucode_instantiate_var(usub_var, ("[var]", "[root to p0]", "[p0 to op0]", "[p1 to op0]"), (f"r{fr}-r{sr}", r_to_r[4][fr], r_to_op0[fr], r_to_op0[sr]))
#         if detailed_print:
#            print(f"   {i} - [2 {int(i/9)} {i%9}] - r{fr} <- r{sr}")
#         i += 1
#      # else:
#      #   ins_map[2][i] = ucode_instantiate_var(usub_same_term_var, ("[var]", "[root to p0]", "[p0 to op0]", "[p1 to op0]"), (f"r{fr}-r{sr}", r_to_r[4][fr], r_to_op0[fr], r_to_op0[sr]))
#      # i += 1

#if not detailed_print:
#   print(f"  usub - iids: {pre_i} - {i - 1}")

# umul ins

# RESERVE UMUL

umul_var = f"""
umul<[var]>

konec
"""

#pre_i = i

#if detailed_print:
#   print("\numul - multiply register by register 2 TODO - RESERVED")

for ins_data in instructions["umul"]:
   ins_map[int(ins_data[0])][int(ins_data[1])] = ucode_instantiate_var(umul_var, ("[var]", "[root to p0]", "[p0 to op0]", "[p1 to op0]"), (f"r{int(ins_data[2])}-r{int(ins_data[3])}", r_to_r[4][int(ins_data[2])], r_to_op0[int(ins_data[2])], r_to_op0[int(ins_data[3])]))

#for fr in range(4):
#   for sr in range(4):
#      if not fr == sr:
#         ins_map[2][i] = ucode_instantiate_var(umul_var, ("[var]", "[root to p0]", "[p0 to op0]", "[p1 to op0]"), (f"r{fr}-r{sr}", r_to_r[4][fr], r_to_op0[fr], r_to_op0[sr]))
#         if detailed_print:
#            print(f"   {i} - [2 {int(i/9)} {i%9}] - r{fr} <- r{sr}")
#         i += 1

#if not detailed_print:
#   print(f"  umul - iids: {pre_i} - {i - 1} TODO - RESERVED")


# udiv ins

# RESERVE UDIV

udiv_var = f"""
udiv<[var]>

konec
"""

#pre_i = i

#if detailed_print:
#   print("\nudiv - divide register by register 2 TODO - RESERVED")

for ins_data in instructions["udiv"]:
   ins_map[int(ins_data[0])][int(ins_data[1])] = ucode_instantiate_var(udiv_var, ("[var]", "[root to p0]", "[p0 to op0]", "[p1 to op0]"), (f"r{int(ins_data[2])}-r{int(ins_data[3])}", r_to_r[4][int(ins_data[2])], r_to_op0[int(ins_data[2])], r_to_op0[int(ins_data[3])]))


#for fr in range(4):
#   for sr in range(4):
#      if not fr == sr:
#         ins_map[2][i] = ucode_instantiate_var(udiv_var, ("[var]", "[root to p0]", "[p0 to op0]", "[p1 to op0]"), (f"r{fr}-r{sr}", r_to_r[4][fr], r_to_op0[fr], r_to_op0[sr]))
#         if detailed_print:
#            print(f"   {i} - [2 {int(i/9)} {i%9}] - r{fr} <- r{sr}")
#         i += 1

#if not detailed_print:
#   print(f"  udiv - iids: {pre_i} - {i - 1} TODO - RESERVED")



# uinc ins

uinc_var = f"""
uinc<[var]>
   {root_align}
   {inc_and_carry}
   [root to p0]
   {inc_and_carry}
   {root_align}
konec
"""

#pre_i = i

#if detailed_print:
#   print("\nuinc - increment register")

for ins_data in instructions["uinc"]:
   ins_map[int(ins_data[0])][int(ins_data[1])] = ucode_instantiate_var(uinc_var, ("[var]", "[root to p0]"), (f"r{int(ins_data[2])}", r_to_r[4][int(ins_data[2])]))

#for fr in range(4):
#   ins_map[2][i] = ucode_instantiate_var(
#      uinc_var, ("[var]", "[root to p0]"), (f"r{fr}", r_to_r[4][fr]))
#   if detailed_print:
#      print(f"   {i} - [2 {int(i/9)} {i%9}] - r{fr}")
#   i += 1

#if not detailed_print:
#   print(f"  uinc - iids: {pre_i} - {i - 1}")


# udec ins

udec_var = f"""
udec<[var]>
   {root_align}
   {inc_and_carry}
   [root to p0]
   {sub_one_and_carry}
   {root_align}
konec
"""

#pre_i = i

#if detailed_print:
#   print("\nudec - decrement register")


for ins_data in instructions["udec"]:
   ins_map[int(ins_data[0])][int(ins_data[1])] = ucode_instantiate_var(udec_var, ("[var]", "[root to p0]"), (f"r{int(ins_data[2])}", r_to_r[4][int(ins_data[2])]))
   

#for fr in range(4):
#   ins_map[2][i] = ucode_instantiate_var(
#      udec_var, ("[var]", "[root to p0]"), (f"r{fr}", r_to_r[4][fr]))
#   if detailed_print:
#      print(f"   {i} - [2 {int(i/9)} {i%9}] - r{fr}")
#   i += 1

#if not detailed_print:
#   print(f"  udec - iids: {pre_i} - {i - 1}")


#print("")

#print("control - gid: 3")

i = 0

# ce/nce ins

is_re_comp_var = f"""
is-re-comp-rec<[var]>
   když není značka
      [write value]
   konec, jinak
      zvedni
      is-re-comp-rec<[var]>
      když není značka
         // more than value
         [write value]
         {behind}
      konec, jinak
      konec
      když je jih
         polož
      konec, jinak
         zvedni
      konec
   konec
konec

is-re-comp-rec-res<[var]>
   když není značka
      [write value]
   konec, jinak
      zvedni
      is-re-comp-rec-res<[var]>
      zvedni
   konec
konec

is-re-comp<[var]>
   is-re-comp-rec<[var]>
   když není značka
      [write value]
   konec, jinak
      když je jih
         // restore dir from more than value
         vlevo-vbok
      konec, jinak
         // less than value
         is-re-comp-rec-res<[var]>
         {right_side}
      konec
   konec
konec
"""

is_re_var = f"""

{ucode_redefine_var_func(is_re_comp_var, ("[var]", "[write value]"), ("[var]-k0", "[k0]"))}
{ucode_redefine_var_func(is_re_comp_var, ("[var]", "[write value]"), ("[var]-k1", "[k1]"))}
{ucode_redefine_var_func(is_re_comp_var, ("[var]", "[write value]"), ("[var]-k2", "[k2]"))}

is-re<[var]>
   is-re-comp<[var]-k0>
   když není východ
      krok
      is-re-comp<[var]-k1>
      když není východ
         krok
         is-re-comp<[var]-k2>
         když není východ
         konec, jinak
            {shift_right}
            {shift_right}
         konec
      konec, jinak
         {shift_right}
      konec
   konec, jinak
   konec
konec
"""

is_re_subins = []
for re_data in instructions["re"]:
   is_re_subins.append(ucode_instantiate_var(is_re_var, ("[var]", "[k0]", "[k1]", "[k2]"), (f"b{int(re_data[3])}", set_value[int(re_data[0])], set_value[int(re_data[1]) // 9], set_value[int(re_data[1]) % 9])))

ce_var = f"""
ce-step<[var]>
   vlevo-vbok
   is-re<b[bit]>
   když není východ
      {root_align}
      {r_to_op0[4]}
      {op0_to_op[1]}
      {invert}
   konec, jinak
      {adr_step}
      ce-step<[var]>
   konec
   {inc_and_carry_no_inv}
konec

{ucode_redefine_var_func(copy_fetch_var, ("[var]", "[p0 to op0]", "[p1 to op0]"), ("ce-[var]", r_to_op0[4], op0_to_op[1]))}

ce-mid<[var]>
   {behind}
   {op0_to_op[1]}
   {r_to_op0[4]}
   {behind}
konec

{ucode_redefine_var_func(move_kyte_var, ("[var]", "[user place]", "[user mid point]"), ("ce-[var]", "polož", "ce-mid<[var]>"))}

ce-success<[var]>
   {root_align}
   {inc_and_carry}
   {shift_right}
konec

ce-fail<[var]>
   {root_align}
   copy-fetch<ce-[var]>
   {address}
   {right_side}
   ce-step<[var]>
   {invert}
   move-kyte<ce-[var]>
   {shift_right}
konec

[condition impl]

ce<[var]>
   {root_align}
   {shift_right}
   [condition]
   {root_align}
konec
"""

for ins_data in instructions["ce"]:
   c_impl = ucode_redefine_var_func(cond_check_vars[int(ins_data[2])], ("[var]", "[success]", "[fail]"), (f"ce-[var]", f"ce-success<[var]>", f"ce-fail<[var]>"))

   ins_map[int(ins_data[0])][int(ins_data[1])] = ucode_instantiate_var(ce_var, ("[condition impl]", "[condition]", "[var]", "[bit]"), (c_impl, ucode_dry_define(c_impl), f"c{int(ins_data[2])}-b{int(ins_data[3])}", f"{int(ins_data[3])}"))

# note: ice uses the ce implementation except it swithes the success and fail branches to invert the result

ice_var = f"""
[condition impl]

ice<[var]>
   {root_align}
   {shift_right}
   [condition]
   {root_align}
konec
"""

for ins_data in instructions["ice"]:
   c_impl = ucode_redefine_var_func(cond_check_vars[int(ins_data[2])], ("[var]", "[success]", "[fail]"), (f"ice-[var]", f"ce-fail<[var]>", f"ce-success<[var]>"))

   ins_map[int(ins_data[0])][int(ins_data[1])] = ucode_instantiate_var(ice_var, ("[condition impl]", "[condition]", "[var]"), (c_impl, ucode_dry_define(c_impl), f"c{int(ins_data[2])}-b{int(ins_data[3])}"))

# re ins (no-op)

re_impl = ucode_define(f"""
re<>
   {root_align}
   {inc_and_carry}
konec
""")

for ins_data in instructions["re"]:
   ins_map[int(ins_data[0])][int(ins_data[1])] = re_impl

# dre block

# just a variable code block (not a func) must be ucode_redefined!
dre_restore_var = f"""// restore instruction kat
   opakuj [resval]-krát
      polož
   konec
   krok
"""

dre_subgid_var = f"""
dre-gid-[gid]-iid-[biid]-[eiid]
   [restore func]
   když není značka
      [ins-[biid]-0]
   konec, jinak
      zvedni
      když není značka
         opakuj 1-krát
            polož
         konec
         [ins-[biid]-1]
      konec, jinak
         zvedni
         když není značka
            opakuj 2-krát
               polož
            konec
            [ins-[biid]-2]
         konec, jinak
            zvedni
            když není značka
               opakuj 3-krát
                  polož
               konec
               [ins-[biid]-3]
            konec, jinak
               zvedni
               když není značka
                  opakuj 4-krát
                     polož
                  konec
                  [ins-[biid]-4]
               konec, jinak
                  zvedni
                  když není značka
                     opakuj 5-krát
                        polož
                     konec
                     [ins-[biid]-5]
                  konec, jinak
                     zvedni
                     když není značka
                        opakuj 6-krát
                           polož
                        konec
                        [ins-[biid]-6]
                     konec, jinak
                        zvedni
                        když není značka
                           opakuj 7-krát
                              polož
                           konec
                           [ins-[biid]-7]
                        konec, jinak
                           zvedni
                           když není značka
                              opakuj 8-krát
                                 polož
                              konec
                              [ins-[biid]-8]
                           konec, jinak
                              {_f_unreachable}
                           konec
                        konec
                     konec
                  konec
               konec
            konec
         konec
      konec
   konec
konec
"""

dre_gid_var = f"""
{ucode_redefine_var_func(dre_subgid_var, ("[biid]", "[eiid]", "[restore func]"), (0, 8, "krok"))}
{ucode_redefine_var_func(dre_subgid_var, ("[biid]", "[eiid]", "[restore func]"), (9, 17, ucode_redefine_var_func(dre_restore_var, ("[resval]", ), (1, ))))}
{ucode_redefine_var_func(dre_subgid_var, ("[biid]", "[eiid]", "[restore func]"), (18, 26, ucode_redefine_var_func(dre_restore_var, ("[resval]", ), (2, ))))}
{ucode_redefine_var_func(dre_subgid_var, ("[biid]", "[eiid]", "[restore func]"), (27, 35, ucode_redefine_var_func(dre_restore_var, ("[resval]", ), (3, ))))}
{ucode_redefine_var_func(dre_subgid_var, ("[biid]", "[eiid]", "[restore func]"), (36, 44, ucode_redefine_var_func(dre_restore_var, ("[resval]", ), (4, ))))}
{ucode_redefine_var_func(dre_subgid_var, ("[biid]", "[eiid]", "[restore func]"), (45, 53, ucode_redefine_var_func(dre_restore_var, ("[resval]", ), (5, ))))}
{ucode_redefine_var_func(dre_subgid_var, ("[biid]", "[eiid]", "[restore func]"), (54, 62, ucode_redefine_var_func(dre_restore_var, ("[resval]", ), (6, ))))}
{ucode_redefine_var_func(dre_subgid_var, ("[biid]", "[eiid]", "[restore func]"), (63, 71, ucode_redefine_var_func(dre_restore_var, ("[resval]", ), (7, ))))}
{ucode_redefine_var_func(dre_subgid_var, ("[biid]", "[eiid]", "[restore func]"), (72, 80, ucode_redefine_var_func(dre_restore_var, ("[resval]", ), (8, ))))}

dre-gid-[gid]
   [restore func]
   když není značka
      dre-gid-[gid]-iid-0-8
   konec, jinak
      zvedni
      když není značka
         dre-gid-[gid]-iid-9-17
      konec, jinak
         zvedni
         když není značka
            dre-gid-[gid]-iid-18-26
         konec, jinak
            zvedni
            když není značka
               dre-gid-[gid]-iid-27-35
            konec, jinak
               zvedni
               když není značka
                  dre-gid-[gid]-iid-36-44
               konec, jinak
                  zvedni
                  když není značka
                     dre-gid-[gid]-iid-45-53
                  konec, jinak
                     zvedni
                     když není značka
                        dre-gid-[gid]-iid-54-62
                     konec, jinak
                        zvedni
                        když není značka
                           dre-gid-[gid]-iid-63-71
                        konec, jinak
                           zvedni
                           když není značka
                              dre-gid-[gid]-iid-72-80
                           konec, jinak
                              {_f_unreachable}
                           konec
                        konec
                     konec
                  konec
               konec
            konec
         konec
      konec
   konec
konec
"""

dre_usage = 9 * 81

for gid in ins_map:
   for iid in gid:
      if iid == _f_unknown_instruction:
         dre_usage -= 1

print(f"root dre block usage: {round(dre_usage / (9 * 81) * 100, 2)}%")

# maps instructions from ins_map to the var dre block


def map_dre_gid_var(gid):
   _impl = dre_gid_var

   for biid in range(0, 81, 9):
      _impl = ucode_redefine_var_func(_impl, (f"[ins-{biid}-0]", f"[ins-{biid}-1]", f"[ins-{biid}-2]", f"[ins-{biid}-3]", f"[ins-{biid}-4]", f"[ins-{biid}-5]", f"[ins-{biid}-6]", f"[ins-{biid}-7]", f"[ins-{biid}-8]"), (
         ins_map[gid][biid + 0], ins_map[gid][biid + 1], ins_map[gid][biid + 2], ins_map[gid][biid + 3], ins_map[gid][biid + 4], ins_map[gid][biid + 5], ins_map[gid][biid + 6], ins_map[gid][biid + 7], ins_map[gid][biid + 8]))

   return _impl


dre = ucode_define(f"""
{ucode_redefine_var_func(map_dre_gid_var(0), ("[gid]", "[restore func]"), (0, "krok"))}
{ucode_redefine_var_func(map_dre_gid_var(1), ("[gid]", "[restore func]"), (1, ucode_redefine_var_func(dre_restore_var, ("[resval]", ), (1, ))))}
{ucode_redefine_var_func(map_dre_gid_var(2), ("[gid]", "[restore func]"), (2, ucode_redefine_var_func(dre_restore_var, ("[resval]", ), (2, ))))}
{ucode_redefine_var_func(map_dre_gid_var(3), ("[gid]", "[restore func]"), (3, ucode_redefine_var_func(dre_restore_var, ("[resval]", ), (3, ))))}
{ucode_redefine_var_func(map_dre_gid_var(4), ("[gid]", "[restore func]"), (4, ucode_redefine_var_func(dre_restore_var, ("[resval]", ), (4, ))))}
{ucode_redefine_var_func(map_dre_gid_var(5), ("[gid]", "[restore func]"), (5, ucode_redefine_var_func(dre_restore_var, ("[resval]", ), (5, ))))}
{ucode_redefine_var_func(map_dre_gid_var(6), ("[gid]", "[restore func]"), (6, ucode_redefine_var_func(dre_restore_var, ("[resval]", ), (6, ))))}
{ucode_redefine_var_func(map_dre_gid_var(7), ("[gid]", "[restore func]"), (7, ucode_redefine_var_func(dre_restore_var, ("[resval]", ), (7, ))))}
{ucode_redefine_var_func(map_dre_gid_var(8), ("[gid]", "[restore func]"), (8, ucode_redefine_var_func(dre_restore_var, ("[resval]", ), (8, ))))}

__dre__
   // decode, restore, execute combined function
   když není značka
      dre-gid-0
   konec, jinak
      zvedni
      když není značka
         dre-gid-1
      konec, jinak
         zvedni
         když není značka
            dre-gid-2
         konec, jinak
            zvedni
            když není značka
               dre-gid-3
            konec, jinak
               zvedni
               když není značka
                  dre-gid-4
               konec, jinak
                  zvedni
                  když není značka
                     dre-gid-5
                  konec, jinak
                     zvedni
                     když není značka
                        dre-gid-6
                     konec, jinak
                        zvedni
                        když není značka
                           dre-gid-7
                        konec, jinak
                           zvedni
                           když není značka
                              dre-gid-8
                           konec, jinak
                              {_f_unreachable}
                           konec
                        konec
                     konec
                  konec
               konec
            konec
         konec
      konec
   konec
konec
""")

# main funcs

boot = ucode_define("""
==boot==
   root-align
   __main__
konec
""")

main = ucode_define("""
__main__
   dokud není sever
      __fetch__
      __dre__
   konec
konec
""")

fetch = ucode_define(f"""
{ucode_redefine_var_func(copy_fetch_var, ("[var]", "[p0 to op0]", "[p1 to op0]"), ("fetch", r_to_op0[4], op0_to_op[1]))}

__fetch__
   copy-fetch<fetch>
   {r_to_op0[4]}
   {op0_to_op[1]}
   address
konec
""")

# == set world ==

pre_world = """
Velikost města: 20, 20
Pozice Karla: 7, 1
Otočení Karla: VÝCHOD
Umístění domova: 7, 1
Definice města:
"""

out.write(pre_world)

world = """
....................
....................
....................
....................
....................
....................
....................
....................
....................
....................
....................
....................
....................
....................
....................
....................
....................
....................
....................
....................
"""
out.write(world.replace("\n","", 1))


# == end ucode ==

out.close()


# == save copies ==

data = []

with open(f"{arch}v{major}.{minor}.K99", "r") as f:
   for line in f.readlines():
      data.append(line)


# == save copy as KPU.K99 ==

if save_copy_as_KPU:
   with open(f"{arch}.K99", "w") as f:
      for line in data:
         f.write(line)


# == save copy to Keap/assembly ==

if save_to_Keap_ASM:
   with open(f"Keap/asembly/{arch}.K99", "w") as f:
      for line in data:
         f.write(line)