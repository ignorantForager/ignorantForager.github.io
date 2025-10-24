Title: A Practical Approach to Finding 100GB QSFPs
Date: 2024-05-02
Category: networking
Tags: cisco,powershell,plink,qsfp

## Automating 100GB QSFP Transceiver Inventory with PowerShell

Understanding the quantity and distribution of 100GB QSFP transceivers in your data center can be essential for optimizing network performance. But how can you efficiently gather this information across multiple devices? Let me share with you a straightforward method I’ve developed using PowerShell, which you can adapt to suit your environment.

Firstly, I typically start by SSH’ing into my devices to manually gather information. This initial exploration helps me identify patterns that can be automated later. One command I’ve found to be particularly useful is `show interface transceiver`, which lists all SFP transceivers used on the device. By filtering for lines containing `40/100`, I can quickly identify 100GB QSFPs.

### PowerShell Script for Automating the Process

```powershell
# Prompt the user to enter a username and password
$username = Read-Host -Prompt "Username"
$password = Read-Host -Prompt "Password" -AsSecureString

# Convert the SecureString password into a plain text string (security risk!)
$temppass = [System.Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUnicode($password)
$password = [System.Runtime.InteropServices.Marshal]::PtrToStringUni($temppass)

# Import device list from a CSV file (expects a file named 'devices.csv' in the same directory)
$devices = Import-Csv ".\devices.csv"

# Initialize counters and a variable to store transceiver count
$totalcount = 0
$count = 1
$t = $null

# Loop through each device listed in the CSV file
foreach ($device in $devices) {
	Clear  # Clears the screen for a cleaner output
	
	# Display progress information
	Write-Host ""
	Write-Host " ------------------------" -foreground Cyan
	Write-Host " Querying device: $count of $($devices.count)" -foreground Cyan
	Write-Host " ------------------------" -foreground Cyan
	Write-Host ""

	# Test connectivity to the device using its IP address (returns $True if reachable)
	$testconnection = Test-Connection $($device.ipaddress) -Count 1 -Quiet
	
	if ($testconnection -eq $True) {
		# Attempt an SSH connection using Plink (first echo y to accept new SSH host keys)
		echo y | plink $($device.ipaddress) -ssh
		
		# Execute a command remotely to check for 40/100Gb transceivers
		$t = $(plink $($device.ipaddress) -l $username -pw $password -batch "show interface transceiver | include 40/100")
		
		# Add the count of detected transceivers to the total
		$totalcount = $totalcount + $t.count
	}
	
	# Increment the counter for device tracking
	$count++
}

# Display the total count of detected QSFP transceivers
Write-Host ""
Write-Host " Total 100GB QSFP Transceivers: $totalcount"
```

### Key Considerations

1. **Password Handling:**
    - This script converts the secure string into a regular string due to Plink’s inability to handle secure strings correctly.
    - While it prevents shoulder surfing during password entry, handling passwords as plain text, even temporarily, poses security risks.
    - Consider using SSH keys or credential vaults for improved security.

2. **Device Input:**
    - The script imports device information from a CSV file.
    - You can adapt it to read from a text file if that better suits your setup.

3. **Manual Progress Display:**
    - Instead of PowerShell’s built-in progress bar module, a manual display is used.
    - The built-in progress bar tends to drift off-screen after iterating through many devices.

4. **Plink Usage:**
    - Plink, the PuTTY CLI interface, is used for SSH access to Cisco devices.
    - It provides a convenient way to query information across multiple devices.

Feel free to tailor this script to your needs and environment. With automation, you can streamline the process of gathering network inventory data, enabling better decision-making and optimization of your data center infrastructure.

