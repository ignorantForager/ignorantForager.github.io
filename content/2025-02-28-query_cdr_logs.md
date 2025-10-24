Title: Querying Service Desk Call Metrics with Python
Date: 2025-02-28
Category: networking
Tags: cisco,cucm,sql,api,python

# Extracting Metrics from Cisco Unified Call Manager (CUCM)

## Background

About a year and a half ago, I was asked to find a way to extract metrics from Cisco Unified Call Manager (CUCM) to support our Service Desk team. They needed basic insights:
- How many calls were made to the service desk
- Who answered the calls
- How many calls went to voicemail

Over time, additional requests came in, such as tracking evening-hour calls to determine if extra support was needed.

## Initial Challenges

After some research, I found that CUCM didn’t provide an easy way to access this information through its GUI. Eventually, I discovered the Call Detail Record (CDR) page, but it had significant limitations:
- It only allowed me to export 30 days of logs manually as a CSV file.
- There was no built-in automation for data retrieval.
- Each CSV contained tens of thousands of rows of call data.

The challenge then became parsing through it to extract meaningful information.

## Key CDR Fields

I won’t go into all the details of the CDR fields—it’s a massive dataset—but a few key fields for my purposes were:

- **`dateTimeOrigination`**: The date and time when the user goes off the hook or when an H.323 SETUP message is received for an incoming call.
- **`originalCalledPartyPattern`**: The original call destination before any translations are applied.
- **`finalCalledPartyPattern`**: The final call destination before it is answered or ringing ends.
- **`destDeviceName`**: The name of the destination device.

