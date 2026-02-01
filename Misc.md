# ssh

```
➜  original-firmware /Users/dcorder/Documents/engenius/firmware-utils/src/mksenaofw -d Fit6_4x4_Lite_EWS377-FIT_firmware_v1.1.65-2.bin -o Fit6_4x4_Lite_EWS377-FIT_firmware_v1.1.65-2-decoded.bin
Header.head:
0
Header.vendor_id:
257
Header.product_id:
300
Header.firmware_type:
0
Header.filesize:
36967696
Header.chksum:
2462
Header.magic:
305419896
cw_header.mod:
1634495488
cw_header.sku:
0
cw_header.firmware_ver[0]:
1
cw_header.firmware_ver[1]:
1
cw_header.firmware_ver[2]:
65
cw_header.datecode:
250205
cw_header.capwap_ver[0]:
0
cw_header.capwap_ver[1]:
0
cw_header.capwap_ver[2]:
0
cw_header.model_size:
10
pmodel:

➜  original-firmware /Users/dcorder/Documents/engenius/firmware-utils/src/mksenaofw -d Cloud6_4x4_ECW230v3_firmware_v1.8.103-7.bin -o Cloud6_4x4_ECW230v3_firmware_v1.8.103-7-decoded.bin
Header.head:
0
Header.vendor_id:
257
Header.product_id:
284
Header.firmware_type:
0
Header.filesize:
44569872
Header.chksum:
1151
Header.magic:
305419896
cw_header.mod:
1634495488
cw_header.sku:
0
cw_header.firmware_ver[0]:
1
cw_header.firmware_ver[1]:
8
cw_header.firmware_ver[2]:
103
cw_header.datecode:
251009
cw_header.capwap_ver[0]:
0
cw_header.capwap_ver[1]:
0
cw_header.capwap_ver[2]:
0
cw_header.model_size:
8
pmodel:
```

```
➜  original-firmware binwalk Fit6_4x4_Lite_EWS377-FIT_firmware_v1.1.65-2-decoded.bin

           /Users/dcorder/Documents/engenius/ecw230v3/convert-back-to-stock/original-firmware/Fit6_4x4_Lite_EWS377-FIT_firmware_v1.1.65-2-decoded.bin
----------------------------------------------------------------------------------------------------------------------------------------------------------------
DECIMAL                            HEXADECIMAL                        DESCRIPTION
----------------------------------------------------------------------------------------------------------------------------------------------------------------
0                                  0x0                                Device tree blob (DTB), version: 17, CPU ID: 0, total size: 36967696 bytes
----------------------------------------------------------------------------------------------------------------------------------------------------------------

Analyzed 1 file for 85 file signatures (187 magic patterns) in 137.0 milliseconds
```


lighttpd -f /etc/lighttpd/lighttpd.conf

https://192.168.1.1:4331/

# asdfasdf

`/lib/upgrade/common.sh get_magic_long`

```
get_image "$@" | dd bs=4 count=1 | hexdump -v -n 4 -e '1/1 "%02x"') 2>/
dev/null
```
```
get_image() { # <source> [ <command> ]
	local from="$1"
	local cmd="$2"

	if [ -z "$cmd" ]; then
		local magic="$(dd if="$from" bs=2 count=1 2>/dev/null | hexdump
-n 2 -e '1/1 "%02x"')"
		case "$magic" in
			1f8b) cmd="zcat";;
			425a) cmd="bzcat";;
			*) cmd="cat";;
		esac
	fi

	cat "$from" 2>/dev/null | $cmd
}
```
Uploading legit file gives:

```

-rw-r--r--    1 root     root            75 Feb  5 01:12 fw_id.txt
-rw-r--r--    1 root     root      36967842 Feb  5 01:12 firmware.img
```

```
sn_decode_image_header() {
	# decode image
	local input="$@"

	if [ $input ]; then
		#free mem
		sync;echo 3 > /proc/sys/vm/drop_caches
		magic=$( hexdump -v -n 4 -e '1/1 "%02x"' $input)
		echo " magic num  = $magic" >> /dev/console
		if [ $magic -ne 27051956 ] && [ $magic -eq 00000000 ]; then
			fw_version=`header -g "$input" |awk '/^version id:/{prin
