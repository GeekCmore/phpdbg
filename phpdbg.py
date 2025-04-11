import gdb
from collections import OrderedDict
import struct

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
            pointer_str = " —▸ ".join(pointers)
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
        


# ANSI颜色代码
COLOR_RESET = "\033[0m"
COLOR_ADDR = "\033[92m"   # 绿色
COLOR_TYPE = "\033[93m"    # 黄色
COLOR_INFO = "\033[96m"    # 青色
COLOR_HUGE = "\033[91m"    # 红色
COLOR_LARGE = "\033[94m"   # 蓝色

# Zend内存常量
ZEND_MM_CHUNK_SIZE = 2 * 1024 * 1024  # 2MB
ZEND_MM_PAGE_SIZE = 4096              # 4KB
ZEND_MM_PAGES = ZEND_MM_CHUNK_SIZE // ZEND_MM_PAGE_SIZE

class ZendMMChunk:
    def __init__(self, addr):
        self.addr = int(addr)
        self.map = []
        self.load()

    def load(self):
        """加载chunk内存结构"""
        chunk_type = gdb.lookup_type('struct _zend_mm_chunk').pointer()
        chunk = gdb.Value(self.addr).cast(chunk_type)
        for i in range(ZEND_MM_PAGES):
            self.map.append(int(chunk['map'][i]))

class PhpElement(gdb.Command):
    def __init__(self):
        super(PhpElement, self).__init__("pelement", gdb.COMMAND_USER)
    
    def get_heap(self):
        """获取堆结构"""
        return gdb.parse_and_eval('alloc_globals.mm_heap')

    def check_huge_block(self, addr):
        """检查是否属于huge块"""
        heap = self.get_heap()
        huge_list = heap['huge_list']
        while huge_list:
            entry = huge_list.dereference()
            ptr = int(entry['ptr'])
            size = int(entry['size'])
            if ptr <= addr < (ptr + size):
                return (ptr, size)
            huge_list = entry['next']
        return None

    def get_chunk(self, addr):
        """查找包含地址的chunk"""
        heap = self.get_heap()
        main_chunk = int(heap['main_chunk'])
        current = main_chunk
        while True:
            chunk_start = current
            chunk_end = current + ZEND_MM_CHUNK_SIZE
            if chunk_start <= addr < chunk_end:
                return ZendMMChunk(chunk_start)
            next_ptr = int(gdb.Value(current).cast(gdb.lookup_type('struct _zend_mm_chunk').pointer())['next'])
            if next_ptr == main_chunk:
                break
            current = next_ptr
        return None

    def analyze_small(self, chunk, page_num, addr):
        """分析Small内存块"""
        info = chunk.map[page_num]
        bin_num = info & 0x1F  # 提取bin编号
        
        try:
            element_size = int(gdb.parse_and_eval(f'bin_data_size[{bin_num}]'))
            elements_per_page = int(gdb.parse_and_eval(f'bin_elements[{bin_num}]'))
        except:
            element_size = ZEND_MM_PAGE_SIZE
            elements_per_page = 1

        # 计算元素精确地址
        page_start = chunk.addr + page_num * ZEND_MM_PAGE_SIZE
        element_index = (addr - page_start) // element_size
        return {
            'type': 'small',
            'start': page_start + element_index * element_size,
            'size': element_size,
            'bin_num': bin_num,
            'page_start': page_start,
            'elements': elements_per_page
        }

    def analyze_large(self, chunk, page_num):
        """分析Large内存块"""
        info = chunk.map[page_num]
        pages = info & 0x3FF  # 提取页面数量
        return {
            'type': 'large',
            'start': chunk.addr + page_num * ZEND_MM_PAGE_SIZE,
            'size': pages * ZEND_MM_PAGE_SIZE,
            'pages': pages
        }

    def print_result(self, addr, result):
        """彩色输出结果"""
        print(f"{COLOR_ADDR}Target address:{COLOR_RESET} 0x{addr:x}")
        
        if result['type'] == 'huge':
            print(f"{COLOR_TYPE}Block type:{COLOR_RESET}    {COLOR_HUGE}HUGE{COLOR_RESET}")
            print(f"{COLOR_INFO}Block start:{COLOR_RESET}   0x{result['start']:x}")
            print(f"{COLOR_INFO}Block size:{COLOR_RESET}    {hex(result['size'])} bytes")
        elif result['type'] == 'large':
            print(f"{COLOR_TYPE}Block type:{COLOR_RESET}    {COLOR_LARGE}LARGE{COLOR_RESET}")
            print(f"{COLOR_INFO}Chunk start:{COLOR_RESET}   0x{result['chunk_start']:x}")
            print(f"{COLOR_INFO}Block start:{COLOR_RESET}   0x{result['start']:x}")
            print(f"{COLOR_INFO}Block size:{COLOR_RESET}    {hex(result['size'])} bytes ({result['pages']} pages)")
        else:
            print(f"{COLOR_TYPE}Block type:{COLOR_RESET}    {COLOR_TYPE}SMALL{COLOR_RESET}")
            print(f"{COLOR_INFO}Chunk start:{COLOR_RESET}   0x{result['chunk_start']:x}")
            print(f"{COLOR_INFO}Page start:{COLOR_RESET}    0x{result['page_start']:x}")
            print(f"{COLOR_INFO}Element start:{COLOR_RESET} 0x{result['start']:x}")
            print(f"{COLOR_INFO}Element size:{COLOR_RESET}  {hex(result['size'])} bytes (bin #{result['bin_num']})")
            print(f"{COLOR_INFO}Elements/page:{COLOR_RESET} {result['elements']}")

    def invoke(self, arg, from_tty):
        args = gdb.string_to_argv(arg)
        if len(args) != 1:
            print(f"{COLOR_INFO}Usage: phpmm <address>{COLOR_RESET}")
            return

        try:
            addr = int(gdb.parse_and_eval(args[0]))
        except:
            print(f"{COLOR_INFO}Invalid address format{COLOR_RESET}")
            return

        # 1. 检查huge块
        huge_block = self.check_huge_block(addr)
        if huge_block:
            self.print_result(addr, {
                'type': 'huge',
                'start': huge_block[0],
                'size': huge_block[1]
            })
            return

        # 2. 查找chunk
        chunk = self.get_chunk(addr)
        if not chunk:
            print(f"{COLOR_INFO}Address not in any chunk{COLOR_RESET}")
            return

        # 3. 分析chunk内分配
        page_num = (addr - chunk.addr) // ZEND_MM_PAGE_SIZE
        info = chunk.map[page_num]
        
        if info & 0x80000000:  # SRUN (SMALL)
            result = self.analyze_small(chunk, page_num, addr)
            result['chunk_start'] = chunk.addr
            result['type'] = 'small'
        elif info & 0x40000000:  # LRUN (LARGE)
            result = self.analyze_large(chunk, page_num)
            result['chunk_start'] = chunk.addr
            result['type'] = 'large'
        else:
            print(f"{COLOR_INFO}Address points to free memory{COLOR_RESET}")
            return

        self.print_result(addr, result)

# 注册自定义命令
PhpStartCommand()
PhpSmallHeapCommand()
PhpHeap()
PhpElement()