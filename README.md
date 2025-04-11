# phpdbg
phpdbg is a gdb plugin for assisting in debugging analysis of php pwn.
## Install
```sh
git clone https://github.com/GeekCmore/phpdbg.git
cd phpdbg
echo "source /path/to/phpdbg" >> ~/.gdbinit
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

