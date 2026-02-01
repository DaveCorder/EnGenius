# Format

The format of an EnGenius serial number is this:

```
XXXXMMMYYYYC
```

Where:

``` shell
"XXXX" = any four characters
"MMM"  = three-character model code
"YYYY" = any four characters
"C"    = check character of the string "XXXXMMMYYYY"
         using the Code27 algorithm.
```

# Generating Serial Numbers

Here is some sample Python code to generate a random serial number (just change the `model_code` variable to whatever you want/need).

``` python
#!/opt/homebrew/bin/python3

import random

### CHANGE THIS TO WHATEVER YOU NEED ###
model_code="X45"

CODE27_HASHTABLE = { "0" : "1", "1" : "D", "2" : "K", "3" : "3", "4" : "R", "5" : "5", "6" : "F", "7" : "P", "8" : "W", "9" : "M", "10" : "E", "11" : "4", "12" : "7", "13" : "G", "14" : "T", "15" : "X", "16" : "8", "17" : "V", "18" : "L", "19" : "2", "20" : "J", "21" : "6", "22" : "C", "23" : "9", "24" : "N", "25" : "Q", "26" : "H" }

VALID_SERIAL_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def compute_code27_check( serial ):
    sum = 0
    for c in range(0, len(serial)):
        sum = sum + ord(serial[c])
    return CODE27_HASHTABLE[ str(sum % len(CODE27_HASHTABLE)) ]

def get_random_string( str_len ):
    rand_string = ""
    for j in range(0, str_len):
        rand_string += VALID_SERIAL_CHARS[random.randint(0,len(VALID_SERIAL_CHARS)-1)]
    
    return rand_string
 
prefix_string = get_random_string( 4 )
suffix_string = get_random_string( 4 )
serial_without_check = prefix_string + model_code + suffix_string
check_character = compute_code27_check( serial_without_check )

print( "{serial}{check}".format( serial = serial_without_check, check = check_character ) )
```