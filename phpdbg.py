import gdb
from collections import OrderedDict

class PhpSmallHeapCommand(gdb.Command):
    def __init__(self):
        super(PhpSmallHeapCommand, self).__init__("psmall", gdb.COMMAND_USER)
        self.COLOR_RESET = "\033[0m"
        self.COLOR_SIZE = "\033[33m"
        self.COLOR_COUNT = "\033[36m"
        self.COLOR_ADDR = "\033[32m"
        self.COLOR_WARN = "\033[31m"

    def safe_dereference(self, ptr):
        try:
            return ptr.dereference()
        except gdb.MemoryError:
            return None

    def traverse_list(self, head):
        visited = OrderedDict()
        current = head
        cycle_start = None
        last_ptr = 0
        next_value = 0

        while int(current) != 0:
            if int(current) in visited:
                cycle_start = visited[int(current)]
                next_value = current
                break

            visited[int(current)] = len(visited) + 1
            entry = self.safe_dereference(current)
            
            if not entry:
                break

            next_ptr = entry['next_free_slot']
            last_ptr = current
            current = next_ptr

            if len(visited) > 100:  # Safety limit
                break

        return visited, cycle_start, last_ptr, next_value

    def invoke(self, arg, from_tty):
        bin_sizes = [
            8, 16, 24, 32, 40, 48, 56, 64, 80, 96,
            112, 128, 160, 192, 224, 256, 320, 384, 448, 512,
            640, 768, 896, 1024, 1280, 1536, 1792, 2048, 2560, 3072
        ]

        try:
            alloc_globals = gdb.parse_and_eval("alloc_globals")
            mm_heap = alloc_globals['mm_heap']
            if int(mm_heap) == 0:
                print(f"{self.COLOR_WARN}mm_heap is NULL{self.COLOR_RESET}")
                return
        except gdb.error as e:
            print(f"{self.COLOR_WARN}Error: {e}{self.COLOR_RESET}")
            return

        for idx in range(len(bin_sizes)):
            size = bin_sizes[idx]
            hex_size = f"0x{size:x}"
            free_slot = mm_heap['free_slot'][idx]

            visited, cycle_start, last_ptr, next_val = self.traverse_list(free_slot)
            count = len(visited)
            pointers = []

            for i, addr in enumerate(visited.keys()):
                if i < 7:
                    pointers.append(f"{self.COLOR_ADDR}0x{addr:x}{self.COLOR_RESET}")
                else:
                    pointers.append(f"{self.COLOR_WARN}...{self.COLOR_RESET}")
                    break

            # Build pointer string
            pointer_str = " -> ".join(pointers)
            if count > 0:
                final_value = ""
                if cycle_start is not None:
                    final_value = f"{self.COLOR_WARN}◂— 0x{int(next_val):x} (cycle detected at entry #{cycle_start}){self.COLOR_RESET}"
                else:
                    try:
                        final_next = int(last_ptr.dereference()['next_free_slot']) if int(last_ptr) != 0 else 0
                        final_value = f"◂— {self.COLOR_ADDR}0x{final_next:x}{self.COLOR_RESET}"
                    except:
                        final_value = f"{self.COLOR_WARN}◂— [invalid]{self.COLOR_RESET}"

                pointer_str += f" {final_value}"

            print(f"{self.COLOR_SIZE}{hex_size}{self.COLOR_RESET} "
                  f"[{self.COLOR_COUNT}{count:3}{self.COLOR_RESET}]: "
                  f"{pointer_str if count > 0 else f'{self.COLOR_ADDR}0x0 ◂— 0{self.COLOR_RESET}'}")

class PhpHeap(gdb.Command):
    def __init__(self):
        super(PhpHeap, self).__init__("pheap", gdb.COMMAND_USER)
    
    def invoke(self, arg, from_tty):
        gdb.execute("p/x *alloc_globals.mm_heap")

class PhpStartCommand(gdb.Command):
    def __init__(self):
        super(PhpStartCommand, self).__init__("pstart", gdb.COMMAND_USER)
    
    def invoke(self, arg, from_tty):
        gdb.execute("start")
        gdb.Breakpoint("php_module_startup")
        gdb.execute("continue")
        gdb.execute("finish")
        


# 注册自定义命令
PhpStartCommand()
PhpSmallHeapCommand()
PhpHeap()