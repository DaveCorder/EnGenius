# ENS620EXT to ECW160 conversion

Here's some tinkering I did recently to convert an ENS620EXT access point to an ECW160 AP.

## Working Theory

My working theory behind all this is

1. The ENS620EXT and ENH1350EXT are presumed to be basically the same, hardware-wise
2. The ECW160 is exactly the same as the ENH1350EXT, based on the fact that they have the same FCC ID.

All three models are described as a "11ac Wave 2, MU-MIMO, Dual-Band Wireless AC1300 Outdoor Access Point" and they all offer speeds of 867 Mbps on the 5 GHz band and 400 Mbps on the 2.4 GHz band.

I'd done some previous poking around in a root shell on the ENS1350EXT and ENS620EXT and, as far as I could tell, they used the same CPU and the same WiFi chips, with the same amount of RAM and flash memory.

The main differences between these models, as far as I've been able to determine, are:

1. The ENS620EXT has two Ethernet ports, versus one on the ENH1350EXT/ECW160
2. The ENS620EXT uses EnGenius's proprietary 24v PoE implementation, versus standard 802.3at PoE on the ENH1350EXT/ECW160.
3. The ENS620EXT is IP55-rated, whereas the ENH1350EXT/ECW160 are IP67.

So, in theory, the ENS620EXT and ENH1350EXT are close enough in their hardware that the firmware for one should be able to run on the other, barring any sort of low-level differences that I didn't see at first glance. And since the ENH1350EXT is the same hardware as the ECW160, then if I can run the ENH1350EXT firmware on the ENS620EXT, then I should also be able to run the ECW160 firmware on the ENS620EXT.

Oh, and I should mention, EnGenius devices run a private fork of OpenWRT - this is important later.

## But Why?

Why would one want to do this? TL;DR: To use the ENS620EXT in a local FitController.

WiFi 5 is an older standard, but it is still quite useful (not everyone needs or can take advantage of the higher speeds in the first place). Personally, I wanted something good and cheap that I could place somewhere on the back of our house and get decent WiFi coverage in the backyard (our house has foil-backed insulation in the exterior walls, which hampers the signals from our indoor APs). I don't need a lot of speed, just a solid signal for WiFi calling, streaming music and videos, the occasional video call between my kids and their grandparents to show off their new T-ball skills or what have you, etc.

The ENH1350EXT and ENS620EXT are old enough that they don't support the new Fit Controller, just the legacy EZ Master controller. But the ECW160 is part of their cloud product line and, as of early 2024, also supports use with a local Fit Controller instead of being cloud-only.

In 2023, I migrated to the EnGenius ecosystem, starting with the EZ Master controller software with two EWS377APv3 indoor APs and the ENS620EXT and ENH1350EXT APs for outdoor coverage.

Later, though, I moved to the local Fit Controller stack because EZ Master was essentially end-of-life. And in order to do that, I needed a FIT-compatible outdoor AP or two. The only one at the time was the EWS850-FIT, because the ECW line hadn't yet gained the ability to use a local controller. But the EWS850 stuff was expensive, even second hand on eBay (I did manage to acquire a non-FIT EWS850AP and convert it to the FIT variant, but that's another story). For a while I suffered with two controller stacks, FIT for the newer stuff, and an EZ Master for the outdoor APs.

Eventually, in early 2024, the ECW line gained the ability to use a local controller instead of the cloud. Somewhere in between, I had learned that the ECW160 and ENH1350EXT were the same hardware and this cross-flashing idea gradually formed in the back of my head. Eventually, a few months later, I had enough free time to start looking into it.

## UART Access

In order to perform this cross-flash, you will need to have serial (UART) access to the u-Boot bootloader on the ENS620EXT. This requires opening the ENS620EXT and soldering leads onto three pads on the underside of the PCB. Fortunately the ENS620EXT is just held together by screws (the ECW160 has highly annoying and breakable plastic clips), so it's not difficult. You will need an 8mm socket to unscrew the top antenna connectors so you can pull out the PCB (they're attached directly to the PCB; the bottom antenna connectors are attached with leads that you can just disconnect).

Here is the pinout:

(todo: insert image here)

## The Devil is in the Details

