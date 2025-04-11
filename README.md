# phpdbg
phpdbg is a gdb plugin for assisting in debugging analysis of php pwn.
## Install
```sh
git clone https://github.com/GeekCmore/phpdbg.git
echo "source /path/to/phpdbg/phpdbg.py" >> ~/.gdbinit
sudo apt install php-cli-dbgsym
```

## Command

### pstart
When launching the program, use `pstart` instead of `start`, which will stop at the location where the extension module loading is completed, after which you can set a breakpoint in the extension module.
```
gdb> pstart
...
gdb> b zif_some_mod_func
```

### pheap
Print the topmost heap management structure.
```
gdb> pheap
$2 = {
  use_custom_heap = 0x0,
  storage = 0x0,
  size = 0x30,
  peak = 0x30,
  free_slot = {0x0, 0x0, 0x0, 0x0, 0x0, 0x7ffff4e01030, 0x0 <repeats 24 times>},
  real_size = 0x200000,
  real_peak = 0x200000,
  limit = 0xffffffffffffffff,
  overflow = 0x0,
  huge_list = 0x0,
  main_chunk = 0x7ffff4e00000,
  cached_chunks = 0x0,
  chunks_count = 0x1,
  peak_chunks_count = 0x1,
  cached_chunks_count = 0x0,
  avg_chunks_count = 0x3ff0000000000000,
  last_chunks_delete_boundary = 0x0,
  last_chunks_delete_count = 0x0,
  custom_heap = {
    std = {
      _malloc = 0x0,
      _free = 0x0,
      _realloc = 0x0
    },
    debug = {
      _malloc = 0x0,
      _free = 0x0,
      _realloc = 0x0
    }
  },
  tracked_allocs = 0x0
}
```

### psmall
This command show php zend small heap like this:
```
gdb> psmall
0x8 [  0]: 0x0 ◂— 0
0x10 [  0]: 0x0 ◂— 0
0x18 [  0]: 0x0 ◂— 0
0x20 [  0]: 0x0 ◂— 0
0x28 [  0]: 0x0 ◂— 0
0x30 [ 84]: 0x7ffff4e01030 -> 0x7ffff4e01060 -> 0x7ffff4e01090 -> 0x7ffff4e010c0 -> 0x7ffff4e010f0 -> 0x7ffff4e01120 -> 0x7ffff4e01150 -> ... ◂— 0x0
0x38 [  0]: 0x0 ◂— 0
0x40 [  0]: 0x0 ◂— 0
0x50 [  0]: 0x0 ◂— 0
0x60 [  0]: 0x0 ◂— 0
0x70 [  0]: 0x0 ◂— 0
0x80 [  0]: 0x0 ◂— 0
0xa0 [  0]: 0x0 ◂— 0
0xc0 [  0]: 0x0 ◂— 0
0xe0 [  0]: 0x0 ◂— 0
0x100 [  0]: 0x0 ◂— 0
0x140 [  0]: 0x0 ◂— 0
0x180 [  0]: 0x0 ◂— 0
0x1c0 [  0]: 0x0 ◂— 0
0x200 [  0]: 0x0 ◂— 0
0x280 [  0]: 0x0 ◂— 0
0x300 [  0]: 0x0 ◂— 0
0x380 [  0]: 0x0 ◂— 0
0x400 [  0]: 0x0 ◂— 0
0x500 [  0]: 0x0 ◂— 0
0x600 [  0]: 0x0 ◂— 0
0x700 [  0]: 0x0 ◂— 0
0x800 [  0]: 0x0 ◂— 0
0xa00 [  0]: 0x0 ◂— 0
0xc00 [  0]: 0x0 ◂— 0

```

### pelement
Given an address, find the element it belongs to.
```
gdb> pelement 0x7ffff4e57078
Target address: 0x7ffff4e57078
Block type:    SMALL
Chunk start:   0x7ffff4e00000
Page start:     0x7ffff4e57000
Element start: 0x7ffff4e57078
Element size:  24 bytes (bin #2)
Elements/page: 170
```