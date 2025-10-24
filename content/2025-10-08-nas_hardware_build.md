Title: Building a 300TB NAS and the Hardware That Hated Me
Date: 2025-10-08
Category: homelab
Tags: nas, truenas, hardware, homelab, storage

## Part 1: Building a 300TB NAS and the Hardware That Hated Me

It started with an exciting vision: to build a true "endgame" home server. The goal was to consolidate my sprawling setup into a single, powerful All-in-One server. I already had the chassis, a 45Drives HL15, and the storage—fifteen 20TB Seagate drives ready to go. Now, I just needed to pick the brains of the operation.

After a bit of research, I landed on what felt like a killer combo for a TrueNAS SCALE build.

**The Final Parts List (after all my troubleshooting):**

*   **Case:** 45Drives HL15
*   **Motherboard:** Supermicro X13SAE-F
*   **CPU:** Intel Core i5-13500 (13th Gen)
*   **CPU Cooler:** Noctua NH-D9L (2x NF-A9 92mm fan)
*   **PSU:** Seasonic GX-1000
*   **Boot Drives:** 2x 1TB Samsung 990 EVO (Mirrored)
*   **RAM:** 2x Supermicro 32GB DDR5-4800 ECC UDIMM
*   **HBA:** LSI 9300-16i
*   **OS:** TrueNAS SCALE
*   **Hard Drives:** 4x 20TB Seagate Iron Wolf Pro, 11x Refurbished 20TB Seagate Exos X20
> I originally was going to build with all Seagate Iron Wolf Pros and purchased five to start. However, I soon learned that refurbished drives can be just as reliable, if not more so (as you'll see later on).

With everything ordered, I was ready for a straightforward build. What I got instead was a multi-week saga of troubleshooting.

### Chapter 1: The DOA Motherboard and RAM Fiasco

I started assembling the build, eager to get it running. The first snag hit when I tried to install the RAM. Originally, I had bought two sticks of "Samsung 32GB DDR5 ECC RDIMM." When they arrived, I realized my mistake: RDIMM ("Registered") modules are for heavy-duty enterprise servers and don't work with my consumer-grade CPU and workstation motherboard. The sticks literally wouldn't fit.

Frustrated with myself for this simple oversight, I sent them back and ordered a non-ECC kit that would work: a "Crucial Pro 96GB DDR5 RAM Kit (2x48GB)." With the new RAM installed, I finished the build. I hit the power switch. And… nothing. Not a single click, fan spin, or light.

This kicked off my first deep dive into troubleshooting. I started with the most likely culprits. First, the PSU. I unplugged the 24-pin motherboard connector, attached the PSU’s included jumper, and everything in the case (PSU fan, case fans) spun to life. So, the PSU was good. Next, I suspected a short circuit. I pulled the entire motherboard out of the case, placed it on its box, connected only the CPU, the new Crucial RAM, and the 24-pin and 8-pin power cables. I jumped the power pins with a screwdriver. Still dead. The real clue was the lack of any standby "heartbeat" LED. A server board (and especially one with IPMI) should have a light on, even when "off" and mine was completely dark. The board I bought used from eBay seemed DOA. Just to make sure, I busted out a brand new PSU that I had laying around from a previous desktop build a few years ago. I hooked this up with the same minimal components. All the same indications. No power on unless I jumped the 24-pin cable. This verified that the PSU was good. Just for good measure, I went through the motherboard manual and identified any jumpers that might be set in the wrong position and might prohibit the board from powering on. I cleared the CMOS and even replaced the CMOS battery entirely. All to no avail. The motherboard was indeed DOA. I initiated a return and refund, then ordered the same model, but this time from a third-party seller on Amazon. (The original motherboard was from a seller on eBay with a great reputation. It looks like it was an unfortunate situation and no fault of theirs. I don't blame them whatsoever).

### Chapter 2: The Zombie Board and the BIOS Mystery

The second motherboard arrived. This time, when I plugged it in, I got that beautiful little green standby light. It was alive! But when I jumped the power pins, it still refused to turn on. The board had power but was *still* not POST-ing. My first thought was a configuration issue, so I turned to the IPMI remote management. I connected it to my network, found its IP, and tried the default `admin`/`admin` credentials. They didn't work. I found a sticker on the board with the motherboards unique BMC password, but those credentials didn't work either. Supermicro does have a tool to change the BMC password or even factory reset the BMC entirely. However, it needs the system to boot in order to load a DOS image or use the UEFI shell to run the tool. As I couldn't even boot my system, I was locked out.

I ended up swapping out the RAM thinking that maybe for some reason the Crucial RAM I had purchased wasn't compatible with the setup. I ended up going with two sticks of "Supermicro 32GB DDR5-4800 ECC UDIMM". This didn't solve the issue either, unfortunately. This led me to a new theory: what if the BIOS was too old to recognize my 13th Gen CPU? The motherboard was originally released during the 12th generation series of CPUs. I did question myself on this one. I thought an incompatible CPU would still let the system power on, maybe giving a beep code or a "CPU not supported" message on the screen. I never imagined it would cause a complete failure to POST. But with all other variables exhausted, it was the only theory that made sense.

To test it, I ordered the cheapest compatible 12th Gen CPU I could find at the time, an Intel i3-12100F, to act as a "key." I swapped it in, and just like that, the server powered on and POSTed. It worked. The BIOS incompatibility was the culprit.

With the system finally booting, I updated the BIOS to the latest version. Annoyingly, even after the update, the IPMI credentials still did not work. So, I booted into the UEFI shell, ran Supermicro's IPMICFG tool to factory reset the BMC and, *finally*, I was able to log in and set a new password. After everything was verified working on my original CPU, I returned the i3-12100F.

### Chapter 3: An HBA Saga and a Bad Drive

With the server booting with the i5-13500 and proper ECC RAM, it was time for storage. I installed my HBA card from my previous server, which I had flashed to IT Mode years ago. I booted up TrueNAS, and… no drives.

After a slew of research, I learned that my "HBA" card that I had used in the past wasn't actually an HBA card at all, but rather a SAS Expander. Meant to be used *with* an HBA. My old server must have had a built-in HBA on the motherboard that I either didn't realize or completely forgot about. With this understanding, I ordered a proper, modern HBA: an LSI 9300-16i. As soon as I installed it, TrueNAS detected all 15 drives. Success!

> For structuring the storage, I opted for a single ZFS pool built from three separate, 5-drive RAIDZ2 vdevs. This specific layout, rather than one massive 15-drive vdev, offers two critical advantages for an all-in-one server. Firstly, it dramatically improves performance; since ZFS stripes data across vdevs, having three of them provides roughly triple the random I/O operations per second (IOPS), which is essential for keeping virtual machines and applications like Plex feeling responsive. Secondly, it drastically increases safety and reduces rebuild times. Each vdev is configured as RAIDZ2, meaning every 5-drive group can lose any two drives without any data loss. Should a drive fail, ZFS only needs to resilver the data within that single, smaller vdev. This process is significantly faster and puts far less stress on the remaining drives than rebuilding a giant 15-drive array, which is a crucial consideration for the long-term health of a pool built with massive 20TB drives.

Before loading any data, my first order of business was to kick off a ZFS scrub. This is ZFS's built-in data integrity check, where it systematically reads every block of data across all the drives to ensure it matches stored checksums, proactively searching for any silent corruption or hardware errors. On a new, empty pool, it should be fast, but  still take a few minutes to check all the ZFS metadata distributed across the drives. It finished in **one second** with zero errors. This was a huge red flag. It meant the scrub wasn't actually running.

This led me down yet another troubleshooting journey. The HBA, an LSI 9300-16i, was showing up as two separate controllers. Using the TrueNAS shell, I verified the firmware of the controllers using `sas3flash -listall`. This showed me both controllers and the firmware they were on: "16.00.10.00". While this was the latest firmware for the device, there is a TrueNAS specific firmware "16.00.12.00". I downloaded the TrueNAS firmware from their forums (as far as I'm aware, the TrueNAS specific firmware isn't even available on the LSI website).

> I did end up having to create a dataset in my pool as `/mnt/mainpool/temp`. I then created an SMB share so I could mount it on my computer and transfer the firmware to this dataset to use. I also use this "temporary" dataset later on as you'll see.

I changed directories to the temp dataset and used the SAS 3 Flash tool:
```
sas3flash -o -f SAS9300-16i_IT.bin
```
Then I did the listall command again, but saw that only the first controller was flashed. I tried to flash the second controller specifically with
```
sas3flash -c 1 -o -f SAS9300-16i_IT.bin
```
(the '-c 1' portion points the flash tool to the second controller). This didn't work. I then attempted using the flag "-fwall" to update the firmware on ALL controllers. That didn't work either. I was stumped. I pored over a bunch of forum posts and eventually came across one that said to use the flag `-nossid`. I attempted running this full command: 
```
sas3flash -c 1 -o -f SAS9300-16i_IT.bin -nossid
```
and it finally worked. This command essentially tells the flash tool to ignore the error it was getting about the SubSystem ID not matching. Both of the controllers were now on the latest "16.00.12.00", TrueNAS specific firmware.

I attempted to run the scrub again, but still no dice. It completed immediately with zero issues. Frustrated, I decided to run a simple stress test: write a large file and check its integrity. The write was fast, but when I ran a checksum on the file, `dmesg` lit up with "Unrecovered read error" from drive `/dev/sdj`. This was it. One of my brand new 20TB drives was faulty, and this critical hardware error was causing the ZFS scrub to abort.

To be 100% sure, I ran a SMART test on the suspect drive. It failed within five minutes and just 10% into the test. That was all the proof I needed. I purchased a new drive to get the system up and running immediately and started the RMA process for the failed one, which will soon become my first cold spare. After replacing the drive, the resilver was successful, and a new scrub ran perfectly.

> As an interesting note here, the drive that failed was one of the five original, brand new, Iron Wolf Pros that I had bought. This has definitely improved my, already good, outlook on using refurbished drives. I ended up replacing it with a refurbished Seagate Exos X20.

The hardware was, at long last, stable.

### Chapter 4: The Great Migration

With the server ready, it was time to move approximately 40TB of data from my old server. I set up a direct 10GbE link between them. I set up a network between the two using "192.168.10.2/24" on my older server and "192.168.10.3/24" on my new server. My tool of choice was `rsync`, and I included the `--checksum` flag to guarantee data integrity.

The first few small folders transferred fine. But when I started transferring my movies folder, the transfer got stuck for over an hour on "receiving incremental file list" before even starting the copy. I realized the `--checksum` flag was forcing the old server to read every single byte of data *before* the transfer. I killed the job, removed the flag and re-ran the command. It started copying almost immediately. The `rsync` tool is robust and can pick up where it left off, and on a direct, stable link, the chance of a transfer error is tiny. I decided the speed increase was worth the minuscule risk. Even then, the transfer was slow, averaging 30-50MB/s with occasional jumps over 100MB/s.

To manage this multi-day transfer, I used a crucial tool: `tmux`. It lets you run terminal sessions that persist even if you get disconnected. My initial setup was simple:
1.  Start a session: `tmux`
2.  Elevate to root: `sudo -i`
3.  Start the copy using the command:
    ```
    rsync -rltvhP root@192.168.10.2:/mnt/Zenodotus/Media/movies/ /mnt/mainpool/media/movies
    ```
4.  Detach, leaving the job running: 'Ctrl+b, d'.

My movie folder transferred about 6.7TB in about 48 hours. Not great. I moved ahead with copying my television folder, knowing it would take a significant amount of time to fully transfer. It was about a quarter of the way through copying my television folder that I thought about updating my network settings on the direct link to use an MTU of 9000 (Jumbo Frames). Since it was a direct link, there was no risk of dropped packets that can happen on a switched network and it had the possibility of increasing the transfer speed. Unfortunately that didn't increase the speed at all. The only explanation left was my old server's fragmented ZFS pool as the bottleneck and I couldn't think of anything else to increase the speed. At least on the hardware side.

About halfway through copying my television folder, I did decide to try and speed things up by splitting the transfer into two parallel `rsync` jobs. The way I did this was to create two text files with half of the remaining folders in one text file and the rest in the second text file. Then I would start the rsync job again, but this time point the source at these files. Managing this in `tmux` was easy: I created a second window (Ctrl+b, c) for the second `rsync` job. I could then switch between them with 'Ctrl+b, 0' and 'Ctrl+b, 1'. In the first window, I ran the command:
```
rsync -rltvhP --files-from=/mnt/mainpool/temp/tv-list-1.txt root@192.168.10.2:/mnt/Zenodotus/Media/Television/ /mnt/mainpool/media/television/
```
In the second window:
```
rsync -rltvhP --files-from=/mnt/mainpool/temp/tv-list-2.txt root@192.168.10.2:/mnt/Zenodotus/Media/Television/ /mnt/mainpool/media/television/
```
To my surprise, neither job slowed down and I was now getting nearly double the total throughput.

It was about this time that I wished I was capturing stats. I realized the default `tmux` history was only 2,000 lines, which wasn't enough to capture the full log. While the jobs were running, I increased the buffer:
`set-option -g history-limit 100000`. This wouldn't recover the old history, but it ensured I could capture everything from then on. If I were to do this again, I’d set this at the very beginning, before I ran the initial rsync commands. Once a job finished, I could save the log with:
```
tmux capture-pane -pS -100000 -t 0:0 > /mnt/mainpool/temp/rsync_job1_log.txt
```
(the `-t 0:0` targets the first session, first window of `tmux`. For the second window it would be `-t 0:1`). I plan on going through and attempting to get any stats I can (e.g. average size of files transferred, average transfer speed, and average transfer time per file). It's not needed now that the transfer is fully complete, but it'd be nice to reference and see.
>Ideally I'd love to create something with those stats that could make /r/dataisbeautiful proud.

Once this week-long migration was finished, I went through and ran the original rsync command again on both movies and tv shows in order to capture anything I missed from the split rsync jobs or any new files that appeared while running the jobs. There were only a few files and took less than an hour.

### To Be Continued…

This build fought me to the very end. When I finally looked at the stable, running server, I realized that every single component (the motherboard, PSU, CPU, RAM, HBA, and even a hard drive) had been swapped out at least once. It was a true Server of Theseus, if you will. Rebuilt piece by piece on its journey to completion.

After a journey that tested every bit of my patience, the physical build is complete. The hardware is stable and the data is home, but the project is only half done. In Part 2, I'll tackle the software: installing the full app stack, migrating my Plex metadata, and finally bringing this 300TB beast fully to life.