With a number of successful crossflashes with other EnGenius models under my belt, my first approach was to simply modify an ECW160 firmware image so the ENS620EXT would accept it and flash it.

This, at first glance, seemed to work. The firmware was accepted and written to the flash device, it booted fine from the new kernel image and root fs, and (after a factory reset) the web UI seemed normal (though limited, since it's the ECW line). But try as I might, I couldn't get it to register or communicate with my Fit Controller. That said, there wasn't much I could try, since the cloud communication stuff that EnGenius added to OpenWRT was pretty much a black box and provided basically no logs or other info I could use for troubleshooting.

However, I knew from tinkering with my EWS850AP that there was a special 64kb partition on the flash labeled `cert`, which held a certificate and private key used to authenticate with the EnGenius cloud.

Here's the flash layout of a stock ENS620EXT compared to the ECW160:

<table>
<tr>
<td> ENS620EXT </td> <td> ECW160 </td>
</tr>
<tr>
<td>

```console
root@ENS620EXT:~# cat /proc/mtd
dev:    size   erasesize  name
mtd0: 00040000 00010000 "0:SBL1"
mtd1: 00020000 00010000 "0:MIBIB"
mtd2: 00060000 00010000 "0:QSEE"
mtd3: 00010000 00010000 "0:CDT"
mtd4: 00010000 00010000 "0:DDRPARAMS"
mtd5: 00010000 00010000 "0:APPSBLENV"
mtd6: 00090000 00010000 "0:APPSBL"
mtd7: 00010000 00010000 "0:ART"
mtd8: 00500000 00010000 "0:HLOS"
mtd9: 018c0000 00010000 "rootfs"
mtd10: 00980000 00010000 "rootfs_data"
mtd11: 00010000 00010000 "u-boot-env"
mtd12: 000a0000 00010000 "userconfig"
```

</td>
<td>

```console
root@ECW160:~# cat /proc/mtd
dev:    size   erasesize  name
mtd0: 00040000 00010000 "0:SBL1"
mtd1: 00020000 00010000 "0:MIBIB"
mtd2: 00060000 00010000 "0:QSEE"
mtd3: 00010000 00010000 "0:CDT"
mtd4: 00010000 00010000 "0:DDRPARAMS"
mtd5: 00010000 00010000 "0:APPSBLENV"
mtd6: 00080000 00010000 "0:APPSBL"
mtd7: 00010000 00010000 "0:ART"
mtd8: 00400000 00010000 "0:HLOS"
mtd9: 014e0000 00010000 "rootfs"
mtd10: 001f0000 00010000 "rootfs_data"
mtd11: 00580000 00010000 "failsafe"
mtd12: 00010000 00010000 "failsafe_conf"
mtd13: 00010000 00010000 "cert"
```

</td>
</tr>
</table>
Notice anything? There's no `cert` partition on the ENS620EXT. I surmised that was the root of the problem, and set about trying to figure out how to put one there.

## MTD

It should be noted that, unlike hard drives and SSDs and similarly-behaved block devices, flash chips have no partition table on the flash itself (the reasoning being that flash isn't as reliable as other storage, and you *really* don't want to develop a bad block in the middle of your partition table definition). The partition layout is thusly defined "somewhere else".

On a lot of embedded devices, that "somewhere else" is the environment variables for the u-Boot bootloader, and is often passed to the Linux kernel through the `bootargs`.

## u-Boot

I attempted to change the layout of the flash and sneak in a `cert` partition through the use of bootargs, but it seems that (a) the kernel ignored the usual parameter for specifying the layout (or maybe I just didn't get the syntax of the parameter just right), and (b) the u-Boot environment didn't have anything for the layout, either.

My guess, then, that the layout was hard-coded into the custom u-Boot build used on each device (and possibly also the kernel itself). That would seem to jive with what I was seeing - each device had a slightly different version of u-Boot:

ENS620EXT:
```
U-Boot 2012.07-ENS620EXT-uboot_version:V1.0.4 [Attitude Adjustment 12.09.1,0d3fd33] (Mar 05 2021 - 11:12:06)
```

EWS160:
```
U-Boot 2012.07-ECW160-uboot_version:V1.0.2 [Attitude Adjustment 12.09.1,bb985b7] (Jul 09 2019 - 11:47:15)
```

At this point I had two ECW160 and one EWS850 APs, so I was good on outdoor coverage. Strictly speaking, I didn't *need* the ENS620EXT, so if I bricked it, no big deal. So I did what any enterprising tinkerer would do at 12:30 am, and just flashed the ECW160 bootloader onto the ENS620EXT.

In doing so, I learned a couple things:

1. The first 64kb of flash, labeled `0:SBL1` is basically a stage-1 bootloader, not u-Boot itself.
2. u-Boot is actually the 128k at `0x0000000f0000` (or mtd6, labeled `0:APPSBL` - `BL` for bootloader, I realized)
3. The u-Boot environment variables are stored on at `0x0000000e0000` (or mtd5, `0:APPSBLENV`). And you need these.

## Flashing u-Boot

### Extract Partitions from ECW160

This part is fairly straightforward. But it requires root shell access to the ECW160. I happened to already have that through the UART on mine. In some quick and dirty tests I did, I wasn't able to get a root shell on the ECW160 with the stock firmware using the same method I've used on other (older) devices, so I ended up cracking it open. YMMV (maybe if you cross-flashed it first to an ENH1350EXT, and then downgraded it to an old version, you could manage it...)

Anyway, once you have a root shell, it's easy:

```
cat /proc/mtd5 > /tmp/ecw160-mtd5.bin
cat /proc/mtd6 > /tmp/ecw160-mtd6.bin
```

Retrieve the files from the device however you wish. You may find it easiest to simply spin up the Dropbear SSH server on a non-standard port and SCP through that. This will start an SSH server on port 2022

```
root@ECW160:~# dropbear -p 2022
```

Note that newer SSH clients will by default use the SFTP subsystem for SCP commands, and that won't work with the Dropbear build on the EnGenius devices. So you'll need to use the `-O` flag to revert to the legacy behavior, e.g.:

(The stock SSH server on most EnGenius devices, espeically the ECW series, forces you into their CLI when logging in and doesn't allow for a root shell or SCP or anything else. Hence running your own instance of Dropbear.)

```
scp -O -P 2022 -o HostKeyAlgorithms=+ssh-rsa -o KexAlgorithms=+diffie-hellman-group14-sha1 admin@<ECW160-IP>:/tmp/ecw160-mtd5.bin ~/Documents/engenius/ecw160/ecw160-mtd5.bin
scp -O -P 2022 -o HostKeyAlgorithms=+ssh-rsa -o KexAlgorithms=+diffie-hellman-group14-sha1 admin@<ECW160-IP>:/tmp/ecw160-mtd6.bin ~/Documents/engenius/ecw160/ecw160-mtd6.bin
```

### Flashing Partitions to the ENS620EXT

You just need a root shell for this on the ENS620EXT. You'll need serial access for the remainder, though, so you might as well just get that set up now and use it.

First, start an SSH server on a non-standard port:

```
root@ENS620EXT:~# dropbear -p 2022
```

Then, copy the files over:

```
scp -O -P 2022 -o HostKeyAlgorithms=+ssh-rsa -o KexAlgorithms=+diffie-hellman-group14-sha1 ~/Documents/engenius/ecw160/ecw160-mtd5.bin admin@<ENS620EXT-IP>:/tmp/ecw160-mtd5.bin
scp -O -P 2022 -o HostKeyAlgorithms=+ssh-rsa -o KexAlgorithms=+diffie-hellman-group14-sha1 ~/Documents/engenius/ecw160/ecw160-mtd6.bin admin@<ENS620EXT-IP>:/tmp/ecw160-mtd6.bin
```

Now you are ready to write those files to the flash.

# THIS IS THE POINT OF NO RETURN

Well, that may be a bit over-dramatic, but after you write the new u-Boot to flash, you have a brick that **REQUIRES** using the UART console to un-brick. YOLO.

Write the flash environment configuration to flash:

```
mtd write /tmp/ecw160-mtd5.bin /dev/mtd5
```

Write the bootloader to flash:c

```
mtd write /tmp/ecw160-mtd6.bin /dev/mtd6
```

Reboot or power-cycle the AP. (If you leave it alone, it will now try to boot the kernel from the wrong flash address and crash...)

# Reloading the Kernel and Root FS Partitions

