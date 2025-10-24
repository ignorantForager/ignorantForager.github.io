Title: Fixing Plex Docker Failures - Resolving Disk Space Issues and Optimizing Storage
Date: 2025-02-11
Category: homelab
Tags: homelab, plex, docker, storage

## Introduction
Managing disk space efficiently is crucial for maintaining a stable Plex Media Server, especially when running it as a Docker container on an Ubuntu Live Server VM. Recently, I encountered a critical issue where Plex failed to start and transcode media due to insufficient disk space. Additionally, system updates were blocked due to a full root partition. This post details the root cause analysis, troubleshooting steps, and resolution strategies, including mounting a secondary drive for Plex storage. By following these steps, you can prevent similar issues and optimize your Plex server’s performance.

---

### **Issue Summary:**
Plex Media Server, running as a Docker container on an Ubuntu Live Server VM (hosted on Proxmox), was failing to start properly. Additionally, Plex playback issues occurred when attempting to transcode media, displaying an error stating, "There's not enough space to convert this item." Furthermore, attempting to update Ubuntu (`sudo apt update && sudo apt upgrade`) resulted in the following error:

```
You don't have enough free space in /var/cache/apt/archives/.
```

#### **Error Messages from Plex Logs:**
Upon examining the Plex logs, the following critical error was identified:

```
Starting Plex Media Server. . . (you can ignore the libusb_init error)
libc++abi: terminating with uncaught exception of type std::runtime_error: Codecs: Initialize: 'boost::filesystem::create_directories: No space left on device [system:28]: "/config/Library/Application Support/Plex Media Server/Codecs/e613bce-97f23d579c1001d8e9cc0d2e-linux-x86_64", "/config/Library/Application Support/Plex Media Server/Codecs/e613bce-97f23d579c1001d8e9cc0d2e-linux-x86_64"'
****** PLEX MEDIA SERVER CRASHED, CRASH REPORT WRITTEN: /config/Library/Application Support/Plex Media Server/Crash Reports/
```

### **Root Cause Analysis:**
1. **Root Filesystem Full:**
   - Running `df -h` revealed that the root partition (`/dev/mapper/ubuntu--vg-ubuntu--lv`) was **100% full**, preventing Plex from writing necessary codec files and causing transcode failures.
   - The Plex container's `/config` directory was mapped to `/var/plex/config`, which resided on the full root partition.

2. **Newly Added 2TB Drive Not Utilized:**
   - The Proxmox VM had a secondary **2TB drive** (`/dev/sdb`), but it was not formatted, mounted, or used.
   - Plex was relying on the small root partition for cache, transcoding, and metadata storage, causing failures.

3. **Docker Storage Usage:**
   - Running `docker system df` showed that there were no unused images or containers, so `docker system prune` was not necessary.

### **Resolution Steps:**
To resolve the issue, we took the following steps:

#### **Step 1: Free Up Space on Root Filesystem**
1. **Clean APT cache:**
   ```bash
   sudo apt clean
   ```
2. **Remove old logs:**
   ```bash
   sudo journalctl --vacuum-time=3d
   sudo rm -rf /var/log/*.gz /var/log/*.1
   ```
3. **Identify and remove large unnecessary files:**
   ```bash
   sudo du -ahx / | sort -rh | head -20
   ```

#### **Step 2: Mount the 2TB Drive and Move Plex Config and Transcoding Data**
1. **Format the 2TB disk (`/dev/sdb`):**
   ```bash
   sudo mkfs.ext4 /dev/sdb
   ```
2. **Create a mount point:**
   ```bash
   sudo mkdir -p /mnt/plex_config
   ```
3. **Mount the new drive:**
   ```bash
   sudo mount /dev/sdb /mnt/plex_config
   ```
4. **Move Plex configuration and transcode directories to the new drive:**
   ```bash
   docker stop plex
   sudo mv /var/plex/config /mnt/plex_config/
   sudo mv /var/plex/transcode /mnt/plex_config/
   ```
5. **Ensure correct permissions:**
   ```bash
   sudo chown -R administrator:administrator /mnt/plex_config
   ```
6. **Update Docker container settings to use the new location:**
   - Modify `docker-compose.yml` or the `docker run` command to reflect the new paths:
     ```bash
     -v /mnt/plex_config/config:/config
     -v /mnt/plex_config/transcode:/transcode
     ```
7. **Persist the mount by adding it to `/etc/fstab`:**
   ```bash
   /dev/sdb /mnt/plex_config ext4 defaults 0 2
   ```
8. **Reboot and verify the mount persists:**
   ```bash
   sudo reboot
   ```

#### **Step 3: Restart Plex and Verify Functionality**
1. **Start the Plex container:**
   ```bash
   docker start plex
   ```
2. **Verify Plex is running without errors:**
   ```bash
   docker logs plex -f
   ```
3. **Attempt media playback and confirm that transcoding works without errors.**

### **Final Outcome:**
✅ Plex no longer crashes due to disk space issues.  
✅ APT updates and system operations work without errors.  
✅ Transcoding and playback are stable.  
✅ The root filesystem has ample free space, preventing future failures.  

### **Preventive Measures for Future Issues:**
1. **Monitor disk usage regularly:**
   ```bash
   df -h
   docker system df
   ```
2. **Periodically clean up old logs and temporary files.**
3. **Ensure new storage devices are properly formatted, mounted, and utilized as needed.**