t $3}'`
			echo "fw_version = $fw_version" >> /dev/console
			# downgrade to spf11.x, check version = 1.0.x
			fw_major_ver=$(echo "$fw_version" | awk -F '[.-]' '{prin
t $1}')
			fw_minor_ver=$(echo "$fw_version" | awk -F '[.-]' '{prin
t $2}')
			[ $fw_major_ver -eq 1 -a $fw_minor_ver -eq 0 ] && {
			# spf12.2 wireless.wifix.type=qcawificfg80211
			# spf11.x wireless.wifix.type=qcawifi
				wifi_devices=$(foreach wireless wifi-device)
				for device in $wifi_devices; do
					uci set wireless.${device}.type='qcawifi
'
				done
				uci commit wireless
			}
			# check SENAO HWID
			( eval senao_image_header_check $input ) || {
				if [ $FORCE -eq 1 ]; then
					echo "Image check senao_image_header_che
ck failed but --force given - will update anyway!"
					break
				else
					echo "Image check senao_image_header_che
ck failed."
					if [ -f /usr/sbin/snlogger ]; then
						snlogger "event.info 1.0" "ap_fw
_upgrade_failed,reason='Model mismatch'"
					fi
					exit 1
				fi
			}
		( header -x "$input" | grep "Return OK" ) || {
			if [ -f /usr/sbin/snlogger ]; then
				snlogger "event.info 1.0" "ap_fw_upgrade_failed,
reason='Checksum failed with md5'"
			fi
			echo "Image checksum failed."
			exit
		}
		# free memory & check.
		sn_check_memory $input

		echo "decoding image" >> /dev/console
	else
		echo "normal OpenWRT image" >> /dev/console
		fi
	fi
}
```

```
senao_get_vender_id() {
	get_image "$@" | dd bs=2 count=1 skip=3 2>/dev/null | hexdump -v -n 2 -e
 '1/1 "%02x"'
}

senao_get_product_id() {
	get_image "$@" | dd bs=2 count=1 skip=5 2>/dev/null | hexdump -v -n 2 -e
 '1/1 "%02x"'
}

senao_image_header_check(){
	fw_id_check=1
	fw_invalid_check=1
	senao_magic_long="$(get_magic_long "$1")"
	senao_vendor_id="$(senao_get_vender_id "$1")"
	senao_product_id="$(senao_get_product_id "$1")"
	echo "senao_magic_long = $senao_magic_long" >> /tmp/fw_id.txt
	check_senao_image_header $senao_magic_long $senao_vendor_id $senao_produ
ct_id && fw_id_check=0
	header -k $1 > /dev/null && fw_invalid_check=0
	#echo "fw_id_check $fw_id_check" > /dev/console
	#echo "fw_invalid_check $fw_invalid_check" > /dev/console
	fw_result=$((fw_id_check | fw_invalid_check))
	#echo "0:pass 1:fail fw_result:[$fw_result]" > /dev/console
	return $fw_result
}
```

```
root@EWS377-FIT:/lib# grep senao_image_header_check */*sh
upgrade/sn_common.sh:			( eval senao_image_header_check $input ) || {
upgrade/sn_common.sh:					echo "Image check senao_image_header_check failed but --force given - will update anyway!"
upgrade/sn_common.sh:					echo "Image check senao_image_header_check failed."
upgrade/sn_common.sh:senao_image_header_check(){
upgrade/sn_common.sh:        echo "senao_image_header_check started for $i" >> /tmp/dave.log
```

# EWS377-FIT conversion back to ECW230

Applies to v3 of the hardware (FCC ID: A8J-EWS377APV3A)

From FIT FW 1.1.65.

Disconnect from network. Plug into 12v adapter and secondary Ethernet interface on my desktop. Set desktop interface to 192.168.1.22/255.255.255.0 with gateway 192.168.1.1

Factory reset with button on unit.

Log into web UI at http://192.168.1.1/ with admin/admin.

You should be prompted to set a new username/password.