For a more comprehensive breakdown of CDR fields, I found this resource invaluable: [Understanding CUCM CDR Files](https://www.voipdetective.com/unified-communications/reading-and-understanding-cucm-cdr-files/). Additionally, here’s an official Cisco link with CDR codes: [Cisco CDR Codes](https://www.cisco.com/c/en/us/td/docs/voice_ip_comm/cucm/service/12_5_1/cdrdef/cucm_b_cdr-admin-guide-1251/cucm_b_cdr-admin-guide-1251_chapter_0110.html).

## Initial Solution: PowerShell Script

With this information in hand, I needed a way to process it efficiently. At the time, I relied on PowerShell for automation, so I wrote a script to:
1. Parse the CDR.
2. Filter for Help Desk calls.
3. Extract the requested details.

After parsing the data, I would then put all of this data neatly into an excel file with PivotTables and PivotCharts. Then sent the information out to the parties requesting the information.

### Issues with PowerShell Approach

However, the PowerShell solution had major flaws:
- **Not dynamic**: I had to manually list all help desk phones by device name.
- **Required manual updates**: Any staff changes meant manually updating the script.
- **Inefficient and slow**.

For the past year and a half, I dealt with these limitations. But this week, I decided to fix them.

## Improved Solution: Python Script

Below is a Python script that replicates the PowerShell functionality with crucial improvements, mainly minimizing manual input.

I achieved this using the CUCM **SOAP/AXL API**. (If you're unfamiliar with it, I wrote a [previous post](https://ignorantforager.com/posts/query-cucm-sql/) about it. While it’s not exhaustive, it’s a good starting point if you're interested.)

### Key Improvements

- **Dynamic device retrieval**: A custom SQL query now fetches the current list of Help Desk devices from CUCM, eliminating the need for manual updates.
- **Device correlation**: Each device is linked with its description and primary phone number using a non-SQL query to CUCM.

```python
import pandas as pd
import requests
from lxml import etree
import warnings
from datetime import datetime
import pytz

#### Initialize CUCM settings
url = "192.168.1.1/axl" # Adjust URL for CUCM Publisher IP Address
headers = {
    'Authorization': 'Basic <BASIC AUTH HERE>', # Replace with actual authentication
    'Content-Type': 'text/plain',
    'Cookie': '<COOKIE HERE>' # Replace with actual cookie if required
}
warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestsWarning) # Suppress SSL warnings

# Define XML namespace for parsing responses
ns = {
    "soapenv": "http://schemas.xmlsoap.org/soap/envelope/",
    "ns": "http://www.cisco.com/AXL/API/14.0"
}

# Define constants
helpDesk = "5551234" # Help desk phone number
voicemail_server = "VOICEMAIL_SERVER" # Voicemail server identifier

#### Read CDR (Call Detail Records) from CSV file
cdr_df = pd.read_csv('cdr.csv', low_memory=False)

#### Setting time zones and converting timestamps
utc_zone = pytz.utc
eastern_zone = pytz.timezone('America/New_York')

# Convert start time to Eastern Time
startTime = pd.to_datetime(cdr_df['dateTimeOrigination'].iloc[0], unit='s')
startTime = startTime.replace(tzinfo=utc_zone).astimezone(eastern_zone)
startTime = startTime.strftime("%Y-%m-%d %H:%M:%S")

# Convert end time to Eastern Time
endTime = pd.to_datetime(cdr_df['dateTimeOrigination'].iloc[-1], unit='s')
endTime = endTime.replace(tzinfo=utc_zone).astimezone(eastern_zone)
endTime = endTime.strftime("%Y-%m-%d %H:%M:%S")

#### Retrieve help desk phone devices via AXL API (replace the fknumplan id with the one specific to the help desk line)
payload = """
    <soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:ns=\"http://www.cisco.com/AXL/API/14.0\">
        <soapenv:Header />
        <soapenv:Body>
            <ns:executeSQLQuery>
                <sql>
                    SELECT d.name, d.description
                    FROM devicenumplanmap as dnpm
                    INNER JOIN device AS d ON dnpm.fkdevice = d.pkid
                    WHERE dnpm.fknumplan = 'c3f97eb6-aeae-280d-1aaf-9d2c47528011'
                </sql>
            </ns:executeSQLQuery>
        </soapenv:Body>
    </soapenv:Envelope>
"""
response = requests.request("POST", url, headers=headers, data=payload, verify=False)
responseText = response.text.encode('utf-8')
root = etree.fromstring(responseText)

# Parse device names and descriptions from XML response
device_names = root.xpath("//ns:executeSQLQueryResponse/return/row/name", namespace=ns)
descriptions = root.xpath("//ns:executeSQLQueryResponse/return/row/description", namespace=ns)
phones = {device_name.text: description.text for device_name, description in zip(device_names, descriptions)}

#### Sort calls into different categories
helpDeskCalls = cdr_df[cdr_df['originalCalledPartyPattern'] == helpDesk].copy()
helpDeskAnswered = helpDeskCalls[helpDeskCalls['finalCalledPartyPattern'] == helpDesk]

# Identify calls that reached voicemail
voicemailCalls = helpDeskCalls[helpDeskCalls['finalCalledPartyPattern'] == '8888'].copy()
voicemailCalls['dateTimeOrigination'] = pd.to_datetime(voicemailCalls['dateTimeOrigination'], unit='s', utc=True)
voicemailCalls['dateTimeEastern'] = voicemailCalls['dateTimeOrigination'].dt.tz_convert(eastern_zone)

# Convert call timestamps
helpDeskCalls['dateTimeOrigination'] = pd.to_datetime(helpDeskCalls['dateTimeOrigination'], unit='s', utc=True)
helpDeskCalls['dateTimeEastern'] = helpDeskCalls['dateTimeOrigination'].dt.tz_convert(eastern_zone)

# Identify calls made between 5 PM and 8 PM
eveningCalls = helpDeskCalls[
    (helpDeskCalls['dateTimeEastern'].dt.hour >= 17) &
    (helpDeskCalls['dateTimeEastern'].dt.hour < 20)
].copy()

#### Count calls per device
calling_numbers = helpDeskCalls['destDeviceName']
call_counts = calling_numbers.value_counts().reset_index()
call_counts.columns = ['DeviceName', 'CallCount']
call_counts['Description'] = call_counts['DeviceName'].map(phones)
call_counts.loc[call_counts['DeviceName'] == voicemail_server, 'Description'] = "Voicemail"
call_counts['Description'] = call_counts['Description'].fillna("Unknown")

#### Retrieve phone numbers for devices using AXL API
for index, row in call_counts.iterrows():
    device = row['DeviceName']
    if device == voicemail_server:
        call_counts.loc[index, 'PhoneNumber'] = "8888"
        continue
    payload = f"""
        <soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:ns=\"http://www.cisco.com/AXL/API/14.0\">
            <soapenv:Header />
            <soapenv:Body>
                <ns:getPhone>
                    <name>{device}</name>
                </ns:getPhone>
            </soapenv:Body>
        </soapenv:Envelope>
    """
    response = requests.request("POST", url, headers=headers, data=payload, verify=False)
    responseText = response.text.encode("utf-8")
    root = etree.fromstring(responseText)
    phone_numbers = root.xpath("//ns:getPhoneResponse/return/phone/lines/line/dirn/pattern", namespaces=ns)
    phone_number = phone_numbers[0].text if phone_numbers else "Unknown"
    call_counts.loc[index, 'PhoneNumber'] = phone_number

# Organize call counts data
call_counts = call_counts.reindex(columns=['PhoneNumber', 'Description', 'DeviceName', 'CallCount'])
call_counts = call_counts.sort_values(by='PhoneNumber', ascending=True)

#### Output evening and voicemail calls to text files
evening_calls_text = eveningCalls[['dateTimeEastern']].to_string(index=False, header=False)
with open('evening_calls.txt', 'w') as file:
    file.write(evening_calls_text)

voicemail_calls_text = voicemailCalls[['dateTimeEastern']].to_string(index=False, headers=False)
with open('voicemail_calls.txt', 'w') as file:
    file.write(voicemail_calls_text)

#### Print summary information
print("\n---------------------------")
print(f"Start Time: {startTime} ET")
print(f"End Time: {endTime} ET")
print("---------------------------")
print(f"Total Calls: {len(cdr_df)}")
print(f"Total Help Desk Calls: {len(helpDeskCalls)}")
print(f"Total Help Desk Voicemails: {len(voicemailCalls)}")
print(f"Total 5-8 Calls made: {len(eveningCalls)}")
print("---------------------------")
print(call_counts)
print("---------------------------\n")

```

## Remaining Challenges

This solution is about **75% automated** (98.7% of all stats are made up, this one included). The biggest remaining manual task is **downloading the CSV file**. Additionally, I still **import the data into Excel** for visualization. Though I know Python has libraries for this, I lack the access to Python’s visualization tools, which is an unfortunate limitation for now.

## Conclusion

Overall, this approach is a significant improvement over my previous workflow, making Service Desk call metrics tracking much more efficient.

