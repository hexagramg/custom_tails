# custom_tails
python3 partial implementation of classic *tails* utility
```
usage: tails.py [-h] [--retry] [-c BYTES] [-f] [-n N] [-s S] file

positional arguments:
   file                  path to file to read
   
options:
  -h, --help            show this help message and exit
  --retry               keep trying to open a file
  -c BYTES, --bytes BYTES
                        output last N bytes
  -f, --follow          output appended data as the file grows
  -n N                  output the last N lines, default 10
  -s S                  with -f sleep for S seconds between polling
  ```
