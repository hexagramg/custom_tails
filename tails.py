import argparse
from pathlib import Path
import io
import logging
from time import sleep
from typing import Any, AnyStr, Tuple, Iterator
import sys
from unittest import skip

class IOWrapper:
    """ Wrapper class for binary IOBase
    Cursor starts at the end of file
    """
    def __init__(self, base: io.IOBase) -> None:
        self._base = base
        self._start_position = base.tell()
        self._end_position = base.seek(0, io.SEEK_END)
        self._size =  self._end_position - self._start_position 
        self._cur_postion = self._base.tell()
        self._ended_without_eos = False

    def _seek(self, offset, whence) -> int:
        self._cur_postion = self._base.seek(offset,whence)
        return self._cur_postion

    @property
    def size(self) ->int :
        """size of buffer

        Returns:
            int: size 
        """
        return self._size    
    
    @property
    def position(self) -> int:
        return self._cur_postion    
    
    def _seek_end(self) -> int:
        """
        moves cursor to the end, 
        """ 
        return self._seek(0, io.SEEK_END)
    
    def seek_offset(self, offset:int) -> int:
         
        return self._seek(offset, io.SEEK_CUR) 
    
    def read(self, bytes:int) -> Any:
        symb = self._base.read(bytes)
        self._cur_postion = self._base.tell()
        return symb

    def read_without_advance(self, bytes:int) -> Any:
        symb = self._base.read(bytes)
        self.seek_offset(-bytes)
        return symb

    @property
    def bytes_left(self) -> Tuple[int,int] :
        """ Get how many bytes left from both sides of the cursor
        
        Returns:
            Tuple[int,int]: left, right 
        """
        return self._cur_postion -self._start_position , self._end_position - self._cur_postion 

    def seek_start_of_line(self) -> int:
        """ find start of current line

        Returns:
            int: position 
        """
        first = True
        while self.bytes_left[0] > 0:
            self.seek_offset(-1)
                
            symb = self.read_without_advance(1)
            if symb  == b'\n':
                if first:
                    first = False
                    continue
                self.seek_offset(1)
                break
            first = False
        return self.position
    
    def seek_last_bytes(self, num: int) -> int:
        """move cursor up for num bytes
        if there is not enought bytes cut at 0

        Args:
            num (int): amount of bytes to shift 

        Returns:
            int: current position 
        """
        left, _ = self.bytes_left
        if left < num:
            num =  left
        self.seek_offset(-num)
        return self.position
        
    
    def seek_previous_lines(self, num:int) -> int:
        """try to move cursor up "num" lines 

        Args:
            num (int): amount of lines to seek  

        Returns:
            int: current position 
        """
        while num > 0 and self.bytes_left[0] >= 0:
            num -= 1
            self.seek_start_of_line()
            if num > 0 and self.bytes_left[0] > 0: #do not shift last iteration 
                self.seek_offset(-1)
        
        return self.position
    
    def check_size(self) -> Tuple[bool, bool]:    
        """check if the file size has changed

        Returns:
            Tuple[bool, bool]: changed, increased
        """
        cur_cursor = self.position
        end = self._seek_end()
        changed, increased = False, False
        
        if end != self._end_position:
            changed = True
            if end > self._end_position:
                increased = True
        if changed and cur_cursor > end:
            self._cur_postion = end
        else:
            self.seek_offset(cur_cursor - end)
        self._end_position = end
        return  changed, increased
        
    def __iter__(self) -> Iterator:
        """returns itself, use for reading lines through iterator
        """
        return self   

    def __next__(self) -> AnyStr:
        """Read one line from file
        if previous read was withous eos then 
        skip one line if it consists only of "\n"

        Raises:
            StopIteration: when file is exhausted 

        Returns:
            AnyStr: decoded line from file 
        """
        skip_once = True
        while skip_once:
            if self.bytes_left[1] <= 0:
                raise StopIteration
            line = self._base.readline()
            line = line.decode(sys.stdout.encoding)
            # if previous line was without eos and this one has only eos 
            # then do not print this eos 
            if self._ended_without_eos :
                self._ended_without_eos = False
                if not (len(line) == 1 and line[0]=="\n"):
                    skip_once = False 
            else:
                skip_once = False
            # if this line was withous eos set flag
            if len(line) > 0 and line[-1] != "\n":
                self._ended_without_eos = True
            else:
                line = line.replace("\n", "")
            self._cur_postion = self._base.tell()
        return line 

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--retry", 
                        help="keep trying to open a file",
                        action='store_true')
    parser.add_argument("-c", "--bytes",
                        help="output last N bytes",
                        type=int)
    parser.add_argument("-f", "--follow",
                        help="output appended data as the file grows",
                        action='store_true')
    parser.add_argument("-n", 
                        help="output the last N lines, default 10",
                        type=int,
                        default=10)
    parser.add_argument("-s",
                        help="with -f sleep for S seconds between polling",
                        default=1)
    parser.add_argument("file", help="path to file to read")
    args = parser.parse_args()
    path = Path(args.file)
    while True:
        first = False
        try:
            if path.is_file():
                p = path.resolve()
                with open(path.resolve(), mode="r+b") as file:
                    wrapper = IOWrapper(file)
                    if args.bytes is None:
                        wrapper.seek_previous_lines(args.n)
                    else:
                        wrapper.seek_last_bytes(args.bytes)
                    for line in wrapper:
                        print(line)
                    
                    while True:
                        sleep(args.s)
                        changed, increased = wrapper.check_size()
                        if changed:
                            if not increased:
                                logging.warning("file got truncated")
                                wrapper.seek_previous_lines(args.n)
                            for line in wrapper:
                                print(line)
                                 
                                
                            
                        
        except OSError as e:
            logging.warning(f'catched error {e} when file was processed')
        
        if not args.retry:
            break
            
    pass